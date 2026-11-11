"""Importação reproduzível do acervo oficial; execute com --descobrir ou --baixar."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request

BASE='https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos'
PASTA=Path(__file__).resolve().parent/'assets'/'enem'


def obter(url):
    req=urllib.request.Request(url,headers={'User-Agent':'EditorMatematica/1.0 (acervo educacional)'})
    with urllib.request.urlopen(req,timeout=90) as response:
        return response.read()


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.secao='';self.heading=None;self.partes=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('h2','h3'):self.heading=tag;self.partes=[]
        if tag=='a':
            href=dict(attrs).get('href','')
            if 'download.inep.gov.br' in href and '.pdf' in href.lower():
                self.links.append((self.secao,href))
    def handle_data(self,data):
        if self.heading:self.partes.append(data)
    def handle_endtag(self,tag):
        if tag==self.heading:self.secao=' '.join(''.join(self.partes).split());self.heading=None


def descobrir(ano):
    url=f'{BASE}/{ano}';parser=Links();parser.feed(obter(url).decode('utf-8'))
    candidatos={}
    for secao,href in parser.links:
        nome=href.rsplit('/',1)[-1]
        especial=nome in ('P2_05_AMARELO_LC_MT_2016_REG.pdf','P2_05_AMARELO.pdf',
                         '2DIA_05_AMARELO_BAIXA.pdf','2018_PV_reaplicacao_PPL_D2_CD17.pdf',
                         '2025_PV_impresso_D6_CD5.pdf')
        if not especial and not re.search(r'_PV_.*D2_CD(?:5|13)\.pdf$',nome,re.I):continue
        if 'digital' in nome.lower():continue
        candidatos.setdefault(secao,href)
    return [{'ano':ano,'aplicacao':secao,'url':href,'fonte':url,
             'id':f'{ano}-'+('regular' if 'regular' in secao.lower() else 'segunda' if secao=='2ª aplicação' else 'ppl'),
             'arquivo':href.rsplit('/',1)[-1]} for secao,href in candidatos.items()]


def main():
    p=argparse.ArgumentParser();p.add_argument('--descobrir',action='store_true');p.add_argument('--baixar',action='store_true')
    args=p.parse_args()
    if args.descobrir:
        with ThreadPoolExecutor(max_workers=3) as pool:
            provas=[q for grupo in pool.map(descobrir,range(2015,2026)) for q in grupo]
        PASTA.mkdir(parents=True,exist_ok=True)
        (PASTA/'fontes.json').write_text(json.dumps(provas,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for q in provas:print(q['id'],q['aplicacao'],q['url'],flush=True)
    if args.baixar:
        from acervo_enem import baixar_prova,indexar_prova,salvar_json
        fontes=json.loads((PASTA/'fontes.json').read_text(encoding='utf-8'))
        def baixar(q):
            path=baixar_prova(q)
            print('Baixado:',q['id'],path.stat().st_size,flush=True)
            return q,path
        with ThreadPoolExecutor(max_workers=3) as pool:
            arquivos=list(pool.map(baixar,fontes))
        itens=[]
        for q,path in arquivos:
            q['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            grupo=indexar_prova(q,path);itens.extend(grupo)
            print('Indexado:',q['id'],len(grupo),flush=True)
        salvar_json(PASTA/'indice.json',{'versao':1,'questoes':itens})
        salvar_json(PASTA/'fontes.json',fontes)


if __name__=='__main__':main()
