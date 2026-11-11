import unittest
from PIL import Image,ImageDraw
from recortes_enem import aparar_branco


class RecortesTests(unittest.TestCase):
    def test_tira_branco_apos_barra_sem_mudar_largura(self):
        im=Image.new('RGB',(700,1200),'white');d=ImageDraw.Draw(im)
        d.rectangle((30,20,600,300),fill='black');d.line((20,320,680,320),fill='black',width=2)
        saida=aparar_branco(im,horizontal=False)
        self.assertEqual(saida.width,700);self.assertLess(saida.height,340)
        self.assertIsNotNone(saida.getbbox())

    def test_preserva_grafico_com_rotulos_abaixo(self):
        im=Image.new('RGB',(700,900),'white');d=ImageDraw.Draw(im)
        d.rectangle((30,20,600,300),fill='black');d.line((20,700,680,700),fill='black',width=2)
        d.text((40,730),'0 1 2 3 4 5',fill='black')
        self.assertGreater(aparar_branco(im).height,700)

    def test_rodape_independente_da_resolucao(self):
        im=Image.new('RGB',(700,900),'white');d=ImageDraw.Draw(im)
        d.rectangle((30,20,600,300),fill='black');d.line((20,850,680,850),fill='black',width=2)
        for scale in (1,2,3):
            saida=aparar_branco(im.resize((700*scale,900*scale)),horizontal=False)
            self.assertLess(saida.height,330*scale)


if __name__=='__main__':unittest.main()
