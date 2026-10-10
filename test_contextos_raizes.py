import unittest
from dataclasses import asdict
from contextos_raizes import CENARIOS
from contextos_quadraticas import grupo,cenarios_grupo,imagem,orientacao
from parabolas import Parabola
from documentos import dados_documento,validar_documento
from listas import Lista,dados_lista,validar_lista,pdf_lista
from apoio_quadraticas import calcular

COEFICIENTES=((-5,15,20),(-1,14,-40),(1,-8,12),(-1,10,-16),(1,-7,10),(1,-7,6))

def exemplos():
    return [Parabola(*abc,apresentacao='Expressão da função',cenario=c,alvo_contexto='Raízes',incluir_imagem=True)
            for c,abc in zip(CENARIOS,COEFICIENTES)]


class RaizesTests(unittest.TestCase):
    def test_separacao(self):
        self.assertFalse(set(cenarios_grupo('Raízes')) & set(cenarios_grupo('Vértice')))
        for q in exemplos():
            self.assertEqual(grupo(q.cenario,q.alvo_contexto),'Raízes')
            q.alvo_contexto='yv'
            with self.assertRaises(ValueError): q.dados()

    def test_textos_imagens_orientacoes(self):
        for i,q in enumerate(exemplos()):
            q.dados()
            texto=q.enunciado()
            self.assertIn('f(x)',texto)
            self.assertNotIn('vértice',texto)
            self.assertNotIn('{f}',texto)
            self.assertTrue(orientacao(q.cenario))
            if i in (1,2): self.assertIsNone(imagem(q))
            else: self.assertTrue(imagem(q).is_file())
            q.incluir_imagem=False; self.assertIsNone(imagem(q))

    def test_raizes_e_a_e_apoio(self):
        for q in exemplos():
            _,_,roots=q.dados()
            q.modo='Raízes e a';q.raiz1=str(roots[0]);q.raiz2=str(roots[1])
            self.assertEqual(q.dados()[2],roots)
            campos={k:str(v) for k,v in asdict(q).items()}
            _,aviso=calcular(campos)
            self.assertIn('compatíveis',aviso)
            q.quantidade_raizes='1'
            with self.assertRaises(ValueError): q.dados()

    def test_json_aba_lista_legado(self):
        itens=exemplos()
        restored=validar_documento(dados_documento([(2,itens,2,'Teste')]))[0][1]
        self.assertEqual([asdict(q) for q in restored],[asdict(q) for q in itens])
        lista=validar_lista(dados_lista(Lista(itens=[(2,q) for q in itens])))
        self.assertEqual(len(lista.itens),6)
        q=Parabola(-1,10,0,apresentacao='Expressão da função',cenario='Chute do goleiro',alvo_contexto='Raízes')
        validar_documento(dados_documento([(2,[q],2,'Legado')]))


if __name__=='__main__': unittest.main()
