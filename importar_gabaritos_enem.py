"""Importa gabaritos vinculados aos cadernos do acervo pelo portal oficial."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import re
from importar_enem import Links,obter
from acervo_enem import ASSETS,DADOS,salvar_json,normalizar


def extrair_respostas(texto):
    pares=re.findall(r'\b(1[3-8]\d)\s+(ANULAD[AO]|[A-E])\b',texto,re.I)
    respostas={}
    for numero,resposta in pares:
        if not 136<=int(numero)<=180:continue
        if numero in respostas:raise ValueError(f'Questão {numero} duplicada no gabarito.')
        respostas[numero]='Anulada' if resposta.upper().startswith('ANULAD') else resposta.upper()
    if set(respostas)!={str(n) for n in range(136,181)}:
        faltam=sorted(set(range(136,181))-{int(n) for n in respostas})
        raise ValueError(f'Gabarito de matemática incompleto: faltam {faltam}.')
    return respostas


def indexar_gabaritos():
    import pypdfium2 as pdfium
    fontes=json.loads((ASSETS/'fontes_gabaritos.json').read_text(encoding='utf-8'))
    catalogo={}
    for f in fontes:
        path=DADOS/'gabaritos'/(f['prova']+'.pdf')
        with pdfium.PdfDocument(path) as doc:
            textos=[]
            for page in doc:
                tp=page.get_textpage();textos.append(tp.get_text_range());tp.close();page.close()
        texto='\n'.join(textos)
        respostas=extrair_respostas(texto)
        esperado=13 if f['prova'] in ('2015-ppl','2016-ppl') else 17 if f['prova']=='2018-ppl' else 5
        cadernos={int(n) for n in re.findall(r'caderno\s*0*(\d+)',normalizar(texto))}
        print(f['prova'],len(respostas),'caderno:',cadernos,'anuladas:',[n for n,a in respostas.items() if a=='Anulada'],flush=True)
        if cadernos!={esperado}:raise ValueError(f"{f['prova']}: caderno {cadernos}, esperado {esperado}. Cabeçalho: {texto[:200]!r}")
        if f['prova'][:4] not in texto:raise ValueError('Ano não encontrado no gabarito.')
        catalogo[f['prova']]={**f,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                              'caderno':esperado,'respostas':respostas}
    salvar_json(ASSETS/'gabaritos.json',{'versao':1,'provas':catalogo})


def descobrir_gabaritos():
    provas=json.loads((ASSETS/'fontes.json').read_text(encoding='utf-8'))
    def links(url):
        parser=Links();parser.feed(obter(url).decode('utf-8'));return url,parser.links
    with ThreadPoolExecutor(max_workers=3) as pool:
        paginas=dict(pool.map(links,sorted({p['fonte'] for p in provas})))
    fontes=[]
    for p in provas:
        lista=paginas[p['fonte']];pos=next(i for i,(_,url) in enumerate(lista) if url==p['url'])
        candidatos=[]
        for secao,url in lista[pos+1:]:
            if secao!=p['aplicacao']:break
            nome=url.rsplit('/',1)[-1]
            if '/gabaritos/' in url or re.search(r'(?:_GB_|GAB|gabarito)',nome,re.I):
                candidatos.append(url);break
        # O portal de 2015 repete, por engano, o link do dia 1 no bloco do
        # caderno 13. O link correto também está publicado na mesma seção.
        if p['id']=='2015-ppl':
            candidatos=[url for secao,url in lista if secao==p['aplicacao']
                        and url.endswith('GAB_ENEM2015_2aAPLICACAO_DIA2_CADERNO_13.pdf')]
        if not candidatos:raise ValueError(f"Gabarito não localizado: {p['id']}")
        fontes.append({'prova':p['id'],'url':candidatos[0],'fonte':p['fonte'],
                       'arquivo':candidatos[0].rsplit('/',1)[-1]})
    return fontes


def main():
    p=argparse.ArgumentParser();p.add_argument('--descobrir',action='store_true')
    p.add_argument('--indexar',action='store_true')
    args=p.parse_args()
    if args.descobrir:
        fontes=descobrir_gabaritos();salvar_json(ASSETS/'fontes_gabaritos.json',fontes)
        for f in fontes:print(f['prova'],f['url'],flush=True)
    if args.indexar:indexar_gabaritos()


if __name__=='__main__':main()
