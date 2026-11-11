"""Acervo local do Enem: PDFs oficiais, recortes e filtros sem serviços externos."""
from pathlib import Path
import hashlib
import json
import os
import re
import tempfile
import threading
import unicodedata
from urllib.parse import urlparse
from urllib.request import Request,urlopen

RAIZ=Path(__file__).resolve().parent
ASSETS=RAIZ/'assets'/'enem'
DADOS=RAIZ/'acervo_enem'
PDF_LOCK=threading.RLock()


def salvar_json(path,dados):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,nome=tempfile.mkstemp(dir=path.parent,suffix='.tmp')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as out:
            json.dump(dados,out,ensure_ascii=False,indent=2);out.write('\n')
        os.replace(nome,path)
    finally:
        if os.path.exists(nome):os.unlink(nome)


def caminho_pdf(prova,pasta=DADOS):
    nome=prova['arquivo']
    if Path(nome).name!=nome or not nome.endswith('.pdf'):raise ValueError('Nome de PDF inválido.')
    return Path(pasta)/'pdfs'/nome


def baixar_prova(prova,pasta=DADOS):
    """Download atômico, validado por assinatura e, se disponível, SHA-256."""
    path=caminho_pdf(prova,pasta)
    esperado=prova.get('sha256')
    if path.exists() and path.read_bytes().startswith(b'%PDF-'):
        if not esperado or hashlib.sha256(path.read_bytes()).hexdigest()==esperado:return path
    url=prova['url'];parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.hostname!='download.inep.gov.br':
        raise ValueError('O download deve vir do domínio oficial do Inep.')
    req=Request(url,headers={'User-Agent':'EditorMatematica/1.0'})
    with urlopen(req,timeout=90) as response:
        if urlparse(response.url).hostname!='download.inep.gov.br':raise ValueError('Redirecionamento inesperado.')
        data=response.read(60*1024*1024+1)
    if len(data)>60*1024*1024 or not data.startswith(b'%PDF-'):raise ValueError('Arquivo recebido não é um PDF válido ou excede 60 MB.')
    if esperado and hashlib.sha256(data).hexdigest()!=esperado:raise ValueError('O PDF mudou no Inep; atualize o índice antes de utilizá-lo.')
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,nome=tempfile.mkstemp(dir=path.parent,suffix='.part')
    try:
        with os.fdopen(fd,'wb') as out:out.write(data)
        os.replace(nome,path)
    finally:
        if os.path.exists(nome):os.unlink(nome)
    return path


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD',texto.casefold()) if not unicodedata.combining(c))


# Sugestões auditáveis, não classificações oficiais do Inep.
REGRAS={
 'Função de 1º grau':r'funcao (?:afim|linear)|primeiro grau|1.? grau|coeficiente angular|custo fixo|y\s*=\s*\d*\s*x\s*[+-]',
 'Função de 2º grau':r'parabol|quadratic|segundo grau|2.? grau|vertice.*funcao|\b[xyht]\s*[2²]\s*[+−–-]',
 'Função exponencial e logaritmos':r'exponencia|logarit|meia.vida|log\s*\(|(?:dobra|duplica|triplica) a cada',
 'Progressões':r'progressao|sequencia.*(?:termos|razao)|termos.*sequencia',
 'Trigonometria':r'sen\s*\(|cos\s*\(|tangente|seno|cosseno|trigonomet',
 'Geometria espacial':r'volume|cilindr|esfer|piramid|prisma|cubo|cubico|cone\b|conico|poliedr|paralelepiped',
 'Geometria plana':r'area|perimetro|triangul|retangul|circunferen|circulo|losango|trapezio|hexagon|quadrado|poligono',
 'Geometria analítica':r'plano cartesiano|coordenadas|equacao da reta|abscissa|ordenada',
 'Estatística':r'\bmediana\b|\bmoda\b|\bmedia\b|desvio|variancia|frequencia|histograma',
 'Probabilidade':r'probabilidade|aleatoriamente|ao acaso|sorteio',
 'Análise combinatória':r'combinac|permutac|anagram|maneiras distintas|formas distintas|possibilidades|senhas|senha',
 'Porcentagem e matemática financeira':r'porcent|percent|juros|desconto|taxa.*(?:mensal|anual)|%',
 'Razão, proporção e escalas':r'proporc|escala|razao entre|regra de tres|diretamente|inversamente|velocidade media|densidade',
 'Grandezas e unidades':r'unidade de medida|conversao|quilomet|mililit|milimet|litros|metros cubicos',
 'Álgebra e sistemas':r'sistema de equac|incognita|equacao|inequacao',
 'Gráficos e tabelas':r'grafico|tabela|diagrama',
}
CONTEUDOS=tuple(REGRAS)+('Matemática básica / a revisar',)


