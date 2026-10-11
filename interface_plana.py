"""Editor de geometria plana, também utilizado em Criar Lista."""
import tkinter as tk
from tkinter import ttk,messagebox
from dataclasses import asdict
from functools import lru_cache
from html import unescape
import re
from interface import Aba
from geometria_plana import FiguraPlana,FIGURAS,NOMES,PEDIDOS,REGIOES,campos,padrao,apoio,gerar,PASTA
from numeros_exatos import ler


@lru_cache(maxsize=40)
def miniatura(figura,tamanho):
    from PIL import Image
    with Image.open(PASTA/(figura+'.png')) as im:
        preview=im.convert('RGB')
        preview.thumbnail((tamanho,tamanho));return preview


def converter_medidas(figura,valores,origem,destino):
    """Troca raio/diâmetro preservando a figura e a notação decimal digitada."""
    from decimal import Decimal
    resultado={}
    for (antes,_),(depois,_) in zip(campos(figura,origem),campos(figura,destino)):
        texto=valores.get(antes,'')
        if antes!=depois:
            try:
                value,_=ler(texto);fator=2 if destino=='Diâmetro' else .5
                if re.fullmatch(r'\d+(?:[.,]\d+)?',texto.strip()):
                    numero=Decimal(texto.strip().replace(',','.'))*Decimal(str(fator))
                    texto=format(numero,'f').rstrip('0').rstrip('.') if '.' in format(numero,'f') else format(numero,'f')
                    if ',' in valores[antes]:texto=texto.replace('.',',')
                else:texto=str(value*2 if destino=='Diâmetro' else value/2)
            except ValueError:pass # Preserva entrada incompleta para correção pelo professor.
        resultado[depois]=texto
    return resultado


