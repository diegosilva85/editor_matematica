import math
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
import sympy as sp
import pypdfium2 as pdfium
from geometria_plana import (FiguraPlana,FIGURAS,PEDIDOS,REGIOES,campos,padrao,
                             grandezas,gerar,apoio,imagem,tracos_concentricos)
from interface_plana import converter_medidas
from documentos import dados_documento,validar_documento,carregar_documento
from listas import Lista,dados_lista,validar_lista,pdf_lista,planejar
from parabolas import salvar_documento


CHAVES=list(FIGURAS)
def exemplo(n,**kw):
    key=CHAVES[n-1]
    return FiguraPlana(figura=key,valores=padrao(key,kw.get('circular','Raio')),**kw)


class PlanaTests(unittest.TestCase):
    def test_cotas_todas_as_figuras_e_atualizacao(self):
        from cotas_planas import anotacoes,miniatura
        for n in range(1,30):
            for modo in ('Raio','Diâmetro'):
                q=exemplo(n,circular=modo)
                self.assertEqual({x[0] for x in anotacoes(q)},set(q.valores))
        q=exemplo(1);antes=miniatura(q).tobytes()
        q.valores['a']='7,6'
        self.assertEqual(anotacoes(q)[0][1],'7,6 cm')
        self.assertNotEqual(antes,miniatura(q).tobytes())
        diam=anotacoes(exemplo(25,circular='Diâmetro'))[-1]
        self.assertEqual(diam[2:4],((115,90),(285,90)))

    def test_acervo_completo_e_medidas_exatas(self):
        self.assertEqual(len(FIGURAS),29)
        for n in range(1,30):
            q=exemplo(n);q.validar()
            self.assertTrue(imagem(q).is_file())
            A,P=grandezas(q);self.assertGreater(float(A),0);self.assertGreater(float(P),0)
            for pedido in PEDIDOS:self.assertIn('Calcule',replace(q,pedido=pedido).enunciado())
        q=exemplo(1);q.valores['a']='7,6'
        self.assertEqual(grandezas(q),(sp.Rational(1444,25),sp.Rational(152,5)))
        self.assertNotIn('7,6',q.enunciado());self.assertIn('7,6',replace(q,incluir_imagem=False).enunciado())
        q.valores['a']='2√3/3';self.assertEqual(grandezas(q)[0],sp.Rational(4,3))

    def test_referencias_numericas_todas_as_figuras(self):
        pi=math.pi;s=math.sqrt
        referencias=[(64,32),(84,38),(84,38),(24,24),(48,32),(25*pi,10*pi),
            (96,52),(96,52),(126,28+2*s(61)),(60+12.5*pi,22+5*pi),
            (40+12.5*pi,2*s(89)+5*pi),(9*pi,6*pi),(54*s(3),36),(88,40),
            (126,41+s(65)),(100-25*pi,40+10*pi),(96,8*s(34)),(100,30+2*s(89)),
            (96+16*pi,24+8*pi),(48*pi,16*pi),(78,20+6*s(13)),(64+32*pi,16*pi),
            (88,52),(120,68),(180-8*pi,48+4*pi),(24*pi,8+12*pi),
            (216-9*pi,60+6*pi),(104+12.5*pi,16+2*s(73)+5*pi),(132,52)]
        for n,(area,perimetro) in enumerate(referencias,1):
            with self.subTest(n=n):
                A,P=grandezas(exemplo(n))
                self.assertAlmostEqual(float(A),area);self.assertAlmostEqual(float(P),perimetro)

    def test_poligonos_por_coordenadas_independentes(self):
        polys={
            7:[(0,0),(12,0),(12,5),(4,5),(4,14),(0,14)],
            8:[(0,12),(14,12),(14,8),(9.5,8),(9.5,0),(4.5,0),(4.5,8),(0,8)],
            15:[(0,0),(14,0),(14,8),(7,8),(0,12)],
            18:[(0,0),(10,0),(10,-2),(18,3),(10,8),(10,6),(0,6)],
            21:[(0,0),(3,4),(6,0),(9,4),(12,0),(6,-9)],
            24:[(0,0),(14,0),(14,12),(10,12),(10,4),(4,4),(4,12),(0,12)],
            29:[(0,0),(12,0),(12,12),(9,12),(6,8),(3,12),(0,12)]}
        for n,points in polys.items():
            pares=list(zip(points,points[1:]+points[:1]))
            area=abs(sum(x*v-u*y for (x,y),(u,v) in pares))/2
            per=sum(math.hypot(x-u,y-v) for (x,y),(u,v) in pares)
            A,P=grandezas(exemplo(n));self.assertAlmostEqual(float(A),area);self.assertAlmostEqual(float(P),per)

    def test_regioes_e_contornos_circulares(self):
        q=exemplo(12,regiao=REGIOES[1])
        self.assertEqual(grandezas(q),(55*sp.pi,22*sp.pi))
        self.assertEqual(grandezas(replace(q,regiao=REGIOES[2])),(64*sp.pi,16*sp.pi))
        for regiao in REGIOES:
            for x,y,u,v in tracos_concentricos(regiao):
                mx=(x+u)/2-200;my=(y+v)/2-200;dist=math.hypot(mx,my)
                if regiao==REGIOES[0]:self.assertLessEqual(dist,60)
                elif regiao==REGIOES[1]:self.assertGreaterEqual(dist,60-1e-8)
                else:self.assertLessEqual(dist,145)
        self.assertIn('externos e internos',exemplo(27).enunciado())
        self.assertIn('comprimento da circunferência',exemplo(6,pedido=PEDIDOS[1]).enunciado())

    def test_raio_diametro_preserva_figura_e_notacao(self):
        for n in (6,12,20,25,26,27):
            self.assertEqual(grandezas(exemplo(n)),grandezas(exemplo(n,circular='Diâmetro')))
        self.assertEqual(converter_medidas(CHAVES[5],{'r':'7,6'},'Raio','Diâmetro'),{'d':'15,2'})
        self.assertEqual(converter_medidas(CHAVES[5],{'d':'10'},'Diâmetro','Raio'),{'r':'5'})
        for v in ('3/2','√2','2√3/3'):
            values=converter_medidas(CHAVES[5],{'r':v},'Raio','Diâmetro')
            self.assertEqual(grandezas(FiguraPlana(CHAVES[5],{'r':v})),grandezas(FiguraPlana(CHAVES[5],values,circular='Diâmetro')))

    def test_validacao_de_recortes_e_dimensoes(self):
        casos={2:dict(b='5',h='6'),3:dict(b='7',h='6'),7:dict(t='12'),8:dict(t='12'),
               12:dict(r='8'),14:dict(c='14'),15:dict(c='14'),18:dict(B='6'),23:dict(t='14'),
               24:dict(t='12'),25:dict(r='10'),26:dict(r='9'),27:dict(r='6'),29:dict(b='12')}
        for n,change in casos.items():
            q=exemplo(n);q.valores.update(change)
            with self.subTest(n=n),self.assertRaises(ValueError):q.validar()
        for value in ('0','-1','NaN','1/0','100001','__import__("os")',''):
            with self.assertRaises(ValueError):FiguraPlana(valores={'a':value}).validar()
        for change in (dict(figura='../secret'),dict(valores={}),dict(valores={'a':'2','x':'5'}),dict(incluir_imagem='sim'),dict(pedido='outro'),dict(unidade='kg')):
            with self.assertRaises(ValueError):replace(exemplo(1),**change).validar()

    def test_geracao_aleatoria_valida_e_sem_mutacoes(self):
        for n in range(1,30):
            for circular in ('Raio','Diâmetro'):
                q=exemplo(n,circular=circular);antes=dict(q.valores)
                for seed in range(4):
                    values=gerar(q,2,20,seed)
                    self.assertTrue(all(2<=int(v)<=20 for v in values.values()))
                    replace(q,valores=values).validar()
                    self.assertEqual(q.valores,antes)
        self.assertEqual(gerar(exemplo(7),seed=42),gerar(exemplo(7),seed=42))
        with self.assertRaises(ValueError):gerar(exemplo(7),5,5,seed=1)
        for lo,hi in ((0,10),(10,2),(1,1001),(1.5,4)):
            with self.assertRaises(ValueError):gerar(exemplo(1),lo,hi)

    def test_json_lista_e_documento(self):
        qs=[exemplo(n) for n in range(1,13)]
        pages=[(8,qs,3,'Geometria plana')]
        self.assertEqual(validar_documento(dados_documento(pages)),pages)
        lista=Lista(colunas=3,itens=[(8,exemplo(n)) for n in range(1,30)])
        self.assertEqual(validar_lista(dados_lista(lista)),lista)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'plana.pdf';salvar_documento(path,pages)
            self.assertEqual(carregar_documento(path.with_suffix('.json')),pages)
        with self.assertRaises(ValueError):validar_documento(dados_documento([(8,qs+[qs[0]],3,'')]))

    def test_pdf_sem_gabarito_e_opcoes_de_pedido(self):
        for pedido,trecho in ((PEDIDOS[0],'Calcule a área'),(PEDIDOS[1],'Calcule o perímetro'),(PEDIDOS[2],'Calcule a área')):
            q=exemplo(1,pedido=pedido)
            with pdfium.PdfDocument(pdf_lista(Lista(itens=[(8,q)]))) as doc:
                page=doc[0];tp=page.get_textpage();text=' '.join(tp.get_text_range().split());tp.close();page.close()
                self.assertIn(trecho,text);self.assertNotIn('64',text);self.assertNotIn('32',text)
            self.assertIn('64',apoio(q)[0]);self.assertTrue(apoio(q)[1])
        self.assertIsNone(imagem(exemplo(1,incluir_imagem=False)))

    def test_documento_com_as_oito_abas(self):
        from test_documentos import DocumentosTests
        from progressao import Progressao
        from estatistica import Estatistica
        base=DocumentosTests();base.setUp()
        pages=base.paginas+[(6,[Progressao()],2,'PA'),(7,[Estatistica()],2,'Estatística'),(8,[exemplo(1)],3,'Plana')]
        self.assertEqual(validar_documento(dados_documento(pages)),pages)

    def test_todas_as_figuras_cabem_em_ate_tres_colunas(self):
        for cols in (1,2,3):
            lista=Lista(colunas=cols,itens=[(8,exemplo(n)) for n in range(1,30)])
            pages=planejar(lista)
            self.assertEqual(sum(map(len,pages)),29)
            for page in pages:
                self.assertLessEqual(len(page),12)
                self.assertLessEqual(len({c[1] for c in page}),cols)
                self.assertTrue(all(c[2]>=40 for c in page))
        with pdfium.PdfDocument(pdf_lista(lista)) as doc:self.assertEqual(len(doc),len(pages))


if __name__=='__main__':unittest.main()
