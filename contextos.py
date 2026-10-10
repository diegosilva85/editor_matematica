"""Enunciados e ilustrações em preto e branco de situações de trigonometria.

As imagens detalhadas são compartilhadas pelo editor e pelo PDF; as primitivas
vetoriais antigas permanecem como fallback para instalações sem os assets.
"""
import math
from pathlib import Path
from xml.sax.saxutils import escape
from triangulos import medida

# Ordem das medidas: cateto horizontal, cateto vertical, hipotenusa.
CENARIOS={
 'Avião decolando': (
  'Durante um voo de treinamento, um avião decola de uma pista plana e passa a subir em uma trajetória retilínea. No trecho analisado, sua trajetória mantém um ângulo de {angulo}° com o solo horizontal. Desconsidere a curvatura da Terra e considere a altura medida a partir do nível da pista.',
  ('distância horizontal desde o ponto de decolagem','altura atingida pelo avião','distância percorrida pelo avião na subida')),
 'Barco atravessando o rio': (
  'Um barqueiro sai de uma margem para alcançar a margem oposta de um rio, cujas margens são retas e paralelas. O percurso efetivo do barco é retilíneo e forma um ângulo de {angulo}° com a direção perpendicular às margens. O barco chega a um ponto deslocado em relação ao ponto diretamente em frente à partida.',
  ('largura do rio','deslocamento ao longo da margem de chegada','distância percorrida pelo barco')),
 'Escada na parede': (
  'Para realizar um reparo na fachada de uma casa, um trabalhador apoia uma escada reta em uma parede vertical. O pé da escada está sobre um piso horizontal, e a escada forma com esse piso um ângulo de {angulo}°. Considere desprezíveis a espessura da escada e eventuais irregularidades da parede.',
  ('distância do pé da escada à parede','altura alcançada pela escada na parede','comprimento da escada')),
 'Sombra de um prédio': (
  'Em determinado horário, um prédio vertical projeta sua sombra sobre uma praça plana e horizontal. Nesse instante, os raios solares formam um ângulo de {angulo}° com o terreno. Considere o raio que passa pelo topo do prédio e atinge a extremidade da sombra, sem interferência de outros obstáculos.',
  ('comprimento da sombra','altura do prédio','trajeto do raio solar')),
 'Pessoa observando um prédio': (
  'Durante uma atividade de medição, uma pessoa observa o topo de um prédio vertical a partir de um terreno horizontal, no mesmo nível da base do prédio. A linha de visada forma um ângulo de elevação de {angulo}° com a horizontal que passa pelos seus olhos. Os olhos da pessoa estão a {extra} m do chão.',
  ('distância horizontal da pessoa ao prédio','altura total do prédio','distância dos olhos da pessoa ao topo do prédio')),
 'Antena e avião': (
  'Uma estação de comunicação acompanha um avião que voa acima de sua antena. O segmento retilíneo que liga o ponto de emissão ao avião forma um ângulo de {angulo}° com a horizontal. O ponto de emissão está a {extra} m acima de um terreno plano; a altura do avião deve ser medida em relação a esse terreno.',
  ('distância horizontal da antena à projeção do avião','altura do avião em relação ao terreno','distância do ponto de emissão ao avião')),
 'Terreno de uma chácara': (
  'O proprietário de uma chácara pretende planejar a divisão de um terreno retangular. Para isso, considera a diagonal que liga dois vértices opostos e que forma um ângulo de {angulo}° com o lado AB. O lado perpendicular a AB será chamado de BC. Considere as medidas sobre o plano do terreno.',
  ('comprimento do lado AB','comprimento do lado BC','comprimento da diagonal AC')),
 'Rampa de acesso': (
  'Uma equipe está estudando uma rampa retilínea que conecta um piso inferior a uma plataforma elevada. A rampa faz um ângulo de {angulo}° com o piso horizontal. Considere o desnível como a distância vertical entre os dois pisos e despreze a espessura do revestimento da rampa.',
  ('distância horizontal entre as extremidades da rampa','desnível entre os pisos','comprimento da rampa')),
 'Pipa no céu': (
  'Em um campo plano, uma pessoa observa sua pipa enquanto mantém a linha completamente esticada. Considere a linha retilínea, formando um ângulo de {angulo}° com a horizontal, e despreze sua curvatura e o tamanho da pipa. A mão que segura a linha está a {extra} m do chão.',
  ('distância horizontal entre a pessoa e a projeção da pipa','altura da pipa em relação ao chão','comprimento da linha esticada')),
 'Cabo de sustentação': (
  'Uma torre vertical é estabilizada por um cabo que liga seu topo a um ponto de ancoragem no chão. O terreno é horizontal, e o cabo, completamente esticado, forma um ângulo de {angulo}° com ele. Considere o cabo retilíneo e despreze suas espessuras e as dos pontos de fixação.',
  ('distância da base da torre ao ponto de ancoragem','altura da torre','comprimento do cabo')),
 'Teleférico': (
  'Em um trecho entre duas estações, um teleférico sobe seguindo uma trajetória considerada retilínea. Esse trecho forma um ângulo de {angulo}° com a horizontal. Para o estudo, desconsidere a curvatura do cabo e considere apenas a diferença de altura entre as extremidades do trecho.',
  ('distância horizontal entre as extremidades do trecho','desnível entre as estações','comprimento do trecho percorrido')),
 'Mergulhador': (
  'Durante um treinamento em águas tranquilas, um mergulhador parte da superfície e segue uma trajetória retilínea de descida. Seu percurso forma um ângulo de {angulo}° com a superfície horizontal da água. Considere a profundidade medida verticalmente a partir da superfície e despreze o deslocamento causado por correntes.',
  ('distância horizontal desde o ponto de partida','profundidade atingida','distância percorrida pelo mergulhador')),
}
EXTRAS={'Pessoa observando um prédio':'Altura dos olhos', 'Antena e avião':'Altura do ponto de emissão', 'Pipa no céu':'Altura da mão'}
IMAGENS=dict(zip(CENARIOS, ('aviao','barco','escada','sombra','pessoa','antena',
                          'chacara','rampa','pipa','cabo','teleferico','mergulhador')))


