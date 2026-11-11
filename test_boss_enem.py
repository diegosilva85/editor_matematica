import unittest
from unittest.mock import patch
from PIL import Image
import pypdfium2 as pdfium
from boss_enem import planejar, gerar_boss
from reportlab.lib.pagesizes import A4


class BossTests(unittest.TestCase):
    def test_pequena_repete_e_preserva_proporcao(self):
        p=planejar(250,180)
        self.assertGreater(p['quantidade'],1)
        self.assertGreaterEqual(p['escala'],.9)
        self.assertAlmostEqual(p['largura']/p['altura'],250/180)

    def test_grande_so_uma_sem_distorcer(self):
        p=planejar(520,900)
        self.assertEqual(p['quantidade'],1)
        self.assertAlmostEqual(p['largura']/p['altura'],520/900)
        self.assertLess(p['altura'],A4[1])

    def test_pdf_unica_pagina(self):
        q=dict(ano=2025,numero=136,recortes=[dict(bbox=[0,0,250,180])])
        with patch('boss_enem.imagem_questao',return_value=Image.new('RGB',(750,540),'white')):
            dados,preview,plano=gerar_boss(q,{})
        with pdfium.PdfDocument(dados) as doc:
            self.assertEqual(len(doc),1)
            self.assertAlmostEqual(doc[0].get_width(),A4[0],places=2)
        self.assertGreater(preview.height,preview.width)
        self.assertEqual(plano['quantidade'],8)


if __name__=='__main__':unittest.main()
