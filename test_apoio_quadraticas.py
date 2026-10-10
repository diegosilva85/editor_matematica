import unittest
from unittest.mock import Mock
import tkinter as tk
from apoio_quadraticas import calcular
from contextos_quadraticas import CENARIOS, orientacao
from janelas import maximizar


class ApoioTests(unittest.TestCase):
    def campos(self,**kwargs):
        return dict(a='1',b='-6',c='13',cenario='Cabo suspenso',**kwargs)

    def test_cabo_valido(self):
        resultado,aviso=calcular(self.campos())
        self.assertIn('Não há raízes reais',resultado)
        self.assertIn('V = (3; 4)',resultado)
        self.assertIn('compatíveis',aviso)

    def test_invalido_ainda_calcula(self):
        campos=self.campos();campos['c']='5'
        resultado,aviso=calcular(campos)
        self.assertIn('x₁ = 1',resultado)
        self.assertIn('yv = -4',resultado)
        self.assertIn('aumente c',aviso)

    def test_raizes_ignorando_campos_desabilitados(self):
        resultado,aviso=calcular(dict(a='-1/2',b='',c='',modo='Raízes e a',raiz1='0',raiz2='6',cenario='Chute do goleiro'))
        self.assertIn('V = (3; 4,5)',resultado)
        self.assertIn('compatíveis',aviso)
        _,aviso=calcular(dict(a='1',modo='Raízes e a',raiz1='2',raiz2='4',cenario='Cabo suspenso'))
        self.assertIn('Troque para Coeficientes',aviso)

    def test_digitacao_parcial_e_formatos(self):
        for a in ('','-','1/','0','1/0'):
            resultado,aviso=calcular(dict(a=a,b='0',c='0'))
            self.assertIn('Preencha',resultado)
            self.assertTrue(aviso)
        resultado,_=calcular(dict(a='0,5',b='0',c='-√2'))
        self.assertIn('x₁',resultado)
        resultado,_=calcular(dict(a='1',modo='Raízes e a',quantidade_raizes='1',raiz1='√2',raiz2=''))
        self.assertIn('Raiz dupla',resultado)

    def test_orientacoes(self):
        for c in CENARIOS: self.assertTrue(orientacao(c))
        self.assertIn('não há raízes reais',orientacao('Cabo suspenso'))

    def test_maximizar(self):
        janela=Mock(); maximizar(janela)
        janela.after_idle.call_args.args[0]()
        janela.state.assert_called_with('zoomed')
        janela.state.side_effect=tk.TclError()
        janela.after_idle.call_args.args[0]()
        janela.attributes.assert_called_with('-zoomed',True)
        janela.attributes.side_effect=tk.TclError()
        janela.winfo_screenwidth.return_value=1920; janela.winfo_screenheight.return_value=1080
        janela.after_idle.call_args.args[0]()
        janela.geometry.assert_called_with('1920x1080+0+0')


if __name__=='__main__': unittest.main()
