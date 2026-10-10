"""Acervo de 29 figuras: medidas suficientes, regiões e cálculos exatos."""
from dataclasses import dataclass,field,replace
from pathlib import Path
from functools import lru_cache
from xml.sax.saxutils import escape
import json
import random
import math
import sympy as sp
from numeros_exatos import ler,rotulo

PASTA=Path(__file__).parent/'assets'/'geometria_plana'
CATALOGO=json.loads((PASTA/'catalogo.json').read_text(encoding='utf-8'))['figuras']
PEDIDOS=('Área','Perímetro/comprimento','Área e perímetro/comprimento')
REGIOES=('Disco central hachurado','Anel entre os círculos','Disco maior')
# Campos: chave, significado geométrico, valor inicial. As descrições fixam a
# construção, evitando inferir simetrias ou alturas apenas pela ilustração.
ESPECIFICACOES=[
 ([('a','Lado','8')],'Quadrado.'),
 ([('b','Base','12'),('h','Altura','7')],'Retângulo horizontal.'),
 ([('b','Base','7'),('h','Altura','12')],'Retângulo vertical.'),
 ([('b','Cateto horizontal','6'),('h','Cateto vertical','8')],'Triângulo retângulo.'),
 ([('b','Base','12'),('h','Altura relativa à base','8')],'Triângulo isósceles; a altura divide a base ao meio.'),
 ([('r','Raio','5')],'Círculo.'),
 ([('b','Largura total','12'),('h','Altura total','14'),('t','Largura do braço vertical','4'),('u','Altura do braço horizontal','5')],'Figura em L formada por dois retângulos perpendiculares, alinhados à esquerda e embaixo.'),
 ([('b','Largura da barra superior','14'),('h','Altura total','12'),('t','Espessura da barra superior','4'),('u','Largura da haste','5')],'Figura em T com barra superior e haste retangulares; a haste é centralizada.'),
 ([('b','Largura do retângulo','12'),('h','Altura do retângulo','8'),('t','Altura do telhado triangular','5')],'Retângulo encimado por um triângulo isósceles cuja base coincide com a largura do retângulo.'),
 ([('b','Largura do retângulo','10'),('h','Altura da parte retangular','6')],'Retângulo encimado por um semicírculo cujo diâmetro coincide com a largura do retângulo.'),
 ([('b','Base do triângulo','10'),('h','Altura do triângulo','8')],'Triângulo isósceles unido a um semicírculo. A base do triângulo coincide com o diâmetro do semicírculo.'),
 ([('R','Raio maior','8'),('r','Raio menor','3')],'Dois círculos concêntricos.'),
 ([('a','Lado','6')],'Hexágono regular.'),
 ([('b','Base maior','14'),('c','Base menor','8'),('h','Altura','8')],'Trapézio retângulo; o lado esquerdo é perpendicular às bases.'),
 ([('b','Largura do retângulo','14'),('h','Altura do retângulo','8'),('c','Base do triângulo superior','7'),('t','Altura do triângulo superior','4')],'Retângulo com um triângulo retângulo sobre a parte esquerda do topo. O cateto vertical fica alinhado ao lado esquerdo do retângulo.'),
 ([('a','Lado do quadrado','10')],'Círculo inscrito no quadrado, tangente aos quatro lados. Considere somente a região hachurada, externa ao círculo.'),
 ([('a','Lado do quadrado central','6'),('t','Altura de cada triângulo','5')],'Estrela formada por um quadrado e quatro triângulos isósceles congruentes externos, um em cada lado do quadrado. Não conte as divisões internas no contorno.'),
 ([('b','Comprimento da haste retangular','10'),('h','Altura da haste','6'),('B','Base vertical da ponta triangular','10'),('t','Altura horizontal da ponta triangular','8')],'Seta formada por retângulo e triângulo isósceles. A base vertical do triângulo é maior que a altura da haste e está centralizada em relação a ela.'),
 ([('b','Comprimento da parte retangular','12'),('h','Altura da parte retangular','8')],'Retângulo com dois semicírculos laterais externos. Cada diâmetro coincide com a altura do retângulo.'),
 ([('r','Raio do semicírculo maior','8')],'Coração formado por um semicírculo inferior e dois semicírculos superiores iguais. Cada raio menor é metade do raio maior; os dois diâmetros menores, juntos, coincidem com o diâmetro maior.'),
 ([('b','Base do triângulo inferior','12'),('h','Altura do triângulo inferior','9'),('t','Altura de cada triângulo superior','4')],'Coração poligonal formado por um triângulo isósceles inferior e dois triângulos isósceles superiores congruentes. Cada base superior ocupa metade da base inferior.'),
 ([('a','Lado do quadrado central','8')],'Quadrado com quatro semicírculos externos, um sobre cada lado. Cada diâmetro coincide com um lado do quadrado; as divisões internas não pertencem ao contorno.'),
 ([('b','Largura total da cruz','14'),('h','Altura total da cruz','12'),('t','Largura comum dos braços','4')],'Cruz formada pela união de dois retângulos perpendiculares e centralizados, com braços de mesma largura.'),
 ([('b','Largura externa','14'),('h','Altura externa','12'),('u','Largura do recorte','6'),('t','Profundidade do recorte','8')],'Retângulo com recorte retangular central aberto no topo, formando um U.'),
 ([('b','Largura do retângulo','18'),('h','Altura do retângulo','10'),('r','Raio do recorte','4')],'Retângulo com recorte semicircular central no lado superior. Considere a região que resta.'),
 ([('R','Raio externo','8'),('r','Raio interno','4')],'Semi-anel entre dois semicírculos concêntricos, fechado por dois segmentos retilíneos na linha dos diâmetros.'),
 ([('b','Largura da placa','18'),('h','Altura da placa','12'),('r','Raio do furo','3')],'Placa retangular com furo circular central. Considere somente a região hachurada, excluindo o disco.'),
 ([('b','Base maior do trapézio','16'),('c','Base menor do trapézio','10'),('h','Altura do trapézio','8')],'Trapézio isósceles encimado por um semicírculo cujo diâmetro coincide com a base menor.'),
 ([('a','Lado do quadrado','12'),('b','Base do recorte triangular','6'),('h','Profundidade do recorte','4')],'Quadrado com recorte triangular isósceles central aberto no topo. A base do recorte fica sobre o lado superior; considere a região restante.'),
]
FIGURAS={f['arquivo']:dict(f,campos=spec[0],construcao=spec[1]) for f,spec in zip(CATALOGO,ESPECIFICACOES)}
NOMES={f['nome']:key for key,f in FIGURAS.items()}


