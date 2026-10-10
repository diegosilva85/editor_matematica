import unittest
from dataclasses import asdict
from contextos_quadraticas import CENARIOS, ALVOS, imagem
from parabolas import Parabola
from documentos import dados_documento, validar_documento
from listas import Lista, pdf_lista, planejar, dados_lista, validar_lista


def questao(cenario, **kwargs):
    minimo=cenario in ('Cabo suspenso','Temperatura de uma câmara fria')
    return Parabola(1 if minimo else -1,-10 if minimo else 10,30 if minimo else 0,
                    apresentacao='Expressão da função',cenario=cenario,**kwargs)


class ContextosQuadraticasTests(unittest.TestCase):
    def test_cenarios_e_alvos(self):
        for c in CENARIOS[1:]:
            for alvo in ALVOS:
                q=questao(c,alvo_contexto=alvo)
                if alvo=='Raízes' and c in ('Cabo suspenso','Temperatura de uma câmara fria'):
                    q.c=-1 if c.startswith('Temperatura') else 30
                q.dados()
                text=q.enunciado()
                self.assertIn('f(x)',text)
                self.assertNotIn('{f}',text)
                self.assertNotIn('Determine as raízes',text if alvo!='Raízes' else '')

    def test_json_abas_e_lista(self):
        q=questao('Saque de vôlei',incluir_imagem=True,alvo_contexto='yv',eixo_contexto='Tempo')
        doc=validar_documento(dados_documento([(2,[q],1,'Teste')]))
        self.assertEqual(asdict(q),asdict(doc[0][1][0]))
        lista=validar_lista(dados_lista(Lista(itens=[(2,q)])))
        self.assertEqual(asdict(q),asdict(lista.itens[0][1]))

    def test_imagens_opcionais(self):
        for c in CENARIOS:
            q=questao(c)
            self.assertIsNone(imagem(q))
            q.incluir_imagem=True
            if imagem(q): self.assertTrue(imagem(q).is_file())
            q.apresentacao='Gráfico'
            self.assertIsNone(imagem(q))

    def test_layout_e_pdf(self):
        itens=[(2,questao(c,incluir_imagem=True)) for c in CENARIOS[1:]]
        for cols in (1,2,3):
            lista=Lista(colunas=cols,itens=itens)
            self.assertTrue(pdf_lista(lista).startswith(b'%PDF'))
            for page in planejar(lista):
                self.assertLessEqual(len(page),12)
                self.assertTrue(all(cell[2]>=40 for cell in page))
        q=questao('Saque de vôlei')
        self.assertEqual(planejar(Lista(itens=[(2,q)]))[0][0][-1],0)
        q.incluir_imagem=True
        self.assertGreater(planejar(Lista(itens=[(2,q)]))[0][0][-1],0)

    def test_validacao_e_legado(self):
        q=questao('Chute do goleiro'); q.a=1
        with self.assertRaises(ValueError): q.dados()
        q=questao('Jato de água'); q.incluir_imagem='sim'
        with self.assertRaises(ValueError): q.dados()
        self.assertIn('Dada a função',Parabola(1,3,2,apresentacao='Expressão da função').enunciado())


if __name__=='__main__': unittest.main()
