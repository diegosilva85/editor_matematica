import tempfile
import unittest
from dataclasses import replace,asdict
from pathlib import Path
import pypdfium2 as pdfium
from solidos import Solido
from euler import EULER,MANUAL,PREDEFINIDO,SOLIDOS,contagens,enunciado,apoio,imagem
from documentos import dados_documento,validar_documento,carregar_documento
from listas import Lista,dados_lista,validar_lista,pdf_lista,planejar,texto_questao
from parabolas import salvar_documento


def questao(**kwargs):
    return Solido('Cubo',{},modalidade=EULER,**kwargs)


class EulerTests(unittest.TestCase):
    def test_onze_solidos_e_tres_incognitas(self):
        self.assertEqual(len(SOLIDOS),11)
        for nome,(v,a,f,_) in SOLIDOS.items():
            for alvo in 'VAF':
                q=questao(euler_solido=nome,euler_descobrir=alvo)
                q.validar();d=contagens(q)
                self.assertEqual(d,dict(V=v,A=a,F=f));self.assertEqual(v-a+f,2)
                self.assertTrue(imagem(q).is_file());self.assertIn(f'{alvo} = {d[alvo]}',apoio(q))

    def test_manual_calcula_apenas_a_incognita(self):
        for alvo in 'VAF':
            q=questao(euler_origem=MANUAL,euler_v='10',euler_a='15',euler_f='7',euler_descobrir=alvo)
            setattr(q,'euler_'+alvo.lower(),'não utilizado')
            q.validar();self.assertEqual(contagens(q),dict(V=10,A=15,F=7))
            self.assertIsNone(imagem(q))
            self.assertNotIn(str(contagens(q)[alvo]),enunciado(q))

    def test_rejeita_dados_impossiveis(self):
        for v,f in [('0','4'),('-5','5'),('4,5','5'),('4/1','5'),('4','100'),('100','4'),('100001','4'),('','5'),('True','5')]:
            with self.subTest(v=v,f=f),self.assertRaises(ValueError):
                questao(euler_origem=MANUAL,euler_descobrir='A',euler_v=v,euler_f=f).validar()
        for kwargs in ({'euler_origem':'outro'},{'euler_solido':'Esfera'},{'euler_descobrir':'X'},{'incluir_imagem':'sim'}):
            with self.assertRaises(ValueError):questao(**kwargs).validar()

    def test_json_legado_e_novos_modelos(self):
        q=questao(euler_origem=MANUAL,euler_descobrir='A',euler_v='10',euler_f='7')
        pages=[(4,[q,questao()],3,'Euler')]
        self.assertEqual(validar_documento(dados_documento(pages)),pages)
        lista=Lista(itens=[(4,q),(4,questao())])
        self.assertEqual(validar_lista(dados_lista(lista)),lista)
        legacy=dados_documento([(4,[Solido('Cubo',{'a':'5'})],1,'Antigo')])
        for key in tuple(legacy['paginas'][0]['itens'][0]):
            if key.startswith('euler_') or key=='modalidade':del legacy['paginas'][0]['itens'][0][key]
        self.assertEqual(validar_documento(legacy)[0][1][0].modalidade,'Áreas e volumes')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'euler.pdf';salvar_documento(path,pages)
            self.assertEqual(carregar_documento(path.with_suffix('.json')),pages)

    def test_pdf_sem_resposta_e_sem_enunciado_de_volume(self):
        q=questao(euler_solido='Prisma pentagonal',euler_descobrir='A',incluir_imagem=False)
        lista=Lista(itens=[(4,q)])
        with pdfium.PdfDocument(pdf_lista(lista)) as doc:
            page=doc[0];tp=page.get_textpage();text=tp.get_text_range();tp.close();page.close()
        self.assertIn('10 vértices',text);self.assertIn('7 faces',text)
        self.assertNotIn('15',text);self.assertNotIn('volume',text);self.assertNotIn('Resposta',text)
        self.assertIsNone(imagem(q))

    def test_paginacao_mista_e_limites(self):
        qs=[questao(euler_solido=n) for n in SOLIDOS]
        lista=Lista(colunas=3,por_pagina=12,itens=[(4,q) for q in qs])
        pages=planejar(lista)
        self.assertEqual(sum(map(len,pages)),11)
        self.assertTrue(all(len(p)<=12 for p in pages))
        self.assertEqual(len({cell[1] for cell in pages[0]}),3)
        # O contexto antigo, guardado ao trocar de modo, não interfere em Euler.
        q=replace(qs[0],cenario='Aquário sem tampa')
        self.assertIn('Euler',texto_questao(4,q))
        self.assertEqual(len({c[1] for c in planejar(Lista(colunas=3,itens=[(4,q)]*3))[0]}),3)
        with pdfium.PdfDocument(pdf_lista(lista)) as doc:self.assertEqual(len(doc),len(pages))


if __name__=='__main__':unittest.main()
