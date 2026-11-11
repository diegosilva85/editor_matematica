import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch,MagicMock

from acervo_enem import (ASSETS,CONTEUDOS,carregar_acervo,caminho_pdf,baixar_prova,
                         salvar_conteudos,filtrar,classificar,imagem_questao,indexar_prova)
from importar_enem import Links


class AcervoEnemTests(unittest.TestCase):
    def setUp(self):self.fontes,self.questoes=carregar_acervo()

    def test_cobertura_completa_e_identificadores(self):
        self.assertEqual(len(self.fontes),23);self.assertEqual(len(self.questoes),1035)
        self.assertEqual(len({q['id'] for q in self.questoes}),1035)
        for p in self.fontes:
            grupo=filtrar(self.questoes,prova=p['id'])
            self.assertEqual({q['numero'] for q in grupo},set(range(136,181)))
            self.assertTrue(p['url'].startswith('https://download.inep.gov.br/'))
            self.assertEqual(len(p['sha256']),64)
        self.assertEqual({p['ano'] for p in self.fontes},set(range(2015,2026)))
        self.assertIn('2016-segunda',{p['id'] for p in self.fontes})

    def test_recortes_e_conteudos_validos(self):
        for q in self.questoes:
            self.assertTrue(q['texto']);self.assertTrue(q['recortes'])
            self.assertTrue(set(q['conteudos'])<=set(CONTEUDOS))
            headings=re.findall(r'quest\s*ã\s*o\s*(1[3-8]\d)\b',q['texto'],re.I)
            self.assertEqual(headings,[str(q['numero'])],q['id'])
            for r in q['recortes']:
                l,b,rr,t=r['bbox'];self.assertGreater(rr,l);self.assertGreater(t,b)
                self.assertGreaterEqual(min(l,b),0)

    def test_filtros_combinados_busca_sem_acentos(self):
        self.assertEqual(len(filtrar(self.questoes,ano=2016)),135)
        self.assertEqual(len(filtrar(self.questoes,prova='2015-ppl')),45)
        q=filtrar(self.questoes,ano=2015,prova='2015-regular',busca='136')
        self.assertEqual(q[0]['numero'],136)
        for q in filtrar(self.questoes,conteudo='Estatística'):
            self.assertIn('Estatística',q['conteudos'])
        self.assertEqual(filtrar(self.questoes,ano=1990),[])

    def test_largura_inteira_e_ultima_questao_com_continuacao(self):
        index={q['id']:q for q in self.questoes}
        for id in ('2016-segunda-180','2025-regular-158','2025-ppl-136'):
            q=index[id];l,b,r,t=q['recortes'][0]['bbox']
            self.assertGreater(r-l,400,id)
        self.assertIn('20,00',index['2016-segunda-180']['texto'])
        self.assertEqual(len(index['2021-regular-180']['recortes']),2)
        self.assertIn('Considere um visitante',index['2021-regular-180']['texto'])

    def test_correcao_conteudo_persistente_sem_alterar_indice(self):
        original=(ASSETS/'indice.json').read_bytes()
        with tempfile.TemporaryDirectory() as d:
            salvar_conteudos('2015-regular-136',['Função de 2º grau'],d)
            _,questoes=carregar_acervo(d)
            q=next(q for q in questoes if q['id']=='2015-regular-136')
            self.assertEqual(q['conteudos'],['Função de 2º grau']);self.assertTrue(q['revisado'])
            with self.assertRaises(ValueError):salvar_conteudos(q['id'],[],d)
        self.assertEqual((ASSETS/'indice.json').read_bytes(),original)

    def test_classificador_sugestoes(self):
        self.assertIn('Geometria espacial',classificar('Volume do cilindro'))
        self.assertIn('Estatística',classificar('Calcule a mediana'))
        self.assertIn('Probabilidade',classificar('Qual a probabilidade?'))
        self.assertIn('Função de 2º grau',classificar('T(h) = − h2\n + 22h − 85'))
        self.assertEqual(classificar('Um problema sem pistas'),[CONTEUDOS[-1]])

    def test_download_atomico_rejeita_html_e_hash_incorreto(self):
        p=dict(self.fontes[0]);p.pop('sha256')
        with tempfile.TemporaryDirectory() as d:
            response=MagicMock();response.url=p['url'];response.read.return_value=b'<html>erro</html>'
            with patch('acervo_enem.urlopen') as get:
                get.return_value.__enter__.return_value=response
                with self.assertRaises(ValueError):baixar_prova(p,d)
                self.assertFalse(caminho_pdf(p,d).exists())
                response.read.return_value=b'%PDF-1.4 teste'
                p['sha256']='0'*64
                with self.assertRaises(ValueError):baixar_prova(p,d)
                p['sha256']=hashlib.sha256(response.read.return_value).hexdigest()
                path=baixar_prova(p,d);self.assertTrue(path.exists())
                get.reset_mock();self.assertEqual(baixar_prova(p,d),path);get.assert_not_called()
            with self.assertRaises(ValueError):caminho_pdf({'arquivo':'../fora.pdf'},d)
            p['url']='https://outro.example/teste.pdf';p['arquivo']='outro.pdf'
            with self.assertRaises(ValueError):baixar_prova(p,d)

    def test_links_secoes(self):
        p=Links();p.feed('<h3><span>2ª aplicação</span></h3><a href="https://download.inep.gov.br/prova.pdf">Prova</a>')
        self.assertEqual(p.links,[('2ª aplicação','https://download.inep.gov.br/prova.pdf')])

    def test_renderizacao_local_e_continuacao(self):
        p=self.fontes[0]
        if not caminho_pdf(p).exists():self.skipTest('PDF local não baixado')
        grupo=indexar_prova(p,caminho_pdf(p));self.assertEqual(len(grupo),45)
        q=next(q for q in grupo if len(q['recortes'])>1)
        im=imagem_questao(q,p,500);self.assertGreater(im.height,100);self.assertGreater(im.width,400)
        im=imagem_questao(grupo[0],p,500,pagina_inteira=True);self.assertGreater(im.height,im.width)


if __name__=='__main__':unittest.main()
