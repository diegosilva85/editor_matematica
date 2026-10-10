"""Cenários, perguntas e validação física da geometria espacial contextual."""
import math
from pathlib import Path
from xml.sax.saxutils import escape
from triangulos import medida

# Cada cena tem uma geometria definida, também representada na ilustração.
CENARIOS = {
    'Caixa de embalagem': ('Cubo', 'embalagem', ('Volume', 'Área total')),
    'Aquário sem tampa': ('Prisma retangular', 'aquario', ('Volume', 'Fundo e paredes', 'Área lateral')),
    'Lixeira cilíndrica aberta': ('Cilindro', 'lixeira', ('Volume', 'Fundo e paredes', 'Área lateral')),
    'Lata com rótulo': ('Cilindro', 'lata', ('Volume', 'Área total', 'Área lateral')),
    'Canteiro elevado': ('Prisma hexagonal', 'canteiro', ('Volume', 'Área lateral', 'Fundo e paredes')),
    'Barraca de camping': ('Prisma triangular', 'barraca', ('Volume', 'Área total', 'Sem piso')),
    'Casquinha de sorvete': ('Cone', 'casquinha', ('Volume', 'Área lateral')),
    'Cobertura de um quiosque': ('Pirâmide de base quadrada', 'quiosque', ('Volume', 'Área lateral')),
    'Embalagem tetraédrica': ('Tetraedro', 'tetraedro', ('Volume', 'Área total', 'Três faces')),
    'Bola decorativa': ('Esfera', 'bola', ('Volume', 'Área total')),
    'Peça mergulhada em aquário': ('Cubo', 'imersao_aquario', ('Volume deslocado', 'Elevação do nível', 'Nível final', 'Transbordamento', 'Volume pela elevação')),
    'Teste em tanque cilíndrico': ('Esfera', 'imersao_tanque', ('Volume deslocado', 'Elevação do nível', 'Nível final', 'Espaço até a borda', 'Transbordamento', 'Volume pela elevação')),
}
IMERSAO = tuple(CENARIOS)[-2:]
# Mantém os nomes antigos aceitos ao carregar JSON e amplia as escolhas da UI.
for _cenario, (_tipo, _imagem, _alvos) in tuple(CENARIOS.items()):
    if _cenario not in IMERSAO:
        CENARIOS[_cenario]=(_tipo,_imagem,tuple(dict.fromkeys((*_alvos,'Área total','Área disponível','Volume e área total','Volume e área disponível'))))

SUPERFICIES = {
    'Caixa de embalagem': 'de papel necessária para envolver todas as seis faces externas da caixa, sem sobreposição',
    'Aquário sem tampa': 'do fundo disponível para distribuir uma camada de cascalho, sem incluir as paredes',
    'Lixeira cilíndrica aberta': 'da superfície lateral externa disponível para pintura, sem incluir o fundo',
    'Lata com rótulo': 'da superfície lateral disponível para o rótulo, sem incluir as bases',
    'Canteiro elevado': 'da superfície horizontal disponível para plantio, correspondente à base hexagonal',
    'Barraca de camping': 'do piso retangular disponível para acomodar os ocupantes',
    'Casquinha de sorvete': 'da superfície lateral disponível para uma cobertura de chocolate, sem fechar a abertura circular',
    'Cobertura de um quiosque': 'das quatro faces triangulares disponíveis para instalação de telhas, sem incluir a base quadrada',
    'Embalagem tetraédrica': 'das três faces disponíveis para decoração, excluindo a face usada como base',
    'Bola decorativa': 'da superfície externa disponível para pintura',
}
PADRAO = dict(a='6', b='8', h='12', r='5', d='10', g='13',
              recipiente_a='30', recipiente_b='20', recipiente_r='15',
              recipiente_h='30', nivel='15', elevacao='1')


