"""Cálculo e desenho de parábolas; exportação das duas páginas."""
import math
import re
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app_graficos import fmt, gerar_pdf


@dataclass
class Parabola:
    a: float
    b: float
    c: float
    raizes: bool = True
    intercepto: bool = True
    marcar_xv: bool = True
    marcar_yv: bool = True
    modo: str = 'Coeficientes'
    quantidade_raizes: str = '2'
    raiz1: str = '0'
    raiz2: str = '1'
    apresentacao: str = 'Gráfico'
    pedir_raizes: bool = True
    pedir_vertice: bool = True
    a_texto: str = ''
    b_texto: str = ''
    c_texto: str = ''

    def dados(self):
        from numeros_exatos import ler
        for key in ('a','b','c'):
            text=getattr(self,key+'_texto')
            if text and (key=='a' or self.modo=='Coeficientes'):
                setattr(self,key,ler(text)[1])
        if self.apresentacao not in ('Gráfico','Expressão da função'):
            raise ValueError('Escolha gráfico ou expressão da função.')
        if type(self.pedir_raizes) is not bool or type(self.pedir_vertice) is not bool:
            raise ValueError('Selecione as informações a calcular.')
        if self.apresentacao=='Expressão da função' and not (self.pedir_raizes or self.pedir_vertice):
            raise ValueError('Marque raízes, coordenadas do vértice ou ambas.')
        if self.modo not in ('Coeficientes','Raízes e a'):
            raise ValueError('Escolha o modo de entrada da parábola.')
        if self.modo=='Raízes e a':
            if self.quantidade_raizes not in ('1','2'):
                raise ValueError('Escolha uma ou duas raízes.')
            r1=ler(self.raiz1)[1]
            r2=r1 if self.quantidade_raizes=='1' else ler(self.raiz2)[1]
            self.b=-self.a*(r1+r2)
            self.c=self.a*r1*r2
        if not all(math.isfinite(v) for v in (self.a,self.b,self.c)) or self.a == 0:
            raise ValueError('Use coeficientes finitos e a diferente de zero.')
        if self.modo=='Raízes e a':
            xv=r1/2+r2/2
            yv=self.a*(xv-r1)*(xv-r2)
            if not all(math.isfinite(v) for v in (xv,yv)):
                raise ValueError('Valores muito grandes para desenhar a parábola.')
            return xv,yv,sorted(set((r1,r2)))
        xv = -self.b/(2*self.a)
        yv = (self.a*xv+self.b)*xv+self.c
        delta = self.b*self.b-4*self.a*self.c
        if not all(math.isfinite(v) for v in (xv,yv,delta)):
            raise ValueError('Coeficientes muito grandes para calcular a parábola.')
        if delta < 0:
            roots = []
        elif delta == 0:
            roots = [xv]
        else:
            q = -.5*(self.b+math.copysign(math.sqrt(delta),self.b))
            roots = sorted([q/self.a,self.c/q])
        return xv,yv,roots

    def expressao(self):
        from numeros_exatos import ler,rotulo
        import sympy as sp
        from decimal import Decimal, localcontext
        self.dados()
        a,b,c=(ler(getattr(self,k+'_texto'))[0] if getattr(self,k+'_texto') and (k=='a' or self.modo=='Coeficientes')
               else sp.Rational(str(getattr(self,k))) for k in ('a','b','c'))
        if self.modo=='Raízes e a':
            r1=ler(self.raiz1)[0]
            r2=r1 if self.quantidade_raizes=='1' else ler(self.raiz2)[0]
            b=sp.simplify(-a*(r1+r2)); c=sp.simplify(a*r1*r2)
        def formatar(v):
            if not v.is_Rational: return rotulo(v)
            den=int(v.q)
            for prime in (2,5):
                while den%prime==0: den//=prime
            if den!=1: return rotulo(v)
            with localcontext() as ctx:
                ctx.prec=1000
                text=format(Decimal(int(v.p))/Decimal(int(v.q)),'f')
            if '.' in text: text=text.rstrip('0').rstrip('.')
            return text.replace('.',',')
        parts=[]
        for key,value,term in (('a',a,'x²'),('b',b,'x'),('c',c,'')):
            if not value: continue
            magnitude='' if term and abs(value)==1 else formatar(abs(value))
            raw=getattr(self,key+'_texto')
            if raw and (key=='a' or self.modo=='Coeficientes') and magnitude:
                magnitude=raw.strip().lstrip('+-').replace(' ','')
                # A negative denominator is normalized so the outer sign remains correct.
                if '/-' in magnitude: magnitude=rotulo(abs(value))
                magnitude=re.sub(r'sqrt\(([^)]+)\)',r'√(\1)',magnitude)
            if term and magnitude and any(ch in magnitude for ch in ('/','√','+','-')):
                magnitude='('+magnitude+')'
            sign=('-' if value<0 else '') if not parts else (' - ' if value<0 else ' + ')
            parts.append(sign+magnitude+term)
        return 'f(x) = '+''.join(parts)

    def enunciado(self):
        expression=self.expressao()
        pedido=('as raízes reais e as coordenadas do vértice' if self.pedir_raizes and self.pedir_vertice
                else 'as raízes reais' if self.pedir_raizes else 'as coordenadas do vértice')
        return f'Dada a função <b>{expression}</b>, determine {pedido}.'