def campos(figura,circular='Raio'):
    if figura not in FIGURAS:raise ValueError('Escolha uma figura do acervo.')
    if circular not in ('Raio','Diâmetro'):raise ValueError('Escolha raio ou diâmetro.')
    resultado=[]
    for key,label,_ in FIGURAS[figura]['campos']:
        if circular=='Diâmetro' and key in ('r','R'):
            key={'r':'d','R':'D'}[key];label=label.replace('Raio','Diâmetro')
        resultado.append((key,label))
    return resultado


def padrao(figura,circular='Raio'):
    campos(figura,circular)
    return {({'r':'d','R':'D'}.get(k,k) if circular=='Diâmetro' else k):
            str(int(v)*2) if circular=='Diâmetro' and k in ('r','R') else v
            for k,_,v in FIGURAS[figura]['campos']}


def restricoes(n,d):
    def exigir(cond,texto):
        if not cond:raise ValueError(texto)
    if n==2:exigir(d['b']>d['h'],'No retângulo horizontal, a base deve ser maior que a altura.')
    if n==3:exigir(d['h']>d['b'],'No retângulo vertical, a altura deve ser maior que a base.')
    if n==7:exigir(d['t']<d['b'] and d['u']<d['h'],'Os braços do L devem ser menores que as dimensões totais correspondentes.')
    if n==8:exigir(d['t']<d['h'] and d['u']<d['b'],'A barra deve ser mais baixa que a figura; a haste deve ser mais estreita que a barra.')
    if n in (12,26):exigir(d['r']<d['R'],'O raio interno deve ser menor que o externo.')
    if n in (14,28):exigir(d['c']<d['b'],'A base menor deve ser menor que a base maior.')
    if n==15:exigir(d['c']<d['b'],'A base do triângulo superior deve ser menor que a largura do retângulo.')
    if n==18:exigir(d['B']>d['h'],'A base vertical da ponta deve ser maior que a altura da haste.')
    if n==23:exigir(d['t']<min(d['b'],d['h']),'A largura dos braços deve ser menor que a largura e a altura totais.')
    if n==24:exigir(d['u']<d['b'] and d['t']<d['h'],'O recorte deve ser mais estreito e menos profundo que o retângulo externo.')
    if n==25:exigir(2*d['r']<d['b'] and d['r']<d['h'],'O diâmetro do recorte deve ser menor que a largura, e seu raio menor que a altura.')
    if n==27:exigir(2*d['r']<min(d['b'],d['h']),'O diâmetro do furo deve ser menor que a largura e a altura da placa.')
    if n==29:exigir(d['b']<d['a'] and d['h']<d['a'],'A base e a profundidade do recorte devem ser menores que o lado do quadrado.')