def campos_recipiente(q):
    if q.cenario not in IMERSAO: return []
    result=([('recipiente_a','Comprimento interno'),('recipiente_b','Largura interna')]
            if q.cenario==IMERSAO[0] else [('recipiente_r','Raio interno')])
    result += [('recipiente_h','Altura interna'),('nivel','Nível inicial')]
    if q.objetivo=='Volume pela elevação': result += [('elevacao','Elevação observada')]
    return result


def medidas(q):
    from solidos import campos
    return {k:medida(q.valores[k])[1] for k,_ in campos(q.tipo,q.circular,q.cone)}


def grandezas(q):
    v=medidas(q); a=v.get('a',0); b=v.get('b',0); h=v.get('h',0)
    r=v.get('r',v.get('d',0)/2); t=q.tipo
    if t=='Cubo': base=a*a; lateral=4*base; volume=a**3
    elif t=='Prisma retangular': base=a*b; lateral=2*(a+b)*h; volume=base*h
    elif t in ('Prisma triangular','Prisma hexagonal'):
        base=a*a*math.sqrt(3)*(1/4 if t=='Prisma triangular' else 3/2)
        lateral=(3 if t=='Prisma triangular' else 6)*a*h; volume=base*h
    elif t=='Cilindro': base=math.pi*r*r; lateral=2*math.pi*r*h; volume=base*h
    elif t=='Cone':
        g=v.get('g',math.hypot(r,h))
        if q.cone=='Geratriz': h=math.sqrt((g-r)*(g+r))
        base=math.pi*r*r; lateral=math.pi*r*g; volume=base*h/3
    elif t=='Pirâmide de base quadrada':
        base=a*a; lateral=2*a*math.hypot(h,a/2); volume=base*h/3
    elif t=='Tetraedro': base=math.sqrt(3)*a*a/4; lateral=3*base; volume=a**3/(6*math.sqrt(2))
    else: base=0; lateral=4*math.pi*r*r; volume=4*math.pi*r**3/3
    total=lateral+base*(2 if t.startswith('Prisma') or t in ('Cubo','Cilindro') else 1)
    total_objeto=(base+lateral if q.cenario in ('Aquário sem tampa','Lixeira cilíndrica aberta','Canteiro elevado') else
                  lateral if q.cenario in ('Casquinha de sorvete','Cobertura de um quiosque') else total)
    disponivel=(base if q.cenario in ('Aquário sem tampa','Canteiro elevado') else
                a*h if q.cenario=='Barraca de camping' else
                lateral if q.cenario in ('Lixeira cilíndrica aberta','Lata com rótulo','Casquinha de sorvete','Cobertura de um quiosque','Embalagem tetraédrica') else total)
    return {'Volume':volume,'Área total':total_objeto,'Área disponível':disponivel,'Área lateral':lateral,
            'Fundo e paredes':base+lateral,'Sem piso':total-a*h,'Três faces':lateral}


def imersao(q):
    v={k:medida(q.valores[k])[1] for k,_ in campos_recipiente(q)}
    base=(v['recipiente_a']*v['recipiente_b'] if q.cenario==IMERSAO[0]
          else math.pi*v['recipiente_r']**2)
    inverso=q.objetivo=='Volume pela elevação'
    volume=base*v['elevacao'] if inverso else grandezas(q)['Volume']
    # No problema inverso, o tamanho da peça é deduzido, não informado.
    tamanho=volume**(1/3) if q.tipo=='Cubo' else 2*(3*volume/(4*math.pi))**(1/3)
    capacidade=v['recipiente_h']; inicial=v['nivel']; livre=inicial+volume/base
    final=min(capacidade,livre)
    return dict(base=base,volume=volume,tamanho=tamanho,altura=capacidade,
                inicial=inicial,final=final,subida=final-inicial,
                excesso=max(0.,base*(livre-capacidade)),borda=capacidade-final,
                largura=min(v['recipiente_a'],v['recipiente_b']) if q.cenario==IMERSAO[0] else 2*v['recipiente_r'])


