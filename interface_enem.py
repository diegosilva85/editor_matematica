"""Navegador paginado de questões oficiais, separado dos editores de criação."""
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from queue import Queue,Empty
from threading import Event
import tkinter as tk
from tkinter import ttk,messagebox
import webbrowser
from PIL import ImageTk
from acervo_enem import (CONTEUDOS,carregar_acervo,filtrar,imagem_questao,
                         caminho_pdf,baixar_prova,salvar_conteudos)
from janelas import maximizar


class JanelaEnem(tk.Toplevel):
    POR_PAGINA=4

    def __init__(self,parent):
        super().__init__(parent);self.title('Questões do Enem — Matemática');self.geometry('1150x850');maximizar(self)
        self.executor=ThreadPoolExecutor(max_workers=1);self.fila=Queue();self.geracao=0;self.pagina=0;self.futuro=None
        self.cancelar=Event();self._resize_job=None;self._consulta=None;self._largura=0
        self.fontes,self.questoes=carregar_acervo();self.provas={p['id']:p for p in self.fontes}
        self.protocol('WM_DELETE_WINDOW',self.fechar)
        self.ano=tk.StringVar(value='Todos');self.prova=tk.StringVar(value='Todas')
        self.conteudo=tk.StringVar(value='Todos');self.busca=tk.StringVar();self.numero_pagina=tk.StringVar(value='1')
        self.status=tk.StringVar(value='');self.resultados=[];self.imagens=[];self.baixando=False
        ttk.Label(self,text='Questões do Enem — Matemática',font=('',18,'bold'),padding=12).pack(anchor='w')
        corpo=ttk.Frame(self,padding=12);corpo.pack(fill='both',expand=True)
        esquerdo=ttk.Frame(corpo,width=290);esquerdo.pack(side='left',fill='y',padx=(0,15));esquerdo.pack_propagate(False)
        ttk.Label(esquerdo,text='Filtrar questões',font=('',12,'bold')).pack(anchor='w',pady=(0,12))
        anos=['Todos']+[str(a) for a in sorted({p['ano'] for p in self.fontes},reverse=True)]
        self.combo_ano=self.combo(esquerdo,'Ano',self.ano,anos)
        self.combo_prova=self.combo(esquerdo,'Prova / aplicação',self.prova,[])
        self.combo(esquerdo,'Conteúdo',self.conteudo,['Todos']+list(CONTEUDOS))
        ttk.Label(esquerdo,text='Número ou palavra no enunciado').pack(anchor='w',pady=(10,3))
        entry=ttk.Entry(esquerdo,textvariable=self.busca);entry.pack(fill='x');entry.bind('<Return>',lambda e:self.aplicar())
        ttk.Button(esquerdo,text='Pesquisar',command=self.aplicar).pack(fill='x',pady=8)
        ttk.Button(esquerdo,text='Limpar filtros',command=self.limpar).pack(fill='x')
        ttk.Separator(esquerdo).pack(fill='x',pady=15)
        ttk.Label(esquerdo,text='Conteúdos sugeridos automaticamente; não são classificações oficiais. Use “Editar conteúdos” na questão para revisar.',wraplength=280,justify='left').pack(anchor='w')
        ttk.Label(esquerdo,text='Um caderno por aplicação, sem repetir as cores. Em 2016, a 2ª aplicação e a PPL aparecem separadas.',wraplength=280,justify='left').pack(anchor='w',pady=12)
        self.download=ttk.Button(esquerdo,text='Baixar PDFs das provas filtradas',command=self.baixar);self.download.pack(fill='x',pady=8)
        self.barra=ttk.Progressbar(esquerdo,mode='determinate');self.barra.pack(fill='x')
        ttk.Button(esquerdo,text='Acervo oficial do Inep',command=lambda:webbrowser.open(self.fontes[0]['fonte'].rsplit('/',1)[0])).pack(fill='x',pady=8)
        ttk.Label(esquerdo,textvariable=self.status,wraplength=280,justify='left').pack(anchor='w',pady=8)
        direito=ttk.Frame(corpo);direito.pack(side='right',fill='both',expand=True)
        nav=ttk.Frame(direito);nav.pack(fill='x',pady=(0,8))
        self.anterior=ttk.Button(nav,text='◀ Anterior',command=lambda:self.mudar(-1));self.anterior.pack(side='left')
        self.paginas=ttk.Combobox(nav,textvariable=self.numero_pagina,state='readonly',width=6);self.paginas.pack(side='left',padx=8)
        self.paginas.bind('<<ComboboxSelected>>',lambda e:self.ir_pagina())
        self.proxima=ttk.Button(nav,text='Próxima ▶',command=lambda:self.mudar(1));self.proxima.pack(side='left')
        self.contagem=ttk.Label(nav);self.contagem.pack(side='left',padx=12)
        area=ttk.Frame(direito);area.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(area,background='#e8ebef',highlightthickness=0)
        scroll=ttk.Scrollbar(area,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True)
        self.cards=ttk.Frame(self.canvas,padding=10);self.window=self.canvas.create_window(0,0,window=self.cards,anchor='nw')
        self.cards.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',self.redimensionar)
        # Binding na janela, não bind_all: não interfere nas demais abas.
        self.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'))
        self.bind('<Button-4>',lambda e:self.canvas.yview_scroll(-3,'units'))
        self.bind('<Button-5>',lambda e:self.canvas.yview_scroll(3,'units'))
        self.combo_ano.bind('<<ComboboxSelected>>',lambda e:self.trocar_ano())
        self.trocar_ano();self._consulta=self.after(80,self.consultar)

    def redimensionar(self,event):
        self.canvas.itemconfigure(self.window,width=event.width)
        if abs(event.width-self._largura)<30:return
        self._largura=event.width
        if self._resize_job:self.after_cancel(self._resize_job)
        self._resize_job=self.after(250,self.mostrar)

    def combo(self,parent,label,var,values):
        ttk.Label(parent,text=label).pack(anchor='w',pady=(8,3))
        widget=ttk.Combobox(parent,textvariable=var,values=values,state='readonly');widget.pack(fill='x')
        widget.bind('<<ComboboxSelected>>',lambda e:self.aplicar());return widget

    def trocar_ano(self):
        self.opcoes={'Todas':''}
        for p in reversed(self.fontes):
            if self.ano.get()=='Todos' or str(p['ano'])==self.ano.get():
                self.opcoes[f"{p['ano']} — {p['aplicacao']}"]=p['id']
        self.combo_prova.configure(values=list(self.opcoes));self.prova.set('Todas');self.aplicar()

    def limpar(self):
        self.ano.set('Todos');self.conteudo.set('Todos');self.busca.set('');self.trocar_ano()

    def aplicar(self):
        self.resultados=filtrar(self.questoes,'' if self.ano.get()=='Todos' else self.ano.get(),
                               self.opcoes.get(self.prova.get(),''),
                               '' if self.conteudo.get()=='Todos' else self.conteudo.get(),self.busca.get())
        self.pagina=0;self.mostrar()

    def mudar(self,delta):
        self.pagina=max(0,min(self.pagina+delta,max(0,ceil(len(self.resultados)/self.POR_PAGINA)-1)));self.mostrar()

    def ir_pagina(self):self.pagina=int(self.numero_pagina.get())-1;self.mostrar()

    def mostrar(self):
        self.geracao+=1;token=self.geracao
        if self.futuro:self.futuro.cancel()
        for w in self.cards.winfo_children():w.destroy()
        self.imagens=[];self.canvas.yview_moveto(0)
        total=max(1,ceil(len(self.resultados)/self.POR_PAGINA));self.numero_pagina.set(str(self.pagina+1))
        self.paginas.configure(values=[str(n) for n in range(1,total+1)])
        self.anterior.configure(state='normal' if self.pagina else 'disabled')
        self.proxima.configure(state='normal' if self.pagina+1<total else 'disabled')
        self.contagem.configure(text=f'{len(self.resultados)} questões • página {self.pagina+1} de {total}')
        itens=self.resultados[self.pagina*self.POR_PAGINA:(self.pagina+1)*self.POR_PAGINA]
        if not itens:ttk.Label(self.cards,text='Nenhuma questão encontrada. Experimente outros filtros.',padding=25).pack()
        self.slots=[]
        largura=max(350,min(900,self.canvas.winfo_width()-45))
        if self.canvas.winfo_width()<100:largura=700
        for q in itens:
            p=self.provas[q['prova']];card=ttk.LabelFrame(self.cards,text=f"Enem {q['ano']} — {p['aplicacao']} — questão {q['numero']}",padding=12)
            card.pack(fill='x',pady=(0,15))
            ttk.Label(card,text=('Revisado: ' if q.get('revisado') else 'Sugestão: ')+', '.join(q['conteudos']),wraplength=largura).pack(anchor='w')
            if q.get('texto_limitado'):
                ttk.Label(card,text='Texto parcialmente codificado no PDF: a busca e a classificação podem ser incompletas. Confira a imagem.',wraplength=largura).pack(anchor='w')
            botoes=ttk.Frame(card);botoes.pack(fill='x',pady=8)
            ttk.Button(botoes,text='Ampliar',command=lambda q=q:self.ampliar(q)).pack(side='left')
            ttk.Button(botoes,text='Página original',command=lambda q=q:self.ampliar(q,True)).pack(side='left',padx=5)
            ttk.Button(botoes,text='Editar conteúdos',command=lambda q=q:self.editar(q)).pack(side='left')
            label=ttk.Label(card,text='Carregando imagem…');label.pack(anchor='center');self.slots.append(label)
        def renderizar():
            for n,q in enumerate(itens):
                if token!=self.geracao:return
                try:result=imagem_questao(q,self.provas[q['prova']],largura)
                except Exception as exc:result=str(exc)
                self.fila.put(('imagem',token,n,result))
        self.futuro=self.executor.submit(renderizar)
        if not self.baixando:
            faltam=sum(not caminho_pdf(p).exists() for p in self.fontes)
            self.status.set(f'{len(self.fontes)-faltam}/{len(self.fontes)} PDFs disponíveis neste computador.\nAs imagens são geradas dos originais e funcionam offline após o download.')

    def consultar(self):
        try:
            while True:
                tipo,*args=self.fila.get_nowait()
                if tipo=='imagem':
                    token,n,result=args
                    if token!=self.geracao:continue
                    if isinstance(result,str):self.slots[n].configure(text=result,wraplength=500)
                    else:
                        photo=ImageTk.PhotoImage(result);self.imagens.append(photo);self.slots[n].configure(image=photo,text='')
                elif tipo=='progresso':
                    n,total,msg=args;self.barra.configure(value=n,maximum=max(1,total));self.status.set(msg)
                elif tipo=='baixado':
                    erros=args[0];self.baixando=False;self.download.configure(state='normal');self.mostrar()
                    if erros:messagebox.showwarning('Downloads incompletos','\n'.join(erros),parent=self)
                elif tipo=='ampliada':
                    q,inteira,result=args
                    if isinstance(result,str):messagebox.showerror('Visualização',result,parent=self)
                    else:self.exibir_ampliada(q,result,inteira)
        except Empty:pass
        self._consulta=self.after(80,self.consultar)

    def baixar(self):
        if self.baixando:return
        ids={q['prova'] for q in self.resultados}
        fontes=[p for p in self.fontes if p['id'] in ids]
        if not fontes:return
        self.baixando=True;self.download.configure(state='disabled')
        def tarefa():
            erros=[]
            for n,p in enumerate(fontes):
                if self.cancelar.is_set():return
                self.fila.put(('progresso',n,len(fontes),f"Baixando {p['ano']} — {p['aplicacao']}…"))
                try:baixar_prova(p)
                except Exception as exc:erros.append(f"{p['id']}: {exc}")
            self.fila.put(('progresso',len(fontes),len(fontes),'Downloads concluídos.'))
            self.fila.put(('baixado',erros))
        self.executor.submit(tarefa)

    def ampliar(self,q,inteira=False):
        def tarefa():
            try:result=imagem_questao(q,self.provas[q['prova']],1200,pagina_inteira=inteira)
            except Exception as exc:result=str(exc)
            self.fila.put(('ampliada',q,inteira,result))
        self.executor.submit(tarefa)

    def exibir_ampliada(self,q,im,inteira):
        win=tk.Toplevel(self);win.title(f"Enem {q['ano']} — questão {q['numero']}"+(' — página original' if inteira else ''));maximizar(win)
        canvas=tk.Canvas(win,background='white');y=ttk.Scrollbar(win,command=canvas.yview);x=ttk.Scrollbar(win,orient='horizontal',command=canvas.xview)
        y.pack(side='right',fill='y');x.pack(side='bottom',fill='x');canvas.pack(fill='both',expand=True)
        canvas.configure(yscrollcommand=y.set,xscrollcommand=x.set);canvas._photo=ImageTk.PhotoImage(im)
        canvas.create_image(0,0,image=canvas._photo,anchor='nw');canvas.configure(scrollregion=(0,0,im.width,im.height))
        canvas.bind('<MouseWheel>',lambda e:canvas.yview_scroll(-int(e.delta/120),'units'))
        canvas.bind('<Button-4>',lambda e:canvas.yview_scroll(-3,'units'));canvas.bind('<Button-5>',lambda e:canvas.yview_scroll(3,'units'))

    def editar(self,q):
        win=tk.Toplevel(self);win.title(f"Conteúdos — questão {q['numero']}");win.transient(self)
        ttk.Label(win,text='Marque os conteúdos desta questão:',padding=12).pack(anchor='w');vars={}
        for c in CONTEUDOS:
            var=tk.BooleanVar(value=c in q['conteudos']);vars[c]=var
            ttk.Checkbutton(win,text=c,variable=var).pack(anchor='w',padx=15)
        def salvar():
            values=[c for c,v in vars.items() if v.get()]
            try:salvar_conteudos(q['id'],values)
            except (ValueError,OSError) as exc:messagebox.showerror('Conteúdos',str(exc),parent=win);return
            self.fontes,self.questoes=carregar_acervo();win.destroy();self.aplicar()
        ttk.Button(win,text='Salvar classificação',command=salvar).pack(pady=12)

    def fechar(self):
        self.cancelar.set();self.geracao+=1
        for task in (self._consulta,self._resize_job):
            if task:self.after_cancel(task)
        self.executor.shutdown(wait=False,cancel_futures=True);self.destroy()
