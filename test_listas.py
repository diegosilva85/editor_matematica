import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from listas import Lista,dados_lista,validar_lista,carregar_lista,pdf_lista,salvar_lista,planejar
from progressao import Progressao
import test_documentos
from test_contextos import exemplos as triangulos_contextuais
from test_contextos_pa import exemplos as pa_contextuais


def exemplo_lista():
    fixture=test_documentos.DocumentosTests(); fixture.setUp()
    items=[(grau,item) for grau,itens,_,_ in fixture.paginas for item in itens]
    items += [(6,Progressao()),(3,triangulos_contextuais()[0]),(6,pa_contextuais()[0])]
    items += [(6,replace(pa_contextuais()[1],tipo='Soma dos termos',incognita='sn',indicados='a1,n,r'))]
    return Lista('Lista mista de exercícios',3,12,items*2)


class ListasTests(unittest.TestCase):
    def test_limites_alinhamento_e_ordem(self):
        for cols in (1,2,3):
            for limit in (1,5,12):
                lista=exemplo_lista(); lista.colunas=cols; lista.por_pagina=limit
                pages=planejar(lista)
                self.assertEqual([cell[0] for page in pages for cell in page],list(range(len(lista.itens))))
                for page in pages:
                    self.assertLessEqual(len(page),limit)
                    rows={}
                    for i,x,y,w,h,th,gh in page:
                        self.assertGreaterEqual(y,40); self.assertLessEqual(x+w,566)
                        rows.setdefault(y,[]).append((x,w,h))
                    for row in rows.values():
                        self.assertLessEqual(len(row),cols)
                        self.assertEqual(len(set(h for x,w,h in row)),1)

    def test_pdf_json_reabertura(self):
        import pypdfium2 as pdfium
        lista=exemplo_lista()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'lista.pdf'; salvar_lista(path,lista)
            self.assertEqual(carregar_lista(path.with_suffix('.json')),lista)
            with pdfium.PdfDocument(path) as doc:
                self.assertEqual(len(doc),len(planejar(lista)))
                text=''
                for page in doc:
                    tp=page.get_textpage(); text+=tp.get_text_range(); tp.close(); page.close()
                self.assertIn('20.',text)
                self.assertNotIn('(a)',text)
            for cols in (1,2):
                lista.colunas=cols
                self.assertTrue(pdf_lista(lista).startswith(b'%PDF'))

    def test_importa_json_antigo(self):
        from documentos import dados_documento
        fixture=test_documentos.DocumentosTests(); fixture.setUp()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'antigo.json'; path.write_text(json.dumps(dados_documento(fixture.paginas)))
            lista=carregar_lista(path)
            self.assertEqual(len(lista.itens),6)

    def test_rejeita_invalido(self):
        for field,value in [('colunas',4),('por_pagina',13),('itens',[]),('versao',2),('colunas',True)]:
            data=dados_lista(exemplo_lista()); data[field]=value
            with self.assertRaises(ValueError): validar_lista(data)
        data=dados_lista(exemplo_lista()); data['itens'][0]['conteudo']=99
        with self.assertRaises(ValueError): validar_lista(data)


if __name__=='__main__': unittest.main()
