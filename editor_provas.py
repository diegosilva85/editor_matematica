"""Editor de provas reutilizando formulários, prévia e ordenação das listas."""
import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from pathlib import Path
from copy import deepcopy
from editor_listas import EditorLista,QuestaoDialog
from listas import CONTEUDOS
from provas import (Prova,QuestaoProva,texto_editavel,pdf_prova,quadro,
                    carregar_prova,salvar_prova,salvar_rascunho)
from progresso import gerar_com_progresso


class EditorProva(EditorLista):
    def __init__(self,parent):
        super().__init__(parent)
        self.window.title('Nova Prova');self.lista=Prova()
        for child in self.config.winfo_children():child.destroy()
        self.meta={}
        for i,(key,label,width) in enumerate((('escola','Escola',28),('professor','Professor',23),('titulo','Título',28),('numero','Número da prova',7),('mensagem','Mensagem final',45))):
            row=0 if i<3 else 1;col=(i if i<3 else i-3)*2
            var=tk.StringVar(value=getattr(self.lista,key));self.meta[key]=var
            ttk.Label(self.config,text=label+':').grid(row=row,column=col,sticky='w',padx=5,pady=4)
            ttk.Entry(self.config,textvariable=var,width=width).grid(row=row,column=col+1,sticky='w',padx=5)
            var.trace_add('write',self.alterado)
        ttk.Button(self.config,text='Salvar rascunho JSON',command=self.rascunho).grid(row=1,column=4,columnspan=2,padx=8)
        self.meta['tamanho_quadrados']=tk.StringVar(value='3,0')
        ttk.Label(self.config,text='Lado dos quadrados NOTA/PM (cm):').grid(row=2,column=0,columnspan=2,sticky='w',padx=5,pady=4)
        ttk.Spinbox(self.config,from_=1.5,to=3,increment=.1,textvariable=self.meta['tamanho_quadrados'],width=7).grid(row=2,column=2,sticky='w')
        def ajustar_quadrados(*args):
            self.preview.page=0
            self.alterado()
        self.meta['tamanho_quadrados'].trace_add('write',ajustar_quadrados)
        self.tree.heading('conteudo',text='Questões da prova (1 a 10)')
        self.atualizar();self.dirty=False

    def sincronizar(self):
        for key,var in self.meta.items():
            value=var.get()
            if key=='tamanho_quadrados':
                try:value=float(value.replace(',','.'))
                except ValueError:raise ValueError('Informe o lado dos quadrados em centímetros (1,5 a 3).') from None
            setattr(self.lista,key,value)

    def atualizar(self,content=None):
        if getattr(self,'_exportando',False):return
        if self.pending:self.window.after_cancel(self.pending);self.pending=None
        selected=self.selecionado();self.tree.delete(*self.tree.get_children())
        for i,(g,q) in enumerate(self.lista.itens):self.tree.insert('','end',iid=str(i),values=(f'{i+1}. {CONTEUDOS[g]}',))
        if selected is not None and selected<len(self.lista.itens):self.tree.selection_set(str(selected))
        try:
            self.sincronizar();self.preview.mostrar(content if content is not None else pdf_prova(self.lista))
            self.status.set(f'{len(self.lista.itens)}/10 questões. Quatro páginas verticais: capa + 4 + 4 + 2. Alternativas em branco são permitidas só no rascunho.')
        except (ValueError,OverflowError,OSError,tk.TclError) as exc:
            self.preview.limpar('Corrija os dados para visualizar.');self.status.set(str(exc))

    def adicionar(self):
        if len(self.lista.itens)>=10:messagebox.showinfo('Prova completa','A prova já tem dez questões. Edite ou remova uma delas.',parent=self.window);return
        QuestaoProvaDialog(self)

    def editar(self):
        i=self.selecionado()
        if i is not None:QuestaoProvaDialog(self,i)

    def carregar(self):
        path=filedialog.askopenfilename(parent=self.window,filetypes=[('JSON de prova','*.json')])
        if not path:return
        try:
            prova=carregar_prova(path)
            if not self.descartar():return
            self.lista=prova
            for key,var in self.meta.items():var.set(getattr(prova,key))
            self.atualizar();self.dirty=False
        except (ValueError,OSError) as exc:messagebox.showerror('Não foi possível carregar',str(exc),parent=self.window)

    def rascunho(self):
        try:
            self.sincronizar()
            path=filedialog.asksaveasfilename(parent=self.window,defaultextension='.json',initialfile='rascunho_prova.json',filetypes=[('JSON','*.json')])
            if path:salvar_rascunho(path,self.lista);self.dirty=False;self.status.set('Rascunho salvo. Pode ser reaberto mesmo com menos de dez questões.')
        except (ValueError,OSError) as exc:messagebox.showerror('Não foi possível salvar',str(exc),parent=self.window)

    def salvar(self):
        try:
            self.sincronizar()
            from provas import validar_prova,dados_prova
            validar_prova(dados_prova(self.lista),completa=True)
            path=filedialog.asksaveasfilename(parent=self.window,defaultextension='.pdf',initialfile='prova_'+self.lista.numero+'.pdf',filetypes=[('PDF','*.pdf')])
            if not path:return
            if Path(path).with_suffix('.json').exists() and not messagebox.askyesno('Substituir JSON?','Substituir o par PDF e JSON?',parent=self.window):return
            snapshot=deepcopy(self.lista)
            if self.pending:self.window.after_cancel(self.pending);self.pending=None
            self._exportando=True
            try:gerar_com_progresso(self.window,lambda:salvar_prova(path,snapshot))
            finally:self._exportando=False
            self.dirty=False;self.status.set('Prova salva: '+path)
            messagebox.showinfo('Prova salva','PDF de quatro páginas e JSON salvos. Para impressão, escolha duas páginas por folha no visualizador de PDF.',parent=self.window)
        except Exception as exc:messagebox.showerror('Não foi possível salvar',str(exc),parent=self.window)


