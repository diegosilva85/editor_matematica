import math
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
import pypdfium2 as pdfium
from solidos import Solido
from contextos_solidos import CENARIOS, PADRAO, enunciado, grandezas, imersao, imagem, apoio
from documentos import dados_documento, validar_documento, carregar_documento
from listas import Lista, dados_lista, validar_lista, planejar, pdf_lista
from parabolas import salvar_documento


def exemplo(cenario, objetivo=None, **kw):
    tipo,_,alvos=CENARIOS[cenario]
    return Solido(tipo,dict(PADRAO),cenario=cenario,objetivo=objetivo or alvos[0],**kw)


class ContextosSolidosTests(unittest.TestCase):
    def test_cenarios_e_perguntas(self):
        self.assertEqual(len(CENARIOS),12)
        for c,(_,_,alvos) in CENARIOS.items():
            for alvo in alvos:
                with self.subTest(c=c,alvo=alvo):
                    q=exemplo(c,alvo); q.validar()
                    self.assertTrue(enunciado(q));self.assertTrue(apoio(q));self.assertTrue(imagem(q).is_file())

    def test_formulas(self):
        self.assertEqual(grandezas(exemplo('Caixa de embalagem'))['Área total'],216)
        self.assertEqual(grandezas(exemplo('Aquário sem tampa'))['Fundo e paredes'],384)
        q=exemplo('Lixeira cilíndrica aberta')
        self.assertAlmostEqual(grandezas(q)['Fundo e paredes'],145*math.pi)
        self.assertAlmostEqual(grandezas(exemplo('Barraca de camping'))['Sem piso'],144+18*math.sqrt(3))
        q=exemplo('Casquinha de sorvete');q.cone='Geratriz'
        self.assertAlmostEqual(grandezas(q)['Volume'],100*math.pi)
        self.assertAlmostEqual(grandezas(exemplo('Bola decorativa'))['Área total'],100*math.pi)

    def test_imersao(self):
        q=exemplo('Peça mergulhada em aquário','Elevação do nível')
        d=imersao(q);self.assertAlmostEqual(d['subida'],.36)
        q.objetivo='Transbordamento';q.valores['nivel']='30'
        q.validar();self.assertAlmostEqual(imersao(q)['excesso'],216)
        q.objetivo='Elevação do nível'
        with self.assertRaisesRegex(ValueError,'sem perda'): q.validar()
        q=exemplo('Teste em tanque cilíndrico','Volume pela elevação')
        q.valores['r']='';q.validar()
        self.assertNotIn('A peça tem',enunciado(q))
        self.assertAlmostEqual(imersao(q)['volume'],225*math.pi)

    def test_impossiveis(self):
        for key,value in [('a','40'),('nivel','31'),('nivel','1')]:
            q=exemplo('Peça mergulhada em aquário');q.valores[key]=value
            with self.assertRaises(ValueError): q.validar()
        q=exemplo('Bola decorativa','Área lateral')
        with self.assertRaises(ValueError): q.validar()
        q=exemplo('Casquinha de sorvete');q.cone='Geratriz';q.valores['g']='4'
        with self.assertRaises(ValueError): q.validar()

    def test_formatos_e_sem_imagem(self):
        q=exemplo('Aquário sem tampa',incluir_imagem=False,unidade='m')
        q.valores.update(a='7,6',b='3/2',h='√2')
        q.validar();texto=enunciado(q)
        self.assertIn('7,6 m',texto);self.assertIn('3/2 m',texto);self.assertIn('raiz de 2 m',texto)
        self.assertIsNone(imagem(q))

    def test_json_antigo_e_novo(self):
        antiga={'formato':'criador-de-graficos','versao':1,'paginas':[dict(aba=4,colunas=1,titulo='',itens=[dict(tipo='Cubo',valores={'a':'6'})])]}
        self.assertEqual(validar_documento(antiga)[0][1][0].cenario,'Sem contexto')
        itens=[exemplo(c,incluir_imagem=i%2==0) for i,c in enumerate(CENARIOS)]
        pages=[(4,itens,3,'Contextos')]
        self.assertEqual(validar_documento(dados_documento(pages)),pages)
        lista=Lista(itens=[(4,q) for q in itens]);self.assertEqual(validar_lista(dados_lista(lista)),lista)

    def test_pdf_paginacao_e_imagens(self):
        itens=[exemplo(c) for c in CENARIOS]
        lista=Lista(colunas=3,itens=[(4,q) for q in itens])
        plan=planejar(lista)
        self.assertTrue(all(len(p)<=4 for p in plan))
        self.assertTrue(all(len(set(r[1] for r in p))<=2 for p in plan))
        with pdfium.PdfDocument(pdf_lista(lista)) as doc:
            self.assertEqual(len(doc),len(plan))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'geometria.pdf'
            salvar_documento(path,[(4,itens,3,'Geometria contextual')])
            self.assertEqual(carregar_documento(path.with_suffix('.json'))[0][1],itens)
            with pdfium.PdfDocument(path) as doc:
                self.assertEqual(len(doc),len(plan))
        q=replace(itens[0],incluir_imagem=False)
        self.assertEqual(planejar(Lista(itens=[(4,q)]))[0][0][-1],0)


if __name__=='__main__': unittest.main()
