"""Painel reutilizável com atualização limitada às mudanças dos campos."""
from tkinter import ttk,TclError
from apoio_funcoes import calcular


def instalar(parent,registro,tipo,aba):
    panel=ttk.LabelFrame(parent,text='Apoio ao professor — não sai no PDF',padding=10)
    panel.pack(side='bottom',fill='x',pady=(10,0));panel._largura_fixa=True
    label=ttk.Label(panel,justify='left',wraplength=550 if getattr(aba,'apoio_embaixo',False) else 780)
    label.pack(anchor='w')
    ttk.Label(panel,text='Resultados numéricos aproximados, com até 8 algarismos significativos.',wraplength=550).pack(anchor='w',pady=(6,0))
    pending=[None];last=[None]
    def atualizar():
        pending[0]=None
        if not panel.winfo_exists():return
        try:
            campos={k:([x.get() for x in v] if k=='xs' else v.get()) for k,v in registro.items() if not k.startswith('_')}
            key=repr(campos)
            if key!=last[0]:
                text,ok=calcular(tipo,campos);label.configure(text=text,foreground='#166534' if ok else '#9a3412');last[0]=key
        except TclError:last[0]=None;label.configure(text='Preencha os campos para conferir.',foreground='#9a3412')
        pending[0]=panel.after(250,atualizar)
    def destruir(event):
        if event.widget==panel and pending[0]:panel.after_cancel(pending[0]);pending[0]=None
    panel.bind('<Destroy>',destruir,add='+');atualizar()
    return panel