def caminho_imagem(nome):
    return Path(__file__).resolve().parent/'assets'/'contextos'/(IMAGENS[nome]+'.png')


def opcoes(cenario):
    return CENARIOS[cenario][1][:2] if cenario=='Sombra de um prédio' else CENARIOS[cenario][1]


def validar(t):
    if t.cenario not in CENARIOS: raise ValueError('Escolha um cenário.')
    if not math.isfinite(t.angulo) or not 0<t.angulo<90: raise ValueError('Use um ângulo entre 0° e 90°.')
    opts=opcoes(t.cenario)
    if t.dado_contexto not in opts or t.pedido_contexto not in opts or t.dado_contexto==t.pedido_contexto:
        raise ValueError('Escolha medidas diferentes para o dado e a pergunta.')
    value=medida(t.valor)[1]
    extra=medida(t.altura_extra)[1] if t.cenario in EXTRAS else 0
    if CENARIOS[t.cenario][1].index(t.dado_contexto)==1 and value<=extra:
        raise ValueError('A altura total deve ser maior que a altura dos olhos, da mão ou da antena.')


def enunciado(t):
    validar(t)
    texto=CENARIOS[t.cenario][0].format(angulo=f'{t.angulo:g}',extra=t.altura_extra)
    def com_artigo(medida):
        masculino=medida.startswith(('comprimento','deslocamento','desnível','trajeto'))
        return ('o ' if masculino else 'a ')+medida
    introducao='Considerando que' if t.dado_contexto.startswith('distância') else 'Sabendo que'
    texto+=f' {introducao} {com_artigo(t.dado_contexto)} é de {t.valor} m, determine {com_artigo(t.pedido_contexto)}.'
    if t.angulo not in (30,45,60): texto+=' Use calculadora e arredonde o resultado para duas casas decimais.'
    return texto