def classificar(texto):
    t=' '.join(normalizar(texto).split())
    tags=[k for k,pattern in REGRAS.items() if re.search(pattern,t)]
    if 'Função de 2º grau' in tags and 'Estatística' in tags and not re.search(r'mediana|moda\b|media (?:aritmetica|ponderada|d[aeo]s?)\b|desvio|variancia|frequencia',t):
        tags.remove('Estatística')
    if texto_limitado(texto):tags.append(CONTEUDOS[-1])
    return tags or [CONTEUDOS[-1]]


def texto_limitado(texto):
    # Alguns originais têm fontes sem mapeamento Unicode; as imagens são íntegras.
    return sum(ord(c)<32 and c not in '\n\r\t' for c in texto)>5


def carregar_acervo(pasta=DADOS):
    fontes=json.loads((ASSETS/'fontes.json').read_text(encoding='utf-8'))
    index=ASSETS/'indice.json'
    questoes=json.loads(index.read_text(encoding='utf-8'))['questoes'] if index.exists() else []
    gabaritos_path=ASSETS/'gabaritos.json'
    gabaritos=json.loads(gabaritos_path.read_text(encoding='utf-8'))['provas'] if gabaritos_path.exists() else {}
    ajustes=Path(pasta)/'conteudos.json'
    edits=json.loads(ajustes.read_text(encoding='utf-8')) if ajustes.exists() else {}
    for q in questoes:
        oficial=gabaritos.get(q['prova'],{})
        resposta=oficial.get('respostas',{}).get(str(q['numero']))
        q['gabarito']=resposta if resposta in ('A','B','C','D','E','Anulada') else None
        q['gabarito_url']=oficial.get('url','') if q['gabarito'] else ''
        if q['id'] in edits:
            q['conteudos']=[t for t in edits[q['id']] if t in CONTEUDOS] or [CONTEUDOS[-1]]
            q['revisado']=True
    return fontes,questoes


def rotulo_gabarito(questao):
    return 'Gabarito oficial: '+(questao.get('gabarito') or 'Não disponível')


def salvar_conteudos(identificador,conteudos,pasta=DADOS):
    if not conteudos or any(c not in CONTEUDOS for c in conteudos):raise ValueError('Selecione um conteúdo válido.')
    path=Path(pasta)/'conteudos.json'
    dados=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    dados[identificador]=list(dict.fromkeys(conteudos));salvar_json(path,dados)


def filtrar(questoes,ano='',prova='',conteudo='',busca=''):
    busca=normalizar(busca.strip())
    return [q for q in questoes if (not ano or str(q['ano'])==str(ano))
            and (not prova or q['prova']==prova)
            and (not conteudo or conteudo in q['conteudos'])
            and (not busca or busca in normalizar(str(q['numero'])+' '+q['texto']))]


def imagem_questao(q,prova,largura=700,pasta=DADOS,pagina_inteira=False):
    from PIL import Image
    import pypdfium2 as pdfium
    path=caminho_pdf(prova,pasta)
    if not path.exists():raise FileNotFoundError('Baixe esta prova para visualizar as questões.')
    imagens=[]
    with PDF_LOCK,pdfium.PdfDocument(path) as doc:
        for trecho in q['recortes']:
            page=doc[trecho['pagina']];w,h=page.get_size()
            left,bottom,right,top=(0,0,w,h) if pagina_inteira else trecho['bbox']
            scale=min(3,largura/(right-left))
            bitmap=page.render(scale=scale,crop=(left,bottom,w-right,h-top))
            try:im=bitmap.to_pil().convert('RGB').copy();imagens.append(im)
            finally:bitmap.close();page.close()
            if pagina_inteira:break
    width=max(im.width for im in imagens);height=sum(im.height for im in imagens)+12*(len(imagens)-1)
    out=Image.new('RGB',(width,height),'white');y=0
    for im in imagens:out.paste(im,(0,y));y+=im.height+12
    return out


