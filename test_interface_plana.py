"""Transições do editor sem depender de servidor gráfico."""
import tkinter as tk
import unittest
from unittest.mock import patch,Mock
from contextlib import ExitStack
from test_interface_euler import Widget
from interface_plana import AbaPlana
from geometria_plana import FiguraPlana,FIGURAS,padrao,grandezas


class Controle(Widget):
    tarefas={}
    contador=0
    def __init__(self,parent=None,**kw):super().__init__(parent,**kw);self.parent=parent
    def grid(self,**kw):pass
    def bind(self,event,callback,**kw):self.bindings[event]=callback
    def winfo_children(self):return list(self.children)
    def winfo_exists(self):return True
    def after(self,delay,callback):
        Controle.contador+=1;key=str(Controle.contador);self.tarefas[key]=callback;return key
    def after_cancel(self,key):self.tarefas.pop(key,None)
    def destroy(self):
        if self.parent:self.parent.children.remove(self)


class InterfacePlanaTests(unittest.TestCase):
    def test_miniaturas_todas_as_figuras(self):
        from interface_plana import miniatura
        for key in FIGURAS:
            with self.subTest(figura=key):
                im=miniatura(key,130)
                self.assertEqual(im.mode,'RGB')
                self.assertLessEqual(max(im.size),130)

    def test_selecao_conversao_e_restauracao(self):
        tcl=tk.Tcl();stringvar=tk.StringVar;boolvar=tk.BooleanVar
        Widget.todos=[];Controle.tarefas={}
        aba=AbaPlana.__new__(AbaPlana);aba.grau=8;aba.corpo=Controle();aba.frame=Controle();aba.registros=[]
        aba.total=tk.IntVar(master=tcl,value=1);aba.colunas=tk.IntVar(master=tcl,value=2);aba.titulo=stringvar(master=tcl,value='Plana')
        with ExitStack() as stack:
            for name in ('Frame','Label','LabelFrame','Combobox','Checkbutton','Entry','Button'):
                stack.enter_context(patch('interface_plana.ttk.'+name,Controle))
            stack.enter_context(patch('interface_plana.tk.Canvas',Controle))
            stack.enter_context(patch('interface_plana.tk.StringVar',lambda **kw:stringvar(master=tcl,**kw)))
            stack.enter_context(patch('interface_plana.tk.BooleanVar',lambda **kw:boolvar(master=tcl,**kw)))
            stack.enter_context(patch('PIL.ImageTk.PhotoImage',Mock()))
            aba.editor(FiguraPlana(),0);r=aba.registros[0]
            self.assertEqual(aba.pagina()[1],[FiguraPlana()])
            combo=next(w for w in Widget.todos if w.kw.get('textvariable') is r['_nome'])
            r['_nome'].set('Círculo');combo.bindings['<<ComboboxSelected>>']()
            r['valores']['r'].set('7,6');original=grandezas(aba.modelo(r))
            circular=next(w for w in Widget.todos if w.kw.get('textvariable') is r['circular'])
            r['circular'].set('Diâmetro');circular.bindings['<<ComboboxSelected>>']()
            self.assertEqual(r['valores']['d'].get(),'15,2');self.assertEqual(grandezas(aba.modelo(r)),original)
            for callback in list(Controle.tarefas.values()):callback()
            key='27_retangulo_furo_circular';q=FiguraPlana(key,padrao(key,'Diâmetro'),circular='Diâmetro',pedido='Área')
            pagina=(8,[q],3,'Placas');aba.restaurar(pagina)
            self.assertEqual(aba.pagina(),pagina)
            for callback in list(Controle.tarefas.values()):callback()


if __name__=='__main__':unittest.main()
