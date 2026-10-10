"""Interface com páginas independentes de primeiro e segundo grau."""
import os
import tempfile
import webbrowser
from pathlib import Path
from dataclasses import asdict
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app_graficos import Funcao, numero
from parabolas import Parabola, salvar_documento
from triangulos import Triangulo, POSICOES, LADOS, vertices, PITAGORAS, LADOS_PIT
from solidos import Solido, TIPOS, campos, desenho
from exponenciais import Exponencial, TIPOS as TIPOS_EXP, coeficiente
from documentos import carregar_documento
from progressao import Progressao, TIPOS as TIPOS_PA, ALVOS as ALVOS_PA, PADRAO as PADRAO_PA, DADOS_SOMA
from janelas import maximizar


class Aba:
    def __init__(self, notebook, grau):
        self.grau=grau
        self.registros=[]
        self.frame=ttk.Frame(notebook,padding=12)
        notebook.add(self.frame,text=f'{grau}º grau')
        self.total=tk.IntVar(value=4)
        self.colunas=tk.IntVar(value=2)
        self.titulo=tk.StringVar(value=f'Funções de {"primeiro" if grau==1 else "segundo"} grau')
        config=ttk.Frame(self.frame); config.pack(fill='x')
        ttk.Label(config,text='Quantidade:').pack(side='left')
        self.quantidade=ttk.Spinbox(config,from_=1,to=15 if grau==1 else 10,textvariable=self.total,width=4,state='readonly')
        self.quantidade.pack(side='left',padx=8)
        ttk.Label(config,text='Por linha:').pack(side='left')
        self.seletor_colunas=ttk.Combobox(config,values=(1,2,3) if grau==1 else (1,2),textvariable=self.colunas,width=3,state='readonly')
        self.seletor_colunas.pack(side='left',padx=8)
        ttk.Button(config,text='Criar documento',command=self.criar).pack(side='left',padx=8)
        ttk.Button(config,text='Limpar aba',command=self.limpar).pack(side='left')
        ttk.Label(self.frame,text='Título da página:').pack(anchor='w',pady=(10,2))
        ttk.Entry(self.frame,textvariable=self.titulo).pack(fill='x')
        if grau==2:
            ttk.Label(self.frame,text='Marque as informações que devem aparecer. Raízes sem valores reais não são marcadas.').pack(anchor='w',pady=6)
        area=ttk.Frame(self.frame); area.pack(fill='both',expand=True,pady=8)
        canvas=tk.Canvas(area,highlightthickness=0)
        barra=ttk.Scrollbar(area,orient='vertical',command=canvas.yview)
        horizontal=ttk.Scrollbar(area,orient='horizontal',command=canvas.xview)
        horizontal.pack(side='bottom',fill='x')
        canvas.configure(xscrollcommand=horizontal.set)
        canvas.configure(yscrollcommand=barra.set)
        barra.pack(side='right',fill='y'); canvas.pack(side='left',fill='both',expand=True)
        self.corpo=ttk.Frame(canvas)
        janela=canvas.create_window((0,0),window=self.corpo,anchor='nw')
        def ajustar_area(event=None):
            canvas.itemconfigure(janela,width=max(canvas.winfo_width(),self.corpo.winfo_reqwidth()))
            canvas.configure(scrollregion=canvas.bbox('all'))
        self.corpo.bind('<Configure>',ajustar_area)
        canvas.bind('<Configure>',ajustar_area)

    def limpar(self, confirmar=True):
        if self.registros and confirmar and not messagebox.askyesno('Limpar aba','Apagar os gráficos desta aba?'):
            return False
        for child in self.corpo.winfo_children(): child.destroy()
        self.registros.clear()
        return True

    def criar(self):
        if not self.limpar(): return
        for i in range(self.total.get()):
            card=ttk.LabelFrame(self.corpo,text=f'Gráfico {i+1}',padding=12); card.pack(fill='x',pady=6)
            if self.grau==2:
                quadro=card
                card=ttk.Frame(quadro); card.pack(side='top' if getattr(self,'apoio_embaixo',False) else 'left',fill='both',expand=True)
            row=ttk.Frame(card); row.pack(fill='x')
            reg={}
            entradas={}
            for key in ('a','b') if self.grau==1 else ('a','b','c'):
                reg[key]=tk.StringVar(value='1' if key=='a' else '0')
                ttk.Label(row,text=f'{key}:').pack(side='left')
                entradas[key]=ttk.Entry(row,textvariable=reg[key],width=10)
                entradas[key].pack(side='left',padx=(5,18))
            self.registros.append(reg)
            if self.grau==2:
                reg.update({key:tk.StringVar(value=value) for key,value in {'modo':'Coeficientes','quantidade_raizes':'2','raiz1':'0','raiz2':'1'}.items()})
                modo_row=ttk.Frame(card); modo_row.pack(fill='x',before=row,pady=(0,8))
                ttk.Label(modo_row,text='Informar por:').pack(side='left')
                seletor=ttk.Combobox(modo_row,values=('Coeficientes','Raízes e a'),textvariable=reg['modo'],state='readonly',width=18); seletor.pack(side='left',padx=8)
                roots_row=ttk.Frame(card)
                ttk.Label(roots_row,text='Quantidade de raízes:').pack(side='left')
                quantidade=ttk.Combobox(roots_row,values=('1','2'),textvariable=reg['quantidade_raizes'],state='readonly',width=3); quantidade.pack(side='left',padx=6)
                ttk.Label(roots_row,text='Raiz 1:').pack(side='left')
                ttk.Entry(roots_row,textvariable=reg['raiz1'],width=9).pack(side='left',padx=6)
                ttk.Label(roots_row,text='Raiz 2:').pack(side='left')
                segunda=ttk.Entry(roots_row,textvariable=reg['raiz2'],width=9); segunda.pack(side='left',padx=6)
                ttk.Label(roots_row,text='Uma raiz = raiz dupla.').pack(side='left')
                def atualizar_modo(event=None,reg=reg,entradas=entradas,roots_row=roots_row,row=row,segunda=segunda):
                    por_raizes=reg['modo'].get()=='Raízes e a'
                    for key in ('b','c'): entradas[key].configure(state='disabled' if por_raizes else 'normal')
                    if por_raizes: roots_row.pack(fill='x',after=row,pady=8)
                    else: roots_row.pack_forget()
                    segunda.configure(state='disabled' if reg['quantidade_raizes'].get()=='1' else 'normal')
                reg['_atualizar_modo']=atualizar_modo
                seletor.bind('<<ComboboxSelected>>',atualizar_modo); quantidade.bind('<<ComboboxSelected>>',atualizar_modo)
                atualizar_modo()
                options=ttk.Frame(card); options.pack(fill='x',pady=(10,0))
                for key,label in [('raizes','Raízes'),('intercepto','c (eixo y)'),('marcar_xv','xv (eixo x)'),('marcar_yv','yv (eixo y)')]:
                    reg[key]=tk.BooleanVar(value=True)
                    ttk.Checkbutton(options,text=label,variable=reg[key]).pack(side='left',padx=(0,14))
                presentation=ttk.Frame(card); presentation.pack(fill='x',before=modo_row,pady=(0,8))
                reg['apresentacao']=tk.StringVar(value='Gráfico')
                ttk.Label(presentation,text='Apresentação:').pack(side='left')
                select=ttk.Combobox(presentation,textvariable=reg['apresentacao'],values=('Gráfico','Expressão da função'),state='readonly',width=25)
                select.pack(side='left',padx=8)
                ttk.Label(card,text='Coeficientes e raízes: -1/2, 0,5, √2, 2√3/3 ou sqrt(2).',wraplength=700).pack(fill='x',pady=6)
                pedidos=ttk.Frame(card)
                ttk.Label(pedidos,text='Pedir para calcular:').pack(side='left',padx=(0,10))
                for key,label in [('pedir_raizes','Raízes reais'),('pedir_vertice','Coordenadas do vértice')]:
                    reg[key]=tk.BooleanVar(value=True)
                    ttk.Checkbutton(pedidos,text=label,variable=reg[key]).pack(side='left',padx=8)
                from contextos_quadraticas import CENARIOS, ALVOS, EIXOS, PROJETEIS, IMAGENS, grupo, cenarios_grupo
                contexto=ttk.Frame(card)
                reg['cenario']=tk.StringVar(value='Sem contexto')
                reg['alvo_contexto']=tk.StringVar(value='xv e yv')
                reg['eixo_contexto']=tk.StringVar(value=EIXOS[0])
                reg['incluir_imagem']=tk.BooleanVar(value=False)
                reg['_grupo_contexto']=tk.StringVar(value='Sem contexto')
                ttk.Label(contexto,text='Tipo de questão:').grid(row=0,column=0,sticky='w',pady=5)
                tipo_contexto=ttk.Combobox(contexto,textvariable=reg['_grupo_contexto'],values=('Sem contexto','Raízes','Vértice'),state='readonly',width=20)
                tipo_contexto.grid(row=0,column=1,sticky='w',padx=8)
                ttk.Label(contexto,text='Contexto:').grid(row=1,column=0,sticky='w',pady=5)
                cen=ttk.Combobox(contexto,textvariable=reg['cenario'],values=CENARIOS,state='readonly',width=35)
                cen.grid(row=1,column=1,sticky='w',padx=8)
                ttk.Label(contexto,text='Perguntar:').grid(row=2,column=0,sticky='w')
                alvo=ttk.Combobox(contexto,textvariable=reg['alvo_contexto'],values=ALVOS,state='readonly',width=20)
                alvo.grid(row=2,column=1,sticky='w',padx=8)
                eixo_label=ttk.Label(contexto,text='x representa:')
                eixo_label.grid(row=3,column=0,sticky='w',pady=5)
                eixo=ttk.Combobox(contexto,textvariable=reg['eixo_contexto'],values=EIXOS,state='readonly',width=22)
                eixo.grid(row=3,column=1,sticky='w',padx=8)
                img=ttk.Checkbutton(contexto,text='Incluir imagem (ilustrativa, sem escala)',variable=reg['incluir_imagem'])
                img.grid(row=4,column=0,columnspan=2,sticky='w',pady=5)
                ttk.Label(contexto,text='Expressões: até 4 questões por página, 2 por linha. As demais seguem em novas folhas; imagens ajustadas automaticamente.',wraplength=600).grid(row=5,column=0,columnspan=2,sticky='w')
                def atualizar_apresentacao(event=None,reg=reg,options=options,pedidos=pedidos,contexto=contexto,alvo=alvo,eixo=eixo,img=img,cen=cen,eixo_label=eixo_label):
                    tipo=grupo(reg['cenario'].get(),reg['alvo_contexto'].get())
                    reg['_grupo_contexto'].set(tipo)
                    cenarios=cenarios_grupo(tipo)
                    # Preserva enunciados de JSONs antigos, sem oferecê-los em novas questões.
                    if reg['cenario'].get() not in cenarios: cenarios=(*cenarios,reg['cenario'].get())
                    cen.configure(values=cenarios,state='disabled' if tipo=='Sem contexto' else 'readonly')
                    alvos=('Raízes',) if tipo=='Raízes' else ('xv','yv','xv e yv')
                    alvo.configure(values=alvos)
                    contextual=reg['cenario'].get()!='Sem contexto'
                    alvo.configure(state='readonly' if contextual else 'disabled')
                    eixo.configure(state='readonly' if reg['cenario'].get() in PROJETEIS else 'disabled')
                    if reg['cenario'].get() in PROJETEIS:
                        eixo.grid(); eixo_label.grid()
                    else:
                        eixo.grid_remove(); eixo_label.grid_remove()
                    img.configure(state='normal' if reg['cenario'].get() in IMAGENS else 'disabled')
                    if reg['apresentacao'].get()=='Expressão da função':
                        options.pack_forget(); contexto.pack(fill='x',pady=(10,0))
                        if contextual: pedidos.pack_forget()
                        else: pedidos.pack(fill='x',pady=(10,0))
                    else:
                        contexto.pack_forget(); pedidos.pack_forget(); options.pack(fill='x',pady=(10,0))
                reg['_atualizar_apresentacao']=atualizar_apresentacao
                def trocar_grupo(event=None,reg=reg,atualizar=atualizar_apresentacao):
                    tipo=reg['_grupo_contexto'].get()
                    reg['cenario'].set(cenarios_grupo(tipo)[0])
                    reg['alvo_contexto'].set('Raízes' if tipo=='Raízes' else 'xv e yv')
                    reg['incluir_imagem'].set(False)
                    atualizar()
                tipo_contexto.bind('<<ComboboxSelected>>',trocar_grupo)
                select.bind('<<ComboboxSelected>>',atualizar_apresentacao)
                cen.bind('<<ComboboxSelected>>',atualizar_apresentacao)
                self.apoio_quadratica(quadro,reg)
            else:
                n=tk.IntVar(value=3)
                ttk.Label(row,text='Pontos:').pack(side='left')
                spin=ttk.Spinbox(row,from_=0,to=8,textvariable=n,width=3,state='readonly'); spin.pack(side='left',padx=6)
                points=ttk.Frame(card); points.pack(fill='x',pady=(10,0))
                reg['xs']=[]
                def atualizar(reg=reg,n=n,points=points):
                    old=[v.get() for v in reg['xs']]
                    for child in points.winfo_children(): child.destroy()
                    reg['xs']=[]
                    for j in range(n.get()):
                        v=tk.StringVar(value=old[j] if j<len(old) else str(j+1)); reg['xs'].append(v)
                        ttk.Label(points,text=f'x{j+1}:').grid(row=j//4,column=j%4*2,padx=4,pady=4)
                        ttk.Entry(points,textvariable=v,width=9).grid(row=j//4,column=j%4*2+1,padx=(0,12),pady=4)
                reg['_quantidade_pontos']=n
                reg['_atualizar_pontos']=atualizar
                spin.configure(command=atualizar); atualizar()

    def apoio_quadratica(self,quadro,reg):
        from apoio_quadraticas import calcular
        from contextos_quadraticas import orientacao
        panel=ttk.LabelFrame(quadro,text='Apoio ao professor',padding=10)
        panel._largura_fixa=True
        resultado=tk.StringVar(); aviso=tk.StringVar(); dica=tk.StringVar()
        ttk.Label(panel,text='Somente no editor — não sai no PDF.',wraplength=265).pack(anchor='w',pady=(0,8))
        ttk.Label(panel,textvariable=resultado,wraplength=265,justify='left',font=('',11,'bold')).pack(anchor='w')
        ttk.Label(panel,text='Resultados numéricos (até 8 algarismos significativos).',wraplength=265).pack(anchor='w',pady=6)
        ttk.Label(panel,textvariable=aviso,wraplength=265,foreground='#9a3412',justify='left').pack(anchor='w',pady=6)
        ttk.Separator(panel).pack(fill='x',pady=8)
        ttk.Label(panel,textvariable=dica,wraplength=265,justify='left').pack(anchor='w')
        if getattr(self,'apoio_embaixo',False):
            for widget in panel.winfo_children():
                if isinstance(widget,ttk.Label): widget.configure(wraplength=550)
        pending=[None]
        def atualizar():
            pending[0]=None
            if not panel.winfo_exists(): return
            if reg['apresentacao'].get()!='Expressão da função':
                panel.pack_forget(); return
            if getattr(self,'apoio_embaixo',False): panel.pack(side='bottom',fill='x',pady=(12,0))
            else: panel.pack(side='right',fill='y',padx=(15,0),anchor='n')
            campos={k:v.get() for k,v in reg.items() if not k.startswith('_')}
            texto,alerta=calcular(campos)
            resultado.set(texto); aviso.set(alerta)
            dica.set(orientacao(campos['cenario']))
        def agendar(*args):
            if pending[0]: panel.after_cancel(pending[0])
            pending[0]=panel.after(180,atualizar)
        def destruir(event):
            if event.widget==panel and pending[0]:
                panel.after_cancel(pending[0]); pending[0]=None
        panel.bind('<Destroy>',destruir,add='+')
        for key in ('a','b','c','modo','quantidade_raizes','raiz1','raiz2','apresentacao','cenario','alvo_contexto','eixo_contexto'):
            reg[key].trace_add('write',agendar)
        atualizar()

    def restaurar(self,pagina):
        _,items,colunas,titulo=pagina
        self.limpar(confirmar=False)
        self.total.set(len(items)); self.colunas.set(colunas); self.titulo.set(titulo)
        self.criar()
        for reg,item in zip(self.registros,items):
            for key,value in asdict(item).items():
                if self.grau==2 and key in ('a_texto','b_texto','c_texto'):
                    if value: reg[key[0]].set(value)
                elif key=='xs':
                    reg['_quantidade_pontos'].set(len(value)); reg['_atualizar_pontos']()
                    for var,x in zip(reg['xs'],value): var.set(str(x))
                elif key=='valores':
                    for name,text in value.items():
                        if name in reg['valores']: reg['valores'][name].set(text)
                else: reg[key].set(value)
            if 'atualizar' in reg: reg['atualizar']()
            if '_atualizar_lado' in reg: reg['_atualizar_lado']()
            if '_atualizar_modo' in reg: reg['_atualizar_modo']()
            if '_atualizar_contexto' in reg: reg['_atualizar_contexto']()
            if '_atualizar_apresentacao' in reg: reg['_atualizar_apresentacao']()

    def pagina(self):
        funcoes=[]
        for i,r in enumerate(self.registros):
            try:
                from numeros_exatos import ler
                parse=(lambda text:ler(text)[1]) if self.grau==2 else numero
                a=parse(r['a'].get())
                b=0 if self.grau==2 and r['modo'].get()=='Raízes e a' else parse(r['b'].get())
                if self.grau==1:
                    f=Funcao(a,b,[numero(v.get()) for v in r['xs']]); f.validar()
                else:
                    c=0 if r['modo'].get()=='Raízes e a' else parse(r['c'].get())
                    f=Parabola(a,b,c,*[r[k].get() for k in ('raizes','intercepto','marcar_xv','marcar_yv')],
                               **{k+'_texto':r[k].get() for k in ('a','b','c')},
                               **{k:r[k].get() for k in ('modo','quantidade_raizes','raiz1','raiz2','apresentacao','pedir_raizes','pedir_vertice','cenario','alvo_contexto','eixo_contexto','incluir_imagem')}); f.dados()
                funcoes.append(f)
            except ValueError as e:
                raise ValueError(f'Aba {self.grau}º grau, gráfico {i+1}: {e}')
        return self.grau,funcoes,self.colunas.get(),self.titulo.get()


class AbaTriangulos(Aba):
    def __init__(self,notebook):
        super().__init__(notebook,1)
        self.grau=3
        notebook.tab(self.frame,text='Trigonometria')
        self.titulo.set('Trigonometria')

    def criar(self):
        if not self.limpar(): return
        for i in range(self.total.get()):
            outer=ttk.LabelFrame(self.corpo,text=f'Questão {i+1}',padding=10); outer.pack(fill='x',pady=6)
            card=ttk.Frame(outer); card.pack(fill='x')
            reg={k:tk.StringVar(value=v) for k,v in {'angulo':'30','razao':'Seno','conhecido':'Hipotenusa','valor':'2√3','posicao':POSICOES[0],'lado_x':'Hipotenusa','valor2':'4'}.items()}
            self.registros.append(reg)
            row=ttk.Frame(card); row.pack(fill='x')
            ttk.Label(row,text='Ângulo (graus):').pack(side='left')
            angle_entry=ttk.Entry(row,textvariable=reg['angulo'],width=6); angle_entry.pack(side='left',padx=6)
            ttk.Label(row,text='Questão de:').pack(side='left')
            razao=ttk.Combobox(row,textvariable=reg['razao'],values=[*LADOS,PITAGORAS],state='readonly',width=20); razao.pack(side='left',padx=6)
            lado_label=ttk.Label(row,text='Lado conhecido:'); lado_label.pack(side='left')
            lado=ttk.Combobox(row,textvariable=reg['conhecido'],values=LADOS['Seno'],state='readonly',width=18); lado.pack(side='left',padx=6)
            row2=ttk.Frame(card); row2.pack(fill='x',pady=8)
            medida_label=ttk.Label(row2,text='Medida:'); medida_label.pack(side='left')
            ttk.Entry(row2,textvariable=reg['valor'],width=16).pack(side='left',padx=6)
            ttk.Label(row2,text='Ex.: 5, 2√3, √3/3, 3/2, sqrt(2)').pack(side='left')
            row3=ttk.Frame(card)
            medida2_label=ttk.Label(row3,text='Segunda medida:'); medida2_label.pack(side='left')
            ttk.Entry(row3,textvariable=reg['valor2'],width=16).pack(side='left',padx=6)
            unknown=tk.StringVar()
            ttk.Label(card,textvariable=unknown).pack(anchor='w')
            def atualizar(event=None,reg=reg,lado=lado,unknown=unknown,angle_entry=angle_entry,lado_label=lado_label,medida_label=medida_label,medida2_label=medida2_label,row3=row3,row2=row2):
                if reg['razao'].get()==PITAGORAS:
                    angle_entry.configure(state='disabled')
                    lado_label.configure(text='Calcular (x):')
                    lado.configure(values=LADOS_PIT,textvariable=reg['lado_x'])
                    nomes=[k for k in LADOS_PIT if k!=reg['lado_x'].get()]
                    medida_label.configure(text=nomes[0]+':'); medida2_label.configure(text=nomes[1]+':')
                    row3.pack(fill='x',after=row2,pady=4)
                    unknown.set('Informe os dois lados conhecidos. O ângulo será calculado apenas para desenhar.')
                    if '_redesenhar' in reg: reg['_redesenhar']()
                    return
                angle_entry.configure(state='normal'); row3.pack_forget()
                lado_label.configure(text='Lado conhecido:'); medida_label.configure(text='Medida:')
                lado.configure(textvariable=reg['conhecido'])
                options=LADOS[reg['razao'].get()]; lado.configure(values=options)
                if reg['conhecido'].get() not in options: reg['conhecido'].set(options[0])
                unknown.set('Lado a calcular (x): '+next(v for v in options if v!=reg['conhecido'].get()))
                if '_redesenhar' in reg: reg['_redesenhar']()
            reg['_atualizar_lado']=atualizar
            razao.bind('<<ComboboxSelected>>',atualizar); lado.bind('<<ComboboxSelected>>',atualizar); atualizar()
            positions=ttk.Frame(card); positions.pack(fill='x',pady=(8,0))
            miniaturas=[]
            for j,nome in enumerate(POSICOES):
                cell=ttk.Frame(positions); cell.grid(row=0,column=j,padx=3)
                mini=tk.Canvas(cell,width=112,height=62,highlightthickness=0)
                mini.pack()
                miniaturas.append((mini,nome))
                mini.bind('<Button-1>',lambda e,v=reg['posicao'],nome=nome:v.set(nome))
                texto=nome.replace('Virado para ', 'Virado para\n').replace('De cabeça para baixo para ', 'De cabeça para baixo\npara ').replace('Hipotenusa apontada para ', 'Hipotenusa\napontada para ')
                ttk.Radiobutton(cell,text=texto,value=nome,variable=reg['posicao']).pack()
            def redesenhar(*args,reg=reg,miniaturas=miniaturas):
                try:
                    angulo=(Triangulo(45,reg['posicao'].get(),PITAGORAS,'',reg['valor'].get(),reg['lado_x'].get(),reg['valor2'].get()).angulo_desenho()
                            if reg['razao'].get()==PITAGORAS else numero(reg['angulo'].get()))
                    if not 0<angulo<90: return
                except ValueError: return
                for mini,nome in miniaturas:
                    pts=vertices(nome,angulo)
                    minx,maxx=min(x for x,y in pts),max(x for x,y in pts)
                    miny,maxy=min(y for x,y in pts),max(y for x,y in pts)
                    escala=min(80/(maxx-minx),42/(maxy-miny))
                    coords=[(56+(x-(minx+maxx)/2)*escala,31-(y-(miny+maxy)/2)*escala) for x,y in pts]
                    mini.delete('all')
                    mini.create_polygon(*[v for p in coords for v in p],fill='',outline='#2563eb',width=2)
                    if reg['razao'].get()!=PITAGORAS:
                        mini.create_text(coords[1][0],coords[1][1],text='θ',anchor='sw')
            reg['_redesenhar']=redesenhar
            reg['angulo'].trace_add('write',redesenhar)
            for key in ('valor','valor2','lado_x'): reg[key].trace_add('write',redesenhar)
            redesenhar()
            self.editor_contextual(outer,card,reg)

    def editor_contextual(self,outer,simples,r):
        from contextos import CENARIOS, EXTRAS, opcoes, enunciado, preview
        defaults={'apresentacao':'Triângulo simples','cenario':'Avião decolando',
                  'dado_contexto':CENARIOS['Avião decolando'][1][2],
                  'pedido_contexto':CENARIOS['Avião decolando'][1][1],'altura_extra':'1,6'}
        for k,v in defaults.items(): r[k]=tk.StringVar(value=v)
        mode=ttk.Frame(outer); mode.pack(fill='x',before=simples,pady=(0,8))
        ttk.Label(mode,text='Apresentação:').pack(side='left')
        seletor=ttk.Combobox(mode,textvariable=r['apresentacao'],values=('Triângulo simples','Contextual'),state='readonly',width=22)
        seletor.pack(side='left',padx=8)
        frame=ttk.Frame(outer)
        def campo(label,key,values=None):
            row=ttk.Frame(frame); row.pack(fill='x',pady=3)
            ttk.Label(row,text=label,width=23).pack(side='left')
            w=(ttk.Combobox(row,textvariable=r[key],values=values,state='readonly',width=65) if values is not None
               else ttk.Entry(row,textvariable=r[key],width=16))
            w.pack(side='left'); return row,w
        _,scenario=campo('Cenário:','cenario',list(CENARIOS))
        campo('Ângulo (graus):','angulo')
        _,known=campo('Medida conhecida:','dado_contexto',())
        campo('Valor conhecido (m):','valor')
        _,asked=campo('Calcular:','pedido_contexto',())
        extra,extra_entry=campo('Altura adicional (m):','altura_extra')
        ttk.Label(frame,text='Aceita raízes e frações. Com questões contextuais: até 2 por linha e 6 por página.',wraplength=700).pack(anchor='w',pady=6)
        drawing=tk.Canvas(frame,width=440,height=280,background='white',highlightthickness=0); drawing.pack(anchor='w')
        text=tk.StringVar(); ttk.Label(frame,textvariable=text,wraplength=740).pack(fill='x',pady=6)
        def atualizar(event=None):
            contextual=r['apresentacao'].get()=='Contextual'
            if not contextual:
                frame.pack_forget(); simples.pack(fill='x'); return
            simples.pack_forget(); frame.pack(fill='x')
            name=r['cenario'].get(); opts=opcoes(name)
            known.configure(values=opts)
            if r['dado_contexto'].get() not in opts: r['dado_contexto'].set(opts[0])
            remaining=[v for v in opts if v!=r['dado_contexto'].get()]
            asked.configure(values=remaining)
            if r['pedido_contexto'].get() not in remaining: r['pedido_contexto'].set(remaining[0])
            if name in EXTRAS:
                extra.winfo_children()[0].configure(text=EXTRAS[name]+' (m):'); extra.pack(fill='x',before=drawing,pady=3)
            else: extra.pack_forget()
            try:
                model=self.modelo(r)
                text.set(enunciado(model))
                preview(drawing,name,model)
            except ValueError as e:
                text.set(str(e)); preview(drawing,name)
        r['_atualizar_contexto']=atualizar
        for widget in (seletor,scenario,known,asked): widget.bind('<<ComboboxSelected>>',atualizar)
        for key in ('angulo','valor','altura_extra'): r[key].trace_add('write',lambda *args:atualizar())
        atualizar()

    @staticmethod
    def modelo(r):
        angle=45 if r['razao'].get()==PITAGORAS and r['apresentacao'].get()!='Contextual' else numero(r['angulo'].get())
        return Triangulo(angle,**{key:r[key].get() for key in ('posicao','razao','conhecido','valor','lado_x','valor2',
                         'apresentacao','cenario','dado_contexto','pedido_contexto','altura_extra')})

    def pagina(self):
        items=[]
        for i,r in enumerate(self.registros):
            try:
                t=self.modelo(r)
                t.validar(); items.append(t)
            except ValueError as e: raise ValueError(f'Triângulo {i+1}: {e}')
        return 3,items,self.colunas.get(),self.titulo.get()


class AbaSolidos(Aba):
    def __init__(self,notebook):
        super().__init__(notebook,1)
        self.grau=4
        self.quantidade.configure(to=12)
        notebook.tab(self.frame,text='Geometria espacial')
        self.titulo.set('Geometria espacial')

    def criar(self):
        if not self.limpar(): return
        for i in range(self.total.get()):
            card=ttk.LabelFrame(self.corpo,text=f'Sólido {i+1}',padding=10); card.pack(fill='x',pady=6)
            r={'tipo':tk.StringVar(value='Cubo'),'circular':tk.StringVar(value='Raio'),'cone':tk.StringVar(value='Altura'),
               'valores':{k:tk.StringVar(value=v) for k,v in {'a':'6','b':'8','h':'12','r':'5','d':'10','g':'13'}.items()}}
            self.registros.append(r)
            row=ttk.Frame(card); row.pack(fill='x')
            ttk.Label(row,text='Sólido:').pack(side='left')
            seletor=ttk.Combobox(row,textvariable=r['tipo'],values=TIPOS,state='readonly',width=30); seletor.pack(side='left',padx=8)
            body=ttk.Frame(card); body.pack(fill='x',pady=8)
            preview=tk.Canvas(body,width=190,height=175,background='white',highlightthickness=1,highlightbackground='#cbd5e1'); preview.pack(side='left',padx=(0,18))
            editor=ttk.Frame(body); editor.pack(side='left',fill='x',expand=True)
            def atualizar(event=None,r=r,preview=preview,editor=editor):
                for child in editor.winfo_children(): child.destroy()
                tipo=r['tipo'].get()
                if tipo in ('Cilindro','Cone','Esfera'):
                    row=ttk.Frame(editor); row.pack(anchor='w',pady=3)
                    ttk.Label(row,text='Fornecer:').pack(side='left')
                    for name in ('Raio','Diâmetro'):
                        ttk.Radiobutton(row,text=name,value=name,variable=r['circular'],command=r['atualizar']).pack(side='left',padx=6)
                if tipo=='Cone':
                    row=ttk.Frame(editor); row.pack(anchor='w',pady=3)
                    for name in ('Altura','Geratriz'):
                        ttk.Radiobutton(row,text=name,value=name,variable=r['cone'],command=r['atualizar']).pack(side='left',padx=6)
                for key,label in campos(tipo,r['circular'].get(),r['cone'].get()):
                    row=ttk.Frame(editor); row.pack(anchor='w',pady=3)
                    ttk.Label(row,text=f'{label} ({key}), cm:',width=24).pack(side='left')
                    ttk.Entry(row,textvariable=r['valores'][key],width=14).pack(side='left')
                notes={'Prisma triangular':'Base: triângulo equilátero. Prisma reto.', 'Prisma hexagonal':'Base: hexágono regular. Prisma reto.',
                       'Pirâmide de base quadrada':'Pirâmide reta: altura perpendicular ao centro da base.', 'Tetraedro':'Tetraedro regular: todas as arestas iguais.'}
                ttk.Label(editor,text=notes.get(tipo,'')+'\nAceita 5, 2√3, √3/3 ou 3/2.',wraplength=480).pack(anchor='w',pady=5)
                preview.delete('all')
                lines,labels=desenho(tipo,r['circular'].get(),r['cone'].get())
                for points,dash in lines:
                    preview.create_line(*[v for x,y in points for v in (15+x*155,160-y*155)],fill='#2563eb',width=1.5,dash=(3,3) if dash else ())
                for x,y,label in labels: preview.create_text(15+x*155,160-y*155,text=label,fill='#172b4d')
            r['atualizar']=atualizar
            seletor.bind('<<ComboboxSelected>>',atualizar); atualizar()

    def pagina(self):
        items=[]
        for i,r in enumerate(self.registros):
            try:
                s=Solido(r['tipo'].get(),{k:v.get() for k,v in r['valores'].items()},r['circular'].get(),r['cone'].get())
                s.validar(); items.append(s)
            except ValueError as e: raise ValueError(f'Sólido {i+1}: {e}')
        return 4,items,self.colunas.get(),self.titulo.get()


class AbaExponenciais(Aba):
    def __init__(self,notebook):
        super().__init__(notebook,1)
        self.quantidade.configure(to=8)
        self.seletor_colunas.configure(values=(1,2))
        notebook.tab(self.frame,text='Exponenciais')
        self.titulo.set('Funções exponenciais')

    def criar(self):
        antigos=list(self.registros)
        super().criar()
        if self.registros and antigos and self.registros[0] is antigos[0]: return
        for reg,card in zip(self.registros,self.corpo.winfo_children()):
            reg['a'].set('2'); reg['b'].set('1')
            reg['tipo']=tk.StringVar(value=TIPOS_EXP[0])
            row=ttk.Frame(card)
            row.pack(fill='x',before=card.winfo_children()[0],pady=(0,8))
            ttk.Label(row,text='Formato:').pack(side='left')
            ttk.Combobox(row,values=TIPOS_EXP,textvariable=reg['tipo'],state='readonly',width=15).pack(side='left',padx=8)
            ttk.Label(row,text='a e b: 2, 1/2, √2, -√3/3 (a > 0 e a ≠ 1)').pack(side='left')

    def pagina(self):
        items=[]
        for i,r in enumerate(self.registros):
            try:
                f=Exponencial(r['tipo'].get(),r['a'].get(),r['b'].get(),[coeficiente(v.get()) for v in r['xs']])
                f.validar(); items.append(f)
            except ValueError as e: raise ValueError(f'Exponencial {i+1}: {e}')
        return 5,items,self.colunas.get(),self.titulo.get()


class AbaProgressao(Aba):
    def __init__(self,notebook):
        super().__init__(notebook,1)
        self.grau=6
        self.quantidade.configure(to=12)
        self.seletor_colunas.configure(values=(1,2))
        notebook.tab(self.frame,text='Progressão aritmética')
        self.titulo.set('Progressão aritmética')

    def criar(self):
        if not self.limpar(): return
        for i in range(self.total.get()):
            card=ttk.LabelFrame(self.corpo,text=f'Questão {i+1}',padding=12)
            card.pack(fill='x',pady=6)
            r={'tipo':tk.StringVar(value=TIPOS_PA[0]),'incognita':tk.StringVar(value='aj'),
               'indicados':tk.StringVar(value='a1,an,n'),
               **{k:tk.StringVar(value=v) for k,v in {
                   'apresentacao':'Sem contexto','cenario':'Treinamento de corrida ou natação',
                   'periodo':'dia','unidade':'metros','atividade':'corrida'}.items()},
               'valores':{k:tk.StringVar(value=v) for k,v in PADRAO_PA.items()}}
            self.registros.append(r)
            self.editor(card,r)

    def editor(self,card,r):
        from contextos_pa import CENARIOS, grandeza
        quadro=card
        card=ttk.Frame(quadro)
        card.pack(side='top' if getattr(self,'apoio_embaixo',False) else 'left',fill='both',expand=True)
        apoio=ttk.LabelFrame(quadro,text='Apoio ao professor — somente no editor',padding=10)
        apoio._largura_fixa=True
        resultado=tk.StringVar(); aviso=tk.StringVar(); dica=tk.StringVar()
        for var in (resultado,aviso,dica):
            ttk.Label(apoio,textvariable=var,wraplength=550 if getattr(self,'apoio_embaixo',False) else 270,justify='left').pack(anchor='w',pady=5)
        row=ttk.Frame(card); row.pack(fill='x',pady=4)
        ttk.Label(row,text='Tipo:').pack(side='left')
        tipo=ttk.Combobox(row,textvariable=r['tipo'],values=TIPOS_PA,state='readonly',width=20)
        tipo.pack(side='left',padx=8)
        ttk.Label(row,text='Descobrir:').pack(side='left')
        alvo_text=tk.StringVar()
        alvo=ttk.Combobox(row,textvariable=alvo_text,state='readonly',width=30)
        alvo.pack(side='left',padx=8)
        mode_row=ttk.Frame(card); mode_row.pack(fill='x',pady=4)
        ttk.Label(mode_row,text='Apresentação:').pack(side='left')
        mode=ttk.Combobox(mode_row,textvariable=r['apresentacao'],values=('Sem contexto','Contextual'),state='readonly',width=20)
        mode.pack(side='left',padx=8)
        ttk.Label(mode_row,text='Contextos disponíveis para termo geral e soma dos termos.').pack(side='left')
        context=ttk.Frame(card)
        ttk.Label(context,text='Cenário:').grid(row=0,column=0,sticky='w')
        scenario=ttk.Combobox(context,textvariable=r['cenario'],values=list(CENARIOS),state='readonly',width=40)
        scenario.grid(row=0,column=1,columnspan=3,sticky='w',padx=8,pady=4)
        ttk.Label(context,text='Período:').grid(row=1,column=0,sticky='w')
        period=ttk.Combobox(context,textvariable=r['periodo'],state='readonly',width=12)
        period.grid(row=1,column=1,sticky='w',padx=8)
        ttk.Label(context,text='Unidade:').grid(row=1,column=2)
        unit=ttk.Combobox(context,textvariable=r['unidade'],state='readonly',width=14)
        unit.grid(row=1,column=3,padx=8)
        activity_label=ttk.Label(context,text='Atividade:')
        activity=ttk.Combobox(context,textvariable=r['atividade'],values=('corrida','natação'),state='readonly',width=14)
        fields=ttk.Frame(card); fields.pack(fill='x',pady=8)
        status=tk.StringVar()
        ttk.Label(card,textvariable=status,wraplength=730).pack(fill='x',pady=8)
        ttk.Label(card,text='Aceita inteiros, negativos, decimais e frações (ex.: -3, 2,5, 1/2). Posições começam em 1.',wraplength=730).pack(anchor='w')

        def modelo():
            return Progressao(r['tipo'].get(),r['incognita'].get(),
                              {k:v.get() for k,v in r['valores'].items()},r['indicados'].get(),
                              **{k:r[k].get() for k in ('apresentacao','cenario','periodo','unidade','atividade')})
        def previa(*args):
            if r['apresentacao'].get()=='Contextual':
                if getattr(self,'apoio_embaixo',False): apoio.pack(side='bottom',fill='x',pady=(12,0))
                else: apoio.pack(side='right',fill='y',padx=(15,0),anchor='n')
                from apoio_pa import calcular
                texto,alerta,orientacao=calcular(modelo())
                resultado.set(texto); aviso.set(alerta); dica.set(orientacao)
            else: apoio.pack_forget()
            try:
                import re
                text=modelo().enunciado()
                text=re.sub(r'<sub>(.*?)</sub>',r'[\1]',text)
                status.set('Prévia: '+text)
            except ValueError as e: status.set('Ajuste necessário: '+str(e))
        def atualizar(event=None):
            for child in fields.winfo_children(): child.destroy()
            geral=r['tipo'].get()==TIPOS_PA[0]
            mode.configure(state='readonly')
            contextual=r['apresentacao'].get()=='Contextual'
            if contextual:
                context.pack(fill='x',before=fields,pady=6)
                c=CENARIOS[r['cenario'].get()]
                for key,widget,options in (('periodo',period,c['periodos']),('unidade',unit,c['unidades'])):
                    widget.configure(values=options)
                    if r[key].get() not in options: r[key].set(options[0])
                if r['cenario'].get()=='Treinamento de corrida ou natação':
                    activity_label.grid(row=2,column=0,sticky='w',pady=4)
                    activity.grid(row=2,column=1,sticky='w',padx=8)
                else: activity_label.grid_remove(); activity.grid_remove()
            else: context.pack_forget()
            options=ALVOS_PA[r['tipo'].get()]
            target=r['incognita'].get()
            if target not in options:
                target=next(iter(options)); r['incognita'].set(target)
            alvo.configure(values=list(options.values())); alvo_text.set(options[target])
            if r['tipo'].get()==TIPOS_PA[0]:
                names={'i':'Posição do termo de referência (i)', 'ai':'Valor do termo de referência (aᵢ)',
                       'j':'Posição do termo procurado (j)' if target=='aj' else 'Posição do segundo termo (j)',
                       'aj':'Número cuja posição será descoberta' if target=='j' else 'Valor do segundo termo (aⱼ)',
                       'r':'Razão (r)'}
                if contextual:
                    measure=grandeza(modelo()).capitalize(); p=r['periodo'].get(); u=r['unidade'].get()
                    names={'i':f'Número de referência ({p})', 'ai':f'{measure} de referência ({u})',
                           'j':f'Número do outro período ({p})', 'aj':f'{measure} no outro período ({u})',
                           'r':f'Variação por {p} ({u}): + aumenta / − diminui'}
                keys=['i','ai']+[k for k in ('j','aj','r') if k!=target]
                for j,key in enumerate(keys):
                    ttk.Label(fields,text=names[key]).grid(row=j,column=0,sticky='w',padx=4,pady=3)
                    ttk.Entry(fields,textvariable=r['valores'][key],width=18).grid(row=j,column=1,padx=8)
            else:
                ttk.Label(fields,text='Marque os dados a indicar no enunciado:').grid(row=0,column=0,columnspan=2,sticky='w')
                selected=set(r['indicados'].get().split(','))
                flags={key:tk.BooleanVar(value=key in selected and key!=target) for key in DADOS_SOMA}
                labels=dict(DADOS_SOMA)
                if contextual:
                    p=r['periodo'].get(); u=r['unidade'].get()
                    labels={'a1':f'Medida inicial ({u})', 'an':f'Medida final ({u})',
                            'n':f'Quantidade de períodos ({p})', 'sn':f'Total acumulado ({u})',
                            'r':f'Variação por {p} ({u}): + aumenta / − diminui'}
                def selecionar():
                    r['indicados'].set(','.join(k for k,v in flags.items() if v.get()))
                    atualizar()
                for j,key in enumerate(DADOS_SOMA,1):
                    check=ttk.Checkbutton(fields,text=labels[key],variable=flags[key],command=selecionar)
                    check.grid(row=j,column=0,sticky='w',padx=4,pady=3)
                    entry=ttk.Entry(fields,textvariable=r['valores'][key],width=18)
                    entry.grid(row=j,column=1,padx=8)
                    if key==target: check.configure(state='disabled')
                    entry.configure(state='normal' if flags[key].get() and key!=target else 'disabled')
                ttk.Label(fields,text='A incógnita fica oculta. Marque dados suficientes para uma resposta única; a razão também pode ser fornecida.',wraplength=700).grid(row=6,column=0,columnspan=2,sticky='w',pady=6)
            previa()
        def trocar_tipo(event=None):
            r['incognita'].set('aj' if r['tipo'].get()==TIPOS_PA[0] else 'sn')
            r['indicados'].set('a1,an,n'); atualizar()
        def trocar_alvo(event=None):
            options=ALVOS_PA[r['tipo'].get()]
            target=next(k for k,v in options.items() if v==alvo_text.get())
            r['incognita'].set(target)
            if r['tipo'].get()==TIPOS_PA[1]:
                r['indicados'].set('a1,n,sn' if target=='r' else ','.join(k for k in ('a1','an','n','sn') if k!=target))
            atualizar()
        tipo.bind('<<ComboboxSelected>>',trocar_tipo); alvo.bind('<<ComboboxSelected>>',trocar_alvo)
        for widget in (mode,scenario,period,unit,activity): widget.bind('<<ComboboxSelected>>',atualizar)
        for var in r['valores'].values(): var.trace_add('write',previa)
        r['atualizar']=atualizar
        atualizar()

    def pagina(self):
        items=[]
        for i,r in enumerate(self.registros):
            try:
                item=Progressao(r['tipo'].get(),r['incognita'].get(),
                                {k:v.get() for k,v in r['valores'].items()},r['indicados'].get(),
                                **{k:r[k].get() for k in ('apresentacao','cenario','periodo','unidade','atividade')})
                item.validar(); items.append(item)
            except ValueError as e: raise ValueError(f'PA, questão {i+1}: {e}')
        return 6,items,self.colunas.get(),self.titulo.get()


def iniciar():
    root=tk.Tk(); root.title('Criador de gráficos — retas, parábolas e triângulos'); root.geometry('900x780')
    maximizar(root)
    style=ttk.Style(root); style.theme_use('clam'); style.configure('TButton',padding=8)
    ttk.Label(root,text='Criador de gráficos',font=('',20,'bold'),padding=14).pack(anchor='w')
    from editor_listas import EditorLista
    ttk.Button(root,text='Criar Lista',command=lambda:EditorLista(root)).pack(anchor='w',padx=14,pady=(0,8))
    notebook=ttk.Notebook(root); notebook.pack(fill='both',expand=True,padx=12)
    from interface_estatistica import AbaEstatistica
    abas=[Aba(notebook,1),Aba(notebook,2),AbaTriangulos(notebook),AbaSolidos(notebook),AbaExponenciais(notebook),AbaProgressao(notebook),AbaEstatistica(notebook)]
    status=tk.StringVar(value='Crie as questões na aba desejada. Questões contextuais são distribuídas em páginas A4 adicionais.')
    ttk.Label(root,textvariable=status,padding=12,wraplength=850).pack(anchor='w')
    buttons=ttk.Frame(root,padding=12); buttons.pack(fill='x')
    def exportar(prever=False):
        try:
            preenchidas=[aba for aba in abas if aba.registros]
            if not preenchidas: raise ValueError('Clique em Criar documento em uma das abas primeiro.')
            selecionadas=preenchidas
            if len(preenchidas)>1:
                resposta=messagebox.askyesnocancel('Incluir todas as páginas?', f'{len(preenchidas)} abas têm conteúdo. Deseja incluir todas as páginas no PDF?\n\nSim: todas as abas preenchidas.\nNão: somente a aba atual.\nCancelar: voltar à edição.')
                if resposta is None: return
                if not resposta: selecionadas=[abas[notebook.index(notebook.select())]]
            if any(not aba.registros for aba in selecionadas):
                raise ValueError('A aba atual está vazia. Crie seu documento ou escolha incluir todas as páginas.')
            paginas=[aba.pagina() for aba in selecionadas]
            if prever:
                fd,destino=tempfile.mkstemp(prefix='graficos_',suffix='.pdf'); os.close(fd)
            else:
                destino=filedialog.asksaveasfilename(defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile='graficos.pdf')
                if not destino: return
            json_path=Path(destino).with_suffix('.json')
            if not prever and json_path.exists() and not messagebox.askyesno('Substituir JSON?',f'O arquivo {json_path.name} já existe. Substituir o PDF e o JSON?'):
                return
            from progresso import gerar_com_progresso
            gerar_com_progresso(root,lambda:salvar_documento(destino,paginas))
            status.set(f'PDF e JSON salvos: {destino}')
            if prever: webbrowser.open(Path(destino).as_uri())
            else: messagebox.showinfo('Arquivos prontos',f'PDF:\n{destino}\n\nDados para reabrir:\n{json_path}')
        except Exception as e:
            messagebox.showerror('Não foi possível gerar',str(e))
    def carregar():
        caminho=filedialog.askopenfilename(title='Carregar documento JSON',filetypes=[('Documento JSON','*.json')])
        if not caminho: return
        try:
            paginas=carregar_documento(caminho)
            # A validação completa ocorre antes de alterar qualquer aba.
            if any(aba.registros for aba in abas) and not messagebox.askyesno('Carregar documento','Substituir o conteúdo atual das abas pelo documento salvo?'):
                return
            for aba in abas: aba.limpar(confirmar=False)
            for pagina in paginas: abas[pagina[0]-1].restaurar(pagina)
            notebook.select(abas[paginas[0][0]-1].frame)
            status.set(f'Documento carregado: {caminho}. As abas podem ser editadas e exportadas novamente.')
        except (ValueError,OSError,OverflowError) as e:
            messagebox.showerror('Não foi possível carregar',str(e))
    ttk.Button(buttons,text='Carregar JSON',command=carregar).pack(side='left',padx=(0,10))
    ttk.Button(buttons,text='Visualizar PDF',command=lambda:exportar(True)).pack(side='left')
    ttk.Button(buttons,text='Salvar PDF',command=exportar).pack(side='right')
    root.mainloop()
