"""Editor de tabelas com células editáveis e apoio em tempo real."""
import tkinter as tk
from tkinter import ttk,messagebox
from dataclasses import asdict
from interface import Aba
from estatistica import Estatistica,CONTEXTOS,TIPOS,MEDIDAS,NOMES,apoio,gerar,numero,fmt
from estatistica_multicolunas import TIPOS_MULTIPLOS,COMPARACAO,FALTANTE,CONTEXTOS_MULTIPLOS,redimensionar


class AbaEstatistica(Aba):
    def __init__(self,notebook):
        super().__init__(notebook,1)
        self.grau=7;self.total.set(1)
        self.quantidade.configure(to=12)
        self.seletor_colunas.configure(values=(1,2))
        notebook.tab(self.frame,text='Estatística')
        self.titulo.set('Estatística')

    def criar(self):
        if not self.limpar(): return
        for i in range(self.total.get()): self.editor(Estatistica(),i)

    def modelo(self,r):
        return Estatistica(**{k:v.get() for k,v in r.items() if not k.startswith('_') and k!='linhas'},
                           linhas=[[v.get() for v in row] for row in r['linhas']])

    def editor(self,q,index):
        outer=ttk.LabelFrame(self.corpo,text=f'Questão {index+1}',padding=12);outer.pack(fill='x',pady=6)
        abaixo=getattr(self,'apoio_embaixo',False)
        form=ttk.Frame(outer);form.pack(side='top' if abaixo else 'left',fill='both',expand=True)
        panel=ttk.LabelFrame(outer,text='Apoio ao professor (não sai no PDF)',padding=10)
        panel._largura_fixa=True
        panel.pack(side='bottom' if abaixo else 'right',fill='x' if abaixo else 'y',padx=12,pady=8)
        r={k:(tk.BooleanVar(value=v) if type(v) is bool else tk.StringVar(value=v)) for k,v in asdict(q).items() if k!='linhas'}
        r['linhas']=[];r['_n']=tk.IntVar(value=len(q.linhas))
        self.registros.append(r)
        row=ttk.Frame(form);row.pack(fill='x',pady=4)
        ttk.Label(row,text='Tabela:').pack(side='left')
        tipo=ttk.Combobox(row,textvariable=r['tipo'],values=TIPOS,state='readonly',width=28);tipo.pack(side='left',padx=6)
        ttk.Label(row,text='Linhas:').pack(side='left')
        n=ttk.Spinbox(row,from_=2,to=20,textvariable=r['_n'],state='readonly',width=4);n.pack(side='left',padx=6)
        row=ttk.Frame(form);row.pack(fill='x',pady=4)
        ttk.Label(row,text='Medidas por linha (sem contar identificação e média):').pack(side='left')
        colunas=ttk.Spinbox(row,from_=2,to=8,textvariable=r['quantidade_medidas'],state='readonly',width=4);colunas.pack(side='left',padx=6)
        row=ttk.Frame(form);row.pack(fill='x',pady=4)
        ttk.Label(row,text='Contexto:').pack(side='left')
        contexto=ttk.Combobox(row,textvariable=r['cenario'],values=tuple(CONTEXTOS),state='readonly',width=36);contexto.pack(side='left',padx=6)
        row=ttk.Frame(form);row.pack(fill='x',pady=4)
        ttk.Label(row,text='Pedir:').pack(side='left')
        selecoes={}
        for k in MEDIDAS:
            selecoes[k]=ttk.Checkbutton(row,text=NOMES[k].capitalize(),variable=r['pedir_'+k]);selecoes[k].pack(side='left',padx=8)
        instrucao=tk.StringVar()
        ttk.Label(form,textvariable=instrucao,wraplength=540,justify='left').pack(anchor='w',pady=5)
        table=ttk.Frame(form);table.pack(fill='x',pady=8)
        result=tk.StringVar();info=tk.StringVar()
        ttk.Label(panel,textvariable=result,wraplength=540 if abaixo else 285,justify='left').pack(anchor='w',pady=5)
        ttk.Label(panel,textvariable=info,wraplength=540 if abaixo else 285,justify='left').pack(anchor='w',pady=5)
        pending=[None]
        def atualizar():
            pending[0]=None
            if not panel.winfo_exists(): return
            text,hint=apoio(self.modelo(r));result.set(text);info.set(hint)
        def agendar(*args):
            if pending[0]: panel.after_cancel(pending[0])
            pending[0]=panel.after(150,atualizar)
        def destruir(event):
            if event.widget==panel and pending[0]: panel.after_cancel(pending[0]);pending[0]=None
        panel.bind('<Destroy>',destruir,add='+')
        def montar_linhas(linhas=None):
            old=[[v.get() for v in row] for row in r['linhas']] if linhas is None else linhas
            for widget in table.winfo_children(): widget.destroy()
            r['linhas']=[]
            for col,label in enumerate(self.modelo(r).cabecalhos()): ttk.Label(table,text=label).grid(row=0,column=col,padx=4,pady=3,sticky='w')
            c=CONTEXTOS[r['cenario'].get()]
            multi=r['tipo'].get() in TIPOS_MULTIPLOS
            if multi:old=redimensionar(self.modelo(r),r['_n'].get(),old)
            for i in range(r['_n'].get()):
                v=fmt(numero(c[4])+i*numero(c[6]))
                values=old[i] if i<len(old) else ([f'{c[0]} {i+1}',v] if r['tipo'].get()=='Simples' else [v,'1'])
                variables=[]
                for col,value in enumerate(values):
                    var=tk.StringVar(value=value);variables.append(var)
                    ttk.Entry(table,textvariable=var,width=(18 if col==0 else 9) if multi else (28 if col==0 else 18)).grid(row=i+1,column=col,sticky='ew',padx=4,pady=2)
                    var.trace_add('write',agendar)
                r['linhas'].append(variables)
            agendar()
        n.configure(command=montar_linhas)
        colunas.configure(command=montar_linhas)
        def ajustar_tipo():
            t=r['tipo'].get();multi=t in TIPOS_MULTIPLOS
            colunas.configure(state='readonly' if multi else 'disabled')
            for k,widget in selecoes.items():
                widget.configure(state='disabled' if t==FALTANTE or (t==COMPARACAO and k=='moda') else 'normal',
                                 text=('Maior '+NOMES[k] if t==COMPARACAO and k!='moda' else NOMES[k].capitalize()))
            instrucao.set('Deixe a última medida em branco (ou digite ?) nas linhas com incógnita. Preencha a coluna Média com a média exata. As outras células são editáveis.' if t==FALTANTE else
                          'Cada linha é analisada separadamente. Selecione maior média e/ou maior mediana. Empates são permitidos.' if t==COMPARACAO else
                          'Edite diretamente as duas colunas da tabela.')
        tipo_anterior=[q.tipo]
        def trocar_tipo(event=None):
            if not messagebox.askyesno('Trocar tabela','Trocar o tipo reinicia as células da tabela. Continuar?',parent=self.frame.winfo_toplevel()):
                r['tipo'].set(tipo_anterior[0]);return
            tipo_anterior[0]=r['tipo'].get();ajustar_tipo();montar_linhas([])
        tipo.bind('<<ComboboxSelected>>',trocar_tipo)
        contexto_anterior=[q.cenario]
        def trocar_contexto(event=None):
            c=CONTEXTOS[r['cenario'].get()]
            for key,value in zip(('minimo','maximo','passo'),c[4:]): r[key].set(value)
            # Mantém as medidas já editadas; troca apenas identificações padrão.
            rows=[[v.get() for v in row] for row in r['linhas']]
            if r['tipo'].get()!='Frequência':
                contexts=CONTEXTOS_MULTIPLOS if r['tipo'].get() in TIPOS_MULTIPLOS else CONTEXTOS
                old_label=contexts[contexto_anterior[0]][0]
                for i,row in enumerate(rows):
                    if row[0]==f'{old_label} {i+1}': row[0]=f'{contexts[r["cenario"].get()][0]} {i+1}'
            contexto_anterior[0]=r['cenario'].get()
            montar_linhas(rows)
        contexto.bind('<<ComboboxSelected>>',trocar_contexto)
        box=ttk.LabelFrame(form,text='Gerar valores aleatórios',padding=8);box.pack(fill='x',pady=8)
        ttk.Label(box,text='Metas opcionais (em branco = livre). Moda informada = moda única. Nos formatos com várias medidas, as metas se aplicam a cada linha.',wraplength=540).grid(row=0,column=0,columnspan=6,sticky='w')
        for i,k in enumerate(MEDIDAS):
            ttk.Label(box,text=NOMES[k].capitalize()+':').grid(row=1,column=i*2,sticky='w')
            ttk.Entry(box,textvariable=r['meta_'+k],width=9).grid(row=1,column=i*2+1,padx=5,pady=5)
        for i,(key,label) in enumerate((('minimo','Mínimo'),('maximo','Máximo'),('passo','Passo'))):
            ttk.Label(box,text=label+':').grid(row=2,column=i*2,sticky='w')
            ttk.Entry(box,textvariable=r[key],width=9).grid(row=2,column=i*2+1,padx=5,pady=5)
        ttk.Label(box,text='Total de observações (só na frequência):').grid(row=3,column=0,columnspan=4,sticky='w')
        ttk.Entry(box,textvariable=r['observacoes'],width=9).grid(row=3,column=4,columnspan=2)
        ttk.Label(box,text='Passo: 1 para inteiros; 0,1 para décimos. Na simples, o total é o número de linhas. A busca preserva a tabela se não encontrar solução.',wraplength=540).grid(row=4,column=0,columnspan=6,sticky='w',pady=5)
        def aleatorio():
            try:
                from progresso import gerar_com_progresso
                snapshot=self.modelo(r);count=r['_n'].get()
                rows=gerar_com_progresso(self.frame.winfo_toplevel(),lambda:gerar(snapshot,count),titulo='Gerando tabela',mensagem='Buscando valores para as metas…')
                montar_linhas(rows)
            except Exception as exc: messagebox.showerror('Não foi possível gerar',str(exc),parent=self.frame.winfo_toplevel())
        ttk.Button(box,text='Gerar valores',command=aleatorio).grid(row=5,column=0,columnspan=6,sticky='w',pady=5)
        for k,v in r.items():
            if not k.startswith('_') and k!='linhas': v.trace_add('write',agendar)
        ajustar_tipo();montar_linhas(q.linhas)

    def pagina(self):
        itens=[]
        for i,r in enumerate(self.registros):
            try:
                q=self.modelo(r);q.validar();itens.append(q)
            except ValueError as exc: raise ValueError(f'Estatística, questão {i+1}: {exc}') from exc
        return 7,itens,self.colunas.get(),self.titulo.get()

    def restaurar(self,pagina):
        _,items,cols,title=pagina
        self.limpar(confirmar=False);self.total.set(len(items));self.colunas.set(cols);self.titulo.set(title)
        for i,q in enumerate(items): self.editor(q,i)
