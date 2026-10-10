"""Modelos e desenho vetorial compartilhado pela prévia e pelo PDF."""
import math
from dataclasses import dataclass
from triangulos import medida, expressao

TIPOS=['Cubo','Prisma retangular','Prisma triangular','Prisma hexagonal',
       'Cilindro','Cone','Pirâmide de base quadrada','Tetraedro','Esfera']


def campos(tipo,circular='Raio',cone='Altura'):
    if tipo in ('Cubo','Tetraedro'): return [('a','Aresta')]
    if tipo=='Prisma retangular': return [('a','Comprimento'),('b','Largura'),('h','Altura')]
    if tipo in ('Prisma triangular','Prisma hexagonal','Pirâmide de base quadrada'):
        return [('a','Aresta da base'),('h','Altura')]
    result=[('r' if circular=='Raio' else 'd',circular)]
    if tipo=='Cilindro': result.append(('h','Altura'))
    if tipo=='Cone': result.append(('h' if cone=='Altura' else 'g',cone))
    return result


@dataclass
class Solido:
    tipo: str
    valores: dict
    circular: str = 'Raio'
    cone: str = 'Altura'
    cenario: str = 'Sem contexto'
    objetivo: str = 'Volume'
    incluir_imagem: bool = True
    unidade: str = 'cm'

    def validar(self):
        if self.tipo not in TIPOS: raise ValueError('Escolha um sólido.')
        if self.circular not in ('Raio','Diâmetro') or self.cone not in ('Altura','Geratriz'):
            raise ValueError('Escolha o tipo de medida.')
        inverso=self.cenario in ('Peça mergulhada em aquário','Teste em tanque cilíndrico') and self.objetivo=='Volume pela elevação'
        values={} if inverso else {k:medida(self.valores.get(k,''))[1] for k,_ in campos(self.tipo,self.circular,self.cone)}
        if self.tipo=='Cone' and self.cone=='Geratriz':
            r=values['r'] if 'r' in values else values['d']/2
            if values['g']<=r: raise ValueError('A geratriz do cone deve ser maior que o raio.')
        from contextos_solidos import validar
        validar(self)


def desenho(tipo,circular='Raio',cone='Altura'):
    """Coordenadas normalizadas (y para cima), caminhos e rótulos."""
    lines=[]; labels=[]
    def line(points,dash=False): lines.append((points,dash))
    def label(x,y,text): labels.append((x,y,text))
    def ellipse(cx,cy,rx,ry,start=0,end=360,dash=False):
        line([(cx+rx*math.cos(math.radians(start+(end-start)*i/60)),cy+ry*math.sin(math.radians(start+(end-start)*i/60))) for i in range(61)],dash)
    if tipo in ('Cubo','Prisma retangular'):
        w=.53; h=.53 if tipo=='Cubo' else .65
        A=(.15,.12); B=(.15+w,.12); C=(.15+w,.12+h); D=(.15,.12+h)
        shift=lambda p:(p[0]+.18,p[1]+.14)
        E,F,G,H=map(shift,(A,B,C,D))
        line([A,B,C,D,A]); line([D,H,G,C]); line([B,F,G]); line([A,E,F],True); line([E,H],True)
        label(.42,.03,'a')
        if tipo=='Prisma retangular': label(.84,.15,'b'); label(.96,.53,'h')
    elif tipo in ('Prisma triangular','Prisma hexagonal'):
        n=3 if tipo=='Prisma triangular' else 6
        base=[(.5+.34*math.cos(2*math.pi*i/n-math.pi/2),.2+.13*math.sin(2*math.pi*i/n-math.pi/2)) for i in range(n)]
        top=[(x,y+.55) for x,y in base]
        line(top+[top[0]])
        for i in range(n):
            j=(i+1)%n
            line([base[i],base[j]],(base[i][1]+base[j][1])/2>.2)
            silhouette=math.isclose(base[i][0],min(x for x,y in base)) or math.isclose(base[i][0],max(x for x,y in base))
            line([base[i],top[i]],base[i][1]>.26 and not silhouette)
        label(.68,.04,'a'); label(.9,.5,'h')
    elif tipo in ('Cilindro','Cone','Esfera'):
        if tipo=='Esfera':
            ellipse(.5,.5,.34,.34)
            ellipse(.5,.5,.34,.1,180,360); ellipse(.5,.5,.34,.1,0,180,True)
            cy=.5
        else:
            cy=.2
            ellipse(.5,cy,.32,.1,180,360); ellipse(.5,cy,.32,.1,0,180,True)
            if tipo=='Cilindro':
                ellipse(.5,.78,.32,.1); line([(.18,.2),(.18,.78)]); line([(.82,.2),(.82,.78)])
                label(.91,.49,'h')
            else:
                line([(.18,.2),(.5,.88),(.82,.2)])
                if cone=='Altura': line([(.5,.2),(.5,.88)],True); label(.56,.55,'h')
                else: label(.77,.57,'g')
        line([(.5 if circular=='Raio' else .18,cy),(.82,cy)],True)
        label(.66 if circular=='Raio' else .5,cy-.07,'r' if circular=='Raio' else 'd')
    elif tipo=='Pirâmide de base quadrada':
        A,B,C,D=(.14,.21),(.48,.08),(.86,.28),(.52,.41)
        T=(.5,.9)
        line([A,B,C]); line([C,D,A],True)
        for p in (A,B,C): line([p,T])
        line([D,T],True); line([(.5,.25),T],True)
        label(.29,.07,'a'); label(.56,.57,'h')
    elif tipo=='Tetraedro':
        A,B,C,T=(.16,.27),(.5,.08),(.84,.27),(.5,.87)
        line([A,B,C,T,A]); line([B,T]); line([A,C],True)
        label(.28,.12,'a')
    return lines,labels


