"""Cotas alinhadas à geometria do acervo (coordenadas SVG 400 × 400)."""
from io import BytesIO
from dataclasses import replace
from geometria_plana import FIGURAS

# chave, início, fim, posição da linha de cota (x para vertical, y para horizontal)
COTAS={
1:[('a',(75,325),(325,325),370)],
2:[('b',(45,290),(355,290),345),('h',(45,110),(45,290),0)],
3:[('b',(110,355),(290,355),395),('h',(110,45),(110,355),55)],
4:[('b',(70,330),(340,330),375),('h',(70,60),(70,330),15)],
5:[('b',(55,325),(345,325),375),('h',(200,65),(200,325),200)],
6:[('r',(200,200),(345,200),200)],
7:[('b',(65,345),(335,345),390),('h',(65,55),(65,345),15),('t',(65,55),(175,55),15),('u',(335,235),(335,345),390)],
8:[('b',(45,65),(355,65),15),('h',(45,65),(45,335),0),('t',(355,65),(355,160),400),('u',(155,335),(245,335),380)],
9:[('b',(75,335),(325,335),380),('h',(75,155),(75,335),20),('t',(200,60),(200,155),200)],
10:[('b',(80,330),(320,330),380),('h',(80,185),(80,330),25)],
11:[('b',(65,185),(335,185),185),('h',(200,185),(200,350),200)],
12:[('R',(200,200),(55,200),200),('r',(200,200),(200,260),200)],
13:[('a',(325.574,127.5),(325.574,272.5),375)],
14:[('b',(65,305),(350,305),360),('c',(65,110),(250,110),65),('h',(65,110),(65,305),15)],
15:[('b',(65,325),(335,325),375),('h',(335,155),(335,325),385),('c',(65,155),(210,155),155),('t',(65,70),(65,155),15)],
16:[('a',(60,340),(340,340),390)],
17:[('a',(145,255),(255,255),255),('t',(200,40),(200,145),200)],
18:[('b',(45,255),(235,255),385),('h',(45,145),(45,255),0),('B',(235,70),(235,330),400),('t',(235,200),(355,200),200)],
19:[('b',(125,110),(275,110),65),('h',(125,110),(125,290),125)],
20:[('r',(200,180),(340,180),180)],
21:[('b',(50,175),(350,175),175),('h',(200,175),(200,340),200),('t',(125,90),(125,175),125)],
22:[('a',(130,130),(270,130),130)],
23:[('b',(45,250),(355,250),400),('h',(45,45),(45,355),0),('t',(150,45),(250,45),0)],
24:[('b',(60,340),(340,340),390),('h',(60,60),(60,340),10),('u',(145,60),(255,60),15),('t',(200,60),(200,255),200)],
25:[('b',(45,315),(355,315),365),('h',(45,90),(45,315),0),('r',(200,90),(200,175),200)],
26:[('R',(200,280),(45,280),330),('r',(200,280),(290,280),280)],
27:[('b',(40,310),(360,310),365),('h',(40,90),(40,310),-10),('r',(200,200),(275,200),200)],
28:[('b',(45,330),(355,330),380),('c',(110,175),(290,175),175),('h',(200,175),(200,330),200)],
29:[('a',(340,60),(340,340),390),('b',(130,60),(270,60),15),('h',(200,60),(200,170),200)],
}


def anotacoes(q):
    result=[]
    for key,p1,p2,offset in COTAS[FIGURAS[q.figura]['numero']]:
        if key in ('r','R') and q.circular=='Diâmetro':
            key={'r':'d','R':'D'}[key]
            p1=(2*p1[0]-p2[0],2*p1[1]-p2[1])
            if FIGURAS[q.figura]['numero']==25:
                p1,p2,offset=(115,90),(285,90),90
            elif FIGURAS[q.figura]['numero']==12 and key=='D':
                offset=400
        value=q.valores[key].strip()
        prefix=('r = ' if key in ('r','R') else 'd = ' if key in ('d','D') else '')
        result.append((key,prefix+value+' '+q.unidade,p1,p2,offset))
    return result


def desenhar(pdf,q,origem,scale):
    """Cotas vetoriais com etiquetas brancas, sem revelar medidas calculadas."""
    ox,oy=origem
    pdf.saveState();pdf.translate(ox,oy);pdf.scale(scale,scale)
    pdf.setStrokeColorRGB(0,0,0);pdf.setFillColorRGB(0,0,0)
    size=max(18,6.5/scale)
    for key,text,(x1,y1),(x2,y2),offset in anotacoes(q):
        vertical=x1==x2
        a=(offset,400-y1) if vertical else (x1,400-offset)
        b=(offset,400-y2) if vertical else (x2,400-offset)
        pdf.setLineWidth(.9);pdf.setDash(4,4)
        pdf.line(x1,400-y1,*a);pdf.line(x2,400-y2,*b)
        pdf.line(*a,*b);pdf.setDash()
        for x,y in (a,b):
            if vertical:pdf.line(x-4,y,x+4,y)
            else:pdf.line(x,y-4,x,y+4)
        pdf.saveState();pdf.translate((a[0]+b[0])/2,(a[1]+b[1])/2)
        if vertical:pdf.rotate(90)
        # Lado de fora ou da própria linha; fundo branco evita cruzar hachuras.
        fs=min(size,190/max(1,pdf.stringWidth(text,'Helvetica',size))*size)
        pdf.setFont('Helvetica',fs);width=pdf.stringWidth(text,'Helvetica',fs)
        pdf.setFillColorRGB(1,1,1);pdf.rect(-width/2-3,3,width+6,fs+5,stroke=0,fill=1)
        pdf.setFillColorRGB(0,0,0);pdf.drawCentredString(0,6,text);pdf.restoreState()
    pdf.restoreState()


def miniatura(q,tamanho=290):
    """A prévia usa o mesmo desenho e as mesmas cotas do PDF."""
    from reportlab.pdfgen.canvas import Canvas
    from geometria_plana import desenhar_imagem
    import pypdfium2 as pdfium
    q=replace(q,incluir_imagem=True)
    stream=BytesIO();pdf=Canvas(stream,pagesize=(tamanho,tamanho))
    desenhar_imagem(pdf,q,(0,0,tamanho,tamanho));pdf.save()
    with pdfium.PdfDocument(stream.getvalue()) as doc:
        page=doc[0];bitmap=page.render(scale=1.5)
        try:
            im=bitmap.to_pil().copy();im.thumbnail((tamanho,tamanho));return im
        finally:bitmap.close();page.close()
