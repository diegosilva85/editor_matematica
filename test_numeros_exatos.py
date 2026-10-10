import unittest
import math
from numeros_exatos import ler
from parabolas import Parabola
from documentos import dados_documento,validar_documento
from listas import Lista,dados_lista,validar_lista,pdf_lista


class NumerosExatosTests(unittest.TestCase):
    def test_formatos(self):
        for text,expected in [('1/2',.5),('-1/2',-.5),('0,50',.5),('√2',math.sqrt(2)),
                              ('2√3/3',2*math.sqrt(3)/3),('sqrt(2)',math.sqrt(2)),
                              ('1/√2',1/math.sqrt(2)),('1/-2',-.5),('0',0),('√0',0),('.5',.5)]:
            self.assertAlmostEqual(ler(text)[1],expected)
        for text in ('','1/0','1/√0','√-2','nan','1e999','__import__("os")','1+2','1/2/3','9'*81):
            with self.subTest(text=text),self.assertRaises(ValueError): ler(text)

    def test_coeficientes_preservados(self):
        f=Parabola(1,0,0,a_texto='1/2',b_texto='-√2',c_texto='0,50',apresentacao='Expressão da função')
        text=f.expressao()
        self.assertIn('(1/2)x²',text); self.assertIn('(√2)x',text); self.assertIn('0,50',text)
        self.assertAlmostEqual(f.a,.5)
        g=Parabola(1,0,0,a_texto='sqrt(2)',b_texto='1/3',c_texto='-2√3/3')
        self.assertIn('√(2)',g.expressao()); self.assertIn('1/3',g.expressao())
        with self.assertRaises(ValueError): Parabola(1,0,0,a_texto='0/2').dados()

    def test_raizes_exatas(self):
        f=Parabola(1,0,0,a_texto='1/2',modo='Raízes e a',raiz1='√2',raiz2='-√2')
        self.assertEqual(f.expressao(),'f(x) = (1/2)x² - 1')
        f=Parabola(1,0,0,modo='Raízes e a',raiz1='1/3',raiz2='2/3')
        self.assertEqual(f.expressao(),'f(x) = x² - x + 2/9')
        f=Parabola(1,0,0,a_texto='√2',modo='Raízes e a',quantidade_raizes='1',raiz1='1/2',raiz2='ignorada')
        self.assertEqual(len(f.dados()[2]),1)
        self.assertNotIn('1.414',f.expressao())

    def test_json_e_pdf(self):
        f=Parabola(1,0,0,a_texto='1/2',b_texto='-√2',c_texto='0,50',apresentacao='Expressão da função')
        f.dados()
        pages=[(2,[f],1,'')]
        self.assertEqual(validar_documento(dados_documento(pages)),pages)
        lista=Lista(itens=[(2,f)])
        self.assertEqual(validar_lista(dados_lista(lista)),lista)
        self.assertTrue(pdf_lista(lista).startswith(b'%PDF'))