@dataclass
class FiguraPlana:
    figura:str='01_quadrado'
    valores:dict=field(default_factory=lambda:{'a':'8'})
    pedido:str=PEDIDOS[2]
    unidade:str='cm'
    circular:str='Raio'
    regiao:str=REGIOES[0]
    incluir_imagem:bool=True

    def dados(self):
        if self.pedido not in PEDIDOS:raise ValueError('Escolha área, perímetro/comprimento ou ambos.')
        if self.unidade not in ('mm','cm','m'):raise ValueError('Escolha mm, cm ou m.')
        if self.regiao not in REGIOES:raise ValueError('Escolha uma região válida.')
        if type(self.incluir_imagem) is not bool:raise ValueError('Opção de imagem inválida.')
        fields=campos(self.figura,self.circular)
        if not isinstance(self.valores,dict) or set(self.valores)!={k for k,_ in fields}:
            raise ValueError('Preencha exatamente as medidas indicadas para esta figura.')
        d={}
        for key,label in fields:
            texto=self.valores[key]
            if not isinstance(texto,str) or len(texto)>40:raise ValueError(f'{label}: use até 40 caracteres.')
            value,num=ler(texto)
            if not 0<num<=100000:raise ValueError(f'{label}: use uma medida positiva, até 100000.')
            canonical={'d':'r','D':'R'}.get(key,key)
            d[canonical]=value/2 if key in ('d','D') else value
        restricoes(FIGURAS[self.figura]['numero'],d)
        return d

    def validar(self):self.dados()

    def enunciado(self):
        self.validar();n=FIGURAS[self.figura]['numero']
        intro=FIGURAS[self.figura]['construcao']
        if intro.rstrip('.').lower()==FIGURAS[self.figura]['nome'].lower():intro=''
        if n==12:intro+=f' Considere apenas: {self.regiao.lower()}.'
        medidas='; '.join(f'{label.lower()}: {escape(self.valores[key].strip())} {self.unidade}' for key,label in campos(self.figura,self.circular))
        if n==6:perimetro='o comprimento da circunferência'
        elif n==12 and self.regiao!=REGIOES[1]:perimetro='o comprimento da circunferência que limita o disco escolhido'
        elif n in (16,27) or (n==12 and self.regiao==REGIOES[1]):
            perimetro='o comprimento total das bordas da região indicada (inclua os contornos externos e internos)'
        else:perimetro='o perímetro da figura (todo o contorno, incluindo recortes e arcos, sem divisões internas)'
        alvo='a área da região indicada' if n in (12,16,27) else 'a área da figura'
        pergunta=alvo if self.pedido==PEDIDOS[0] else perimetro if self.pedido==PEDIDOS[1] else alvo+' e '+perimetro
        pi=' Deixe π na resposta quando necessário.' if n in (6,10,11,12,16,19,20,22,25,26,27,28) else ''
        escala=' Figura ilustrativa, sem escala.' if self.incluir_imagem else ''
        return f'<b>{escape(FIGURAS[self.figura]["nome"])}.</b> {intro} Medidas: {medidas}. Calcule {pergunta}.{pi}{escala}'


def grandezas(q):
    d=q.dados();n=FIGURAS[q.figura]['numero']
    return _calcular(n,tuple(sorted(d.items())),q.regiao)