def cena(nome):
    """Primitivas normalizadas; ilustração de contexto, sem escala."""
    ops=[]
    def line(*pts): ops.append(('linha',list(pts)))
    def poly(*pts): ops.append(('poligono',list(pts)))
    def rect(x,y,w,h): poly((x,y),(x+w,y),(x+w,y+h),(x,y+h))
    def circ(x,y,r): ops.append(('circulo',(x,y,r)))
    def pessoa(x,y):
        circ(x,y+.16,.025); line((x,y+.13),(x,y+.06)); line((x-.04,y),(x,y+.06),(x+.04,y)); line((x-.045,y+.09),(x,y+.115),(x+.045,y+.09))
    def predio(x,y,w,h):
        rect(x,y,w,h)
        for j in range(3):
            for i in range(2): rect(x+.025+i*w*.48,y+.05+j*h*.27,w*.2,h*.12)
    def aviao(x,y):
        poly((x-.1,y-.02),(x-.025,y+.01),(x-.055,y+.085),(x-.015,y+.07),(x+.03,y+.025),(x+.1,y+.04),(x+.12,y+.025),(x+.03,y-.015),(x-.025,y-.09),(x-.055,y-.1),(x-.04,y-.025))
    line((.06,.12),(.94,.12))
    if nome in ('Avião decolando','Antena e avião'):
        aviao(.79,.72); line((.17,.53) if nome=='Antena e avião' else (.16,.2),(.68,.66))
        if nome=='Antena e avião':
            poly((.09,.12),(.17,.5),(.25,.12)); line((.12,.26),(.21,.36),(.15,.4)); circ(.17,.53,.025)
            for dx in (0,.04): line((.22+dx,.53),(.25+dx,.56),(.22+dx,.59))
        else:
            line((.06,.17),(.33,.17)); line((.1,.145),(.17,.145)); line((.21,.145),(.28,.145))
    elif nome=='Barco atravessando o rio':
        line((.14,.16),(.14,.86)); line((.86,.16),(.86,.86))
        for x,y in ((.28,.28),(.54,.23),(.32,.72),(.7,.77)): line((x,y),(x+.04,y+.015),(x+.08,y))
        poly((.57,.52),(.8,.52),(.75,.47),(.61,.47)); line((.67,.52),(.67,.73)); poly((.67,.72),(.76,.56),(.67,.56)); line((.2,.25),(.57,.48))
    elif nome in ('Escada na parede','Sombra de um prédio','Pessoa observando um prédio'):
        predio(.68,.12,.2,.67)
        if nome=='Escada na parede':
            line((.22,.12),(.65,.66)); line((.27,.12),(.7,.66))
            for j in range(1,7): line((.22+.43*j/7,.12+.54*j/7),(.27+.43*j/7,.12+.54*j/7))
        elif nome=='Sombra de um prédio':
            circ(.9,.91,.055)
            for j in range(8):
                a=j*math.pi/4; line((.9+.07*math.cos(a),.91+.07*math.sin(a)),(.9+.095*math.cos(a),.91+.095*math.sin(a)))
            poly((.15,.12),(.68,.12),(.59,.16)); line((.15,.12),(.68,.79))
        else: pessoa(.19,.12); line((.19,.28),(.68,.79))
    elif nome=='Terreno de uma chácara':
        poly((.12,.23),(.77,.23),(.9,.72),(.25,.72)); line((.12,.23),(.9,.72))
        rect(.35,.48,.14,.11); poly((.33,.59),(.42,.68),(.51,.59))
        for x in (.65,.73): line((x,.48),(x,.59)); circ(x,.63,.05)
    elif nome=='Rampa de acesso':
        poly((.14,.17),(.78,.17),(.78,.66)); line((.14,.28),(.78,.77)); line((.18,.21),(.18,.31)); line((.7,.61),(.7,.72)); rect(.78,.12,.14,.54)
    elif nome=='Pipa no céu':
        pessoa(.18,.12); poly((.74,.87),(.85,.73),(.74,.61),(.66,.73)); line((.74,.87),(.74,.61)); line((.66,.73),(.85,.73)); line((.74,.61),(.71,.55),(.77,.49)); line((.22,.22),(.74,.73))
    elif nome=='Cabo de sustentação':
        rect(.68,.12,.09,.68); line((.2,.12),(.72,.8)); line((.18,.12),(.22,.08))
        for j in range(5): line((.68,.15+.12*j),(.77,.27+.12*j))
    elif nome=='Teleférico':
        line((.1,.25),(.85,.8)); line((.16,.12),(.16,.3)); line((.83,.12),(.83,.81)); line((.53,.56),(.53,.44)); rect(.43,.29,.2,.15); rect(.46,.35,.14,.06)
    elif nome=='Mergulhador':
        for j in range(9): line((.08+j*.09,.83),(.12+j*.09,.85),(.17+j*.09,.83))
        circ(.63,.4,.035); line((.65,.37),(.76,.29),(.85,.3)); line((.73,.31),(.8,.22),(.89,.23)); line((.65,.35),(.59,.29)); rect(.7,.36,.08,.055); line((.18,.8),(.57,.45)); circ(.59,.52,.012); circ(.57,.58,.016)
    return ops


