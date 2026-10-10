"""Janela de espera animada; geração pesada fora da thread do Tk."""
from queue import Queue, Empty
from threading import Thread
import tkinter as tk
from tkinter import ttk


def executar_tarefa(tarefa, fila):
    """O worker não acessa widgets; resultado e erros voltam pela fila."""
    try:
        fila.put((True,tarefa()))
    except Exception as exc:
        fila.put((False,exc))


def gerar_com_progresso(parent,tarefa,titulo='Gerando PDF',mensagem='Criando o PDF…'):
    """Espera com event loop ativo e devolve o resultado (ou relança o erro)."""
    dialog=tk.Toplevel(parent)
    dialog.title(titulo)
    dialog.transient(parent)
    dialog.resizable(False,False)
    body=ttk.Frame(dialog,padding=24); body.pack(fill='both',expand=True)
    ttk.Label(body,text=mensagem,font=('',12,'bold')).pack(anchor='w')
    ttk.Label(body,text='Aguarde a conclusão do processamento.',wraplength=390).pack(anchor='w',pady=(8,14))
    barra=ttk.Progressbar(body,mode='indeterminate',length=390)
    barra.pack(fill='x')
    ttk.Label(body,text='Esta janela fecha automaticamente ao concluir.',wraplength=390).pack(anchor='w',pady=(12,0))
    dialog.update_idletasks()
    x=max(0,parent.winfo_rootx()+(parent.winfo_width()-dialog.winfo_reqwidth())//2)
    y=max(0,parent.winfo_rooty()+(parent.winfo_height()-dialog.winfo_reqheight())//2)
    dialog.geometry(f'+{x}+{y}')
    anterior=parent.grab_current()
    # Impede fechar a aplicação no meio da publicação do par PDF/JSON.
    janelas={parent.winfo_toplevel(),parent._root(),dialog}
    ancestral=parent.master
    while ancestral is not None:
        if isinstance(ancestral,(tk.Tk,tk.Toplevel)): janelas.add(ancestral)
        ancestral=ancestral.master
    protocolos={w:w.protocol('WM_DELETE_WINDOW') for w in janelas}
    for w in janelas: w.protocol('WM_DELETE_WINDOW',dialog.bell)
    fila=Queue(); resultado=[]
    def consultar():
        try: item=fila.get_nowait()
        except Empty:
            dialog.after(75,consultar)
            return
        resultado.append(item)
        barra.stop(); dialog.destroy()
    try:
        dialog.grab_set(); barra.start(12)
        Thread(target=executar_tarefa,args=(tarefa,fila),daemon=False).start()
        dialog.after(75,consultar)
        parent.wait_window(dialog)
    finally:
        for w,protocolo in protocolos.items():
            if w.winfo_exists(): w.protocol('WM_DELETE_WINDOW',protocolo)
        if anterior is not None and anterior.winfo_exists(): anterior.grab_set()
    if not resultado: raise RuntimeError('A geração foi interrompida antes de terminar.')
    sucesso,valor=resultado[0]
    if not sucesso: raise valor
    return valor