@lru_cache(maxsize=256)
def _calcular(n,itens,regiao):
    d=dict(itens);a,b,c,h,t,u,r,R,B=(d.get(k,sp.Integer(0)) for k in ('a','b','c','h','t','u','r','R','B'))
    raiz=sp.sqrt;pi=sp.pi
    if n==1:A,P=a*a,4*a
    elif n in (2,3):A,P=b*h,2*(b+h)
    elif n==4:A,P=b*h/2,b+h+raiz(b*b+h*h)
    elif n==5:A,P=b*h/2,b+2*raiz(b*b/4+h*h)
    elif n==6:A,P=pi*r*r,2*pi*r
    elif n==7:A,P=b*u+t*(h-u),2*(b+h)
    elif n==8:A,P=b*t+u*(h-t),2*(b+h)
    elif n==9:A,P=b*h+b*t/2,b+2*h+2*raiz(b*b/4+t*t)
    elif n==10:A,P=b*h+pi*b*b/8,b+2*h+pi*b/2
    elif n==11:A,P=b*h/2+pi*b*b/8,2*raiz(b*b/4+h*h)+pi*b/2
    elif n==12:
        if regiao==REGIOES[0]:A,P=pi*r*r,2*pi*r
        elif regiao==REGIOES[1]:A,P=pi*(R*R-r*r),2*pi*(R+r)
        else:A,P=pi*R*R,2*pi*R
    elif n==13:A,P=3*raiz(3)*a*a/2,6*a
    elif n==14:A,P=(b+c)*h/2,b+c+h+raiz((b-c)**2+h*h)
    elif n==15:A,P=b*h+c*t/2,2*b+2*h-c+t+raiz(c*c+t*t)
    elif n==16:A,P=a*a-pi*a*a/4,4*a+pi*a
    elif n==17:A,P=a*a+2*a*t,8*raiz(a*a/4+t*t)
    elif n==18:A,P=b*h+B*t/2,2*b+B+2*raiz(B*B/4+t*t)
    elif n==19:A,P=b*h+pi*h*h/4,2*b+pi*h
    elif n==20:A,P=3*pi*r*r/4,2*pi*r
    elif n==21:A,P=b*(h+t)/2,2*raiz(b*b/4+h*h)+4*raiz(b*b/16+t*t)
    elif n==22:A,P=a*a+pi*a*a/2,2*pi*a
    elif n==23:A,P=t*(b+h)-t*t,2*(b+h)
    elif n==24:A,P=b*h-u*t,2*(b+h)+2*t
    elif n==25:A,P=b*h-pi*r*r/2,2*(b+h)-2*r+pi*r
    elif n==26:A,P=pi*(R*R-r*r)/2,pi*(R+r)+2*(R-r)
    elif n==27:A,P=b*h-pi*r*r,2*(b+h)+2*pi*r
    elif n==28:A,P=(b+c)*h/2+pi*c*c/8,b+2*raiz((b-c)**2/4+h*h)+pi*c/2
    elif n==29:A,P=a*a-b*h/2,4*a-b+2*raiz(h*h+b*b/4)
    else:raise ValueError('Figura desconhecida.')
    return sp.simplify(A),sp.simplify(P)


def apoio(q):
    try:
        area,perimetro=grandezas(q)
        def exibir(v):return rotulo(v).replace('pi','π')+f' ≈ {float(v):.4f}'.replace('.',',')
        return (f'Área: {exibir(area)} {q.unidade}²\nPerímetro/comprimento: {exibir(perimetro)} {q.unidade}\n'
                'Resultados apenas para conferência; não aparecem no PDF. Nas uniões, não se somam bordas internas; em furos, inclui-se a borda interna.'),True
    except (ValueError,OverflowError) as exc:return 'Confira: '+str(exc),False