class QuestaoProvaDialog(QuestaoDialog):
    def montar(self,item=None):
        q=item if isinstance(item,QuestaoProva) else None
        super().montar(q.modelo if q else None)
        self.personalizar=tk.BooleanVar(value=q is not None and q.texto is not None)
        box=ttk.LabelFrame(self.aba.corpo,text='Enunciado e alternativas da prova',padding=10);box.pack(fill='x',pady=8)
        self.fonte=tk.StringVar(value=str(q.fonte) if q and q.fonte is not None else 'Automático')
        fontes=ttk.Frame(box);fontes.pack(fill='x',pady=5)
        ttk.Label(fontes,text='Fonte do enunciado e alternativas (pt):').pack(side='left')
        ttk.Combobox(fontes,textvariable=self.fonte,values=('Automático',8,9,10,11,12,13,14,15,16,17,18),width=12).pack(side='left',padx=8)
        ttk.Label(box,text='O texto automático acompanha o modelo. Ao personalizar, revise-o se mudar as medidas; ele não será sobrescrito.',wraplength=650).pack(anchor='w')
        ttk.Checkbutton(box,text='Usar enunciado personalizado',variable=self.personalizar).pack(anchor='w')
        self.texto=tk.Text(box,height=6,wrap='word',undo=True);self.texto.pack(fill='x',pady=5)
        def padrao():
            try:
                g,modelo=super(QuestaoProvaDialog,self).questao()
                self.texto.delete('1.0','end');self.texto.insert('1.0',texto_editavel(g,modelo));self.personalizar.set(True)
            except ValueError as exc:messagebox.showerror('Confira os dados',str(exc),parent=self.window)
        if q and q.texto is not None:self.texto.insert('1.0',q.texto)
        else:
            try:
                g,m=super().questao();self.texto.insert('1.0',texto_editavel(g,m))
            except ValueError:pass
        def editado(event=None):
            if self.texto.edit_modified():self.personalizar.set(True);self.texto.edit_modified(False)
        self.texto.edit_modified(False);self.texto.bind('<<Modified>>',editado)
        ttk.Button(box,text='Copiar texto atualizado do modelo',command=padrao).pack(anchor='w')
        self.alternativas=[]
        ttk.Label(box,text='Nas alternativas: x^2; x^{n+1}; 3 over 4; (x+1) over (x-1); 2*x. A prévia mostra a notação formatada.',wraplength=650).pack(anchor='w',pady=5)
        for i,label in enumerate('abcde'):
            row=ttk.Frame(box);row.pack(fill='x',pady=3)
            ttk.Label(row,text=label+')',width=3).pack(side='left')
            entry=tk.Text(row,height=2,wrap='word',undo=True);entry.pack(side='left',fill='x',expand=True)
            entry.insert('1.0',q.alternativas[i] if q else '');self.alternativas.append(entry)
        self.add.configure(text='Salvar alteração' if self.index is not None else 'Acrescentar à prova',command=self.confirmar)
        self.last=None

    def questao(self):
        g,modelo=super().questao()
        texto_fonte=self.fonte.get().strip()
        try:fonte=None if texto_fonte=='Automático' else float(texto_fonte.replace(',','.'))
        except ValueError:raise ValueError('Informe o tamanho da fonte entre 8 e 18 pontos.') from None
        return g,QuestaoProva(modelo,self.texto.get('1.0','end-1c') if self.personalizar.get() else None,
                              [w.get('1.0','end-1c') for w in self.alternativas],fonte)

    def poll(self):
        if self.timer:self.window.after_cancel(self.timer);self.timer=None
        try:
            q=self.questao();key=repr(q)
            if q[1].texto is None:
                automatico=texto_editavel(q[0],q[1].modelo)
                if self.texto.get('1.0','end-1c')!=automatico:
                    self.texto.delete('1.0','end');self.texto.insert('1.0',automatico);self.texto.edit_modified(False)
            if key!=self.last:
                self.editor.sincronizar();rascunho=deepcopy(self.editor.lista)
                index=len(rascunho.itens) if self.index is None else self.index
                if self.index is None:rascunho.itens.append(q)
                else:rascunho.itens[index]=q
                content=pdf_prova(rascunho);x,y,w,h=quadro(index)
                self.preview.page=1+index//4;self.preview.mostrar(content,crop=(x,y,w,h));self.last=key
                self.editor.preview.page=1+index//4;self.editor.preview.mostrar(content)
                self.editor.status.set('Prévia temporária da questão em edição; confirme para salvar a alteração.')
                self.status.set('Prévia no tamanho real do quadro da prova. Preencha as cinco alternativas antes de exportar.')
        except (ValueError,OverflowError,OSError,tk.TclError) as exc:
            self.last=None;self.preview.limpar('Confira os dados.');self.status.set(str(exc))
            self.editor.preview.limpar('A questão em edição não cabe ou contém dados inválidos.')
        self.timer=self.window.after(600,self.poll)

    def fechar(self):
        super().fechar()
        self.editor.atualizar() # Descarta só a prévia temporária, não os dados confirmados.

    def confirmar(self):
        if self.timer:self.window.after_cancel(self.timer);self.timer=None
        try:
            q=self.questao();self.editor.sincronizar();snapshot=deepcopy(self.editor.lista)
            if self.index is None:snapshot.itens.append(q)
            else:snapshot.itens[self.index]=q
            if self.editor.pending:self.editor.window.after_cancel(self.editor.pending);self.editor.pending=None
            self.editor._exportando=True
            try:content=gerar_com_progresso(self.window,lambda:pdf_prova(snapshot),mensagem='Conferindo a questão e atualizando a prova…')
            finally:self.editor._exportando=False
            self.editor.receber(q,self.index,content)
            self.fechar()
        except Exception as exc:
            messagebox.showerror('Confira a questão',str(exc),parent=self.window)
            if self.window.winfo_exists():self.timer=self.window.after(600,self.poll)
