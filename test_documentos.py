import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_graficos import Funcao, gerar_pdf
from parabolas import Parabola, salvar_documento
from triangulos import Triangulo, POSICOES
from solidos import Solido
from exponenciais import Exponencial, TIPOS
from documentos import carregar_documento, dados_documento, validar_documento, publicar_par


class DocumentosTests(unittest.TestCase):
    def setUp(self):
        self.paginas=[
            (1,[Funcao(3,5,[]),Funcao(-2,6,[-1,0,2])],2,'Retas'),
            (2,[Parabola(1,-4,3,False,True,False,True)],1,'Parábolas'),
            (3,[Triangulo(45,POSICOES[5],'Cosseno','Cateto adjacente','√3/3')],1,'Triângulos'),
            (4,[Solido('Cone',{'d':'10','g':'13'},'Diâmetro','Geratriz')],1,'Sólidos'),
            (5,[Exponencial(TIPOS[1],'1/2','-√3/3',[-1,0,2])],2,'Exponenciais')]

    def test_exportar_e_reabrir_cinco_abas(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'atividade.pdf'
            salvar_documento(path,self.paginas)
            self.assertTrue(path.read_bytes().startswith(b'%PDF'))
            restaurado=carregar_documento(path.with_suffix('.json'))
            self.assertEqual(restaurado,self.paginas)
            salvar_documento(Path(tmp)/'reaberto.pdf',restaurado)

    def test_exportacao_direta_tambem_gera_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'retas.pdf'
            _,itens,colunas,titulo=self.paginas[0]
            gerar_pdf(path,itens,colunas,titulo)
            self.assertEqual(carregar_documento(path.with_suffix('.json')),[self.paginas[0]])

    def test_rejeita_documento_invalido(self):
        for alteracao in ('versao','colunas','pontos','marcacao'):
            data=dados_documento(self.paginas)
            if alteracao=='versao': data['versao']=99
            elif alteracao=='colunas': data['paginas'][4]['colunas']=3
            elif alteracao=='pontos': data['paginas'][0]['itens'][0]['xs']=[float('nan')]
            else: data['paginas'][1]['itens'][0]['raizes']='false'
            with self.subTest(alteracao=alteracao),self.assertRaises(ValueError): validar_documento(data)

    def test_falha_na_publicacao_preserva_par_anterior(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'atividade.pdf'; side=path.with_suffix('.json')
            path.write_bytes(b'pdf antigo'); side.write_text('json antigo')
            novo=Path(tmp)/'novo.pdf'; novo.write_bytes(b'pdf novo')
            import os
            original=os.replace
            def substituir(src,dst):
                if Path(dst)==path: raise OSError('falha simulada')
                return original(src,dst)
            with patch('documentos.os.replace',side_effect=substituir),self.assertRaises(OSError):
                publicar_par(novo,path,self.paginas)
            self.assertEqual(path.read_bytes(),b'pdf antigo')
            self.assertEqual(side.read_text(),'json antigo')


if __name__=='__main__': unittest.main()