def gerar(q,minimo=2,maximo=20,seed=None):
    if type(minimo) is not int or type(maximo) is not int or not 1<=minimo<=maximo<=1000:
        raise ValueError('Use limites inteiros: 1 ≤ mínimo ≤ máximo ≤ 1000.')
    fields=campos(q.figura,q.circular);rng=random.Random(seed);n=FIGURAS[q.figura]['numero']
    for _ in range(3000):
        valores={key:str(rng.randint(minimo,maximo)) for key,_ in fields}
        d={({'d':'r','D':'R'}.get(k,k)):int(v)/(2 if k in ('d','D') else 1) for k,v in valores.items()}
        try:restricoes(n,d)
        except ValueError:continue
        replace(q,valores=valores).validar()
        return valores
    raise ValueError('Não encontrei medidas compatíveis nesse intervalo. Amplie os limites. Os valores anteriores foram preservados.')


def imagem(q):return PASTA/(q.figura+'.png') if q.incluir_imagem else None


def tracos_concentricos(regiao):
    """Hachura da região pedida; coordenadas ilustrativas iguais às do acervo."""
    R=145;r=60
    externo=r if regiao==REGIOES[0] else R
    interno=r if regiao==REGIOES[1] else 0
    lines=[]
    for k in range(-204,205,12):
        delta=2*externo**2-k*k
        if delta<=0:continue
        lo=(k-math.sqrt(delta))/2;hi=(k+math.sqrt(delta))/2
        intervalos=[(lo,hi)]
        corte=2*interno**2-k*k
        if interno and corte>0:
            a=(k-math.sqrt(corte))/2;b=(k+math.sqrt(corte))/2
            intervalos=[(lo,a),(b,hi)]
        for a,b in intervalos:lines.append((200+a,200+k-a,200+b,200+k-b))
    return lines


@lru_cache(maxsize=3)
def miniatura_concentrica(regiao):
    from PIL import Image,ImageDraw
    im=Image.new('RGB',(400,400),'white');draw=ImageDraw.Draw(im)
    for line in tracos_concentricos(regiao):draw.line(line,fill='black',width=1)
    for r in (145,60):draw.ellipse((200-r,200-r,200+r,200+r),outline='black',width=3)
    im.thumbnail((200,200));return im


def desenhar_imagem(pdf,q,rect):
    from reportlab.lib.utils import ImageReader
    q.validar();path=imagem(q)
    if path is None:return
    x,y,w,h=rect;size=min(w-8,h-6)
    if FIGURAS[q.figura]['numero']==12:
        pdf.saveState();pdf.translate(x+(w-size)/2,y+(h-size)/2);pdf.scale(size/400,size/400)
        pdf.setStrokeColorRGB(0,0,0);pdf.setLineWidth(1.1)
        for x1,y1,x2,y2 in tracos_concentricos(q.regiao):pdf.line(x1,400-y1,x2,400-y2)
        pdf.setLineWidth(3.5)
        for r in (145,60):pdf.circle(200,200,r)
        pdf.restoreState();return
    pdf.drawImage(ImageReader(str(path)),x+(w-size)/2,y+(h-size)/2,width=size,height=size,mask='auto')


def desenhar_pagina(pdf,items,colunas,titulo):
    from listas import Lista,planejar,paragrafo,desenhar_item
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    if not 1<=len(items)<=12 or colunas not in (1,2,3):raise ValueError('Use até 12 figuras e até 3 por linha.')
    for q in items:q.validar()
    lista=Lista(titulo or 'Geometria plana',colunas,12,[(8,q) for q in items]);pages=planejar(lista)
    W,H=A4
    for n,page in enumerate(pages):
        if n:pdf.showPage()
        title=Paragraph(escape(lista.titulo),ParagraphStyle('titulo',fontName='Helvetica-Bold',fontSize=15,leading=18))
        _,height=title.wrap(W-60,60)
        if height>48:raise ValueError('Título muito longo.')
        title.drawOn(pdf,30,H-22-height)
        for index,x,y,w,h,th,gh in page:
            pdf.saveState();pdf.setStrokeGray(.7);pdf.roundRect(x,y,w,h,5)
            p,_=paragrafo(8,items[index],index+1,w);p.drawOn(pdf,x+10,y+h-12-th)
            if gh:desenhar_item(pdf,8,items[index],(x+5,y+5,w-10,h-th-22))
            pdf.restoreState()
        pdf.setFont('Helvetica',8);pdf.drawRightString(W-30,22,f'Página {n+1} de {len(pages)}')
