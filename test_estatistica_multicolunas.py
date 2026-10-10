import tempfile
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import pypdfium2 as pdfium
from estatistica import Estatistica,gerar,apoio,CONTEXTOS,tabela
from estatistica_multicolunas import COMPARACAO,FALTANTE,analisar,vencedores,redimensionar,CONTEXTOS_MULTIPLOS
from documentos import dados_documento,validar_documento,carregar_documento
from listas import Lista,dados_lista,validar_lista,pdf_lista,planejar
from parabolas import salvar_documento


def notas(**kwargs):
    return Estatistica(tipo=COMPARACAO,linhas=[['Ana','6','8','9','9'],['Bia','7','7','10','10'],
                                             ['Caio','8','8','8','8'],['Davi','5','6','7','8']],**kwargs)


class EstatisticaMulticolunasTests(unittest.TestCase):
    def test_comparacao_e_empates(self):
        q=notas();q.validar();s=q.resumo()
        self.assertEqual(s[0]['media'],8);self.assertEqual(s[0]['mediana'],Fraction(17,2))
        self.assertEqual(vencedores(q),dict(media=['Bia'],mediana=['Ana','Bia']))
        self.assertIn('empate',apoio(q)[0]);self.assertIn('todos',q.enunciado())
        q.pedir_media=False;self.assertNotIn('média aritmética',q.enunciado())
        q.pedir_mediana=False
        with self.assertRaises(ValueError):q.validar()

    def test_faltantes_exatos_sem_revelar_respostas(self):
        q=Estatistica(tipo=FALTANTE,linhas=[['Ana','6','7','8','','7,5'],['Bia','4','5','6','?','6']],pedir_media=False,pedir_mediana=False,pedir_moda=False)
        q.validar();self.assertEqual([r['resposta'] for r in analisar(q)],[9,9])
        self.assertIn('valor faltante = 9',apoio(q)[0])
        self.assertNotIn('9',q.enunciado())
        with pdfium.PdfDocument(pdf_lista(Lista(itens=[(7,q)]))) as doc:
            page=doc[0];tp=page.get_textpage();text=tp.get_text_range();tp.close();page.close()
            self.assertIn('?',text);self.assertNotIn('valor faltante =',text)
            self.assertNotIn('9',text)
        q.linhas[0][-2]='9';q.validar()
        self.assertIsNone(analisar(q)[0]['resposta'])

    def test_inteiros_e_medias_fracionarias(self):
        q=Estatistica(tipo=FALTANTE,cenario='Pontuação no basquete',quantidade_medidas='2',linhas=[['A','10','','10,5'],['B','8','','8,5']])
        q.validar();self.assertEqual(analisar(q)[0]['resposta'],11)
        q.linhas[0][-1]='10,2'
        with self.assertRaisesRegex(ValueError,'inteiras'):q.validar()

    def test_dados_invalidos(self):
        q=notas()
        for bad in ('1','9','quatro'):
            with self.assertRaises(ValueError):replace(q,quantidade_medidas=bad).validar()
        for rows in ([['A','6','7','8'],['B','4','5','6']],
                     [['A','6','7','8','9'],['A','4','5','6','7']]):
            with self.assertRaises(ValueError):replace(q,linhas=rows).validar()
        for row in (['A','6','7','8','','10'],['A','','7','8','','7'],['A','6','7','8','9','1']):
            with self.assertRaises(ValueError):Estatistica(tipo=FALTANTE,linhas=[row,['B','4','5','6','','6']]).validar()

    def test_contextos_e_colunas(self):
        self.assertEqual(set(CONTEXTOS),set(CONTEXTOS_MULTIPLOS))
        for c in CONTEXTOS:
            for tipo in (COMPARACAO,FALTANTE):
                q=Estatistica(tipo=tipo,cenario=c)
                q.linhas=redimensionar(q,4,[]);q.validar()
                self.assertTrue(q.enunciado())
                self.assertEqual(len(q.cabecalhos()),6 if tipo==FALTANTE else 5)
        self.assertEqual(replace(notas(),cenario='Pontuação no basquete').cabecalhos()[1],'Partida 1')

    def test_redimensionar_preserva_media_e_incognita(self):
        q=Estatistica(tipo=FALTANTE,quantidade_medidas='6')
        rows=redimensionar(q,2,[['Ana','6','7','8','','7,5']])
        self.assertEqual(rows[0][:4],['Ana','6','7','8']);self.assertEqual(rows[0][-2:],['','7,5'])
        self.assertEqual(len(rows[0]),8)
        q.quantidade_medidas='2';rows=redimensionar(q,2,rows)
        self.assertEqual(rows[0],['Ana','6','','7,5'])

    def test_geracao_com_metas_por_linha(self):
        for tipo in (COMPARACAO,FALTANTE):
            q=Estatistica(tipo=tipo,meta_media='6',passo='1')
            original=[row[:] for row in q.linhas]
            rows=gerar(q,4,seed=17)
            out=replace(q,linhas=rows);out.validar()
            self.assertTrue(all(s['media']==6 for s in analisar(out)))
            self.assertEqual(q.linhas,original)
            if tipo==FALTANTE:self.assertTrue(all(row[-2]=='' and row[-1]=='6' for row in rows))
        q=Estatistica(tipo=FALTANTE,linhas=[['Ana','1','2','3','','5'],['Bia','2','3','4','','7']],passo='1')
        out=replace(q,linhas=gerar(q,2,seed=23))
        self.assertEqual([s['media'] for s in analisar(out)],[5,7])
        q.meta_media='1/3'
        with self.assertRaises(ValueError):gerar(q,2,seed=1)

    def test_json_legado_e_misto_e_pdf_largo(self):
        q=notas();wide=replace(q,quantidade_medidas='8')
        wide.linhas=redimensionar(wide,20,[])
        lista=Lista(colunas=3,itens=[(7,q),(7,wide)])
        self.assertEqual(validar_lista(dados_lista(lista)),lista)
        self.assertTrue(all(len(set(cell[1] for cell in page))==1 for page in planejar(lista)))
        page=(7,[q,wide,wide],2,'Tabelas de estatística')
        self.assertEqual(validar_documento(dados_documento([page])),[page])
        legacy=dados_documento([(7,[Estatistica()],2,'Antigo')]);del legacy['paginas'][0]['itens'][0]['quantidade_medidas']
        self.assertEqual(validar_documento(legacy)[0][1][0].tipo,'Simples')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'stats.pdf';salvar_documento(path,[page])
            self.assertEqual(carregar_documento(path.with_suffix('.json')),[page])
            with pdfium.PdfDocument(path) as doc:self.assertGreaterEqual(len(doc),2)
        self.assertGreater(tabela(wide,515).wrap(515,10000)[1],0)


if __name__=='__main__':unittest.main()
