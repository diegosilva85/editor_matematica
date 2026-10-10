"""Triângulos retângulos e medidas exatas sem avaliação de código."""
import math
import re
from dataclasses import dataclass

POSICOES = ['Virado para direita', 'Virado para esquerda',
            'De cabeça para baixo para direita', 'De cabeça para baixo para esquerda',
            'Hipotenusa apontada para cima', 'Hipotenusa apontada para baixo']
LADOS = {'Seno': ('Cateto oposto', 'Hipotenusa'),
         'Cosseno': ('Cateto adjacente', 'Hipotenusa'),
         'Tangente': ('Cateto oposto', 'Cateto adjacente')}
PITAGORAS='Teorema de Pitágoras'
LADOS_PIT=('Cateto 1','Cateto 2','Hipotenusa')


def termo(texto):
    texto=texto.strip().replace(',', '.').replace(' ', '').replace('*','')
    texto=re.sub(r'sqrt\((\d+(?:\.\d+)?)\)', r'√\1', texto)
    m=re.fullmatch(r'(?:(\d+(?:\.\d+)?))?(?:√(\d+(?:\.\d+)?))?',texto)
    if not m or not any(m.groups()):
        raise ValueError('Use números, raízes ou frações: 5, 2√3, √3/3, 3/2 ou sqrt(2).')
    coef=float(m[1]) if m[1] else 1.
    valor=coef*math.sqrt(float(m[2])) if m[2] else coef
    if not math.isfinite(valor) or valor<=0:
        raise ValueError('As medidas devem ser positivas e finitas.')
    return texto,valor


def medida(texto):
    if len(texto)>40: raise ValueError('Use uma medida com até 40 caracteres.')
    partes=texto.split('/')
    if len(partes)>2: raise ValueError('Use uma única barra para indicar a fração.')
    tokens=[termo(p) for p in partes]
    valor=tokens[0][1]/tokens[1][1] if len(tokens)==2 else tokens[0][1]
    if not math.isfinite(valor) or valor<=0: raise ValueError('Medida fora do intervalo permitido.')
    return [t[0] for t in tokens],valor


@dataclass
class Triangulo:
    angulo: float
    posicao: str
    razao: str
    conhecido: str
    valor: str
    lado_x: str = 'Hipotenusa'
    valor2: str = '4'
    apresentacao: str = 'Triângulo simples'
    cenario: str = 'Avião decolando'
    dado_contexto: str = 'distância percorrida pelo avião na subida'
    pedido_contexto: str = 'altura atingida pelo avião'
    altura_extra: str = '1,6'

    def validar(self):
        if self.apresentacao == 'Contextual':
            from contextos import validar
            validar(self)
            return
        if self.apresentacao != 'Triângulo simples':
            raise ValueError('Escolha a apresentação da questão.')
        if self.razao==PITAGORAS:
            if self.posicao not in POSICOES: raise ValueError('Escolha a posição.')
            self.medidas_pitagoras()
            return
        if not math.isfinite(self.angulo) or not 0<self.angulo<90:
            raise ValueError('O ângulo deve ser maior que 0° e menor que 90°.')
        if self.posicao not in POSICOES or self.razao not in LADOS:
            raise ValueError('Escolha a posição e a razão trigonométrica.')
        if self.conhecido not in LADOS[self.razao]: raise ValueError('Escolha um lado compatível com a razão.')
        medida(self.valor)

    @property
    def incognita(self):
        if self.razao==PITAGORAS:
            return {'Cateto 1':'Cateto adjacente','Cateto 2':'Cateto oposto','Hipotenusa':'Hipotenusa'}[self.lado_x]
        return next(l for l in LADOS[self.razao] if l!=self.conhecido)

    def medidas_pitagoras(self):
        if self.lado_x not in LADOS_PIT: raise ValueError('Escolha o lado a calcular.')
        conhecidos=[k for k in LADOS_PIT if k!=self.lado_x]
        valores=dict(zip(conhecidos,(medida(self.valor)[1],medida(self.valor2)[1])))
        if self.lado_x=='Hipotenusa':
            valores[self.lado_x]=math.hypot(*valores.values())
        else:
            h=valores['Hipotenusa']; cat=valores[conhecidos[0]]
            if h<=cat: raise ValueError('A hipotenusa deve ser maior que o cateto informado.')
            valores[self.lado_x]=h*math.sqrt((1-cat/h)*(1+cat/h))
        if not all(math.isfinite(v) and v>0 for v in valores.values()): raise ValueError('Medidas fora do intervalo permitido.')
        return valores

    def angulo_desenho(self):
        if self.razao!=PITAGORAS: return self.angulo
        v=self.medidas_pitagoras()
        return math.degrees(math.atan2(v['Cateto 2'],v['Cateto 1']))


