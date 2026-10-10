"""Testa transições do formulário sem depender de um servidor gráfico."""
import tkinter as tk
import unittest
from unittest.mock import patch,Mock
from contextlib import ExitStack
from solidos import Solido
from euler import EULER,MANUAL,contagens
from interface_euler import instalar,CAMPOS_MODELO


class Widget:
    todos=[]
    def __init__(self,parent=None,**kw):
        self.children=[];self.kw=kw;self.bindings={};self.packed=False;self.drawn=False
        self.todos.append(self)
        if parent:parent.children.append(self)
    def pack(self,**kw):self.packed=True
    def pack_info(self):return {'fill':'x'}
    def pack_forget(self):self.packed=False
    def winfo_children(self):return self.children
    def configure(self,**kw):self.kw.update(kw)
    def bind(self,event,callback):self.bindings[event]=callback
    def delete(self,*args):self.drawn=False
    def find_all(self):return (1,) if self.drawn else ()
    def create_image(self,*args,**kw):self.drawn=True
    def create_text(self,*args,**kw):self.drawn=True


class InterfaceEulerTests(unittest.TestCase):
    def test_modos_alvos_e_restauracao_sem_mutar_campos(self):
        tcl=tk.Tcl();variable=tk.StringVar;Widget.todos=[]
        r={'incluir_imagem':tk.BooleanVar(master=tcl,value=True)}
        def modelo():return Solido('Cubo',{},incluir_imagem=r['incluir_imagem'].get(),**{k:r[k].get() for k in CAMPOS_MODELO})
        with ExitStack() as stack:
            for name in ('Frame','Label','Combobox','Checkbutton','Entry','LabelFrame'):
                stack.enter_context(patch('interface_euler.ttk.'+name,Widget))
            stack.enter_context(patch('interface_euler.tk.Canvas',Widget))
            stack.enter_context(patch('interface_euler.tk.StringVar',lambda **kw:variable(master=tcl,**kw)))
            stack.enter_context(patch('PIL.ImageTk.PhotoImage',Mock()))
            card=Widget();antigo=Widget(card);antigo.pack();old=Mock()
            atualizar=instalar(card,r,modelo,old)
            atualizar();old.assert_called_once()
            r['modalidade'].set(EULER);atualizar()
            self.assertFalse(antigo.packed);self.assertEqual(contagens(modelo())['V'],8)
            r['euler_origem'].set(MANUAL)
            r['euler_descobrir'].set('V')
            r['euler_a'].set('15');r['euler_f'].set('7')
            self.assertEqual(contagens(modelo())['V'],10)
            self.assertEqual(r['euler_v'].get(),'8') # Só a apresentação é calculada.
            alvo=next(w for w in Widget.todos if w.kw.get('textvariable') is r['euler_descobrir'])
            r['euler_descobrir'].set('A');alvo.bindings['<<ComboboxSelected>>']()
            self.assertEqual(contagens(modelo()),dict(V=10,F=7,A=15))
            self.assertEqual(r['euler_v'].get(),'10')
            r['modalidade'].set('Áreas e volumes');atualizar()
            self.assertTrue(antigo.packed);self.assertEqual(old.call_count,2)


if __name__=='__main__':unittest.main()