def desenhar_pagina(pdf,items,colunas,titulo,quadro=None):
    if not quadro and any(s.cenario!='Sem contexto' for s in items):
        from contextos_solidos import desenhar_paginas
        return desenhar_paginas(pdf,items,colunas,titulo)
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor
    if not 1<=len(items)<=12 or colunas not in (1,2,3):
        raise ValueError('Use até 12 sólidos e até 3 por linha.')
    W,H=A4; rows=math.ceil(len(items)/colunas); gap=min(12,40/rows)
    cw=(W-60-(colunas-1)*gap)/colunas; ch=min(265,(H-120-(rows-1)*gap)/rows)
    if quadro: cw,ch=quadro[2:4]
    if ch<110: raise ValueError('Aumente as colunas para acomodar os sólidos e suas medidas com legibilidade.')
    pdf.setFillColor(HexColor('#172b4d')); size=16
    titulo=titulo or 'Geometria espacial'
    while pdf.stringWidth(titulo,'Helvetica-Bold',size)>W-60 and size>6: size-=.5
    pdf.setFont('Helvetica-Bold',size); pdf.drawCentredString(W/2,H-35,titulo)
    pdf.setFont('Helvetica',9); pdf.drawString(30,H-53,'Determine o volume e a área total de cada sólido.')
    pdf.setFont('Helvetica',7)
    pdf.drawString(30,H-67,'Prismas retos e bases regulares; pirâmide reta; tetraedro regular. Medidas em cm. Figuras sem escala.')
    for i,s in enumerate(items):
        s.validar()
        left=30+i%colunas*(cw+gap); bottom=H-83-(i//colunas+1)*ch-(i//colunas)*gap
        if quadro: left,bottom=quadro[:2]
        pdf.setStrokeColor(HexColor('#cbd5e1')); pdf.setLineWidth(.6); pdf.roundRect(left,bottom,cw,ch,6)
        pdf.setFillColor(HexColor('#172b4d')); size=9
        title=f'({chr(97+i)}) {s.tipo}'
        while pdf.stringWidth(title,'Helvetica-Bold',size)>cw-16: size-=.5
        pdf.setFont('Helvetica-Bold',size); pdf.drawString(left+8,bottom+ch-16,title)
        scale=min(cw-30,ch-67); ox=left+(cw-scale)/2; oy=bottom+40
        lines,labels=desenho(s.tipo,s.circular,s.cone)
        pdf.setStrokeColor(HexColor('#2563eb')); pdf.setLineWidth(1)
        for points,dash in lines:
            pdf.setDash(2,2) if dash else pdf.setDash()
            path=pdf.beginPath(); path.moveTo(ox+points[0][0]*scale,oy+points[0][1]*scale)
            for x,y in points[1:]: path.lineTo(ox+x*scale,oy+y*scale)
            pdf.drawPath(path)
        pdf.setDash(); pdf.setFillColor(HexColor('#172b4d')); pdf.setFont('Helvetica-Oblique',9)
        for x,y,label in labels: pdf.drawCentredString(ox+x*scale,oy+y*scale,label)
        fields=campos(s.tipo,s.circular,s.cone)
        pdf.setStrokeColor(HexColor('#172b4d')); pdf.setLineWidth(.6)
        for j,(key,_) in enumerate(fields):
            x=left+(j+.5)*cw/len(fields)
            pdf.setFont('Helvetica',8); pdf.drawRightString(x-9,bottom+19,key+' =')
            expressao(pdf,s.valores[key],x+9,bottom+22,8)
