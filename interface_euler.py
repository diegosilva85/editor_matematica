"""Editor de Euler incorporado à aba e reutilizado pelo editor de listas."""
import tkinter as tk
from tkinter import ttk
from euler import EULER,MEDIDAS,MANUAL,PREDEFINIDO,CAMPOS,SOLIDOS,contagens,enunciado,apoio,imagem

CAMPOS_MODELO=('modalidade','euler_origem','euler_solido','euler_descobrir','euler_v','euler_a','euler_f')


def instalar(card,r,modelo,atualizar_anterior):
    defaults=dict(zip(CAMPOS_MODELO,(MEDIDAS,PREDEFINIDO,'Cubo','V','8','12','6')))
    for key,value in defaults.items():r[key]=tk.StringVar(value=value)
    anteriores=[(w,w.pack_info()) for w in card.winfo_children()]
    barra=ttk.Frame(card);barra.pack(fill='x',before=anteriores[0][0],pady=4)
    ttk.Label(barra,text='Tipo de questão:').pack(side='left')
    modalidade=ttk.Combobox(barra,textvariable=r['modalidade'],values=(MEDIDAS,EULER),state='readonly',width=24)
    modalidade.pack(side='left',padx=8)
    painel=ttk.Frame(card)
    row=ttk.Frame(painel);row.pack(fill='x',pady=5)
    ttk.Label(row,text='Dados:').pack(side='left')
    origem=ttk.Combobox(row,textvariable=r['euler_origem'],values=(PREDEFINIDO,MANUAL),state='readonly',width=25)
    origem.pack(side='left',padx=6)
    seletor=ttk.Combobox(row,textvariable=r['euler_solido'],values=tuple(SOLIDOS),state='readonly',width=24)
    seletor.pack(side='left',padx=6)
    row=ttk.Frame(painel);row.pack(fill='x',pady=4)
    ttk.Label(row,text='O aluno deve descobrir:').pack(side='left')
    alvo=ttk.Combobox(row,textvariable=r['euler_descobrir'],values=tuple(CAMPOS),state='readonly',width=4)
    alvo.pack(side='left',padx=6)
    ttk.Label(row,text='V: vértices | A: arestas | F: faces').pack(side='left')
    incluir=ttk.Checkbutton(painel,text='Incluir imagem do sólido no PDF',variable=r['incluir_imagem'])
    incluir.pack(anchor='w',pady=4)
    body=ttk.Frame(painel);body.pack(fill='x')
    preview=tk.Canvas(body,width=210,height=210,background='white',highlightthickness=0)
    preview.pack(side='left',padx=(0,12))
    campos=ttk.Frame(body);campos.pack(side='left',fill='x',expand=True)
    entries={};calculados={key:tk.StringVar() for key in CAMPOS}
    for key,nome in CAMPOS.items():
        line=ttk.Frame(campos);line.pack(anchor='w',pady=5)
        ttk.Label(line,text=f'{key} - {nome.capitalize()}:',width=17).pack(side='left')
        entries[key]=ttk.Entry(line,width=12);entries[key].pack(side='left')
    ttk.Label(campos,text='No modo manual, preencha as duas quantidades conhecidas.\nA quantidade perguntada é calculada automaticamente.\nSomente inteiros; poliedros convexos.',wraplength=360).pack(anchor='w',pady=8)
    suporte=ttk.LabelFrame(painel,text='Apoio ao professor - não sai no PDF',padding=8);suporte.pack(fill='x',pady=6)
    ajuda=ttk.Label(suporte,justify='left',wraplength=550);ajuda.pack(anchor='w')
    texto=ttk.Label(painel,justify='left',wraplength=550);texto.pack(anchor='w',pady=6)
    ttk.Label(painel,text='As ilustrações não mostram necessariamente todas as arestas. As contagens vêm do cadastro do sólido, não da imagem.',wraplength=550).pack(anchor='w')
    cache=[None]

    def atualizar_dados(*args):
        if r['modalidade'].get()!=EULER:return
        q=modelo();pre=q.euler_origem==PREDEFINIDO
        seletor.configure(state='readonly' if pre else 'disabled')
        incluir.configure(state='normal' if pre else 'disabled')
        for key,entry in entries.items():
            automatico=pre or key==q.euler_descobrir
            entry.configure(textvariable=calculados[key] if automatico else r['euler_'+key.lower()],state='readonly' if automatico else 'normal')
        try:
            dados=contagens(q)
            for key in CAMPOS:calculados[key].set(str(dados[key]))
            ajuda.configure(text=apoio(q),foreground='#166534');texto.configure(text='Enunciado: '+enunciado(q))
        except ValueError as exc:
            for var in calculados.values():var.set('—')
            ajuda.configure(text='Confira: '+str(exc),foreground='#a33');texto.configure(text='Ajuste os dados para gerar a questão.')
        # A figura é mostrada no editor mesmo quando sua inclusão no PDF está desligada.
        from dataclasses import replace
        path=imagem(replace(q,incluir_imagem=True)) if pre else None
        if cache[0]!=path or not preview.find_all():
            cache[0]=path;preview.delete('all')
            if path:
                from PIL import Image,ImageTk
                with Image.open(path) as im:
                    im.thumbnail((200,200));preview._imagem=ImageTk.PhotoImage(im.copy())
                preview.create_image(105,105,image=preview._imagem)
            else:preview.create_text(105,105,text='Poliedro convexo\nDados personalizados\n(sem imagem)',width=185)

    def mudar_alvo(event=None):
        # Preserva a contagem calculada antes de trocar quais campos são editáveis.
        if r['euler_origem'].get()==MANUAL:
            anteriores={key:var.get() for key,var in calculados.items()}
            for key,value in anteriores.items():
                if value.isdigit():r['euler_'+key.lower()].set(value)
        atualizar_dados()

    def atualizar(event=None):
        if r['modalidade'].get()==EULER:
            for w,_ in anteriores:w.pack_forget()
            painel.pack(fill='x',after=barra);atualizar_dados()
        else:
            painel.pack_forget()
            for w,info in anteriores:w.pack(**info)
            atualizar_anterior()

    modalidade.bind('<<ComboboxSelected>>',atualizar)
    origem.bind('<<ComboboxSelected>>',atualizar_dados)
    seletor.bind('<<ComboboxSelected>>',atualizar_dados)
    alvo.bind('<<ComboboxSelected>>',mudar_alvo)
    incluir.configure(command=atualizar_dados)
    for key in ('euler_v','euler_a','euler_f'):r[key].trace_add('write',atualizar_dados)
    r['_atualizar_modo']=atualizar
    return atualizar
