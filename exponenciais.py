"""Funções exponenciais: parâmetros numéricos, raízes e frações."""
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from triangulos import medida
from app_graficos import fmt

TIPOS=['b · a^x','a^x + b']


def fracao_racional(texto):
    """Preserva coeficientes racionais e raízes que resultam em racionais."""
    s=texto.strip().replace(' ','').replace(',','.').replace('*','')
    s=re.sub(r'sqrt\((\d+(?:\.\d+)?)\)',r'√\1',s)
    partes=s.split('/')
    def termo_exato(t):
        if '√' not in t: return Fraction(t)
        coef,rad=t.split('√')
        coef={'':'1','-':'-1','+':'1'}.get(coef,coef)
        r=Fraction(rad); n=math.isqrt(r.numerator); d=math.isqrt(r.denominator)
        if n*n!=r.numerator or d*d!=r.denominator: raise ValueError('Irracional')
        return Fraction(coef)*Fraction(n,d)
    if len(partes)>2: raise ValueError('Fração inválida')
    return termo_exato(partes[0])/(termo_exato(partes[1]) if len(partes)==2 else 1)


def rotulo_y(funcao,x):
    try:
        if not float(x).is_integer() or abs(x)>1000: raise ValueError('Expoente não inteiro')
        a,b=fracao_racional(funcao.a),fracao_racional(funcao.b)
        p=a**int(x)
        return (b*p if funcao.tipo==TIPOS[0] else p+b),False
    except (ValueError,ZeroDivisionError):
        return Fraction(funcao.y(x)).limit_denominator(1000),True


def desenhar_fracao(pdf,valor,aproximado,direita,y):
    pdf.setFont('Helvetica',8)
    sinal='-' if valor<0 else ''
    n,d=str(abs(valor.numerator)),str(valor.denominator)
    prefixo=('~ ' if aproximado else '')+sinal
    if valor.denominator==1:
        pdf.drawRightString(direita,y-3,prefixo+n)
        return
    largura=max(pdf.stringWidth(t,'Helvetica',8) for t in (n,d))+4
    centro=direita-largura/2
    pdf.drawCentredString(centro,y+3,n)
    pdf.line(direita-largura,y,direita,y)
    pdf.drawCentredString(centro,y-9,d)
    pdf.drawRightString(direita-largura-2,y-3,prefixo)


def coeficiente(texto):
    s=texto.strip().replace(' ','')
    sinal=-1 if s.startswith('-') else 1
    if s[:1] in ('-','+'): s=s[1:]
    if re.fullmatch(r'0+(?:[.,]0+)?',s): return 0.
    return sinal*medida(s)[1]


@dataclass
class Exponencial:
    tipo: str
    a: str
    b: str
    xs: list

    def parametros(self):
        a,b=coeficiente(self.a),coeficiente(self.b)
        if self.tipo not in TIPOS: raise ValueError('Escolha o formato da exponencial.')
        if a<=0 or a==1: raise ValueError('A base a deve ser positiva e diferente de 1.')
        if self.tipo==TIPOS[0] and b==0: raise ValueError('Neste formato, b deve ser diferente de zero.')
        if not all(math.isfinite(x) for x in self.xs): raise ValueError('Informe valores de x finitos.')
        return a,b

    def y(self,x):
        a,b=self.parametros()
        try:
            potencia=a**x
            value=b*potencia if self.tipo==TIPOS[0] else potencia+b
        except OverflowError: raise ValueError('Os valores escolhidos são grandes demais. Reduza a base ou os valores de x.')
        if not math.isfinite(value): raise ValueError('O gráfico ultrapassa o intervalo numérico suportado.')
        if self.tipo==TIPOS[1] and abs(value)<=1e-14*max(abs(potencia),abs(b)):
            return 0.
        return value

    def validar(self):
        self.parametros()
        for x in [0,*self.xs]: self.y(x)


