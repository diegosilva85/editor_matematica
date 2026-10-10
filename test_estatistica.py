import unittest
import tempfile
from pathlib import Path
from dataclasses import replace
from fractions import Fraction
from collections import Counter
import pypdfium2 as pdfium
from estatistica import Estatistica,CONTEXTOS,TIPOS,gerar,resumir,apoio
from documentos import dados_documento,validar_documento,carregar_documento
from listas import Lista,dados_lista,validar_lista,pdf_lista,planejar
from parabolas import salvar_documento


class EstatisticaTests(unittest.TestCase):
    def test_simples(self):
        q=Estatistica()
        self.assertEqual(q.resumo(),dict(media=Fraction(37,5),mediana=Fraction(7),modas=[Fraction(7)],total=5))

    def test_frequencia_ponderada_sem_expandir(self):
        q=Estatistica(tipo='Frequência',linhas=[['1','100000'],['9','1']])
        s=q.resumo()
        self.assertEqual(s['media'],Fraction(100009,100001))
        self.assertEqual(s['mediana'],1);self.assertEqual(s['modas'],[1])

    def test_mediana_par_amodal_multimodal_constante(self):
        s=resumir(Counter({Fraction(1):1,Fraction(2):1,Fraction(8):1,Fraction(9):1}))
        self.assertEqual(s['mediana'],5);self.assertEqual(s['modas'],[])
        self.assertEqual(resumir(Counter({Fraction(1):2,Fraction(3):2,Fraction(6):1}))['modas'],[1,3])
        self.assertEqual(resumir(Counter({Fraction(3):5}))['modas'],[3])

    def test_decimais_selecoes(self):
        q=Estatistica(linhas=[['Ana','7,6'],['Bia','38/5']],pedir_moda=False,pedir_mediana=False)
        self.assertEqual(q.resumo()['media'],Fraction(38,5))
        self.assertIn('média.',q.enunciado());self.assertNotIn('mediana',q.enunciado())
        q.pedir_media=False
        with self.assertRaises(ValueError): q.validar()

    def test_dez_contextos_nos_dois_tipos(self):
        self.assertEqual(len(CONTEXTOS),10)
        for c in CONTEXTOS:
            for tipo in TIPOS:
                rows=[['A','2'],['B','4']] if tipo=='Simples' else [['2','3'],['4','1']]
                q=Estatistica(cenario=c,tipo=tipo,linhas=rows)
                q.validar();self.assertIn('tabela',q.enunciado())
        self.assertIn('não os gêneros',Estatistica(cenario='Hábitos musicais').enunciado())

    def test_invalidos(self):
        for rows in ([['A','-1'],['B','2']],[['A','11'],['B','2']],[['A','2'],['A','3']]):
            with self.assertRaises(ValueError): Estatistica(linhas=rows).validar()
        for rows in ([['1','0'],['2','3']],[['1','1/2'],['2','3']],[['1','2'],['1,0','3']]):
            with self.assertRaises(ValueError): Estatistica(tipo='Frequência',linhas=rows).validar()
        with self.assertRaises(ValueError): Estatistica(cenario='Livros lidos',linhas=[['A','1,5'],['B','2']]).validar()

    def test_gerador_metas_exatas(self):
        for tipo,media,moda,mediana,total,n in [('Simples','5','4','4','5',5),('Frequência','4','4','4','10',3)]:
            q=Estatistica(tipo=tipo,meta_media=media,meta_moda=moda,meta_mediana=mediana,observacoes=total,passo='1')
            original=[row[:] for row in q.linhas]
            rows=gerar(q,n,seed=17);s=replace(q,linhas=rows).resumo()
            self.assertEqual(len(rows),n)
            self.assertEqual(s['media'],int(media));self.assertEqual(s['mediana'],int(mediana));self.assertEqual(s['modas'],[int(moda)])
            self.assertEqual(q.linhas,original)

    def test_gerador_livre_e_metas_individuais(self):
        for tipo in TIPOS:
            for key in ('','meta_media','meta_moda','meta_mediana'):
                q=Estatistica(tipo=tipo,passo='1')
                if key: setattr(q,key,'5')
                rows=gerar(q,5,seed=11)
                final=replace(q,linhas=rows);final.validar()
                if key: self.assertIn('atingida',apoio(final)[0])

    def test_gerador_impossivel_e_preservacao(self):
        q=Estatistica(meta_media='1/3',passo='1')
        original=[row[:] for row in q.linhas]
        with self.assertRaises(ValueError): gerar(q,5,seed=1)
        self.assertEqual(q.linhas,original)
        with self.assertRaises(ValueError): gerar(Estatistica(tipo='Frequência',observacoes='2'),5)
        with self.assertRaises(ValueError): gerar(Estatistica(passo='0'),5)

    def test_json_lista_pdf(self):
        q=Estatistica()
        page=(7,[q],2,'Estatística')
        self.assertEqual(validar_documento(dados_documento([page])),[page])
        lista=Lista(itens=[(7,q)]*5)
        self.assertEqual(validar_lista(dados_lista(lista)),lista)
        for p in planejar(lista):
            self.assertTrue(all(cell[2]>=40 for cell in p))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'stats.pdf';salvar_documento(path,[page])
            self.assertEqual(carregar_documento(path.with_suffix('.json')),[page])
            with pdfium.PdfDocument(pdf_lista(lista)) as doc:
                p=doc[0];tp=p.get_textpage();text=tp.get_text_range()
                self.assertIn('Aluno 1',text);self.assertNotIn('Média =',text)
                tp.close();p.close()

    def test_sete_abas_e_tabelas_longas(self):
        from test_documentos import DocumentosTests
        from progressao import Progressao
        base=DocumentosTests();base.setUp()
        q=Estatistica(cenario='Temperaturas diárias',linhas=[[f'Dia {i+1}',str(i-5)] for i in range(20)])
        pages=base.paginas+[(6,[Progressao()],2,'PA'),(7,[q],2,'Estatística')]
        self.assertEqual(len(validar_documento(dados_documento(pages))),7)
        lista=Lista(colunas=2,itens=[(7,q)]*5)
        with pdfium.PdfDocument(pdf_lista(lista)) as doc:
            self.assertEqual(len(doc),3)
        bad=dados_documento([(7,[q],2,'Estatística')]);bad['paginas'][0]['itens'][0]['linhas']=[['A','2','extra']]
        with self.assertRaises(ValueError): validar_documento(bad)


if __name__=='__main__': unittest.main()
