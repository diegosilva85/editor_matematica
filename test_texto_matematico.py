import unittest
from copy import deepcopy
from reportlab.lib.styles import ParagraphStyle
from texto_matematico import partes,caixa,AlternativaMatematica
from provas import Prova,QuestaoProva,pdf_prova,dados_prova,validar_prova
from progressao import Progressao


class MatematicaTests(unittest.TestCase):
    def test_operadores_e_grupos(self):
        for text,kind in [('x^2','power'),('x^{n+1}','power'),('3 over 4','fraction'),('(x+1) over (x-1)','fraction'),('2*x','row'),('2^(-3)','power')]:
            p=partes(text);self.assertEqual(len(p),1,text);self.assertEqual(p[0][0],kind)
            w,a,d,ops=caixa(p[0],12);self.assertGreater(w,0);self.assertGreater(a,0)
            if kind=='fraction':self.assertTrue(any(o[0]=='line' for o in ops))
        self.assertEqual(partes('Texto comum, over.'),['Texto comum, over.'])
        self.assertEqual(partes('Valor: 3 over 4.')[0],'Valor: ')

    def test_incompletos_e_protecao(self):
        for text in ('x^','3 over','(x+1','<img src="/etc/passwd">','__import__(os)'):
            a=AlternativaMatematica('a',text,ParagraphStyle('t',fontSize=12,leading=15));a.wrap(240,10000)
        with self.assertRaises(ValueError):partes('x^'+'{'*20+'2'+'}'*20)

    def test_altura_fonte_quebra_e_persistencia(self):
        def alt(text,size=12):
            a=AlternativaMatematica('b',text,ParagraphStyle('t',fontSize=size,leading=size*1.22));a.wrap(240,10000);return a
        self.assertGreater(alt('1 over 2').height,alt('12').height)
        self.assertGreater(alt('x^2',18).height,alt('x^2',9).height)
        self.assertGreater(len(alt('texto '*40).rows),1)
        q=QuestaoProva(Progressao(),alternativas=['x^2','1 over 2','2*x','(x+1) over (x-1)','2^{n+1}'])
        p=Prova(itens=[(6,q)]);before=deepcopy(dados_prova(p))
        self.assertTrue(pdf_prova(p).startswith(b'%PDF'));self.assertEqual(dados_prova(p),before)
        self.assertEqual(validar_prova(before),p)


if __name__=='__main__':unittest.main()
