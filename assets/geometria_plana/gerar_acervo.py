"""Gera ilustrações vetoriais e PNGs; não modifica o aplicativo.

Fonte: desenhos da foto 20261010_164750.jpg, na ordem de leitura.
Requer ImageMagick (`convert`) para exportar os SVGs em PNG.
"""
from pathlib import Path
import html
import json
import math
import subprocess
import textwrap

DESTINO=Path(__file__).resolve().parent
FIGURAS=[]


def caminho(d,extra=''):
    return f'<path d="{d}" {extra}/>'


def poligono(pontos,extra=''):
    return '<polygon points="'+' '.join(f'{x:.4f},{y:.4f}' for x,y in pontos)+f'" {extra}/>'


def circulo(x,y,r,extra=''):
    return f'<circle cx="{x}" cy="{y}" r="{r}" {extra}/>'


def retangulo(x,y,w,h,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {extra}/>'


def hachura(cx,cy,r,caixa=None):
    """Segmentos exatos: disco interno ou retângulo menos disco, sem máscaras."""
    inicio,fim=(cx+cy-r*math.sqrt(2),cx+cy+r*math.sqrt(2)) if caixa is None else (caixa[0]+caixa[1],sum(caixa))
    segmentos=[]
    for t in range(math.ceil(inicio/12)*12,math.floor(fim/12)*12+1,12):
        k=t-cx-cy;delta=2*r*r-k*k
        disco=None if delta<0 else (cx+(k-math.sqrt(delta))/2,cx+(k+math.sqrt(delta))/2)
        if caixa is None:
            intervalos=[disco] if disco else []
        else:
            x,y,w,h=caixa;lo=max(x,t-y-h);hi=min(x+w,t-y)
            intervalos=[(lo,hi)] if disco is None else [(lo,min(hi,disco[0])),(max(lo,disco[1]),hi)]
        for a,b in intervalos:
            if b>a:segmentos.append(caminho(f'M {a:.5f} {t-a:.5f} L {b:.5f} {t-b:.5f}'))
    return '<g stroke-width="1.1">'+''.join(segmentos)+'</g>'


def adicionar(slug,nome,descricao,corpo):
    numero=len(FIGURAS)+1
    FIGURAS.append(dict(numero=numero,arquivo=f'{numero:02d}_{slug}',nome=nome,
                        origem='foto' if numero<=22 else 'nova',descricao=descricao,corpo=corpo))


adicionar('quadrado','Quadrado','Quatro lados iguais e quatro ângulos retos.',retangulo(75,75,250,250))
adicionar('retangulo_horizontal','Retângulo horizontal','Retângulo com base maior que a altura.',retangulo(45,110,310,180))
adicionar('retangulo_vertical','Retângulo vertical','Retângulo com altura maior que a base.',retangulo(110,45,180,310))
adicionar('triangulo_retangulo','Triângulo retângulo','Catetos vertical e horizontal, com ângulo reto no canto inferior esquerdo.',poligono([(70,60),(70,330),(340,330)]))
adicionar('triangulo_isosceles','Triângulo isósceles','Interpretação regularizada do segundo triângulo da primeira linha da foto.',poligono([(55,325),(200,65),(345,325)]))
adicionar('circulo','Círculo','Círculo simples, sem indicação de raio ou diâmetro.',circulo(200,200,145))
adicionar('forma_l','Figura em L','União de dois retângulos; recorte retangular no canto superior direito.',poligono([(65,55),(175,55),(175,235),(335,235),(335,345),(65,345)]))
adicionar('forma_t','Figura em T','Barra horizontal retangular com haste retangular central.',poligono([(45,65),(355,65),(355,160),(245,160),(245,335),(155,335),(155,160),(45,160)]))
adicionar('casa','Pentágono em forma de casa','Retângulo encimado por um triângulo isósceles.',poligono([(75,335),(325,335),(325,155),(200,60),(75,155)]))
adicionar('retangulo_semicirculo','Retângulo com semicírculo','Semicírculo superior cujo diâmetro coincide com o lado superior do retângulo.',caminho('M 80 330 L 80 185 A 120 120 0 0 1 320 185 L 320 330 Z'))
adicionar('semicirculo_triangulo','Semicírculo com triângulo','Semicírculo superior e triângulo isósceles inferior, unidos pelo diâmetro/base.',caminho('M 65 185 A 135 135 0 0 1 335 185 L 200 350 Z'))
adicionar('circulos_concentricos','Círculos concêntricos','Círculo maior e disco central hachurado, preservando a indicação da foto. O anel permanece branco.',hachura(200,200,60)+circulo(200,200,145)+circulo(200,200,60))
hexagono=[(200+145*math.cos(math.radians(-90+i*60)),200+145*math.sin(math.radians(-90+i*60))) for i in range(6)]
adicionar('hexagono','Hexágono regular','Seis lados iguais, com vértices superior e inferior.',poligono(hexagono))
adicionar('trapezio','Trapézio retângulo','Bases horizontais paralelas e lado esquerdo perpendicular às bases.',poligono([(65,110),(250,110),(350,305),(65,305)]))
adicionar('retangulo_triangulo_parcial','Retângulo com triângulo parcial','Retângulo com um triângulo retângulo sobre a parte esquerda do lado superior; preserva o topo inclinado e o trecho horizontal da foto.',poligono([(65,70),(210,155),(335,155),(335,325),(65,325)]))
adicionar('quadrado_circulo_inscrito','Quadrado com círculo inscrito','Círculo tangente aos quatro lados do quadrado; apenas os quatro cantos externos ao círculo são hachurados.',hachura(200,200,140,(60,60,280,280))+retangulo(60,60,280,280)+circulo(200,200,140))
adicionar('estrela_quatro_pontas','Estrela de quatro pontas','Quadrado central e quatro triângulos isósceles externos. Linhas tracejadas indicam o quadrado, como na foto.',poligono([(145,145),(200,40),(255,145),(360,200),(255,255),(200,360),(145,255),(40,200)])+retangulo(145,145,110,110,'stroke-dasharray="8 7" stroke-width="2.4"'))
adicionar('seta','Seta para a direita','Retângulo unido a um triângulo cuja base é maior que a altura do retângulo.',poligono([(45,145),(235,145),(235,70),(355,200),(235,330),(235,255),(45,255)]))
adicionar('capsula','Cápsula','Retângulo horizontal com dois semicírculos laterais de mesmo diâmetro.',caminho('M 125 110 L 275 110 A 90 90 0 0 1 275 290 L 125 290 A 90 90 0 0 1 125 110 Z'))
adicionar('coracao_arredondado','Coração de semicírculos','Um semicírculo inferior grande e dois semicírculos superiores menores; o fundo é arredondado, como no esboço.',caminho('M 60 180 A 70 70 0 0 1 200 180 A 70 70 0 0 1 340 180 A 140 140 0 0 1 60 180 Z'))
adicionar('coracao_poligonal','Coração poligonal','Triângulo inferior e dois triângulos superiores, formando um coração angular com entalhe central.',poligono([(50,175),(125,90),(200,175),(275,90),(350,175),(200,340)]))
adicionar('quadrado_quatro_semicirculos','Quadrado com quatro semicírculos','Quatro semicírculos externos, um sobre cada lado do quadrado central. As divisões internas são tracejadas, como na foto.',caminho('M 130 130 A 70 70 0 0 1 270 130 A 70 70 0 0 1 270 270 A 70 70 0 0 1 130 270 A 70 70 0 0 1 130 130 Z')+retangulo(130,130,140,140,'stroke-dasharray="8 7" stroke-width="2.4"'))

# Sete novas composições, com uniões e recortes de figuras básicas.
adicionar('cruz','Cruz de retângulos','União de dois retângulos perpendiculares, com braços de mesma largura.',poligono([(150,45),(250,45),(250,150),(355,150),(355,250),(250,250),(250,355),(150,355),(150,250),(45,250),(45,150),(150,150)]))
adicionar('forma_u','Figura em U','Retângulo grande com recorte retangular central aberto na parte superior.',poligono([(60,60),(145,60),(145,255),(255,255),(255,60),(340,60),(340,340),(60,340)]))
adicionar('retangulo_recorte_semicircular','Retângulo com recorte semicircular','Recorte de um semicírculo no centro do lado superior de um retângulo.',caminho('M 45 90 L 115 90 A 85 85 0 0 0 285 90 L 355 90 L 355 315 L 45 315 Z'))
adicionar('semi_anel','Semi-anel','Região entre dois semicírculos concêntricos, fechada por dois segmentos na mesma linha de base.',caminho('M 45 280 A 155 155 0 0 1 355 280 L 290 280 A 90 90 0 0 0 110 280 L 45 280 Z'))
adicionar('retangulo_furo_circular','Placa com furo circular','Retângulo com abertura circular central. A hachura indica somente a região da placa, excluindo o disco.',hachura(200,200,75,(40,90,320,220))+retangulo(40,90,320,220)+circulo(200,200,75))
adicionar('trapezio_semicirculo','Trapézio com semicírculo','Trapézio isósceles encimado por um semicírculo de diâmetro igual à base menor.',caminho('M 45 330 L 110 175 A 90 90 0 0 1 290 175 L 355 330 Z'))
adicionar('quadrado_recorte_triangular','Quadrado com recorte triangular','Quadrado com recorte triangular isósceles aberto no centro do lado superior.',poligono([(60,60),(130,60),(200,170),(270,60),(340,60),(340,340),(60,340)]))

DEFS=''


def svg(corpo,w=400,h=400):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'+DEFS+f'<rect width="{w}" height="{h}" fill="white"/><g fill="none" stroke="black" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">'+corpo+'</g></svg>'


def exportar(path,width):
    subprocess.run(['convert','-background','white','-density','240',str(path),'-resize',f'{width}x','-strip',str(path.with_suffix('.png'))],check=True,capture_output=True)


def painel(figuras,nome,colunas,titulo):
    cw=290;ch=300;w=cw*colunas;h=65+ch*math.ceil(len(figuras)/colunas)
    corpo=f'<text x="25" y="38" fill="black" stroke="none" font-family="DejaVu Sans" font-size="24">{titulo}</text>'
    for i,f in enumerate(figuras):
        x=(i%colunas)*cw;y=65+(i//colunas)*ch
        corpo+=f'<rect x="{x+8}" y="{y+8}" width="274" height="282" rx="8" stroke="#dddddd" stroke-width="1"/>'
        corpo+=f'<g transform="translate({x+35} {y+10}) scale(.55)">{f["corpo"]}</g>'
        for j,line in enumerate(textwrap.wrap(f'{f["numero"]:02d}. {f["nome"]}',29)):
            corpo+=f'<text x="{x+145}" y="{y+249+j*18}" text-anchor="middle" fill="black" stroke="none" font-family="DejaVu Sans" font-size="14">{html.escape(line)}</text>'
    path=DESTINO/(nome+'.svg');path.write_text(svg(corpo,w,h),encoding='utf-8');exportar(path,w)


def main():
    for f in FIGURAS:
        path=DESTINO/(f['arquivo']+'.svg')
        path.write_text(svg(f['corpo']),encoding='utf-8');exportar(path,1200)
    painel(FIGURAS[:22],'catalogo_foto',5,'22 figuras da foto - ordem de leitura')
    painel(FIGURAS[22:],'catalogo_novas',4,'7 novas figuras compostas')
    dados=dict(fonte='20261010_164750.jpg',metodo='Construção vetorial SVG e exportação PNG com ImageMagick; sem geração por IA.',
               observacao='Acervo de ilustrações, ainda não integrado ao aplicativo. Sem medidas ou respostas. A numeração segue as linhas da foto, da esquerda para a direita. Regularizações e interpretações constam na descrição.',
               figuras=[{k:v for k,v in f.items() if k!='corpo'} for f in FIGURAS])
    (DESTINO/'catalogo.json').write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cards=[]
    for f in FIGURAS:
        a=f['arquivo'];nome=html.escape(f['nome']);desc=html.escape(f['descricao'])
        cards.append(f'<article><img src="{a}.png" alt="{nome}"><h2>{f["numero"]:02d}. {nome}</h2><p>{desc}</p><a href="{a}.png">PNG</a> · <a href="{a}.svg">SVG editável</a></article>')
    pagina='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Acervo de geometria plana</title><style>body{font:16px system-ui;max-width:1300px;margin:30px auto;padding:20px;color:#222}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}article{border:1px solid #ddd;border-radius:8px;padding:16px}img{width:100%;aspect-ratio:1;object-fit:contain}h2{font-size:18px}p{line-height:1.5}a{color:#174a82}</style><h1>Acervo de geometria plana</h1><p>Figuras 01–22: foto do caderno, na ordem de leitura. Figuras 23–29: novas composições. Imagens sem medidas, prontas para receber anotações posteriormente. Ainda não integradas ao aplicativo.</p><main>'''+''.join(cards)+'</main></html>'
    (DESTINO/'index.html').write_text(pagina,encoding='utf-8')
    print(f'{len(FIGURAS)} figuras exportadas para {DESTINO}')


if __name__=='__main__':main()