def validar(q):
    if q.cenario!='Sem contexto' and q.cenario not in CENARIOS: raise ValueError('Escolha um contexto válido.')
    if type(q.incluir_imagem) is not bool: raise ValueError('Opção de imagem inválida.')
    if type(q.mostrar_medidas) is not bool: raise ValueError('Opção de medidas na figura inválida.')
    if q.unidade not in ('cm','m'): raise ValueError('Use cm ou m.')
    if q.cenario=='Sem contexto': return
    tipo,_,objetivos=CENARIOS[q.cenario]
    if q.tipo!=tipo: raise ValueError(f'Este cenário representa {tipo}.')
    if q.objetivo not in objetivos: raise ValueError('Escolha uma pergunta compatível com o contexto.')
    try:
        if q.cenario in IMERSAO:
            d=imersao(q)
            if not all(math.isfinite(v) and abs(v)<1e100 for v in d.values()):
                raise ValueError('Medidas muito grandes para o cálculo.')
            if d['inicial']>d['altura']: raise ValueError('O nível inicial não pode ultrapassar a altura do recipiente.')
            if d['tamanho']>=min(d['largura'],d['altura']):
                raise ValueError('A peça deve caber com folga no recipiente. Aumente o recipiente ou reduza a peça/elevação.')
            if d['tamanho']>=d['final']:
                raise ValueError('Não há profundidade para submersão completa. Aumente o nível inicial ou reduza a peça.')
            if q.objetivo in ('Elevação do nível','Volume pela elevação') and d['excesso']>1e-8:
                raise ValueError('Para usar a elevação sem perda de água, aumente a altura do recipiente ou reduza o nível inicial.')
        elif not all(math.isfinite(v) and abs(v)<1e100 for v in grandezas(q).values()):
            raise ValueError('Medidas muito grandes para o cálculo.')
    except (OverflowError,ZeroDivisionError): raise ValueError('Medidas fora do intervalo de cálculo.') from None


def texto_medida(texto):
    # Preserva vírgulas e frações digitadas; evita glifos de raiz ausentes no PDF.
    return escape(texto.strip().replace('√','raiz de '))