def desenhar_pagina(pdf,items,colunas,titulo,quadro=None):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    if not 1<=len(items)<=8 or colunas not in (1,2):
        raise ValueError('Use até 8 exponenciais e no máximo 2 por linha.')
    W,H=A4; rows=math.ceil(len(items)/colunas); gap=min(12,40/rows)
    cw=(W-60-(colunas-1)*gap)/colunas; ch=min(240,(H-110-(rows-1)*gap)/rows)
    if quadro: cw,ch=quadro[2:4]
    pdf.setFillColor(HexColor('#172b4d')); size=16
    titulo=titulo or 'Funções exponenciais'
    while pdf.stringWidth(titulo,'Helvetica-Bold',size)>W-60 and size>6: size-=.5
    pdf.setFont('Helvetica-Bold',size); pdf.drawCentredString(W/2,H-38,titulo)
    pdf.setFont('Helvetica',9); pdf.drawString(30,H-59,'Determine a expressão da função representada em cada gráfico.')
    for i,f in enumerate(items):
        f.validar(); a,b=f.parametros()
        xs=sorted(set(f.xs)); base=xs or [-1,0,1,2]
        xmin=min(0,*base); xmax=max(0,*base)
        if xmin==xmax: xmin,xmax=-1,2
        span=xmax-xmin; xmin-=.15*span; xmax+=.15*span
        values=[0,f.y(0),*[f.y(x) for x in base]]
        low,high=min(values),max(values); dy=high-low
        if dy<=0 or not math.isfinite(dy): raise ValueError('Escolha parâmetros que produzam uma escala numérica válida.')
        ymin,ymax=low-.14*dy,high+.2*dy
        left=30+i%colunas*(cw+gap); bottom=H-80-(i//colunas+1)*ch-(i//colunas)*gap
        if quadro: left,bottom=quadro[:2]
        pdf.setStrokeColor(HexColor('#cbd5e1')); pdf.setLineWidth(.6); pdf.roundRect(left,bottom,cw,ch,6)
        pdf.setFillColor(HexColor('#172b4d')); pdf.setFont('Helvetica-Bold',10); pdf.drawString(left+10,bottom+ch-17,f'({chr(97+i)})')
        factor=min(1,ch/130); px,py=left+42,bottom+28*factor
        pw,ph=cw-61,ch-57*factor
        X=lambda x:px+(x-xmin)/(xmax-xmin)*pw
        Y=lambda y:py+(y-ymin)/(ymax-ymin)*ph
        pdf.saveState(); clip=pdf.beginPath(); clip.rect(px,py,pw,ph); pdf.clipPath(clip,stroke=0)
        pdf.setStrokeColor(HexColor('#94a3b8')); pdf.setLineWidth(.6); pdf.setDash(2,3)
        for x in xs:
            y=f.y(x); pdf.line(X(x),Y(0),X(x),Y(y)); pdf.line(X(0),Y(y),X(x),Y(y))
        pdf.setDash(); pdf.setStrokeColor(HexColor('#2563eb')); pdf.setLineWidth(1.4)
        # Interseção analítica da curva com a faixa vertical para evitar overflow.
        zlow,zhigh=sorted((ymin/b,ymax/b)) if f.tipo==TIPOS[0] else (ymin-b,ymax-b)
        lo,hi=xmin,xmax
        if zhigh>0:
            bound=math.log(zhigh)/math.log(a)
            if a>1: hi=min(hi,bound)
            else: lo=max(lo,bound)
            if zlow>0:
                bound=math.log(zlow)/math.log(a)
                if a>1: lo=max(lo,bound)
                else: hi=min(hi,bound)
            if lo<=hi:
                path=pdf.beginPath()
                for j in range(301):
                    x=lo+(hi-lo)*j/300; y=f.y(x)
                    if j==0: path.moveTo(X(x),Y(y))
                    else: path.lineTo(X(x),Y(y))
                pdf.drawPath(path)
        pdf.restoreState()
        pdf.setStrokeColor(HexColor('#172b4d')); pdf.setLineWidth(.7); pdf.setFillColor(HexColor('#172b4d')); pdf.setFont('Helvetica',8)
        pdf.line(px,Y(0),px+pw,Y(0)); pdf.line(X(0),py,X(0),py+ph)
        for sign in (-1,1):
            pdf.line(px+pw,Y(0),px+pw-4,Y(0)+sign*2); pdf.line(X(0),py+ph,X(0)+sign*2,py+ph-4)
        pdf.drawString(px+pw+3,Y(0)-3,'x'); pdf.drawString(X(0)+4,py+ph+2,'y')
        for x in xs:
            pdf.line(X(x),Y(0)-2,X(x),Y(0)+2); pdf.drawCentredString(X(x),Y(0)-11,fmt(x))
        ultimo=py-20
        pontos={f.y(x):x for x in xs}
        for y in sorted(pontos):
            if y!=0:
                valor,aproximado=rotulo_y(f,pontos[y])
                pos=max(Y(y),ultimo+21)
                pdf.line(X(0)-2,Y(y),X(0)+2,Y(y))
                if abs(pos-Y(y))>1:
                    pdf.line(X(0)-3,Y(y),X(0)-9,pos)
                desenhar_fracao(pdf,valor,aproximado,X(0)-10,pos); ultimo=pos
        pdf.setFillColor(HexColor('#dc2626'))
        for x in xs: pdf.circle(X(x),Y(f.y(x)),2.2,stroke=0,fill=1)
