import unittest
from dataclasses import replace
from io import BytesIO
from contextos_pa import CENARIOS
from progressao import Progressao, PADRAO, desenhar_pagina
from documentos import dados_documento, validar_documento


def exemplos():
    result=[]
    for i,(name,c) in enumerate(CENARIOS.items()):
        r=-5 if c['sentido']==-1 else 5
        result.append(Progressao(incognita=('aj','j','r')[i%3],
            valores={**PADRAO,'ai':'100','i':'1','j':'5','aj':str(100+4*r),'r':str(r)},
            apresentacao='Contextual',cenario=name,periodo=c['periodos'][0],unidade=c['unidades'][0]))
    return result


class ContextosPATests(unittest.TestCase):
    def test_preserva_decimais_fracoes_e_variacao(self):
        t=exemplos()[0]
        for value in ('7,6','7,60','38/5'):
            item=replace(t,valores={**t.valores,'ai':value,'r':'0,5'})
            text=item.enunciado()
            self.assertIn('foi de '+value+' metros',text)
            self.assertIn('aumenta em 0,5 metros',text)
        item=replace(t,valores={**t.valores,'r':'-0,50'})
        self.assertIn('diminui em 0,50 metros',item.enunciado())
        money=replace(exemplos()[1],incognita='aj',valores={**t.valores,'ai':'7,60','r':'1/2'})
        self.assertIn('7,60 reais',money.enunciado())
        self.assertIn('aumenta em 1/2 reais',money.enunciado())

    def test_todos_contextos_e_incognitas_sem_revelar_resposta(self):
        self.assertEqual(len(exemplos()),11)
        for t in exemplos():
            for target in ('aj','j','r'):
                item=replace(t,incognita=target,valores={**t.valores,target:'NAO_MOSTRAR'})
                item.validar()
                text=item.enunciado()
                self.assertNotIn('NAO_MOSTRAR',text)
                self.assertNotIn('progressão aritmética',text)
                self.assertIn('Determine a variação' if target=='r' else ('Qual será' if target=='aj' else 'Em qual'),text)

    def test_variantes(self):
        for t in exemplos():
            for period in CENARIOS[t.cenario]['periodos']:
                for unit in CENARIOS[t.cenario]['unidades']:
                    item=replace(t,periodo=period,unidade=unit)
                    self.assertIn(unit,item.enunciado())
        atleta=replace(exemplos()[0],atividade='natação')
        self.assertIn('programa de natação',atleta.enunciado())
        ciclista=replace(exemplos()[5],unidade='horas')
        self.assertIn('tempo de treino',ciclista.enunciado())

    def test_validacoes_contextuais(self):
        athlete=exemplos()[0]
        cases=[replace(athlete,unidade='reais'),replace(athlete,periodo='mês'),
               replace(athlete,valores={**athlete.valores,'i':'10','ai':'2'}),
               replace(athlete,valores={**athlete.valores,'r':'-30'}),
               replace(athlete,valores={**athlete.valores,'r':'0'}),
               replace(exemplos()[3],incognita='aj',valores={**PADRAO,'ai':'100','r':'1/2'}),
               replace(exemplos()[3],incognita='r',valores={**PADRAO,'ai':'100','aj':'110','j':'4'}),
               replace(exemplos()[10],incognita='aj',valores={**PADRAO,'ai':'100','r':'1'}),
               replace(exemplos()[1],incognita='aj',valores={**PADRAO,'ai':'100','r':'1/3'})]
        for item in cases:
            with self.subTest(cenario=item.cenario),self.assertRaises(ValueError): item.validar()

    def test_soma_todos_contextos_e_alvos(self):
        for t in exemplos():
            r=int(t.valores['r'])
            values={**PADRAO,'a1':'100','an':str(100+4*r),'n':'5','sn':str(500+10*r),'r':str(r)}
            for target in ('a1','an','n','sn','r'):
                selected='a1,n,sn' if target=='r' else ','.join(k for k in ('a1','an','n','sn') if k!=target)
                item=replace(t,tipo='Soma dos termos',incognita=target,indicados=selected,
                             valores={**values,target:'NAO_MOSTRAR'})
                with self.subTest(cenario=t.cenario,alvo=target):
                    text=item.enunciado()
                    self.assertNotIn('NAO_MOSTRAR',text)
                    self.assertIn('total',text)
                    pages=[(6,[item],2,'PA')]
                    self.assertEqual(validar_documento(dados_documento(pages)),pages)
            item=replace(t,tipo='Soma dos termos',incognita='sn',indicados='a1,n,r',
                         valores={**values,'an':'NAO_MOSTRAR','sn':'NAO_MOSTRAR'})
            self.assertNotIn('NAO_MOSTRAR',item.enunciado())

    def test_soma_variantes_e_validacao(self):
        t=replace(exemplos()[5],tipo='Soma dos termos',incognita='sn',indicados='a1,n,r',
                  unidade='horas',valores={**PADRAO,'a1':'7,60','r':'1/2'})
        text=t.enunciado()
        self.assertIn('tempo total de treino',text)
        self.assertIn('7,60 horas',text)
        self.assertIn('1/2 horas',text)
        for index,changes in [(3,{'r':'1/2'}),(1,{'r':'1/3'}),(10,{'r':'3'}),(0,{'a1':'2','r':'-3'})]:
            item=replace(exemplos()[index],tipo='Soma dos termos',incognita='sn',indicados='a1,n,r',
                         valores={**PADRAO,**changes})
            with self.assertRaises(ValueError): item.validar()

    def test_soma_paginacao(self):
        from reportlab.pdfgen.canvas import Canvas
        items=[]
        for t in exemplos():
            r=int(t.valores['r'])
            items.append(replace(t,tipo='Soma dos termos',incognita='r',indicados='a1,an,n,sn',
                         valores={**PADRAO,'a1':'100','an':str(100+4*r),'n':'5','sn':str(500+10*r)}))
        pdf=Canvas(BytesIO()); desenhar_pagina(pdf,items,2,'PA')
        self.assertEqual(pdf.getPageNumber(),2)

    def test_json_compatibilidade_e_paginacao(self):
        items=exemplos()+[Progressao()]
        pages=[(6,items,2,'PA')]
        self.assertEqual(validar_documento(dados_documento(pages)),pages)
        old=dados_documento([(6,[Progressao()],2,'PA')])
        for k in ('apresentacao','cenario','periodo','unidade','atividade'):
            del old['paginas'][0]['itens'][0][k]
        self.assertEqual(validar_documento(old)[0][1],[Progressao()])
        from reportlab.pdfgen.canvas import Canvas
        pdf=Canvas(BytesIO()); desenhar_pagina(pdf,items,2,'PA')
        self.assertEqual(pdf.getPageNumber(),2)
        pdf=Canvas(BytesIO()); desenhar_pagina(pdf,items,1,'PA')
        self.assertEqual(pdf.getPageNumber(),4)


if __name__=='__main__': unittest.main()