def enunciado(q):
    from solidos import campos
    f=lambda key: texto_medida(q.valores[key])+' '+q.unidade
    introducoes={
      'Caixa de embalagem':'Uma loja encomendará caixas cúbicas fechadas para embalar seus produtos.',
      'Aquário sem tampa':'Uma escola pretende montar um aquário com formato de prisma retangular, aberto na parte superior.',
      'Lixeira cilíndrica aberta':'Uma oficina fabricará uma lixeira cilíndrica, com fundo e sem tampa, a partir de uma chapa metálica.',
      'Lata com rótulo':'Uma fábrica utiliza latas cilíndricas fechadas. Um rótulo cobre toda a superfície lateral, sem sobreposição.',
      'Canteiro elevado':'Uma comunidade construirá um canteiro elevado com formato de prisma reto de base hexagonal regular, aberto em cima.',
      'Barraca de camping':'Um grupo planeja uma barraca em forma de prisma reto, com duas faces triangulares equiláteras fechadas e piso retangular.',
      'Casquinha de sorvete':'Uma sorveteria utiliza casquinhas com formato de cone circular reto, abertas na base circular e fechadas na ponta.',
      'Cobertura de um quiosque':'O telhado de um quiosque será modelado por uma pirâmide reta de base quadrada, sem beirais. A base horizontal não recebe telhas.',
      'Embalagem tetraédrica':'Uma empresa desenvolveu uma embalagem fechada em forma de tetraedro regular, com quatro faces triangulares equiláteras.',
      'Bola decorativa':'Um artesão produzirá uma peça decorativa maciça em forma de esfera e pintará sua superfície externa.',
    }
    if q.cenario in IMERSAO:
        recipiente=('um aquário de base retangular, com comprimento interno '+f('recipiente_a')+' e largura interna '+f('recipiente_b')
                    if q.cenario==IMERSAO[0] else 'um tanque cilíndrico de raio interno '+f('recipiente_r'))
        texto=f'Em uma experiência, utiliza-se {recipiente}, altura interna {f("recipiente_h")} e nível inicial de água {f("nivel")}. '
        texto+=f'Uma peça maciça em forma de {q.tipo.lower()}, impermeável, é mantida totalmente submersa por um suporte de volume desprezível. '
        if q.objetivo=='Volume pela elevação':
            texto+=f'Sem transbordamento, o nível sobe {f("elevacao")}. Determine o volume da peça.'
        else:
            texto+='A peça tem '+', '.join(label.lower()+' de '+f(k) for k,label in campos(q.tipo,q.circular,q.cone))+'. '
            texto+={
              'Volume deslocado':'Determine o volume de água deslocado pela peça.',
              'Elevação do nível':'Determine quanto o nível da água sobe, sem transbordamento.',
              'Nível final':'Determine o nível final da água, medido a partir do fundo, considerando eventual transbordamento.',
              'Espaço até a borda':'Determine a distância vertical entre o nível final da água e a borda superior, considerando eventual transbordamento.',
              'Transbordamento':'Verifique se ocorre transbordamento e calcule o volume de água que transborda, se houver.'}[q.objetivo]
        return texto+' Desconsidere absorção de água e respingos.'
    labels=dict(campos(q.tipo,q.circular,q.cone))
    if q.cenario=='Barraca de camping': labels['h']='comprimento da barraca (distância entre as faces triangulares)'
    texto=introducoes[q.cenario]+' Considere as seguintes medidas: '+', '.join(label.lower()+' de '+f(k) for k,label in labels.items())+'. '
    if q.cenario=='Bola decorativa': texto+='Desconsidere perdas de material na fabricação. '
    else: texto+='As medidas de recipientes são internas. Despreze a espessura dos materiais, emendas e perdas. '
    pedidos={
      'Volume': 'Determine o volume '+('de material da peça.' if q.cenario=='Bola decorativa' else
                'sob o telhado, limitado pela base quadrada e pelas faces triangulares.' if q.cenario=='Cobertura de um quiosque' else
                'de terra necessário para preencher o canteiro até a borda.' if q.cenario=='Canteiro elevado' else 'interno disponível.'),
      'Área total':'Determine a área de toda a superfície '+('da esfera a ser pintada.' if q.tipo=='Esfera' else 'da embalagem.'),
      'Área lateral':'Determine a área '+{'Lata com rótulo':'do rótulo, sem incluir as bases.',
         'Casquinha de sorvete':'lateral de massa da casquinha, sem fechar a abertura circular.',
         'Cobertura de um quiosque':'das quatro faces triangulares que receberão telhas.',
         'Canteiro elevado':'das seis paredes laterais a serem revestidas, sem incluir o fundo.'}.get(q.cenario,'das paredes laterais, sem incluir o fundo ou uma tampa.'),
      'Fundo e paredes':'Determine a área de material para cobrir o fundo e todas as paredes, sem tampa. Conte cada superfície apenas uma vez.',
      'Sem piso':'Determine a área de tecido para as duas faces triangulares e as duas faces inclinadas, sem incluir o piso.',
      'Três faces':'Uma face será usada como base. Determine a área das outras três faces que receberão decoração.',
      'Área disponível':'Determine a área '+SUPERFICIES[q.cenario]+'.',
    }
    pedidos['Área total']={
        'Aquário sem tampa':'Determine a área total de vidro: fundo e quatro paredes, sem tampa. Conte cada superfície apenas uma vez.',
        'Lixeira cilíndrica aberta':'Determine a área total de chapa: fundo circular e superfície lateral, sem tampa. Conte cada superfície apenas uma vez.',
        'Canteiro elevado':'Determine a área total de revestimento interno: fundo hexagonal e seis paredes, sem tampa.',
        'Casquinha de sorvete':'Determine a área total de massa da casquinha, correspondente apenas à superfície lateral. Não inclua um disco na abertura.',
        'Cobertura de um quiosque':'Determine a área total da cobertura: as quatro faces triangulares, sem incluir a base horizontal.',
        'Barraca de camping':'Determine a área total de tecido, incluindo o piso, as duas faces triangulares e as duas faces inclinadas.',
    }.get(q.cenario,pedidos['Área total'].replace('a área de toda','a área total de toda'))
    pedidos['Volume e área total']=pedidos['Volume']+' '+pedidos['Área total']
    pedidos['Volume e área disponível']=pedidos['Volume']+' '+pedidos['Área disponível']
    return texto+pedidos[q.objetivo]


