"""Questões de Euler: contagens exatas, independentes das ilustrações."""
from pathlib import Path
import re

EULER='Relação de Euler'
MEDIDAS='Áreas e volumes'
MANUAL='Informar quantidades'
PREDEFINIDO='Sólido predefinido'
CAMPOS={'V':'vértices','A':'arestas','F':'faces'}
# Nome: vértices, arestas, faces, arquivo da ilustração.
SOLIDOS={
    'Tetraedro':(4,6,4,'tetraedro'),
    'Cubo':(8,12,6,'cubo'),
    'Octaedro':(6,12,8,'octaedro'),
    'Dodecaedro':(20,30,12,'dodecaedro'),
    'Icosaedro':(12,30,20,'icosaedro'),
    'Prisma triangular':(6,9,5,'prisma_triangular'),
    'Prisma pentagonal':(10,15,7,'prisma_pentagonal'),
    'Prisma hexagonal':(12,18,8,'prisma_hexagonal'),
    'Pirâmide quadrangular':(5,8,5,'piramide_quadrada'),
    'Pirâmide pentagonal':(6,10,6,'piramide_pentagonal'),
    'Tetraedro truncado':(12,18,8,'tetraedro_truncado'),
}


def contagens(q):
    if q.euler_descobrir not in CAMPOS: raise ValueError('Escolha V, A ou F para descobrir.')
    if type(q.incluir_imagem) is not bool: raise ValueError('Opção de imagem inválida.')
    if q.euler_origem==PREDEFINIDO:
        if q.euler_solido not in SOLIDOS: raise ValueError('Escolha um poliedro predefinido.')
        return dict(zip(CAMPOS,SOLIDOS[q.euler_solido][:3]))
    if q.euler_origem!=MANUAL: raise ValueError('Escolha a origem dos dados de Euler.')
    valores={}
    for key in CAMPOS:
        if key==q.euler_descobrir: continue
        s=getattr(q,'euler_'+key.lower())
        if not isinstance(s,str) or not re.fullmatch(r'[0-9]{1,6}',s.strip()):
            raise ValueError(f'{key}: informe uma quantidade inteira positiva, até 100000.')
        valores[key]=int(s)
    if q.euler_descobrir=='V': valores['V']=2+valores['A']-valores['F']
    elif q.euler_descobrir=='A': valores['A']=valores['V']+valores['F']-2
    else: valores['F']=2+valores['A']-valores['V']
    v,a,f=(valores[k] for k in CAMPOS)
    if not (4<=v<=100000 and 6<=a<=100000 and 4<=f<=100000 and 3*v<=2*a and 3*f<=2*a):
        raise ValueError('Quantidades incompatíveis com um poliedro convexo: V e F ≥ 4, A ≥ 6, 3V ≤ 2A e 3F ≤ 2A; limite 100000.')
    return valores


def enunciado(q):
    dados=contagens(q)
    conhecido=' e '.join(f'{dados[k]} {nome}' for k,nome in CAMPOS.items() if k!=q.euler_descobrir)
    sujeito=f'O sólido {q.euler_solido.lower()}' if q.euler_origem==PREDEFINIDO else 'Um poliedro convexo'
    return f'{sujeito} possui {conhecido}. Determine o número de {CAMPOS[q.euler_descobrir]} usando a relação de Euler.'


def apoio(q):
    d=contagens(q)
    return (f'V = {d["V"]} | A = {d["A"]} | F = {d["F"]}\n'
            f'Conferência: V - A + F = {d["V"]} - {d["A"]} + {d["F"]} = 2.\n'
            f'Resposta: {q.euler_descobrir} = {d[q.euler_descobrir]}. Esse valor não aparece no PDF.')


def imagem(q):
    if q.euler_origem!=PREDEFINIDO or not q.incluir_imagem:return None
    contagens(q)
    return Path(__file__).parent/'assets'/'poliedros_euler_estudos'/(SOLIDOS[q.euler_solido][3]+'.png')


def desenhar_imagem(pdf,q,rect):
    from reportlab.lib.utils import ImageReader
    path=imagem(q)
    if not path:return
    x,y,w,h=rect
    size=min(w-8,h-18)
    pdf.drawImage(ImageReader(str(path)),x+(w-size)/2,y+18,width=size,height=size,mask='auto')
    pdf.setFillColorRGB(0,0,0);pdf.setFont('Helvetica',6)
    pdf.drawCentredString(x+w/2,y+5,'Ilustração: nem todas as arestas são visíveis.')