def desenhar_pagina(pdf, funcoes, colunas, titulo, quadro=None):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    if not 1 <= len(funcoes) <= 10 or colunas not in (1,2):
        raise ValueError('Use até 10 parábolas e 1 ou 2 por linha.')
    W,H=A4
    linhas=math.ceil(len(funcoes)/colunas)
    gap=min(12,40/linhas)
    cw=(W-60-(colunas-1)*gap)/colunas
    ch=min(245,(H-110-(linhas-1)*gap)/linhas)
    if quadro: cw,ch=quadro[2:4]
    pdf.setFillColor(HexColor('#172b4d'))
    size=16
    titulo=titulo or 'Funções de segundo grau'
    while pdf.stringWidth(titulo,'Helvetica-Bold',size)>W-60 and size>7:
        size-=.5
    pdf.setFont('Helvetica-Bold',size)
    pdf.drawCentredString(W/2,H-40,titulo)
    pdf.setFont('Helvetica',9)
    instruction=('Resolva as questões a seguir.' if all(f.apresentacao!='Gráfico' for f in funcoes)
                 else 'Determine c, as raízes, xv, yv, o sinal de delta e o sinal de a em cada gráfico.')
    pdf.drawString(30,H-57,instruction)
    for i,f in enumerate(funcoes):
        xv,yv,roots=f.dados()
        if f.apresentacao=='Expressão da função':
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_JUSTIFY
            left=30+(i%colunas)*(cw+gap); bottom=H-80-(i//colunas+1)*ch-(i//colunas)*gap
            if quadro: left,bottom=quadro[:2]
            pdf.setStrokeColor(HexColor('#cbd5e1')); pdf.setLineWidth(.6)
            pdf.roundRect(left,bottom,cw,ch,6)
            p=Paragraph(f'<b>({chr(97+i)})</b> '+f.enunciado(),ParagraphStyle('expressao',fontName='Helvetica',fontSize=10,leading=14,alignment=TA_JUSTIFY))
            _,height=p.wrap(cw-22,ch-24)
            if height>ch-24: raise ValueError('O enunciado não cabe. Use menos questões ou uma coluna.')
            p.drawOn(pdf,left+11,bottom+ch-12-height)
            continue
        # O enquadramento independe das opções de marcação.
        span=max([1,abs(xv),*[abs(r-xv) for r in roots]])
        xmin=min(0,xv-span*1.4); xmax=max(0,xv+span*1.4)
        dx=xmax-xmin
        xmin-=.12*dx; xmax+=.12*dx
        eval_y=lambda x: f.a*(x-xv)**2+yv
        low=min(0,yv,f.c); high=max(0,yv,f.c)
        amplitude=max(high-low,abs(f.a)*span**2,1)
        if f.a>0: high+=amplitude*.65
        else: low-=amplitude*.65
        dy=high-low
        ymin=low-.14*dy; ymax=high+.14*dy
        if not all(math.isfinite(v) for v in (xmin,xmax,ymin,ymax)):
            raise ValueError('Use coeficientes de menor magnitude.')
        left=30+(i%colunas)*(cw+gap)
        bottom=H-80-(i//colunas+1)*ch-(i//colunas)*gap
        if quadro: left,bottom=quadro[:2]
        pdf.setStrokeColor(HexColor('#cbd5e1')); pdf.setLineWidth(.6)
        pdf.roundRect(left,bottom,cw,ch,6)
        pdf.setFillColor(HexColor('#172b4d')); pdf.setFont('Helvetica-Bold',10)
        pdf.drawString(left+10,bottom+ch-17,f'({chr(97+i)})')
        factor=min(1,ch/130)
        px,py=left+42,bottom+28*factor
        pw,ph=cw-60,ch-57*factor
        X=lambda x:px+(x-xmin)/(xmax-xmin)*pw
        Y=lambda y:py+(y-ymin)/(ymax-ymin)*ph
        pdf.saveState()
        clip=pdf.beginPath(); clip.rect(px,py,pw,ph); pdf.clipPath(clip,stroke=0)
        pdf.setStrokeColor(HexColor('#2563eb')); pdf.setLineWidth(1.4)
        # Limita a curva ao intervalo visível antes de gerar os segmentos.
        reach=math.sqrt(max(0,((ymax if f.a>0 else ymin)-yv)/f.a))
        start=max(xmin,xv-reach); end=min(xmax,xv+reach)
        path=pdf.beginPath()
        for j in range(301):
            x=start+(end-start)*j/300
            if j==0: path.moveTo(X(x),Y(eval_y(x)))
            else: path.lineTo(X(x),Y(eval_y(x)))
        pdf.drawPath(path)
        pdf.setStrokeColor(HexColor('#94a3b8')); pdf.setDash(2,3)
        if f.marcar_xv: pdf.line(X(xv),Y(yv),X(xv),Y(0))
        if f.marcar_yv: pdf.line(X(xv),Y(yv),X(0),Y(yv))
        pdf.restoreState()
        pdf.setStrokeColor(HexColor('#172b4d')); pdf.setFillColor(HexColor('#172b4d')); pdf.setLineWidth(.7)
        pdf.line(px,Y(0),px+pw,Y(0)); pdf.line(X(0),py,X(0),py+ph)
        for sign in (-1,1):
            pdf.line(px+pw,Y(0),px+pw-4,Y(0)+sign*2)
            pdf.line(X(0),py+ph,X(0)+sign*2,py+ph-4)
        pdf.setFont('Helvetica',8)
        pdf.drawString(px+pw+3,Y(0)-3,'x'); pdf.drawString(X(0)+4,py+ph+2,'y')
        xticks=set(roots if f.raizes else [])
        yticks=set([f.c] if f.intercepto else [])
        if f.marcar_xv: xticks.add(xv)
        if f.marcar_yv: yticks.add(yv)
        for x in sorted(xticks):
            pdf.line(X(x),Y(0)-2,X(x),Y(0)+2)
            pdf.drawCentredString(X(x),Y(0)-11,fmt(x))
        for y in sorted(yticks):
            pdf.line(X(0)-2,Y(y),X(0)+2,Y(y))
            pdf.drawRightString(X(0)-4,Y(y)-3,fmt(y))
        points=set((r,0) for r in roots) if f.raizes else set()
        if f.intercepto: points.add((0,f.c))
        if f.marcar_xv or f.marcar_yv: points.add((xv,yv))
        pdf.setFillColor(HexColor('#dc2626'))
        for x,y in points: pdf.circle(X(x),Y(y),2.2,fill=1,stroke=0)


def salvar_documento(destino,paginas):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    if not paginas: raise ValueError('Crie pelo menos uma página.')
    destino=Path(destino)
    fd,tmp=tempfile.mkstemp(suffix='.pdf',dir=destino.parent); os.close(fd)
    try:
        pdf=Canvas(tmp,pagesize=A4)
        for indice,(grau,funcoes,colunas,titulo) in enumerate(paginas):
            if indice: pdf.showPage()
            if grau==1: gerar_pdf(destino,funcoes,colunas,titulo,canvas_existente=pdf)
            elif grau==2: desenhar_pagina(pdf,funcoes,colunas,titulo)
            elif grau==3:
                from triangulos import desenhar_pagina as desenhar_triangulos
                desenhar_triangulos(pdf,funcoes,colunas,titulo)
            elif grau==4:
                from solidos import desenhar_pagina as desenhar_solidos
                desenhar_solidos(pdf,funcoes,colunas,titulo)
            elif grau==5:
                from exponenciais import desenhar_pagina as desenhar_exponenciais
                desenhar_exponenciais(pdf,funcoes,colunas,titulo)
            elif grau==6:
                from progressao import desenhar_pagina as desenhar_pa
                desenhar_pa(pdf,funcoes,colunas,titulo)
            else: raise ValueError('Tipo de página desconhecido.')
        pdf.setTitle('Gráficos de funções')
        pdf.save()
        from documentos import publicar_par
        publicar_par(tmp,destino,paginas)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