def apoio(q):
    q.validar()
    if q.cenario in IMERSAO:
        d=imersao(q)
        return (f'Volume da peça: {d["volume"]:.5g} {q.unidade}³ | Nível final: {d["final"]:.5g} {q.unidade}\n'
                f'Transbordamento: {d["excesso"]:.5g} {q.unidade}³. Peça cabe e pode ficar totalmente submersa.')
    d=grandezas(q)
    resultado=''
    if q.cenario!='Sem contexto':
        alvo=q.objetivo.replace('Volume e área','Área')
        resultado=f'Resultado de {alvo.lower()} (aproximado): {d[alvo]:.5g} '+q.unidade+('³' if alvo=='Volume' else '²')
    return f'Volume: {d["Volume"]:.5g} {q.unidade}³ | Área total considerada: {d["Área total"]:.5g} {q.unidade}²\n'+resultado


def imagem(q):
    if q.cenario=='Sem contexto' or not q.incluir_imagem: return None
    return Path(__file__).resolve().parent/'assets'/'contextos_solidos'/(CENARIOS[q.cenario][1]+'.png')


def anotacoes(q):
    """Rótulos dos dados fornecidos; coordenadas na imagem, com y para baixo.

    Não calcula medidas derivadas nem revela dimensões da peça no problema
    inverso. Os níveis inicial/observado são notas, não cotas do nível desenhado.
    """
    from solidos import campos
    if not imagem(q) or not q.mostrar_medidas: return []
    posicoes={
        'Caixa de embalagem': {'a':(.50,.87,.59,.72)},
        'Aquário sem tampa': {'a':(.23,.09,.50,.44),'b':(.18,.54,.24,.41),'h':(.80,.09,.84,.29)},
        'Lixeira cilíndrica aberta': {'r':(.24,.10,.50,.22),'d':(.24,.10,.50,.22),'h':(.84,.65,.69,.53)},
        'Lata com rótulo': {'r':(.24,.10,.50,.22),'d':(.24,.10,.50,.22),'h':(.82,.65,.79,.52)},
        'Canteiro elevado': {'a':(.46,.91,.49,.76),'h':(.83,.61,.79,.63)},
        'Barraca de camping': {'a':(.24,.91,.31,.78),'h':(.75,.13,.71,.49)},
        'Casquinha de sorvete': {'r':(.23,.13,.50,.21),'d':(.23,.13,.50,.21),'h':(.81,.46,.51,.52),'g':(.81,.65,.56,.63)},
        'Cobertura de um quiosque': {'a':(.49,.48,.49,.38),'h':(.79,.09,.51,.25)},
        'Embalagem tetraédrica': {'a':(.28,.86,.32,.75)},
        'Bola decorativa': {'r':(.81,.32,.52,.43),'d':(.81,.32,.52,.43)},
    }
    campos_dados=campos(q.tipo,q.circular,q.cone)
    if q.cenario in IMERSAO:
        campos_dados=[] if q.objetivo=='Volume pela elevação' else campos_dados
        campos_dados=campos_dados+campos_recipiente(q)
        # Notas explicitamente identificadas; não confundem o nível inicial
        # com o nível final ilustrativo, que pode ser a incógnita.
        slots=[(.23,.09),(.77,.09),(.23,.88),(.77,.88),(.23,.34),(.77,.34)]
        result=[]
        for i,(key,label) in enumerate(campos_dados):
            label={'a':'Aresta da peça','r':'Raio da peça','d':'Diâmetro da peça',
                   'recipiente_a':'Compr. recipiente','recipiente_b':'Larg. recipiente',
                   'recipiente_h':'Altura recipiente','recipiente_r':'Raio recipiente',
                   'nivel':'Nível inicial','elevacao':'Elevação observada'}[key]
            result.append((key,label,q.valores[key],slots[i],None))
        return result
    result=[]
    for key,label in campos_dados:
        if q.cenario=='Barraca de camping' and key=='h': label='Comprimento'
        px,py,ax,ay=posicoes[q.cenario][key]
        result.append((key,label,q.valores[key],(px,py),(ax,ay)))
    return result