def vertices(posicao, angulo=45):
    # R: ângulo reto; A: ângulo conhecido; B: terceiro vértice.
    # Hipotenusa unitária: catetos cos(ângulo) e sen(ângulo).
    if not math.isfinite(angulo) or not 0 < angulo < 90:
        raise ValueError('O ângulo deve ser maior que 0° e menor que 90°.')
    rad=math.radians(angulo)
    pts=[(0,0),(0,math.cos(rad)),(math.sin(rad),0)]
    idx=POSICOES.index(posicao)
    if idx in (1,3): pts=[(-x,y) for x,y in pts]
    if idx in (2,3): pts=[(x,-y) for x,y in pts]
    if idx in (4,5):
        # Rotação rígida alinha a hipotenusa horizontalmente acima de R.
        t=math.pi/2-rad
        pts=[(x*math.cos(t)-y*math.sin(t),x*math.sin(t)+y*math.cos(t)) for x,y in pts]
        if idx==5: pts=[(x,-y) for x,y in pts]
    return pts


def expressao(pdf,texto,x,y,size=10):
    """Desenha radical com barra e fração vertical, centralizados."""
    partes,_=medida(texto)
    def largura(s):
        return pdf.stringWidth(s.replace('√',''), 'Helvetica',size)+(size*.8 if '√' in s else 0)
    def desenhar(s,cx,cy):
        start=cx-largura(s)/2
        pdf.setFont('Helvetica',size)
        if '√' not in s:
            pdf.drawString(start,cy,s.replace('.',',')); return
        coef,rad=s.split('√')
        pdf.drawString(start,cy,coef.replace('.',','))
        start+=pdf.stringWidth(coef,'Helvetica',size)
        p=pdf.beginPath(); p.moveTo(start,cy+size*.35)
        p.lineTo(start+size*.2,cy+size*.45); p.lineTo(start+size*.38,cy-size*.05)
        p.lineTo(start+size*.7,cy+size*.95)
        p.lineTo(start+size*.8+pdf.stringWidth(rad,'Helvetica',size),cy+size*.95)
        pdf.drawPath(p)
        pdf.drawString(start+size*.8,cy,rad.replace('.',','))
    if len(partes)==1: desenhar(partes[0],x,y-size*.3)
    else:
        w=max(map(largura,partes))+4
        desenhar(partes[0],x,y+size*.35)
        pdf.line(x-w/2,y,x+w/2,y)
        desenhar(partes[1],x,y-size*1.2)


