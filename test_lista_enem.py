import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from lista_enem import encaixar,gerar_lista,salvar_lista,LARGURA,ALTURA


class ListaEnemTests(unittest.TestCase):
    def test_encaixe_sem_sobreposicao_ou_perdas(self):
        itens=[dict(largura=w,altura=h,id=n) for n,(w,h) in enumerate(
            [(250,300),(250,180),(520,600),(250,450),(250,120)]*4)]
        paginas=encaixar(itens,.8)
        self.assertEqual(sorted(b['item']['id'] for p in paginas for b in p['itens']),list(range(20)))
        for p in paginas:
            for a in p['itens']:
                self.assertLessEqual(a['x']+a['largura'],LARGURA+1e-6)
                self.assertLessEqual(a['y']+a['altura'],ALTURA+1e-6)
                for b in p['itens']:
                    if a is b:continue
                    self.assertTrue(a['x']+a['largura']<=b['x'] or b['x']+b['largura']<=a['x'] or
                                    a['y']+a['altura']<=b['y'] or b['y']+b['altura']<=a['y'])

    def test_pdf_e_json(self):
        qs=[dict(id=str(n),ano=2025,prova='2025-regular',numero=136+n) for n in range(12)]
        prova={'2025-regular':dict(id='2025-regular')}
        with patch('lista_enem.preparar_imagem',return_value=(Image.new('RGB',(500,600),'white'),
                dict(largura=250,altura=280,escala=1))):
            dados,imagens,ordem=gerar_lista(qs,prova)
        self.assertEqual(len(imagens),2);self.assertEqual(len(ordem),12)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'lista.pdf';salvar_lista(path,dados,ordem,prova)
            self.assertEqual(path.read_bytes(),dados)
            self.assertEqual(len(json.loads(path.with_suffix('.json').read_text())['questoes']),12)

    def test_vazia(self):
        with self.assertRaises(ValueError):gerar_lista([],{})


if __name__=='__main__':unittest.main()
