import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from progressao import Progressao, PADRAO, numero
from documentos import carregar_documento, dados_documento, validar_documento
from parabolas import salvar_documento


def questao(tipo='Termo geral',alvo='aj',**values):
    return Progressao(tipo,alvo,{**PADRAO,**values},
                      ','.join(k for k in ('a1','an','n','sn') if k!=alvo))


class ProgressaoTests(unittest.TestCase):
    def test_preserva_formato_digitado(self):
        for value in ('7,6','7,60','7.6','38/5','76/10'):
            with self.subTest(value=value):
                item=questao(ai=value)
                self.assertIn('= '+value,item.enunciado())
                soma=questao('Soma dos termos','sn',a1=value)
                self.assertIn('primeiro termo é '+value,soma.enunciado())
        self.assertNotIn('38/5',questao(ai='7,6').enunciado())

    def test_termo_geral(self):
        self.assertEqual(questao().resolver(),29)
        self.assertEqual(questao(alvo='r').resolver(),3)
        self.assertEqual(questao(alvo='j').resolver(),10)
        self.assertEqual(questao(i='5',ai='14',j='1',r='3').resolver(),2)
        self.assertEqual(questao(ai='1/2',r='-1/3',j='4').resolver(),Fraction(-1,2))
        self.assertEqual(questao(r='0').resolver(),2)

    def test_soma_todas_incognitas(self):
        for key,expected in [('a1',2),('an',29),('n',10),('sn',155)]:
            with self.subTest(alvo=key):
                self.assertEqual(questao('Soma dos termos',key).resolver(),expected)
        self.assertEqual(questao('Soma dos termos','sn',a1='-3',an='3',n='5').resolver(),0)
        self.assertEqual(questao('Soma dos termos','sn',a1='1/2',an='3/2',n='3').resolver(),3)

    def test_soma_com_razao(self):
        cases=[('sn','a1,n,r',155),('sn','an,n,r',155),
               ('sn','a1,an,r',155),('a1','sn,n,r',2),
               ('an','sn,n,r',29),('n','a1,sn,r',10),
               ('n','a1,an,r',10),('sn','a1,an,n,r',155)]
        for target,selected,expected in cases:
            with self.subTest(target=target,selected=selected):
                item=questao('Soma dos termos',target)
                item.indicados=selected
                self.assertEqual(item.resolver(),expected)
                self.assertIn('a razão é 3',item.enunciado())
        for reason in ('7,6','7,60','38/5'):
            item=questao('Soma dos termos','sn',r=reason,an='IGNORADO')
            item.indicados='a1,n,r'
            self.assertIn('a razão é '+reason,item.enunciado())

    def test_soma_descobrir_razao(self):
        for selected in ('a1,n,sn','an,n,sn','a1,an,sn','a1,an,n','a1,an,n,sn'):
            with self.subTest(selected=selected):
                item=questao('Soma dos termos','r',r='VALOR_OCULTO')
                item.indicados=selected
                self.assertEqual(item.resolver(),3)
                self.assertIn('Determine a razão dessa progressão.',item.enunciado())
                self.assertNotIn('VALOR_OCULTO',item.enunciado())
        for first,total,expected in [('29','155',-3),('2','20',0),('1/2','55/2',Fraction(1,2))]:
            item=questao('Soma dos termos','r',a1=first,sn=total)
            item.indicados='a1,n,sn'
            self.assertEqual(item.resolver(),expected)
        for selected in ('a1,n,sn','a1,an,n,sn','a1,an,sn'):
            item=questao('Soma dos termos','r',a1='7',an='7',n='1',sn='7')
            item.indicados=selected
            with self.assertRaises(ValueError): item.validar()
        item=questao('Soma dos termos','r')
        item.indicados='a1,n,sn,r'
        with self.assertRaises(ValueError): item.validar()

    def test_soma_razao_inconsistente_ou_ambigua(self):
        item=questao('Soma dos termos','sn',r='4')
        item.indicados='a1,an,n,r'
        with self.assertRaises(ValueError): item.validar()
        item=questao('Soma dos termos','n',a1='5',r='-1',sn='9')
        item.indicados='a1,r,sn'  # n = 2 ou n = 9.
        with self.assertRaises(ValueError): item.validar()
        item=questao('Soma dos termos','n',a1='2',r='0',sn='20')
        item.indicados='a1,r,sn'
        self.assertEqual(item.resolver(),10)
        item=questao('Soma dos termos','sn',r='-3',a1='29')
        item.indicados='a1,n,r'
        self.assertEqual(item.resolver(),155)

    def test_rejeita_dados_invalidos(self):
        bad=[questao(alvo='r',j='1'),questao(alvo='j',r='0'),
             questao(alvo='j',aj='30'),questao(j='0'),questao(j='2.5'),
             questao('Soma dos termos','n',a1='-2',an='2',sn='0'),
             questao('Soma dos termos','n',sn='1'),
             questao('Soma dos termos','sn',n='1'),questao(r='1e999999999')]
        for item in bad:
            with self.subTest(item=item),self.assertRaises(ValueError): item.validar()
        for selected in ('a1,an','a1,an,n,sn','a1,a1,n','foo'):
            item=questao('Soma dos termos','sn'); item.indicados=selected
            with self.assertRaises(ValueError): item.validar()

    def test_um_termo(self):
        for key in ('a1','an','n','sn'):
            self.assertEqual(questao('Soma dos termos',key,a1='7',an='7',n='1',sn='7').resolver(),
                             1 if key=='n' else 7)

    def test_incognita_nao_e_lida_ou_revelada(self):
        for tipo,keys in [('Termo geral',('aj','j','r')),('Soma dos termos',('a1','an','n','sn'))]:
            for key in keys:
                item=questao(tipo,key,**{key:'VALOR_OCULTO'})
                text=item.enunciado()
                self.assertNotIn('VALOR_OCULTO',text)
                self.assertNotIn('Resposta',text)

    def test_pdf_json_seis_abas(self):
        from test_documentos import DocumentosTests
        fixture=DocumentosTests(); fixture.setUp()
        items=[questao(alvo=k) for k in ('aj','j','r')]
        items += [questao('Soma dos termos',k) for k in ('a1','an','n','sn')]
        com_razao=questao('Soma dos termos','sn',r='7,6')
        com_razao.indicados='a1,n,r'
        items.append(com_razao)
        descobrir_razao=questao('Soma dos termos','r')
        descobrir_razao.indicados='a1,n,sn'
        items.append(descobrir_razao)
        pages=fixture.paginas+[(6,items,2,'Progressão aritmética')]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'pa.pdf'
            salvar_documento(path,pages)
            self.assertEqual(carregar_documento(path.with_suffix('.json')),pages)
        invalid=dados_documento(pages); invalid['paginas'][-1]['colunas']=3
        with self.assertRaises(ValueError): validar_documento(invalid)


if __name__=='__main__': unittest.main()
