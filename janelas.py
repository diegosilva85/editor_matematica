"""Abertura maximizada, preservando os controles da janela."""
import tkinter as tk


def ocultar_arquivos_ocultos(root):
    """Aplica a todos os diálogos nativos Tk de abrir/salvar no Linux."""
    if root.tk.call('tk','windowingsystem')=='x11':
        root.tk.call('auto_load','::tk::dialog::file::')
        root.tk.setvar('::tk::dialog::file::showHiddenVar',0)
        root.tk.setvar('::tk::dialog::file::showHiddenBtn',0)


def maximizar(janela):
    def aplicar():
        try:
            janela.state('zoomed')
        except tk.TclError:
            try:
                janela.attributes('-zoomed',True)
            except tk.TclError:
                janela.geometry(f'{janela.winfo_screenwidth()}x{janela.winfo_screenheight()}+0+0')
    janela.after_idle(aplicar)