def dessiner(pdf,nome,x,y,w,h,questao=None):
    from reportlab.lib.colors import HexColor
    path=caminho_imagem(nome)
    if path.is_file():
        from PIL import Image
        with Image.open(path) as source: iw,ih=source.size
        scale=min(w/iw,h/ih)
        pdf.drawImage(str(path),x+(w-iw*scale)/2,y+(h-ih*scale)/2,
                      width=iw*scale,height=ih*scale,mask='auto')
        if questao is not None:
            from sobreposicoes import desenhar_pdf
            desenhar_pdf(pdf,questao,x+(w-iw*scale)/2,y+(h-ih*scale)/2,iw*scale,ih*scale)
        return
    pdf.setStrokeColor(HexColor('#000000')); pdf.setFillColor(HexColor('#ffffff')); pdf.setLineWidth(1)
    for kind,data in cena(nome):
        if kind=='circulo':
            cx,cy,r=data; pdf.ellipse(x+(cx-r)*w,y+(cy-r)*h,x+(cx+r)*w,y+(cy+r)*h,stroke=1,fill=0)
        else:
            p=pdf.beginPath(); p.moveTo(x+data[0][0]*w,y+data[0][1]*h)
            for px,py in data[1:]: p.lineTo(x+px*w,y+py*h)
            if kind=='poligono': p.close()
            pdf.drawPath(p,stroke=1,fill=int(kind=='poligono'))


def preview(canvas,nome,questao=None):
    canvas.delete('all')
    path=caminho_imagem(nome)
    if path.is_file():
        from PIL import Image, ImageTk
        width,height=int(canvas.cget('width')),int(canvas.cget('height'))
        with Image.open(path) as source:
            source.thumbnail((width,height),Image.Resampling.LANCZOS)
            canvas._contexto_image=ImageTk.PhotoImage(source,master=canvas)
            iw,ih=source.size
        canvas.create_image(width/2,height/2,image=canvas._contexto_image)
        if questao is not None:
            from sobreposicoes import desenhar_preview
            desenhar_preview(canvas,questao,(width-iw)/2,(height-ih)/2,iw,ih)
        return
    for kind,data in cena(nome):
        if kind=='circulo':
            x,y,r=data; canvas.create_oval((x-r)*220,(1-y-r)*150,(x+r)*220,(1-y+r)*150,outline='#000000')
        else:
            coords=[v for x,y in data for v in (x*220,(1-y)*150)]
            if kind=='poligono': canvas.create_polygon(*coords,fill='#ffffff',outline='#000000')
            else: canvas.create_line(*coords,fill='#000000',width=2)


def desenhar_pagina(pdf,items,colunas,titulo):
    """Até seis questões por página, em duas colunas e três linhas."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_JUSTIFY
    from triangulos import desenhar_quadro
    W,H=A4; cols=min(colunas,2); capacity=cols*3
    for start in range(0,len(items),capacity):
        if start: pdf.showPage()
        pdf.setFillColor(HexColor('#000000')); pdf.setFont('Helvetica-Bold',16)
        pdf.drawCentredString(W/2,H-35,(titulo or 'Trigonometria')[:65])
        pdf.setFont('Helvetica',8); pdf.drawString(30,H-53,'Resolva as questões. Ilustrações de contexto sem escala.')
        batch=items[start:start+capacity]
        rows=math.ceil(len(batch)/cols)
        cw=(W-60-(cols-1)*12)/cols; ch=(H-90)/rows
        for j,t in enumerate(batch):
            left=30+(j%cols)*(cw+12); bottom=H-70-(j//cols+1)*ch
            pdf.setStrokeColor(HexColor('#999999')); pdf.roundRect(left,bottom+8,cw,ch-14,6)
            if t.apresentacao!='Contextual':
                t.validar()
                desenhar_quadro(pdf,t,left,bottom+8,cw,ch-14,start+j)
                continue
            t.validar()
            text=f'<b>({chr(97+start+j)}) {escape(t.cenario)}</b><br/><br/>'+escape(enunciado(t))
            text=text.replace('√','&#8730;')
            style=ParagraphStyle('questao',fontName='Helvetica',fontSize=9,leading=11,
                                 alignment=TA_JUSTIFY,textColor=HexColor('#000000'))
            # Reserva espaço para a ilustração sem sobrepor texto e imagem.
            for size in (9,8.5,8,7.5):
                style.fontSize=size; style.leading=size+2
                p=Paragraph(text,style); _,height=p.wrap(cw-22,ch)
                if height<=ch-112: break
            if height>ch-112:
                raise ValueError('Enunciado muito longo para a página. Selecione uma coluna.')
            p.drawOn(pdf,left+11,bottom+ch-18-height)
            dessiner(pdf,t.cenario,left+11,bottom+16,cw-22,ch-height-42,questao=t)
