import tempfile
import unittest
from pathlib import Path
from triangulos import Triangulo, POSICOES
from contextos import CENARIOS, opcoes, enunciado, cena, caminho_imagem
from documentos import carregar_documento
from parabolas import salvar_documento


def exemplos():
    return [Triangulo(30,POSICOES[0],'Seno','Hipotenusa','20',
            apresentacao='Contextual',cenario=name,dado_contexto=opcoes(name)[0],
            pedido_contexto=opcoes(name)[1]) for name in CENARIOS]


class ContextosTests(unittest.TestCase):
    def test_sobreposicoes_sem_incognita(self):
        from dataclasses import replace
        from sobreposicoes import anotacoes, ANCORAS
        self.assertEqual(set(ANCORAS),set(CENARIOS))
        for t in exemplos():
            for known in opcoes(t.cenario):
                choices=[p for p in opcoes(t.cenario) if p!=known]
                model=replace(t,dado_contexto=known,pedido_contexto=choices[0],valor='20√3/3',angulo=45)
                lines,labels=anotacoes(model,180,120)
                self.assertEqual([(k,v) for k,v,*_ in labels],[('angulo','45°'),('medida','20√3/3')])
                for _,_,x,y in labels:
                    self.assertTrue(0<=x<=180 and 0<=y<=120)
                for asked in choices:
                    self.assertEqual(anotacoes(replace(model,pedido_contexto=asked),180,120),(lines,labels))

    def test_altura_total_nao_rotula_cateto_parcial(self):
        from dataclasses import replace
        from contextos import EXTRAS
        from sobreposicoes import anotacoes, ANCORAS
        for t in exemplos():
            if t.cenario not in EXTRAS: continue
            t=replace(t,dado_contexto=opcoes(t.cenario)[1],pedido_contexto=opcoes(t.cenario)[0])
            lines,_=anotacoes(t,180,120)
            cota=lines[3][0]
            self.assertAlmostEqual(cota[0][1],ANCORAS[t.cenario][3]*120)
            self.assertAlmostEqual(cota[1][1],ANCORAS[t.cenario][2][1]*120)

    def test_layout_seis_justificado_sem_resposta(self):
        from io import BytesIO
        from unittest.mock import patch
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.platypus import Paragraph
        from reportlab.lib.enums import TA_JUSTIFY
        from contextos import desenhar_pagina
        for count in (1,6,7,12,15):
            items=(exemplos()*2)[:count]
            pdf=Canvas(BytesIO())
            with patch('contextos.dessiner') as draw, \
                 patch('reportlab.platypus.Paragraph',wraps=Paragraph) as paragraph, \
                 patch.object(pdf,'drawString',wraps=pdf.drawString) as text:
                desenhar_pagina(pdf,items,2,'Teste')
                self.assertEqual(pdf.getPageNumber(),(count+5)//6)
                self.assertEqual(draw.call_count,count)
                self.assertTrue(all(call.args[-1]>=70 for call in draw.call_args_list))
                self.assertTrue(all(call.args[1].alignment==TA_JUSTIFY for call in paragraph.call_args_list))
                self.assertFalse(any('Resposta:' in str(call) for call in text.call_args_list))

    def test_ilustracoes_detalhadas_disponiveis(self):
        from PIL import Image
        for name in CENARIOS:
            with self.subTest(cenario=name):
                with Image.open(caminho_imagem(name)) as image:
                    self.assertGreaterEqual(image.width,1024)
                    self.assertGreaterEqual(image.height,768)
                    image.verify()

    def test_cenarios_e_variantes(self):
        self.assertEqual(len(CENARIOS),12)
        for t in exemplos():
            self.assertTrue(cena(t.cenario))
            for known in opcoes(t.cenario):
                for asked in opcoes(t.cenario):
                    if known==asked: continue
                    t.dado_contexto=known; t.pedido_contexto=asked
                    texto=enunciado(t)
                    self.assertIn(asked,texto)
                    self.assertNotIn('Medida conhecida:',texto)
                    self.assertIn('Considerando que' if known.startswith('distância') else 'Sabendo que',texto)
                    artigo='o' if known.startswith(('comprimento','deslocamento','desnível','trajeto')) else 'a'
                    self.assertIn(f'que {artigo} {known} é de {t.valor} m, determine ',texto)

    def test_json_e_pdf_misto(self):
        items=exemplos()+[Triangulo(45,POSICOES[0],'Seno','Hipotenusa','3')]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'contextos.pdf'
            salvar_documento(str(path),[(3,items,3,'Trigonometria')])
            loaded=carregar_documento(path.with_suffix('.json'))
            self.assertEqual(loaded[0][1],items)
            self.assertGreater(path.stat().st_size,1000)

    def test_altura_invalida(self):
        t=exemplos()[4]; t.dado_contexto=opcoes(t.cenario)[1]
        t.pedido_contexto=opcoes(t.cenario)[0]; t.valor='1'
        with self.assertRaises(ValueError): t.validar()


if __name__=='__main__': unittest.main()
