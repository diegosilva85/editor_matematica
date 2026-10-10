"""Gerador de atividades: python app_graficos.py (ou --exemplo)."""
import math
import os
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Funcao:
    a: float
    b: float
    xs: list

    def validar(self):
        if not all(math.isfinite(v) for v in [self.a, self.b, *self.xs]):
            raise ValueError('Use somente números finitos.')
        if self.a == 0:
            raise ValueError('O coeficiente a deve ser diferente de zero (primeiro grau).')
        if any(not math.isfinite(self.a*x+self.b) for x in self.xs):
            raise ValueError('Os valores informados produzem coordenadas muito grandes.')


def numero(texto):
    try:
        valor = float(texto.strip().replace(',', '.'))
    except ValueError:
        raise ValueError('Preencha todos os campos com números; use vírgula ou ponto decimal.')
    if not math.isfinite(valor):
        raise ValueError('Use somente números finitos.')
    return valor


def fmt(v):
    if v == 0:
        return '0'
    return f'{v:.4g}'.replace('.', ',')


def gerar_pdf(destino, funcoes, colunas=2, titulo='Funções de primeiro grau', canvas_existente=None, quadro=None):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white
    if not funcoes or not 1 <= colunas <= 3:
        raise ValueError('Informe funções e escolha de 1 a 3 gráficos por linha.')
    for f in funcoes:
        f.validar()
    largura, altura = A4
    margem, intervalo = 30, 12
    linhas = math.ceil(len(funcoes)/colunas)
    if len(funcoes) > 15:
        raise ValueError('Uma página comporta no máximo 15 gráficos.')
    intervalo = min(intervalo, 40 / linhas)
    cw = (largura-2*margem-(colunas-1)*intervalo)/colunas
    ch = min(230, (altura-110-(linhas-1)*intervalo)/linhas)
    if quadro: cw,ch=quadro[2:4]
    destino = Path(destino)
    # Arquivo temporário evita deixar um PDF incompleto em caso de erro.
    fd, temporario = tempfile.mkstemp(suffix='.pdf', dir=destino.parent)
    os.close(fd)
    try:
        c = canvas_existente or canvas.Canvas(temporario, pagesize=A4)
        c.setTitle(titulo or 'Gráficos de funções')
        c.setFont('Helvetica-Bold', 16)
        cabecalho = titulo or 'Gráficos de funções'
        while c.stringWidth(cabecalho, 'Helvetica-Bold', 16) > largura-60:
            cabecalho = cabecalho[:-2]
        c.drawCentredString(largura/2, altura-40, cabecalho)
        c.setFont('Helvetica', 9)
        c.drawString(margem, altura-60, 'Determine a expressão da função representada em cada gráfico.')
        for i, f in enumerate(funcoes):
            left = margem+(i % colunas)*(cw+intervalo)
            bottom = altura-80-(i//colunas+1)*ch-(i//colunas)*intervalo
            if quadro: left,bottom=quadro[:2]
            c.setStrokeColor(HexColor('#cbd5e1'))
            c.setLineWidth(.6)
            c.roundRect(left, bottom, cw, ch, 6)
            c.setFillColor(HexColor('#172b4d'))
            c.setFont('Helvetica-Bold', 10)
            c.drawString(left+10, bottom+ch-18, f'({chr(97+i)})')
            # Reduz margens internas em páginas com muitas linhas.
            fator = min(1, ch / 130)
            px, py = left+37, bottom+29*fator
            pw, ph = cw-54, ch-59*fator
            xs = sorted(set(f.xs))
            base = xs or [0, 1, 2, 3]
            xmin, xmax = min(0, *base), max(0, *base)
            if xmin == xmax:
                xmin, xmax = -1, 1
            dx = xmax-xmin
            xmin, xmax = xmin-.15*dx, xmax+.18*dx
            ys = [f.b, *[f.a*x+f.b for x in base]]
            ymin, ymax = min(0, *ys), max(0, *ys)
            dy = ymax-ymin or 2
            ymin, ymax = ymin-.15*dy, ymax+.18*dy
            if not all(math.isfinite(v) for v in [xmin,xmax,ymin,ymax,xmax-xmin,ymax-ymin]):
                raise ValueError('Use valores de menor magnitude para o gráfico.')
            X = lambda x: px+(x-xmin)/(xmax-xmin)*pw
            Y = lambda y: py+(y-ymin)/(ymax-ymin)*ph
            c.saveState()
            clip = c.beginPath(); clip.rect(px,py,pw,ph)
            c.clipPath(clip, stroke=0)
            c.setStrokeColor(HexColor('#94a3b8')); c.setDash(2,3)
            for x in xs:
                y=f.a*x+f.b
                c.line(X(x),Y(0),X(x),Y(y)); c.line(X(0),Y(y),X(x),Y(y))
            c.setDash()
            c.setStrokeColor(HexColor('#2563eb')); c.setLineWidth(1.5)
            # Interseção com o retângulo, sem coordenadas gigantes fora da página.
            xa, xb = sorted(((ymin-f.b)/f.a, (ymax-f.b)/f.a))
            lo, hi = max(xmin,xa), min(xmax,xb)
            if lo <= hi:
                c.line(X(lo),Y(f.a*lo+f.b),X(hi),Y(f.a*hi+f.b))
            c.restoreState()
            c.setStrokeColor(HexColor('#172b4d')); c.setLineWidth(.8)
            c.line(px,Y(0),px+pw,Y(0)); c.line(X(0),py,X(0),py+ph)
            c.line(px+pw,Y(0),px+pw-4,Y(0)+2)
            c.line(px+pw,Y(0),px+pw-4,Y(0)-2)
            c.line(X(0),py+ph,X(0)-2,py+ph-4)
            c.line(X(0),py+ph,X(0)+2,py+ph-4)
            c.setFillColor(HexColor('#172b4d')); c.setFont('Helvetica',8)
            c.drawString(px+pw+3,Y(0)-3,'x'); c.drawString(X(0)+4,py+ph+2,'y')
            if 0 in xs:
                c.drawString(X(0)+4,Y(0)-11,'0')
            # As escalas são independentes; os quadros têm dimensões idênticas.
            for x in xs:
                if x != 0:
                    c.line(X(x),Y(0)-2,X(x),Y(0)+2)
                    c.drawCentredString(X(x),Y(0)-11,fmt(x))
            for y in sorted(set(f.a*x+f.b for x in xs)):
                if y != 0:
                    c.line(X(0)-2,Y(y),X(0)+2,Y(y))
                    c.drawRightString(X(0)-4,Y(y)-3,fmt(y))
            c.setFillColor(HexColor('#dc2626'))
            for x in xs:
                c.circle(X(x),Y(f.a*x+f.b),2.3,stroke=0,fill=1)
        if canvas_existente is None:
            c.save()
            from documentos import publicar_par
            publicar_par(temporario,destino,[(1,funcoes,colunas,titulo)])
    finally:
        if os.path.exists(temporario):
            os.unlink(temporario)
    return destino


def iniciar():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    root = tk.Tk()
    root.title('Gráficos de primeiro grau — versão 1')
    root.geometry('850x760')
    style = ttk.Style(root); style.theme_use('clam')
    style.configure('TButton',padding=8)
    topo = ttk.Frame(root,padding=18); topo.pack(fill='x')
    ttk.Label(topo,text='Criador de gráficos',font=('',20,'bold')).pack(anchor='w')
    ttk.Label(topo,text='PDF A4 de uma página • quadros iguais • fórmulas ocultas').pack(anchor='w',pady=(4,12))
    config = ttk.Frame(topo); config.pack(fill='x')
    total = tk.IntVar(value=4); cols = tk.IntVar(value=2)
    ttk.Label(config,text='Quantidade de gráficos:').pack(side='left')
    ttk.Spinbox(config,from_=1,to=15,textvariable=total,width=4,state='readonly').pack(side='left',padx=8)
    ttk.Label(config,text='Por linha:').pack(side='left')
    ttk.Combobox(config,textvariable=cols,values=(1,2,3),state='readonly',width=3).pack(side='left',padx=8)
    titulo = tk.StringVar(value='Funções de primeiro grau')
    ttk.Label(topo,text='Título do documento:').pack(anchor='w',pady=(10,2))
    ttk.Entry(topo,textvariable=titulo).pack(fill='x')
    area = ttk.Frame(root); area.pack(fill='both',expand=True,padx=18)
    scroll = tk.Canvas(area,highlightthickness=0)
    barra = ttk.Scrollbar(area,orient='vertical',command=scroll.yview)
    scroll.configure(yscrollcommand=barra.set)
    barra.pack(side='right',fill='y'); scroll.pack(side='left',fill='both',expand=True)
    corpo = ttk.Frame(scroll); janela = scroll.create_window((0,0),window=corpo,anchor='nw')
    corpo.bind('<Configure>',lambda e:scroll.configure(scrollregion=scroll.bbox('all')))
    scroll.bind('<Configure>',lambda e:scroll.itemconfigure(janela,width=e.width))
    registros=[]
    status=tk.StringVar(value='Escolha a quantidade e clique em Criar documento.')
    rodape=ttk.Frame(root,padding=18); rodape.pack(fill='x')
    ttk.Label(rodape,textvariable=status,wraplength=780).pack(anchor='w')
    botoes=ttk.Frame(rodape); botoes.pack(fill='x',pady=(8,0))

    def criar():
        if registros and not messagebox.askyesno('Novo documento','Substituir os campos do documento atual?'):
            return
        for filho in corpo.winfo_children(): filho.destroy()
        registros.clear()
        for i in range(total.get()):
            card=ttk.LabelFrame(corpo,text=f'Gráfico {i+1}',padding=12); card.pack(fill='x',pady=6)
            linha=ttk.Frame(card); linha.pack(fill='x')
            a,b=tk.StringVar(value='1'),tk.StringVar(value='0')
            for rotulo,var in [('Coeficiente a:',a),('Coeficiente b:',b)]:
                ttk.Label(linha,text=rotulo).pack(side='left',padx=(0,6))
                ttk.Entry(linha,textvariable=var,width=10).pack(side='left',padx=(0,18))
            n=tk.IntVar(value=3)
            ttk.Label(linha,text='Pontos:').pack(side='left')
            seletor=ttk.Spinbox(linha,from_=0,to=8,textvariable=n,width=3,state='readonly'); seletor.pack(side='left',padx=6)
            pontos=ttk.Frame(card); pontos.pack(fill='x',pady=(10,0))
            reg={'a':a,'b':b,'xs':[]}; registros.append(reg)
            def atualizar(reg=reg,pontos=pontos,n=n):
                antigos=[v.get() for v in reg['xs']]
                for filho in pontos.winfo_children(): filho.destroy()
                reg['xs']=[]
                for j in range(n.get()):
                    v=tk.StringVar(value=antigos[j] if j<len(antigos) else str(j+1))
                    reg['xs'].append(v)
                    ttk.Label(pontos,text=f'x{j+1}:').grid(row=j//4,column=(j%4)*2,padx=(0,4),pady=4)
                    ttk.Entry(pontos,textvariable=v,width=9).grid(row=j//4,column=(j%4)*2+1,padx=(0,15),pady=4)
            seletor.configure(command=atualizar); atualizar()
        status.set('Preencha a, b e os valores de x. Os valores de y serão calculados automaticamente.')

    def exportar(prever=False):
        try:
            if not registros: raise ValueError('Clique em Criar documento primeiro.')
            funcoes=[]
            for i,r in enumerate(registros):
                try:
                    f=Funcao(numero(r['a'].get()),numero(r['b'].get()),[numero(v.get()) for v in r['xs']]); f.validar()
                    funcoes.append(f)
                except ValueError as e: raise ValueError(f'Gráfico {i+1}: {e}')
            if len(funcoes)>15:
                raise ValueError('Use no máximo 15 gráficos por página.')
            if prever:
                fd,destino=tempfile.mkstemp(prefix='graficos_preview_',suffix='.pdf'); os.close(fd)
            else:
                destino=filedialog.asksaveasfilename(defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile='graficos.pdf')
                if not destino: return
            gerar_pdf(destino,funcoes,cols.get(),titulo.get())
            status.set(f'PDF gerado: {destino}')
            if prever: webbrowser.open(Path(destino).as_uri())
            else: messagebox.showinfo('PDF pronto',f'Arquivo salvo em:\n{destino}')
        except (ValueError,OSError,ImportError) as e: messagebox.showerror('Não foi possível gerar',str(e))
    ttk.Button(config,text='Criar documento',command=criar).pack(side='left',padx=12)
    ttk.Button(botoes,text='Visualizar PDF',command=lambda:exportar(True)).pack(side='left')
    ttk.Button(botoes,text='Salvar PDF',command=exportar).pack(side='right')
    root.mainloop()


if __name__=='__main__':
    if '--exemplo' in sys.argv:
        destino=Path(__file__).parent/'exemplo_graficos.pdf'
        gerar_pdf(destino,[Funcao(3,5,[1,2,3]),Funcao(-3,12,[1,2,3]),Funcao(-3,9,[0,3]),Funcao(3,-1,[2,6])])
        print(destino)
    else:
        from interface import iniciar
        iniciar()
