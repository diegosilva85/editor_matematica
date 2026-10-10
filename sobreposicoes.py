"""Anotações vetoriais sobre ilustrações sem escala, sem revelar a incógnita.

Coordenadas relativas à imagem efetivamente desenhada, com origem inferior
esquerda. A é o vértice do ângulo, R a projeção e B o destino. Nas vistas em
perspectiva, o marcador reto acompanha a projeção dos dois catetos.
"""
import math


ANCORAS = {
    'Avião decolando': ((.12,.19),(.66,.19),(.66,.57),None),
    'Barco atravessando o rio': ((.44,.12),(.27,.69),(.76,.87),None),
    'Escada na parede': ((.47,.11),(.63,.11),(.63,.79),None),
    'Sombra de um prédio': ((.09,.22),(.53,.22),(.53,.87),None),
    'Pessoa observando um prédio': ((.105,.31),(.73,.31),(.73,.88),.12),
    'Antena e avião': ((.20,.62),(.82,.62),(.82,.85),.105),
    'Terreno de uma chácara': ((.25,.14),(.90,.28),(.70,.83),None),
    'Rampa de acesso': ((.21,.22),(.85,.22),(.85,.58),None),
    'Pipa no céu': ((.21,.44),(.746,.44),(.746,.89),.11),
    'Cabo de sustentação': ((.11,.13),(.78,.13),(.78,.91),None),
    'Teleférico': ((.09,.25),(.89,.25),(.89,.86),None),
    'Mergulhador': ((.23,.85),(.62,.85),(.62,.43),None),
}


def anotacoes(t,w,h):
    """Retorna linhas e rótulos; pedido_contexto nunca determina um rótulo."""
    from contextos import CENARIOS
    t.validar()
    a,r,b,ground=ANCORAS[t.cenario]
    A,R,B=[(x*w,y*h) for x,y in (a,r,b)]
    lines=[([A,R,B,A],False)]
    def unit(p,q):
        d=math.dist(p,q)
        return ((q[0]-p[0])/d,(q[1]-p[1])/d)
    u,v=unit(R,A),unit(R,B)
    s=min(5,math.dist(R,A)*.12,math.dist(R,B)*.12)
    lines.append(([(R[0]+s*u[0],R[1]+s*u[1]),
                   (R[0]+s*(u[0]+v[0]),R[1]+s*(u[1]+v[1])),
                   (R[0]+s*v[0],R[1]+s*v[1])],False))
    theta=math.atan2(R[1]-A[1],R[0]-A[0])
    delta=(math.atan2(B[1]-A[1],B[0]-A[0])-theta+math.pi)%(2*math.pi)-math.pi
    radius=min(14,math.dist(A,R)*.22,math.dist(A,B)*.22)
    arc=[(A[0]+radius*math.cos(theta+delta*j/24),
          A[1]+radius*math.sin(theta+delta*j/24)) for j in range(25)]
    lines.append((arc,False))
    mid=theta+delta/2
    labels=[('angulo',f'{t.angulo:g}°',A[0]+(radius+10)*math.cos(mid),
             A[1]+(radius+10)*math.sin(mid))]
    if abs(delta)>1:
        labels[0]=('angulo',f'{t.angulo:g}°',max(14,A[0]-15),
                   max(12,min(h-12,A[1]+18*(1 if delta>0 else -1))))
    side=CENARIOS[t.cenario][1].index(t.dado_contexto)
    p,q=((A,R),(R,B),(A,B))[side]
    if side==1 and ground is not None:
        # O dado é a altura TOTAL, não a diferença de alturas do triângulo.
        xx=min(w-9,B[0]+12)
        p,q=(xx,ground*h),(xx,B[1])
        lines.extend([([p,q],False), ([(xx-3,p[1]),(xx+3,p[1])],False),
                      ([(xx-3,q[1]),(xx+3,q[1])],False)])
        lx,ly=xx+14,(p[1]+q[1])/2
    else:
        ux,uy=unit(p,q); nx,ny=-uy,ux
        mx,my=(p[0]+q[0])/2,(p[1]+q[1])/2
        cx,cy=(A[0]+R[0]+B[0])/3,(A[1]+R[1]+B[1])/3
        if nx*(mx-cx)+ny*(my-cy)<0: nx,ny=-nx,-ny
        lx,ly=mx+nx*11,my+ny*11
    labels.append(('medida',t.valor,max(19,min(w-19,lx)),max(10,min(h-10,ly))))
    return lines,labels


def desenhar_pdf(pdf,t,x,y,w,h):
    from triangulos import expressao
    lines,labels=anotacoes(t,w,h)
    pdf.saveState()
    pdf.setLineJoin(1); pdf.setLineCap(1)
    # Halo branco mantém as linhas visíveis sobre os detalhes da gravura.
    for width,gray in ((2.7,1),(1,0)):
        pdf.setStrokeGray(gray); pdf.setLineWidth(width)
        for points,_ in lines:
            path=pdf.beginPath(); path.moveTo(x+points[0][0],y+points[0][1])
            for px,py in points[1:]: path.lineTo(x+px,y+py)
            pdf.drawPath(path)
    for kind,value,lx,ly in labels:
        cx,cy=x+lx,y+ly
        size=8
        width=(pdf.stringWidth(value,'Helvetica-Bold',size)+4 if kind=='angulo'
               else max(25,len(value)*size*.6+12))
        height=22 if kind=='medida' and '/' in value else (11 if kind=='angulo' else 14)
        pdf.setFillGray(1); pdf.rect(cx-width/2,cy-height/2,width,height,stroke=0,fill=1)
        pdf.setFillGray(0); pdf.setStrokeGray(0); pdf.setLineWidth(.6)
        if kind=='medida':
            expressao(pdf,value,cx-3,cy,size)
            pdf.setFont('Helvetica',6); pdf.drawString(cx+width/2-7,cy-2,'m')
        else:
            pdf.setFont('Helvetica-Bold',size); pdf.drawCentredString(cx,cy-3,value)
    pdf.restoreState()


def desenhar_preview(canvas,t,x,y,w,h):
    # Mesma geometria do PDF; ampliação uniforme dos traços e rótulos.
    scale=max(1,w/220)
    lines,labels=anotacoes(t,w/scale,h/scale)
    for width,color in ((3,'white'),(1,'black')):
        for points,_ in lines:
            coords=[v for px,py in points for v in (x+px*scale,y+h-py*scale)]
            canvas.create_line(*coords,fill=color,width=width*scale)
    for kind,value,lx,ly in labels:
        label=value+' m' if kind=='medida' else value
        item=canvas.create_text(x+lx*scale,y+h-ly*scale,text=label,
                               fill='black',font=('Arial',max(9,round(8*scale)),'bold'))
        bounds=canvas.bbox(item)
        box=canvas.create_rectangle(bounds[0]-3,bounds[1]-2,bounds[2]+3,bounds[3]+2,
                                    fill='white',outline='white')
        canvas.tag_raise(item,box)