class AbaPlana(Aba):
    def __init__(self,notebook):
        super().__init__(notebook,1)
        self.grau=8;self.total.set(1);self.quantidade.configure(to=12)
        notebook.tab(self.frame,text='Geometria plana');self.titulo.set('Geometria plana')
        ttk.Label(self.frame,text='29 figuras. Até 3 por linha e 12 por página; quebra automática para manter a legibilidade.').pack(anchor='w')

    def criar(self):
        if not self.limpar():return
        for i in range(self.total.get()):self.editor(FiguraPlana(),i)

    def modelo(self,r):
        return FiguraPlana(**{k:v.get() for k,v in r.items() if not k.startswith('_') and k!='valores'},
                           valores={k:v.get() for k,v in r['valores'].items()})

    def editor(self,q,index):
        outer=ttk.LabelFrame(self.corpo,text=f'Questão {index+1}',padding=12);outer.pack(fill='x',pady=6)
        abaixo=getattr(self,'apoio_embaixo',False)
        form=ttk.Frame(outer);form.pack(side='top' if abaixo else 'left',fill='both',expand=True)
        panel=ttk.LabelFrame(outer,text='Apoio ao professor - não sai no PDF',padding=10)
        panel._largura_fixa=True
        panel.pack(side='bottom' if abaixo else 'right',fill='x' if abaixo else 'y',padx=10,pady=6)
        r={k:(tk.BooleanVar(value=v) if type(v) is bool else tk.StringVar(value=v)) for k,v in asdict(q).items() if k!='valores'}
        r['valores']={};r['_nome']=tk.StringVar(value=FIGURAS[q.figura]['nome'])
        r['_minimo']=tk.StringVar(value='2');r['_maximo']=tk.StringVar(value='20');self.registros.append(r)
        row=ttk.Frame(form);row.pack(fill='x',pady=4)
        ttk.Label(row,text='Figura:').pack(side='left')
        figura=ttk.Combobox(row,textvariable=r['_nome'],values=tuple(NOMES),state='readonly',width=40)
        figura.pack(side='left',padx=6)
        row=ttk.Frame(form);row.pack(fill='x',pady=4)
        ttk.Label(row,text='Calcular:').pack(side='left')
        ttk.Combobox(row,textvariable=r['pedido'],values=PEDIDOS,state='readonly',width=32).pack(side='left',padx=6)
        ttk.Label(row,text='Unidade:').pack(side='left')
        ttk.Combobox(row,textvariable=r['unidade'],values=('mm','cm','m'),state='readonly',width=4).pack(side='left',padx=6)
        row=ttk.Frame(form);row.pack(fill='x',pady=4)
        ttk.Label(row,text='Medida circular:').pack(side='left')
        circular=ttk.Combobox(row,textvariable=r['circular'],values=('Raio','Diâmetro'),state='readonly',width=12)
        circular.pack(side='left',padx=6)
        ttk.Checkbutton(row,text='Incluir figura no PDF',variable=r['incluir_imagem']).pack(side='left',padx=6)
        row=ttk.Frame(form);row.pack(fill='x',pady=4)
        ttk.Label(row,text='Região (círculos concêntricos):').pack(side='left')
        regiao=ttk.Combobox(row,textvariable=r['regiao'],values=REGIOES,state='readonly',width=29)
        regiao.pack(side='left',padx=6)
        body=ttk.Frame(form);body.pack(fill='x',pady=8)
        preview=tk.Canvas(body,width=295,height=295,background='white',highlightthickness=0);preview.pack(side='left',padx=(0,10))
        fields=ttk.Frame(body);fields.pack(side='left',fill='x',expand=True)
        ttk.Label(form,text='Aceita inteiros, vírgula decimal, frações e raízes: 7,6; 3/2; √3; 2√3/3. A figura é ilustrativa, sem escala.',wraplength=560).pack(anchor='w',pady=4)
        regras=ttk.Label(form,wraplength=560,justify='left');regras.pack(anchor='w',pady=4)
        ajuda=ttk.Label(panel,wraplength=540 if abaixo else 285,justify='left');ajuda.pack(anchor='w')
        texto=ttk.Label(form,wraplength=560,justify='left');texto.pack(anchor='w',pady=6)
        pending=[None];pausado=[False]

        def atualizar():
            pending[0]=None
            if not outer.winfo_exists():return
            modelo=self.modelo(r);mensagem,ok=apoio(modelo)
            ajuda.configure(text=mensagem,foreground='#166534' if ok else '#a33')
            texto.configure(text='Enunciado: '+unescape(re.sub('<[^>]+>','',modelo.enunciado())) if ok else 'Ajuste as medidas para gerar a questão.')
            if ok:
                from cotas_planas import miniatura as miniatura_cotada
                from PIL import ImageTk
                preview._imagem=ImageTk.PhotoImage(miniatura_cotada(modelo))
                preview.delete('all');preview.create_image(147,147,image=preview._imagem)
            else:
                preview.delete('all');preview.create_text(147,147,text='Confira as medidas para atualizar a figura.',width=240)

        def agendar(*args):
            if pausado[0]:return
            if pending[0]:outer.after_cancel(pending[0])
            pending[0]=outer.after(180,atualizar)

        def destruir(event):
            if event.widget==outer and pending[0]:outer.after_cancel(pending[0]);pending[0]=None
        outer.bind('<Destroy>',destruir,add='+')

        def montar(valores):
            pausado[0]=True
            for child in fields.winfo_children():child.destroy()
            r['valores']={}
            for i,(key,label) in enumerate(campos(r['figura'].get(),r['circular'].get())):
                var=tk.StringVar(value=valores.get(key,''));r['valores'][key]=var
                ttk.Label(fields,text=label+':',wraplength=235).grid(row=i,column=0,sticky='w',padx=4,pady=4)
                ttk.Entry(fields,textvariable=var,width=12).grid(row=i,column=1,padx=4,pady=4)
                var.trace_add('write',agendar)
            spec=FIGURAS[r['figura'].get()]
            circular.configure(state='readonly' if any(k in ('r','R') for k,_,_ in spec['campos']) else 'disabled')
            regiao.configure(state='readonly' if spec['numero']==12 else 'disabled')
            regras.configure(text=spec['construcao'])
            from PIL import ImageTk
            preview._imagem=ImageTk.PhotoImage(miniatura(r['figura'].get(),200))
            preview.delete('all');preview.create_image(147,147,image=preview._imagem)
            pausado[0]=False;agendar()

        def trocar_figura(event=None):
            r['figura'].set(NOMES[r['_nome'].get()]);montar(padrao(r['figura'].get(),r['circular'].get()))
        figura.bind('<<ComboboxSelected>>',trocar_figura)
        anterior=[q.circular]
        def trocar_circular(event=None):
            values=converter_medidas(r['figura'].get(),{k:v.get() for k,v in r['valores'].items()},anterior[0],r['circular'].get())
            anterior[0]=r['circular'].get();montar(values)
        circular.bind('<<ComboboxSelected>>',trocar_circular)

        def acervo():
            from PIL import ImageTk
            janela=tk.Toplevel(self.frame);janela.title('Acervo de geometria plana - 29 figuras');janela.geometry('940x720')
            janela.transient(self.frame.winfo_toplevel())
            janela.grab_set()
            canvas=tk.Canvas(janela,highlightthickness=0);scroll=ttk.Scrollbar(janela,orient='vertical',command=canvas.yview)
            canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
            grid=ttk.Frame(canvas);canvas.create_window((0,0),window=grid,anchor='nw')
            grid.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
            janela._imagens=[]
            def selecionar(nome):r['_nome'].set(nome);trocar_figura();janela.destroy()
            for i,(nome,key) in enumerate(NOMES.items()):
                cell=ttk.Frame(grid,padding=5);cell.grid(row=i//6,column=i%6,sticky='n')
                im=ImageTk.PhotoImage(miniatura(key,130));janela._imagens.append(im)
                ttk.Button(cell,image=im,command=lambda nome=nome:selecionar(nome)).pack()
                ttk.Label(cell,text=f'{i+1:02d}. {nome}',wraplength=130,justify='center').pack()
        ttk.Button(form,text='Ver acervo e escolher figura',command=acervo).pack(anchor='w',pady=4)
        box=ttk.LabelFrame(form,text='Gerar medidas aleatórias (inteiros)',padding=8);box.pack(fill='x',pady=6)
        for key,label in (('_minimo','Mínimo'),('_maximo','Máximo')):
            ttk.Label(box,text=label+':').pack(side='left')
            ttk.Entry(box,textvariable=r[key],width=5).pack(side='left',padx=5)
        def aleatorio():
            try:
                snapshot=self.modelo(r);lo=int(r['_minimo'].get());hi=int(r['_maximo'].get())
                from progresso import gerar_com_progresso
                values=gerar_com_progresso(self.frame.winfo_toplevel(),lambda:gerar(snapshot,lo,hi),titulo='Gerando medidas',mensagem='Escolhendo medidas compatíveis com a figura…')
                montar(values)
            except ValueError as exc:messagebox.showerror('Não foi possível gerar',str(exc),parent=self.frame.winfo_toplevel())
        ttk.Button(box,text='Gerar valores',command=aleatorio).pack(side='left',padx=6)
        for key,var in r.items():
            if not key.startswith('_') and key!='valores':var.trace_add('write',agendar)
        montar(q.valores)

    def pagina(self):
        itens=[]
        for i,r in enumerate(self.registros):
            try:
                q=self.modelo(r);q.validar();itens.append(q)
            except ValueError as exc:raise ValueError(f'Geometria plana, questão {i+1}: {exc}') from exc
        return 8,itens,self.colunas.get(),self.titulo.get()

    def restaurar(self,pagina):
        _,items,cols,title=pagina
        self.limpar(confirmar=False);self.total.set(len(items));self.colunas.set(cols);self.titulo.set(title)
        for i,q in enumerate(items):self.editor(q,i)
