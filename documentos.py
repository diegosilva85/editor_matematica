"""Formato versionado para reabrir as páginas exportadas pelo aplicativo."""
import json
import math
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

FORMATO='criador-de-graficos'
LIMITES={1:(15,3),2:(10,2),3:(15,3),4:(12,3),5:(8,2),6:(12,2)}


def dados_documento(paginas):
    return {'formato':FORMATO,'versao':1,'paginas':[
        {'aba':grau,'titulo':titulo,'colunas':colunas,'itens':[asdict(item) for item in itens]}
        for grau,itens,colunas,titulo in paginas]}


def validar_documento(dados):
    from app_graficos import Funcao
    from parabolas import Parabola
    from triangulos import Triangulo
    from solidos import Solido
    from exponenciais import Exponencial
    from progressao import Progressao
    classes={1:Funcao,2:Parabola,3:Triangulo,4:Solido,5:Exponencial,6:Progressao}
    def numero(v):
        return type(v) in (int,float) and math.isfinite(v)
    try:
        if not isinstance(dados,dict) or dados.get('formato')!=FORMATO or type(dados.get('versao')) is not int or dados['versao']!=1:
            raise ValueError('Formato ou versão de JSON não suportado.')
        pages=dados['paginas']
        if not isinstance(pages,list) or not 1<=len(pages)<=6:
            raise ValueError('O documento deve conter de 1 a 6 abas.')
        usados=set(); result=[]
        for page in pages:
            grau=page['aba']; cols=page['colunas']; titulo=page['titulo']; items=page['itens']
            if type(grau) is not int or grau not in classes or grau in usados:
                raise ValueError('Aba desconhecida ou repetida no documento.')
            usados.add(grau)
            limite,maxcols=LIMITES[grau]
            if type(cols) is not int or not 1<=cols<=maxcols or not isinstance(items,list) or not 1<=len(items)<=limite:
                raise ValueError('Quantidade de itens ou colunas inválida.')
            if not isinstance(titulo,str) or len(titulo)>1000: raise ValueError('Título inválido.')
            instancias=[]
            for item in items:
                if not isinstance(item,dict): raise ValueError('Item inválido.')
                for k,v in item.items():
                    if k=='xs':
                        if not isinstance(v,list) or len(v)>8 or not all(numero(x) for x in v): raise ValueError('Lista de pontos inválida.')
                    elif k=='valores':
                        if not isinstance(v,dict) or not all(isinstance(key,str) and isinstance(val,str) and len(val)<=40 for key,val in v.items()): raise ValueError('Medidas inválidas.')
                    elif k in ('raizes','intercepto','marcar_xv','marcar_yv','pedir_raizes','pedir_vertice','incluir_imagem'):
                        if type(v) is not bool: raise ValueError('Opção de marcação inválida.')
                    elif k in ('a','b','c','angulo') and grau!=5:
                        if not numero(v): raise ValueError('Coeficiente ou ângulo inválido.')
                    elif not isinstance(v,str) or len(v)>1000: raise ValueError('Campo textual inválido.')
                obj=classes[grau](**item)
                obj.dados() if grau==2 else obj.validar()
                instancias.append(obj)
            result.append((grau,instancias,cols,titulo))
        return result
    except (KeyError,TypeError,OverflowError,AttributeError) as e:
        raise ValueError('JSON incompleto ou com campos inválidos.') from e


def carregar_documento(caminho):
    path=Path(caminho)
    if path.stat().st_size>2_000_000: raise ValueError('JSON muito grande (máximo de 2 MB).')
    try:
        dados=json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError,UnicodeError) as e:
        raise ValueError('Não foi possível ler o JSON. Verifique o arquivo.') from e
    return validar_documento(dados)


def publicar_par(pdf_temporario,destino,paginas,*,dados_prontos=None):
    """Prepara o JSON antes de substituir os arquivos; restaura o par se falhar."""
    destino=Path(destino); json_path=destino.with_suffix('.json')
    if destino==json_path: raise ValueError('O destino do PDF deve ter extensão .pdf.')
    dados=dados_documento(paginas) if dados_prontos is None else dados_prontos
    if dados_prontos is None: validar_documento(dados)
    else:
        from listas import validar_lista
        validar_lista(dados)
    texto=json.dumps(dados,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    fd,tmp=tempfile.mkstemp(suffix='.json',dir=destino.parent)
    backups={}; alterados=[]
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream: stream.write(texto)
        for path in (destino,json_path):
            if path.exists():
                if not path.is_file(): raise ValueError(f'O destino não é um arquivo: {path}')
                backups[path]=path.read_bytes()
        os.replace(tmp,json_path); alterados.append(json_path)
        os.replace(pdf_temporario,destino); alterados.append(destino)
    except Exception:
        for path in reversed(alterados):
            if path in backups: path.write_bytes(backups[path])
            else: path.unlink(missing_ok=True)
        raise
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return json_path
