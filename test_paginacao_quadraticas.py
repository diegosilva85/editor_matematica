import tempfile
import unittest
from pathlib import Path
import pypdfium2 as pdfium
from parabolas import salvar_documento, Parabola
from documentos import carregar_documento
from listas import Lista,planejar
from test_contextos_quadraticas import questao


class PaginacaoTests(unittest.TestCase):
    def test_paginas_letras_json_e_outras_abas(self):
        from app_graficos import Funcao
        with tempfile.TemporaryDirectory() as tmp:
            for n in (4,5,8,10):
                itens=[questao('Chute do goleiro') for _ in range(n)]
                path=Path(tmp)/'teste.pdf'
                salvar_documento(path,[(2,itens,1,'Parábolas'),(1,[Funcao(1,2,[1])],1,'Retas')])
                with pdfium.PdfDocument(path) as doc:
                    self.assertEqual(len(doc),(n+3)//4+1)
                    for i in range((n+3)//4):
                        page=doc[i]; tp=page.get_textpage()
                        text=tp.get_text_range()
                        self.assertIn(f'({chr(97+i*4)})',text)
                        self.assertNotIn(f'({chr(97+(i+1)*4)})',text)
                        tp.close();page.close()
                self.assertEqual(len(carregar_documento(path.with_suffix('.json'))[0][1]),n)

    def test_com_imagens(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'imagens.pdf'
            itens=[questao('Saque de vôlei',incluir_imagem=True) for _ in range(5)]
            salvar_documento(path,[(2,itens,2,'Contextos')])
            with pdfium.PdfDocument(path) as doc: self.assertEqual(len(doc),2)

    def test_lista_e_graficos_preservados(self):
        items=[(2,questao('Saque de vôlei')) for _ in range(10)]
        pages=planejar(Lista(colunas=3,por_pagina=12,itens=items))
        self.assertEqual([len(p) for p in pages],[4,4,2])
        for page in pages: self.assertLessEqual(len(set(c[1] for c in page)),2)
        self.assertEqual(len(planejar(Lista(colunas=3,itens=[(2,Parabola(1,0,0)) for _ in range(6)]))),1)


if __name__=='__main__': unittest.main()
