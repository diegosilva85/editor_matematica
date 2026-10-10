"""Abertura maximizada, preservando os controles da janela."""
import tkinter as tk


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
