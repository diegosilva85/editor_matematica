import unittest
from dataclasses import asdict
from unittest.mock import Mock,patch
import tkinter as tk
from apoio_funcoes import calcular
from triangulos import Triangulo,POSICOES,PITAGORAS
from exponenciais import TIPOS


def campos(q):
    return {k:str(v) for k,v in asdict(q).items()}


class ApoioFuncoesTests(unittest.TestCase):
    def test_reta(self):
        text,ok=calcular('reta',dict(a='3',b='-6',xs=['0','2','7,6']))
        self.assertTrue(ok);self.assertIn('Raiz: x = 2',text);self.assertIn('y = 16,8',text);self.assertIn('Crescente',text)
        self.assertFalse(calcular('reta',dict(a='0',b='2',xs=[]))[1])
        self.assertFalse(calcular('reta',dict(a='',b='2',xs=['']))[1])

    def test_exponencial(self):
        for a,b,sentido in [('2','3','Crescente'),('1/2','3','Decrescente'),('2','-3','Decrescente'),('1/2','-3','Crescente')]:
            text,ok=calcular('exponencial',dict(tipo=TIPOS[0],a=a,b=b,xs=['0','1']))
            self.assertTrue(ok);self.assertIn(sentido,text);self.assertIn('Não possui raiz real',text)
        text,ok=calcular('exponencial',dict(tipo=TIPOS[1],a='2',b='-8',xs=['3']))
        self.assertTrue(ok);self.assertIn('ln(a) = 3',text);self.assertIn('y = 0',text);self.assertIn('y = -8',text)
        text,ok=calcular('exponencial',dict(tipo=TIPOS[1],a='√2',b='1/2',xs=['2']))
        self.assertTrue(ok);self.assertIn('y = 2,5',text)
        for a,b in [('1','2'),('-2','2'),('2','0')]:
            self.assertFalse(calcular('exponencial',dict(tipo=TIPOS[0],a=a,b=b,xs=[]))[1])

    def test_triangulos_e_pitagoras(self):
        for razao,conhecido in [('Seno','Hipotenusa'),('Cosseno','Hipotenusa'),('Tangente','Cateto adjacente')]:
            q=Triangulo(45,POSICOES[0],razao,conhecido,'2√2' if razao!='Tangente' else '2')
            text,ok=calcular('triangulo',campos(q));self.assertTrue(ok);self.assertIn('Cateto oposto = 2',text)
        for lado,v1,v2 in [('Hipotenusa','3','4'),('Cateto 1','4','5'),('Cateto 2','3','5')]:
            q=Triangulo(45,POSICOES[0],PITAGORAS,'','3',lado_x=lado,valor2=v2);q.valor=v1
            text,ok=calcular('triangulo',campos(q));self.assertTrue(ok);self.assertIn('Hipotenusa = 5',text);self.assertIn('perímetro = 12',text)
        q.valor2='1';self.assertFalse(calcular('triangulo',campos(q))[1])

    def test_contextos_altura_adicional_dado_e_pedido(self):
        from contextos import CENARIOS
        from contextos import EXTRAS
        for name in EXTRAS:
            opts=CENARIOS[name][1]
            for conhecido,valor,pedido in [(opts[0],'10',opts[1]),(opts[1],'11,6',opts[0])]:
                q=Triangulo(45,POSICOES[0],'Seno','Hipotenusa',valor,apresentacao='Contextual',cenario=name,dado_contexto=conhecido,pedido_contexto=pedido,altura_extra='1,6')
                text,ok=calcular('triangulo',campos(q));self.assertTrue(ok,text)
                self.assertIn('Cateto vertical do triângulo = 10 m',text)
                self.assertIn('Medida solicitada: '+('11,6' if pedido==opts[1] else '10'),text)

    def test_pa_sem_contexto(self):
        from progressao import Progressao
        from apoio_pa import calcular as pa
        text,aviso,dica=pa(Progressao())
        self.assertIn('Razão',text);self.assertEqual(aviso,'Valores válidos.');self.assertIn('Sₙ',dica)

    def test_quadratica_grafico_sinais(self):
        from apoio_quadraticas import calcular as quadratica
        text,_=quadratica(dict(a='-1',b='0',c='4',cenario='Sem contexto',apresentacao='Gráfico'))
        self.assertIn('Sinal de Δ: positivo',text);self.assertIn('negativo (máximo)',text);self.assertIn('c = 4',text)

    def test_painel_pontos_dinamicos_e_cancelamento(self):
        from interface_apoio import instalar
        from test_interface_plana import Controle
        tcl=tk.Tcl();r={'a':tk.StringVar(master=tcl,value='2'),'b':tk.StringVar(master=tcl,value='3'),'xs':[]}
        Controle.tarefas={};parent=Controle();aba=Mock();aba.apoio_embaixo=True
        with patch('interface_apoio.ttk.LabelFrame',Controle),patch('interface_apoio.ttk.Label',Controle),patch('interface_apoio.calcular',return_value=('resultado',True)) as calc:
            panel=instalar(parent,r,'reta',aba)
            self.assertEqual(calc.call_count,1)
            callback=list(Controle.tarefas.values())[-1];callback();self.assertEqual(calc.call_count,1)
            r['xs']=[tk.StringVar(master=tcl,value='7,6')];callback()
            self.assertEqual(calc.call_args.args[1]['xs'],['7,6'])
            r['xs'][0].set('');callback();self.assertEqual(calc.call_count,3)
            event=Mock();event.widget=panel
            with patch.object(panel,'after_cancel') as cancel:panel.bindings['<Destroy>'](event);cancel.assert_called_once()


if __name__=='__main__':unittest.main()