def desenhar_pagina(pdf,triangulos,colunas,titulo):
    if any(t.apresentacao == 'Contextual' for t in triangulos):
        from contextos import desenhar_pagina as contextual
        return contextual(pdf,triangulos,colunas,titulo)
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    if not 1<=len(triangulos)<=15 or colunas not in (1,2,3):
        raise ValueError('Use até 15 triângulos, com no máximo 3 por linha.')
    W,H=A4; rows=math.ceil(len(triangulos)/colunas); gap=min(12,40/rows)
    cw=(W-60-(colunas-1)*gap)/colunas
    ch=min(245,(H-120-(rows-1)*gap)/rows)
    pdf.setFillColor(HexColor('#172b4d')); pdf.setFont('Helvetica-Bold',15)
    pdf.drawCentredString(W/2,H-35,(titulo or 'Trigonometria')[:65])
    pdf.setFont('Helvetica',9)
    pdf.drawString(30,H-53,'Determine x em cada triângulo retângulo.')
    pdf.setFont('Helvetica',8); pdf.drawString(30,H-67,'Medidas na mesma unidade.')
    for i,t in enumerate(triangulos):
        t.validar()
        left=30+(i%colunas)*(cw+gap); bottom=H-83-(i//colunas+1)*ch-(i//colunas)*gap
        desenhar_quadro(pdf,t,left,bottom,cw,ch,i)


def desenhar_quadro(pdf,t,left,bottom,cw,ch,indice):
    from reportlab.lib.colors import HexColor
    pdf.setStrokeColor(HexColor('#cbd5e1')); pdf.setLineWidth(.6); pdf.roundRect(left,bottom,cw,ch,6)
    pdf.setFillColor(HexColor('#172b4d')); pdf.setFont('Helvetica-Bold',9)
    pdf.drawString(left+9,bottom+ch-15,f'({chr(97+indice)})')
    raw=vertices(t.posicao,t.angulo_desenho())
    minx=min(x for x,y in raw); maxx=max(x for x,y in raw)
    miny=min(y for x,y in raw); maxy=max(y for x,y in raw)
    scale=min((cw-72)/(maxx-minx),(ch-66)/(maxy-miny))
    if scale<=0: raise ValueError('Escolha mais colunas para que os triângulos caibam na página.')
    cx=left+cw/2; cy=bottom+(ch-14)/2
    pts=[(cx+(x-(minx+maxx)/2)*scale,cy+(y-(miny+maxy)/2)*scale) for x,y in raw]
    R,A,B=pts
    pdf.setStrokeColor(HexColor('#2563eb')); pdf.setLineWidth(1.2)
    p=pdf.beginPath(); p.moveTo(*R); p.lineTo(*A); p.lineTo(*B); p.close(); pdf.drawPath(p)
    def unit(p,q):
        d=math.dist(p,q); return ((q[0]-p[0])/d,(q[1]-p[1])/d)
    u,v=unit(R,A),unit(R,B); s=min(6,math.dist(R,A)*.18,math.dist(R,B)*.18)
    pdf.setStrokeColor(HexColor('#172b4d')); pdf.setLineWidth(.7)
    p=pdf.beginPath(); p.moveTo(R[0]+s*u[0],R[1]+s*u[1]); p.lineTo(R[0]+s*(u[0]+v[0]),R[1]+s*(u[1]+v[1])); p.lineTo(R[0]+s*v[0],R[1]+s*v[1]); pdf.drawPath(p)
    u,v=unit(A,R),unit(A,B)
    theta=math.atan2(u[1],u[0]); delta=(math.atan2(v[1],v[0])-theta+math.pi)%(2*math.pi)-math.pi
    radius=min(15,math.dist(A,R)*.3,math.dist(A,B)*.3)
    p=pdf.beginPath()
    for j in range(21):
        ang=theta+delta*j/20; point=(A[0]+radius*math.cos(ang),A[1]+radius*math.sin(ang))
        if j==0: p.moveTo(*point)
        else: p.lineTo(*point)
    if t.razao!=PITAGORAS: pdf.drawPath(p)
    angle=theta+delta/2
    pdf.setFont('Helvetica',8)
    if t.razao!=PITAGORAS:
        pdf.drawCentredString(A[0]+(radius+10)*math.cos(angle),A[1]+(radius+10)*math.sin(angle)-2,f'{t.angulo:g}°')
    conhecidos={t.conhecido:t.valor}
    if t.razao==PITAGORAS:
        nomes={'Cateto 1':'Cateto adjacente','Cateto 2':'Cateto oposto','Hipotenusa':'Hipotenusa'}
        conhecidos=dict(zip([nomes[k] for k in LADOS_PIT if k!=t.lado_x],(t.valor,t.valor2)))
    centroid=(sum(x for x,y in pts)/3,sum(y for x,y in pts)/3)
    for lado,(p,q) in {'Cateto oposto':(R,B),'Cateto adjacente':(R,A),'Hipotenusa':(A,B)}.items():
        if lado not in conhecidos and lado!=t.incognita: continue
        mid=((p[0]+q[0])/2,(p[1]+q[1])/2)
        ux,uy=unit(p,q); nx,ny=-uy,ux
        if nx*(mid[0]-centroid[0])+ny*(mid[1]-centroid[1])<0: nx,ny=-nx,-ny
        x,y=mid[0]+nx*17,mid[1]+ny*17
        if lado==t.incognita:
            pdf.setFont('Helvetica-Oblique',11); pdf.drawCentredString(x,y-3,'x')
        else: expressao(pdf,conhecidos[lado],x,y,9)
