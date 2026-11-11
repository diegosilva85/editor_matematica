"""Folha A4 de cópias de uma questão, sem deformar ou cortar o original."""
from io import BytesIO
from math import floor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from acervo_enem import imagem_questao, PDF_LOCK

ESCALA_MINIMA = .8


def aparar_branco(im):
    """Remove somente margens externas; preserva desenhos e espaços internos."""
    mascara=im.convert('L').point(lambda p: 255 if p < 250 else 0)
    caixa=mascara.getbbox()
    if caixa is None:return im
    l,t,r,b=caixa
    folga=6
    return im.crop((max(0,l-folga),max(0,t-folga),min(im.width,r+folga),min(im.height,b+folga)))


def planejar(largura, altura):
    if largura <= 0 or altura <= 0:
        raise ValueError('Dimensões inválidas da questão.')
    util_w, util_h = A4[0]-20*mm, A4[1]-20*mm
    espaco = 4*mm
    candidatos = []
    # Até 20% de redução em relação ao caderno oficial; nunca distorcer.
    for colunas in range(1, floor((util_w+espaco)/(ESCALA_MINIMA*largura+espaco))+1):
        for linhas in range(1, floor((util_h+espaco)/(ESCALA_MINIMA*altura+espaco))+1):
            escala = min(1, (util_w-(colunas-1)*espaco)/(colunas*largura),
                         (util_h-(linhas-1)*espaco)/(linhas*altura))
            candidatos.append((colunas*linhas, escala, colunas, linhas))
    if candidatos:
        quantidade, escala, colunas, linhas = max(candidatos)
    else:
        quantidade, colunas, linhas = 1, 1, 1
        escala = min(1, util_w/largura, util_h/altura)
    return dict(quantidade=quantidade, escala=escala, colunas=colunas, linhas=linhas,
                largura=largura*escala, altura=altura*escala)


def gerar_boss(questao, prova):
    im = imagem_questao(questao, prova, 2400)
    largura = max(t['bbox'][2]-t['bbox'][0] for t in questao['recortes'])
    pontos_por_pixel=largura/im.width
    im=aparar_branco(im)
    largura=im.width*pontos_por_pixel
    plano = planejar(largura, largura*im.height/im.width)
    if len(questao['recortes']) > 1:
        # Questões que continuam em outra coluna não precisam virar uma tira
        # vertical minúscula. Mantém os recortes na ordem de leitura, lado a lado.
        from PIL import Image
        partes=[aparar_branco(imagem_questao(dict(questao,recortes=[t]),prova,2400))
                for t in questao['recortes']]
        alternativa=Image.new('RGB',(sum(p.width for p in partes)+18*(len(partes)-1),
                                      max(p.height for p in partes)),'white')
        x=0
        for parte in partes:
            alternativa.paste(parte,(x,0));x+=parte.width+18
        largura_alternativa=alternativa.width*pontos_por_pixel
        outro=planejar(largura_alternativa,largura_alternativa*alternativa.height/alternativa.width)
        if (outro['quantidade'],outro['escala']) > (plano['quantidade'],plano['escala']):
            im,plano=alternativa,outro
    saida = BytesIO()
    pdf = canvas.Canvas(saida, pagesize=A4)
    pdf.setTitle(f"Boss — Enem {questao['ano']} — questão {questao['numero']}")
    cw = (A4[0]-20*mm)/plano['colunas']
    ch = (A4[1]-20*mm)/plano['linhas']
    # A margem de cada célula deixa espaço para tesoura e impressão.
    for linha in range(plano['linhas']):
        for coluna in range(plano['colunas']):
            x = 10*mm+coluna*cw+(cw-plano['largura'])/2
            y = A4[1]-10*mm-(linha+1)*ch+(ch-plano['altura'])/2
            pdf.drawImage(ImageReader(im), x, y, plano['largura'], plano['altura'])
    pdf.setStrokeColorRGB(.65,.65,.65);pdf.setLineWidth(.4);pdf.setDash(3,3)
    for col in range(1,plano['colunas']):
        x=10*mm+col*cw;pdf.line(x,10*mm,x,A4[1]-10*mm)
    for lin in range(1,plano['linhas']):
        y=10*mm+lin*ch;pdf.line(10*mm,y,A4[0]-10*mm,y)
    pdf.showPage();pdf.save()
    dados=saida.getvalue()
    import pypdfium2 as pdfium
    with PDF_LOCK, pdfium.PdfDocument(dados) as doc:
        page=doc[0];bitmap=page.render(scale=1.2)
        try:preview=bitmap.to_pil().convert('RGB').copy()
        finally:bitmap.close();page.close()
    return dados, preview, plano
