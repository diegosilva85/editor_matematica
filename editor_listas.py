"""Janelas do editor de listas; usa os mesmos formulários das abas existentes."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from listas import Lista, CONTEUDOS, pdf_lista, salvar_lista, carregar_lista, planejar
from janelas import maximizar


class Previa(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.content=None; self.crop=None; self.page=0; self.pages=0; self.zoom=1
        bar=ttk.Frame(self); bar.pack(fill='x')
        ttk.Button(bar,text='◀',command=lambda:self.mover(-1)).pack(side='left')
        ttk.Button(bar,text='▶',command=lambda:self.mover(1)).pack(side='left')
        self.status=tk.StringVar(value='Prévia')
        ttk.Label(bar,textvariable=self.status).pack(side='left',padx=6)
        ttk.Button(bar,text='−',command=lambda:self.ampliar(-.25)).pack(side='right')
        ttk.Button(bar,text='+',command=lambda:self.ampliar(.25)).pack(side='right')
        body=ttk.Frame(self); body.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(body,bg='#dce1e7',highlightthickness=0)
        sy=ttk.Scrollbar(body,orient='vertical',command=self.canvas.yview)
        sx=ttk.Scrollbar(body,orient='horizontal',command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        sy.pack(side='right',fill='y'); sx.pack(side='bottom',fill='x')
        self.canvas.pack(fill='both',expand=True)
        self.image=None; self.pending=None
        self.canvas.bind('<Configure>',self.redimensionar)
        self.bind('<Destroy>',self.destruir,add='+')

    def destruir(self,event):
        if event.widget==self and self.pending:
            self.after_cancel(self.pending); self.pending=None

    def redimensionar(self,event=None):
        if self.pending: self.after_cancel(self.pending)
        self.pending=self.after(250,self.render)

    def limpar(self,text='Adicione questões para visualizar a lista.'):
        self.content=None; self.image=None; self.canvas.delete('all'); self.status.set(text)

    def mostrar(self,content,crop=None):
        self.content=content; self.crop=crop; self.render()

    def mover(self,delta):
        self.page=max(0,min(self.pages-1,self.page+delta)); self.render()

    def ampliar(self,delta):
        self.zoom=max(.5,min(3,self.zoom+delta)); self.render()

    def render(self):
        if self.pending: self.after_cancel(self.pending)
        self.pending=None
        if not self.content: return
        try:
            import pypdfium2 as pdfium
            from PIL import ImageTk
            with pdfium.PdfDocument(self.content) as doc:
                self.pages=len(doc); self.page=max(0,min(self.page,self.pages-1))
                page=doc[self.page]
                try:
                    width=page.get_width(); crop=(0,0,0,0)
                    if self.crop:
                        x,y,w,h=self.crop
                        crop=(x,y,width-x-w,page.get_height()-y-h); width=w
                    scale=max(250,self.canvas.winfo_width()-24)/width*self.zoom
                    bitmap=page.render(scale=scale,crop=crop)
                    try: self.image=ImageTk.PhotoImage(bitmap.to_pil().copy(),master=self)
                    finally: bitmap.close()
                finally: page.close()
            self.canvas.delete('all'); self.canvas.create_image(10,10,image=self.image,anchor='nw')
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            self.status.set(f'Página {self.page+1}/{self.pages}')
        except ImportError:
            self.limpar('Instale as dependências: pip install -r requirements.txt')
        except Exception as e:
            self.limpar(f'Não foi possível exibir a prévia: {e}')


class EditorLista:
    def __init__(self,parent):
        self.window=tk.Toplevel(parent); self.window.title('Nova Lista de Exercícios')
        self.window.geometry('1250x850'); self.window.minsize(850,600)
        maximizar(self.window)
        self.lista=Lista(); self.dirty=False; self.pending=None
        self.window.protocol('WM_DELETE_WINDOW',self.fechar)
        config=ttk.Frame(self.window,padding=10); config.pack(fill='x')
        ttk.Label(config,text='Título:').pack(side='left')
        self.title=tk.StringVar(value=self.lista.titulo)
        ttk.Entry(config,textvariable=self.title,width=35).pack(side='left',padx=8)
        ttk.Label(config,text='Por linha:').pack(side='left')
        self.cols=tk.IntVar(value=2)
        ttk.Combobox(config,textvariable=self.cols,values=(1,2,3),state='readonly',width=3).pack(side='left',padx=8)
        ttk.Label(config,text='Máximo por página:').pack(side='left')
        self.limit=tk.IntVar(value=12)
        ttk.Spinbox(config,textvariable=self.limit,from_=1,to=12,width=3,state='readonly').pack(side='left',padx=8)
        body=ttk.Panedwindow(self.window,orient='horizontal'); body.pack(fill='both',expand=True,padx=10)
        left=ttk.Frame(body,width=290); body.add(left,weight=1)
        ttk.Button(left,text='Acrescentar questão',command=self.adicionar).pack(fill='x',pady=6)
        self.tree=ttk.Treeview(left,columns=('conteudo',),show='headings',selectmode='browse')
        self.tree.heading('conteudo',text='Questões (na ordem da lista)'); self.tree.column('conteudo',width=270)
        scroll=ttk.Scrollbar(left,orient='vertical',command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y'); self.tree.pack(fill='both',expand=True)
        self.tree.bind('<Double-1>',lambda e:self.editar())
        actions=ttk.Frame(left); actions.pack(fill='x',pady=8)
        for text,command in [('Editar',self.editar),('Remover',self.remover),('↑',lambda:self.mover(-1)),('↓',lambda:self.mover(1))]:
            ttk.Button(actions,text=text,command=command,width=7).pack(side='left',padx=2)
        self.preview=Previa(body); body.add(self.preview,weight=3)
        footer=ttk.Frame(self.window,padding=10); footer.pack(fill='x')
        ttk.Button(footer,text='Carregar JSON',command=self.carregar).pack(side='left')
        ttk.Button(footer,text='Atualizar prévia',command=self.atualizar).pack(side='left',padx=8)
        ttk.Button(footer,text='Salvar PDF + JSON',command=self.salvar).pack(side='right')
        self.status=tk.StringVar(value='Até 3 por linha e 12 por página. Textos longos recebem mais espaço.')
        ttk.Label(self.window,textvariable=self.status,padding=8,wraplength=1000).pack(fill='x')
        for var in (self.title,self.cols,self.limit): var.trace_add('write',self.alterado)
        self.preview.limpar()

    def sincronizar(self):
        self.lista.titulo=self.title.get(); self.lista.colunas=self.cols.get(); self.lista.por_pagina=self.limit.get()

    def alterado(self,*args):
        self.dirty=True
        if self.pending: self.window.after_cancel(self.pending)
        self.pending=self.window.after(500,self.atualizar)

    def atualizar(self):
        if self.pending: self.window.after_cancel(self.pending); self.pending=None
        selected=self.selecionado()
        self.tree.delete(*self.tree.get_children())
        for i,(grau,item) in enumerate(self.lista.itens):
            self.tree.insert('', 'end',iid=str(i),values=(f'{i+1}. {CONTEUDOS[grau]}',))
        if selected is not None and selected<len(self.lista.itens): self.tree.selection_set(str(selected))
        if not self.lista.itens: self.preview.limpar(); self.status.set('Lista vazia. Acrescente uma questão.'); return
        try:
            self.sincronizar(); content=pdf_lista(self.lista); self.preview.mostrar(content)
            self.status.set(f'{len(self.lista.itens)} questões. A prévia usa a mesma diagramação do PDF salvo.')
        except (ValueError,OverflowError,OSError,tk.TclError) as e:
            self.preview.limpar('Corrija os dados para visualizar.'); self.status.set(str(e))

    def selecionado(self):
        selected=self.tree.selection(); return int(selected[0]) if selected else None

    def adicionar(self): QuestaoDialog(self)
    def editar(self):
        index=self.selecionado()
        if index is not None: QuestaoDialog(self,index)

    def receber(self,questao,index=None):
        if index is None: self.lista.itens.append(questao)
        else: self.lista.itens[index]=questao
        self.dirty=True; self.atualizar()

    def remover(self):
        index=self.selecionado()
        if index is not None and messagebox.askyesno('Remover questão',f'Remover a questão {index+1}?',parent=self.window):
            self.lista.itens.pop(index); self.dirty=True; self.atualizar()

    def mover(self,delta):
        i=self.selecionado()
        if i is not None and 0<=i+delta<len(self.lista.itens):
            self.lista.itens[i],self.lista.itens[i+delta]=self.lista.itens[i+delta],self.lista.itens[i]
            self.dirty=True; self.atualizar(); self.tree.selection_set(str(i+delta))

    def descartar(self):
        return not self.dirty or messagebox.askyesno('Alterações não salvas','Descartar as alterações não salvas?',parent=self.window)

    def carregar(self):
        path=filedialog.askopenfilename(parent=self.window,filetypes=[('JSON','*.json')])
        if not path: return
        try:
            lista=carregar_lista(path)
            if not self.descartar(): return
            self.lista=lista; self.title.set(lista.titulo); self.cols.set(lista.colunas); self.limit.set(lista.por_pagina)
            self.atualizar(); self.dirty=False
        except (ValueError,OSError) as e: messagebox.showerror('Não foi possível carregar',str(e),parent=self.window)

    def salvar(self):
        try:
            self.sincronizar()
            if not self.lista.itens: raise ValueError('Acrescente pelo menos uma questão.')
            path=filedialog.asksaveasfilename(parent=self.window,defaultextension='.pdf',initialfile='lista_exercicios.pdf',filetypes=[('PDF','*.pdf')])
            if not path: return
            if Path(path).with_suffix('.json').exists() and not messagebox.askyesno('Substituir JSON?','O JSON correspondente já existe. Substituir o par PDF e JSON?',parent=self.window): return
            salvar_lista(path,self.lista); self.dirty=False
            self.status.set(f'PDF e JSON salvos em {path}')
            messagebox.showinfo('Lista salva','PDF e JSON salvos. Use o JSON para continuar a edição.',parent=self.window)
        except (ValueError,OSError,OverflowError,tk.TclError) as e: messagebox.showerror('Não foi possível salvar',str(e),parent=self.window)

    def fechar(self):
        if self.descartar():
            if self.pending: self.window.after_cancel(self.pending)
            self.window.destroy()


class QuestaoDialog:
    def __init__(self,editor,index=None):
        self.editor=editor; self.index=index; self.aba=None; self.timer=None; self.last=None
        self.window=tk.Toplevel(editor.window); self.window.title('Editar questão' if index is not None else 'Acrescentar questão')
        self.window.geometry('1450x900'); self.window.minsize(1000,650)
        maximizar(self.window)
        self.window.transient(editor.window); self.window.grab_set(); self.window.protocol('WM_DELETE_WINDOW',self.fechar)
        top=ttk.Frame(self.window,padding=10); top.pack(fill='x')
        ttk.Label(top,text='Conteúdo:').pack(side='left')
        self.content=tk.StringVar(value=CONTEUDOS[editor.lista.itens[index][0]] if index is not None else CONTEUDOS[1])
        combo=ttk.Combobox(top,textvariable=self.content,values=list(CONTEUDOS.values()),state='readonly',width=32)
        combo.pack(side='left',padx=8); combo.bind('<<ComboboxSelected>>',lambda e:self.montar())
        body=ttk.Panedwindow(self.window,orient='horizontal'); body.pack(fill='both',expand=True,padx=10)
        self.form=ttk.Frame(body,width=850); body.add(self.form,weight=3)
        self.preview=Previa(body); body.add(self.preview,weight=2)
        bar=ttk.Frame(self.window,padding=10); bar.pack(fill='x')
        self.status=tk.StringVar(value='A prévia à direita acompanha as alterações.')
        ttk.Label(bar,textvariable=self.status,wraplength=750).pack(side='left')
        self.add=ttk.Button(bar,text='Salvar alteração' if index is not None else 'Acrescentar à lista',command=self.confirmar)
        self.add.pack(side='right')
        ttk.Button(bar,text='Fechar',command=self.fechar).pack(side='right',padx=8)
        self.montar(editor.lista.itens[index][1] if index is not None else None)
        self.poll()

    def montar(self,item=None):
        from interface import Aba,AbaTriangulos,AbaSolidos,AbaExponenciais,AbaProgressao
        for child in self.form.winfo_children(): child.destroy()
        notebook=ttk.Notebook(self.form); notebook.pack(fill='both',expand=True)
        grau=next(k for k,v in CONTEUDOS.items() if v==self.content.get())
        self.aba=Aba(notebook,grau) if grau in (1,2) else {3:AbaTriangulos,4:AbaSolidos,5:AbaExponenciais,6:AbaProgressao}[grau](notebook)
        if item is not None: self.aba.restaurar((grau,[item],1,''))
        else: self.aba.total.set(1); self.aba.criar()
        area=self.aba.corpo.master.master
        for child in self.aba.frame.winfo_children():
            if child!=area: child.pack_forget()
        def ajustar_textos(event=None):
            width=max(180,self.aba.corpo.winfo_width()-70)
            def visit(widget):
                if getattr(widget,'_largura_fixa',False): return
                if isinstance(widget,ttk.Label) and int(widget.cget('wraplength') or 0)>0:
                    widget.configure(wraplength=width)
                for child in widget.winfo_children(): visit(child)
            visit(self.aba.corpo)
        area.bind('<Configure>',ajustar_textos,add='+')
        self.last=None
        self.add.configure(text='Salvar alteração' if self.index is not None else 'Acrescentar à lista',command=self.confirmar)

    def questao(self):
        grau,items,_,_=self.aba.pagina()
        return grau,items[0]

    def poll(self):
        if self.timer: self.window.after_cancel(self.timer); self.timer=None
        try:
            questao=self.questao(); key=repr(questao)
            if key!=self.last:
                lista=Lista('Prévia da questão',self.editor.cols.get(),1,[questao])
                content=pdf_lista(lista)
                _,x,y,w,h,_,_=planejar(lista)[0][0]
                self.preview.mostrar(content,crop=(x-2,y-2,w+4,h+4)); self.last=key
                self.status.set('Confira a questão antes de acrescentar à lista.')
        except (ValueError,OverflowError,OSError,tk.TclError) as e:
            self.last=None; self.preview.limpar('Dados incompletos ou inválidos.'); self.status.set(str(e))
        self.timer=self.window.after(600,self.poll)

    def confirmar(self):
        try:
            questao=self.questao()
            self.editor.sincronizar()
            items=list(self.editor.lista.itens)
            if self.index is None: items.append(questao)
            else: items[self.index]=questao
            # Valida a questão nas dimensões reais da lista antes de confirmar.
            pdf_lista(Lista(self.editor.lista.titulo,self.editor.lista.colunas,self.editor.lista.por_pagina,items))
            self.editor.receber(questao,self.index)
            if self.index is not None: self.fechar(); return
            self.status.set('Questão acrescentada à lista.')
            self.add.configure(text='Acrescentar outra questão',command=self.montar)
        except (ValueError,OSError,OverflowError,tk.TclError) as e:
            messagebox.showerror('Confira a questão',str(e),parent=self.window)

    def fechar(self):
        if self.timer: self.window.after_cancel(self.timer)
        self.window.grab_release(); self.window.destroy()