def desenhar_anotacoes(pdf,q,rect):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    x,y,w,h=rect
    style=ParagraphStyle('medida',fontName='Helvetica-Bold',fontSize=7,leading=8,alignment=TA_CENTER)
    pdf.saveState(); pdf.setLineWidth(.6); pdf.setStrokeColorRGB(0,0,0)
    for key,label,value,(px,py),anchor in anotacoes(q):
        p=Paragraph(escape(label)+': '+texto_medida(value)+' '+q.unidade,style)
        plain=label+': '+value.strip().replace('√','raiz de ')+' '+q.unidade
        bw=min(100,w*.43,max(30,pdf.stringWidth(plain,'Helvetica-Bold',7)+2)); _,bh=p.wrap(bw,1000)
        lx=min(max(x+px*w-bw/2,x+3),x+w-bw-3)
        ly=min(max(y+(1-py)*h-bh/2,y+3),y+h-bh-3)
        if anchor:
            ax=x+anchor[0]*w; ay=y+(1-anchor[1])*h
            pdf.line(lx+bw/2,ly+bh/2,ax,ay)
            pdf.setFillColorRGB(0,0,0);pdf.circle(ax,ay,1,stroke=0,fill=1)
        pdf.setFillColorRGB(1,1,1);pdf.roundRect(lx-2,ly-2,bw+4,bh+4,2,stroke=0,fill=1)
        p.drawOn(pdf,lx,ly)
    pdf.restoreState()


def desenhar_imagem(pdf,q,rect):
    path=imagem(q)
    if path:
        x,y,w,h=rect
        from PIL import Image
        with Image.open(path) as im: iw,ih=im.size
        scale=min(w/iw,max(1,h-12)/ih); dw,dh=iw*scale,ih*scale
        image_rect=(x+(w-dw)/2,y+12+(h-12-dh)/2,dw,dh)
        pdf.drawImage(str(path),*image_rect,mask='auto')
        desenhar_anotacoes(pdf,q,image_rect)
        pdf.setFillColorRGB(.35,.35,.35); pdf.setFont('Helvetica',6)
        pdf.drawCentredString(x+w/2,y+3,'Ilustração sem escala; considere as medidas do enunciado.')


def desenhar_paginas(pdf,items,colunas,titulo):
    from listas import Lista, planejar, paragrafo, desenhar_item
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    if not 1<=len(items)<=12 or colunas not in (1,2,3): raise ValueError('Use até 12 questões e até 3 por linha.')
    for q in items: q.validar()
    lista=Lista(titulo,colunas,4,[(4,q) for q in items]); pages=planejar(lista)
    W,H=A4
    for n,page in enumerate(pages):
        if n: pdf.showPage()
        header=Paragraph(escape(titulo or 'Geometria espacial'),ParagraphStyle('titulo',fontName='Helvetica-Bold',fontSize=15,leading=18))
        _,height=header.wrap(W-60,60)
        if height>48: raise ValueError('Título muito longo.')
        header.drawOn(pdf,30,H-22-height)
        for index,x,y,w,h,th,gh in page:
            q=items[index]; pdf.saveState()
            pdf.setStrokeColorRGB(.72,.76,.8); pdf.roundRect(x,y,w,h,5)
            p,_=paragrafo(4,q,index+1,w); p.drawOn(pdf,x+10,y+h-12-th)
            if gh: desenhar_item(pdf,4,q,(x+5,y+5,w-10,h-th-22))
            pdf.restoreState()
        pdf.setFont('Helvetica',8); pdf.drawRightString(W-30,22,f'Página {n+1} de {len(pages)}')