def indexar_prova(prova,path):
    """Detecta cabeçalhos e separa colunas, preservando continuações de questões."""
    import pypdfium2 as pdfium
    with PDF_LOCK,pdfium.PdfDocument(path) as doc:
        paginas={};cabecalhos=[]
        for i in range(len(doc)):
            page=doc[i];w,h=page.get_size();cx,cy,_,_=page.get_bbox()
            text=page.get_textpage();finder=text.search('QUEST')
            while True:
                match=finder.get_next()
                if match is None:break
                start,count=match;fragment=text.get_text_range(start,min(28,text.count_chars()-start))
                m=re.match(r'QUEST\s*Ã\s*O\s*(\d{3})\b',fragment,re.I)
                if not m or not 136<=int(m[1])<=180:continue
                x0,y0,x1,y1=text.get_charbox(start)
                # Referências no texto não são títulos: títulos iniciam à esquerda da coluna.
                x=x0-cx;y=y1-cy
                if not (10<x<w*.18 or w*.48<x<w*.65):continue
                cabecalhos.append({'numero':int(m[1]),'pagina':i,'coluna':int(x>w/2),'x':x,'top':y+5})
            rects=[]
            for n in range(text.count_rects()):
                l,b,r,t=text.get_rect(n);rects.append((l-cx,b-cy,r-cx,t-cy))
            fundo=32
            footer=text.search('CADERNO');match=footer.get_next()
            while match:
                _,b,_,t=text.get_charbox(match[0]);t-=cy
                if t<h*.10:fundo=max(fundo,t+7)
                match=footer.get_next()
            footer.close()
            paginas[i]={'w':w,'h':h,'cx':cx,'cy':cy,'rects':rects,'fundo':fundo}
            finder.close();text.close();page.close()
        if len(cabecalhos)!=45 or {c['numero'] for c in cabecalhos}!=set(range(136,181)):
            raise ValueError(f"{prova['id']}: esperados 45 cabeçalhos únicos; encontrados {len(cabecalhos)}. Revise o PDF.")
        passo=263 if prova['ano']>=2025 else None
        for i,info in paginas.items():
            heads=[c for c in cabecalhos if c['pagina']==i]
            xs=sorted({round(c['x'],1) for c in heads})
            if xs and xs[-1]-xs[0]>info['w']*.3:passo=xs[-1]-xs[0];break
        passo=passo or 260
        unidades=[]
        primeira=min(c['pagina'] for c in cabecalhos);ultima=max(c['pagina'] for c in cabecalhos)
        for i in range(primeira,ultima+1):
            info=paginas[i];w,h=info['w'],info['h'];heads=[c for c in cabecalhos if c['pagina']==i]
            topo=max([c['top'] for c in heads] or [h-60])
            # Linhas de texto cruzando o centro indicam uma página de coluna única.
            inteira=any(l<w/2-60 and r>w/2+60 and t-b>4 and info['fundo']+20<b<t<topo-8
                        for l,b,r,t in info['rects'])
            xs=[c['x'] for c in heads if c['coluna']==0]
            x=min(xs) if xs else min(c['x'] for c in cabecalhos if c['coluna']==0)
            divisor=x+passo-6
            info['inteira']=inteira;info['limites']=[(max(0,x-4),min(w,x+2*passo-4))] if inteira else [
                (max(0,x-4),divisor-1),(divisor+1,min(w,x+2*passo-4))]
            for c in heads:c['coluna']=0 if inteira else int(c['x']>divisor)
            unidades.extend((i,col) for col in range(len(info['limites'])))
        cabecalhos.sort(key=lambda c:(c['pagina'],c['coluna'],-c['top']))
        if [c['numero'] for c in cabecalhos]!=list(range(136,181)):
            raise ValueError(f"{prova['id']}: ordem de leitura inesperada; é necessária revisão.")
        distancia_topo=min(paginas[c['pagina']]['h']-c['top'] for c in cabecalhos)
        questoes=[]
        for pos,c in enumerate(cabecalhos):
            seguinte=cabecalhos[pos+1] if pos+1<len(cabecalhos) else None
            trechos=[];textos=[]
            inicio=unidades.index((c['pagina'],c['coluna']))
            fim=unidades.index((seguinte['pagina'],seguinte['coluna'])) if seguinte else len(unidades)-1
            for un in range(inicio,fim+1):
                p,col=unidades[un];info=paginas[p]
                w,h,cx,cy=(info[k] for k in ('w','h','cx','cy'))
                topo=c['top'] if un==inicio else h-distancia_topo
                mesmo=seguinte and (p,col)==(seguinte['pagina'],seguinte['coluna'])
                fundo=seguinte['top']+1 if mesmo else info['fundo']
                left,right=info['limites'][col]
                if topo-fundo>8:
                    bbox=[round(v,3) for v in (left,fundo,right,topo)]
                    page=doc[p];tp=page.get_textpage()
                    texto=tp.get_text_bounded(left+cx,fundo+cy,right+cx,topo+cy)
                    tp.close();page.close()
                    # Sem texto pode haver gráficos: preserve o trecho para inspeção visual.
                    trechos.append({'pagina':p,'bbox':bbox});textos.append(texto)
            texto='\n'.join(textos)
            questoes.append({'id':f"{prova['id']}-{c['numero']}",'prova':prova['id'],
                             'ano':prova['ano'],'numero':c['numero'],'recortes':trechos,
                             'texto':texto,'texto_limitado':texto_limitado(texto),
                             'conteudos':classificar(texto),'revisado':False})
        return questoes
