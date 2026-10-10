import unittest
from progressao import Progressao,PADRAO
from apoio_pa import calcular


class ApoioPATests(unittest.TestCase):
    def test_termo_e_contexto(self):
        q=Progressao(apresentacao='Contextual')
        texto,aviso,dica=calcular(q)
        self.assertIn('29',texto);self.assertIn('Razão = 3',texto)
        self.assertIn('compatíveis',aviso); self.assertIn('positivas',dica)
        q.valores['r']='-3'
        texto,aviso,_=calcular(q)
        self.assertIn('-25',texto);self.assertIn('Ajuste',aviso)

    def test_soma_incognitas(self):
        for alvo,indicados in [('sn','a1,an,n'),('a1','an,n,sn'),('an','a1,n,sn'),('n','a1,an,sn'),('r','a1,n,sn')]:
            q=Progressao(tipo='Soma dos termos',incognita=alvo,indicados=indicados,apresentacao='Contextual')
            texto,aviso,_=calcular(q)
            self.assertIn('Sₙ = 155',texto)
            self.assertIn('compatíveis',aviso)

    def test_posicao_razao_e_campos_ocultos(self):
        for alvo in ('j','r'):
            q=Progressao(incognita=alvo,apresentacao='Contextual')
            q.valores[alvo]='inválido'
            texto,aviso,_=calcular(q)
            self.assertIn('compatíveis',aviso)
            self.assertIn('Razão = 3',texto)

    def test_dados_incompletos(self):
        q=Progressao(apresentacao='Contextual');q.valores['r']='1/'
        texto,aviso,dica=calcular(q)
        self.assertIn('Preencha',texto);self.assertTrue(aviso);self.assertTrue(dica)
        q=Progressao(tipo='Soma dos termos',incognita='sn',indicados='a1',apresentacao='Contextual')
        self.assertIn('Preencha',calcular(q)[0])

    def test_orientacoes_especificas(self):
        q=Progressao(apresentacao='Contextual',cenario='Plantio de sementes',unidade='sementes')
        self.assertIn('inteiras',calcular(q)[2])
        q.cenario='Parcelas de uma compra';q.unidade='reais';q.periodo='parcela'
        self.assertIn('negativa',calcular(q)[2]);self.assertIn('0,01',calcular(q)[2])


if __name__=='__main__': unittest.main()
