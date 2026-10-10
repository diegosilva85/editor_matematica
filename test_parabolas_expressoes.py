import unittest
import tempfile
from pathlib import Path
from dataclasses import replace
from parabolas import Parabola,salvar_documento
from documentos import dados_documento,validar_documento,carregar_documento
from listas import Lista,pdf_lista,planejar


class ExpressoesTests(unittest.TestCase):
    def modelo(self,**kwargs):
        return Parabola(1,3,-4,apresentacao='Expressão da função',**kwargs)

    def test_expressoes(self):
        for coeffs,expected in [((1,3,-4),'x² + 3x - 4'),((-1,-1,0),'-x² - x'),
                                ((2,0,5),'2x² + 5'),((1,0,0),'x²'),((.5,-1,2.5),'0,5x² - x + 2,5')]:
            self.assertEqual(Parabola(*coeffs).expressao(),'f(x) = '+expected)
        f=self.modelo(modo='Raízes e a',raiz1='0,1',raiz2='0,2')
        self.assertEqual(f.expressao(),'f(x) = x² - 0,3x + 0,02')
        self.assertEqual(self.modelo(modo='Raízes e a',quantidade_raizes='1',raiz1='2',raiz2='ignorada').expressao(),'f(x) = x² - 4x + 4')

    def test_pedidos(self):
        self.assertIn('raízes reais e as coordenadas',self.modelo().enunciado())
        self.assertNotIn('vértice',self.modelo(pedir_vertice=False).enunciado())
        self.assertNotIn('raízes',self.modelo(pedir_raizes=False).enunciado())
        with self.assertRaises(ValueError): self.modelo(pedir_raizes=False,pedir_vertice=False).dados()
        self.assertEqual(Parabola(1,0,1,apresentacao='Expressão da função').dados()[2],[])

    def test_json_antigo_e_novo(self):
        pages=[(2,[self.modelo(),self.modelo(modo='Raízes e a',raiz1='2',raiz2='3')],2,'Funções')]
        for item in pages[0][1]: item.dados()
        self.assertEqual(validar_documento(dados_documento(pages)),pages)
        old=dados_documento([(2,[Parabola(1,2,3)],1,'')])
        for key in ('apresentacao','pedir_raizes','pedir_vertice'): del old['paginas'][0]['itens'][0][key]
        self.assertEqual(validar_documento(old)[0][1][0].apresentacao,'Gráfico')
        bad=dados_documento(pages); bad['paginas'][0]['itens'][0]['pedir_raizes']='sim'
        with self.assertRaises(ValueError): validar_documento(bad)

    def test_pdf_e_lista(self):
        import pypdfium2 as pdfium
        items=[self.modelo(),self.modelo(pedir_vertice=False),self.modelo(pedir_raizes=False)]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'expressoes.pdf'
            salvar_documento(path,[(2,items,2,'Funções')])
            self.assertEqual(carregar_documento(path.with_suffix('.json'))[0][1],items)
            with pdfium.PdfDocument(path) as doc:
                page=doc[0]; tp=page.get_textpage(); text=tp.get_text_range()
                self.assertIn('f(x)',text); self.assertNotIn('sinal de delta',text)
                tp.close(); page.close()
        lista=Lista(itens=[(2,f) for f in items],colunas=3)
        self.assertTrue(all(cell[-1]==0 for page in planejar(lista) for cell in page))
        self.assertTrue(pdf_lista(lista).startswith(b'%PDF'))


if __name__=='__main__': unittest.main()
