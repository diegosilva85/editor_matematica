"""Listas mistas: paginação compartilhada pelo PDF e pelas prévias."""
from dataclasses import dataclass, field, asdict
from pathlib import Path
from io import BytesIO
import json
import os
import tempfile
from xml.sax.saxutils import escape

from documentos import validar_documento, FORMATO as FORMATO_ABAS, publicar_par

FORMATO='lista-de-exercicios'
CONTEUDOS={1:'Função de primeiro grau',2:'Função de segundo grau',3:'Trigonometria',
           4:'Geometria espacial',5:'Função exponencial',6:'Progressão aritmética',7:'Estatística'}


@dataclass
class Lista:
    titulo: str = 'Lista de Exercícios'
    colunas: int = 2
    por_pagina: int = 12
    itens: list = field(default_factory=list)


def dados_lista(lista):
    return dict(formato=FORMATO,versao=1,titulo=lista.titulo,colunas=lista.colunas,
                por_pagina=lista.por_pagina,
                itens=[{'conteudo':grau,'dados':asdict(item)} for grau,item in lista.itens])


def validar_lista(dados):
    try:
        if not isinstance(dados,dict) or dados.get('formato')!=FORMATO or type(dados.get('versao')) is not int or dados['versao']!=1:
            raise ValueError('Formato de lista não suportado.')
        title=dados['titulo']; cols=dados['colunas']; limit=dados['por_pagina']; items=dados['itens']
        if not isinstance(title,str) or len(title)>200: raise ValueError('Use um título de até 200 caracteres.')
        if type(cols) is not int or not 1<=cols<=3: raise ValueError('Escolha de 1 a 3 questões por linha.')
        if type(limit) is not int or not 1<=limit<=12: raise ValueError('Escolha de 1 a 12 questões por página.')
        if not isinstance(items,list) or not 1<=len(items)<=500: raise ValueError('A lista deve conter de 1 a 500 questões.')
        result=[]
        for index,entry in enumerate(items,1):
            try:
                page={'aba':entry['conteudo'],'colunas':1,'titulo':'','itens':[entry['dados']]}
                validated=validar_documento(dict(formato=FORMATO_ABAS,versao=1,paginas=[page]))[0]
                result.append((validated[0],validated[1][0]))
            except (ValueError,KeyError,TypeError) as e:
                raise ValueError(f'Questão {index}: {e}') from e
        return Lista(title,cols,limit,result)
    except (KeyError,TypeError,AttributeError) as e:
        raise ValueError('JSON de lista incompleto ou inválido.') from e


def carregar_lista(path):
    path=Path(path)
    if path.stat().st_size>2_000_000: raise ValueError('JSON muito grande (máximo de 2 MB).')
    try: dados=json.loads(path.read_text(encoding='utf-8'))
    except (UnicodeError,json.JSONDecodeError) as e: raise ValueError('JSON inválido.') from e
    if isinstance(dados,dict) and dados.get('formato')==FORMATO_ABAS:
        pages=validar_documento(dados)
        return Lista(itens=[(grau,item) for grau,items,_,_ in pages for item in items])
    return validar_lista(dados)


def texto_questao(grau,item):
    if grau==4 and item.modalidade=='Relação de Euler':
        from euler import enunciado
        return enunciado(item)
    if grau==4 and item.cenario!='Sem contexto':
        from contextos_solidos import enunciado
        return '<b>'+escape(item.tipo)+'.</b> '+enunciado(item)
    if grau==2 and item.apresentacao=='Expressão da função': return item.enunciado()
    if grau in (6,7): return item.enunciado()
    if grau==3 and item.apresentacao=='Contextual':
        from contextos import enunciado
        return escape(enunciado(item))
    return {1:'Determine a expressão da função representada no gráfico.',
            2:'Determine c, as raízes, x<sub>v</sub>, y<sub>v</sub>, o sinal de delta e o sinal de a.',
            3:'Determine x no triângulo retângulo. Medidas na mesma unidade.',
            4:f'Determine o volume e a área total: {escape(getattr(item,"tipo",""))}. Medidas em cm. Considere prismas retos com bases regulares, pirâmide reta e tetraedro regular.',
            5:'Determine a expressão da função representada no gráfico.'}[grau]


def paragrafo(grau,item,numero,width):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY
    p=Paragraph(f'<b>{numero}.</b> '+texto_questao(grau,item),
                ParagraphStyle('lista',fontName='Helvetica',fontSize=9,leading=12,alignment=TA_JUSTIFY))
    _,height=p.wrap(width-20,10000)
    return p,height


def planejar(lista):
    """Linhas de altura uniforme, sem dividir questões ou ultrapassar 12/página."""
    from reportlab.lib.pagesizes import A4
    expressoes=any(grau==2 and item.apresentacao=='Expressão da função' for grau,item in lista.itens)
    tabelas=any(grau==7 for grau,item in lista.itens)
    solidos_contextuais=any(grau==4 and item.modalidade!='Relação de Euler' and item.cenario!='Sem contexto' for grau,item in lista.itens)
    cols=min(lista.colunas,2) if expressoes or tabelas or solidos_contextuais else lista.colunas
    if any(grau==7 and len(item.cabecalhos())>5 for grau,item in lista.itens):cols=1
    limit=min(lista.por_pagina,4) if expressoes or solidos_contextuais else lista.por_pagina
    W,H=A4; gap=12; width=(W-60-gap*(cols-1))/cols
    pages=[]; page=[]; top=H-78; count=0; index=0
    while index<len(lista.itens):
        amount=min(cols,limit-count,len(lista.itens)-index)
        row=[]
        for offset in range(amount):
            grau,item=lista.itens[index+offset]
            _,text_height=paragrafo(grau,item,index+offset+1,width)
            textual=grau==6 or (grau==2 and item.apresentacao=='Expressão da função')
            if grau==2 and textual:
                from contextos_quadraticas import imagem
                textual=not bool(imagem(item))
            if grau==4 and item.cenario!='Sem contexto': textual=not item.incluir_imagem
            if grau==4 and item.modalidade=='Relação de Euler':
                from euler import imagem
                textual=not bool(imagem(item))
            graphic=0 if textual else (145 if cols==3 else 185 if cols==2 else 235)
            if grau==7:
                from estatistica import tabela
                _,graphic=tabela(item,width-20).wrap(width-20,10000)
                graphic+=12
            height=max(100,text_height+graphic+30)
            row.append((index+offset,width,height,text_height,graphic))
        height=max(x[2] for x in row)
        if height>H-118: raise ValueError(f'Questão {index+1} muito longa. Reduza o número de colunas.')
        if page and top-height<40:
            pages.append(page); page=[]; top=H-78; count=0
            continue
        for col,(i,w,h,th,gh) in enumerate(row):
            page.append((i,30+col*(width+gap),top-height,width,height,th,gh))
        index+=amount; count+=amount; top-=height+gap
        if count==limit:
            pages.append(page); page=[]; top=H-78; count=0
    if page: pages.append(page)
    return pages


class CanvasQuestao:
    """Reusa gráficos vetoriais sem seus cabeçalhos e rótulos de página."""
    def __init__(self,canvas): self.canvas=canvas
    def __getattr__(self,name): return getattr(self.canvas,name)
    def roundRect(self,*args,**kwargs): pass
    def setTitle(self,*args,**kwargs): pass
    def drawString(self,x,y,text,*args,**kwargs):
        from reportlab.lib.pagesizes import A4
        if y>=A4[1]-70 or text.startswith('(a)'): return
        self.canvas.drawString(x,y,text,*args,**kwargs)
    def drawCentredString(self,x,y,text,*args,**kwargs):
        from reportlab.lib.pagesizes import A4
        if y>=A4[1]-70: return
        self.canvas.drawCentredString(x,y,text,*args,**kwargs)


def desenhar_item(pdf,grau,item,rect):
    if grau==4 and item.modalidade=='Relação de Euler':
        from euler import desenhar_imagem
        desenhar_imagem(pdf,item,rect)
        return
    if grau==4 and item.cenario!='Sem contexto':
        from contextos_solidos import desenhar_imagem
        desenhar_imagem(pdf,item,rect)
        return
    if grau==7:
        from estatistica import tabela
        x,y,w,h=rect
        t=tabela(item,w-10);_,th=t.wrap(w-10,10000)
        t.drawOn(pdf,x+5,y+h-th)
        return
    if grau==2 and item.apresentacao=='Expressão da função':
        from contextos_quadraticas import desenhar_imagem
        desenhar_imagem(pdf,item,rect)
        return
    proxy=CanvasQuestao(pdf)
    if grau==1:
        from app_graficos import gerar_pdf
        gerar_pdf(Path(tempfile.gettempdir())/'lista.pdf',[item],1,'',canvas_existente=proxy,quadro=rect)
    elif grau in (2,4,5):
        from parabolas import desenhar_pagina as parabola
        from solidos import desenhar_pagina as solido
        from exponenciais import desenhar_pagina as exponencial
        {2:parabola,4:solido,5:exponencial}[grau](proxy,[item],1,'',quadro=rect)
    elif grau==3:
        if item.apresentacao=='Contextual':
            from contextos import dessiner
            dessiner(pdf,item.cenario,rect[0]+6,rect[1]+6,rect[2]-12,rect[3]-12,questao=item)
        else:
            from triangulos import desenhar_quadro
            desenhar_quadro(proxy,item,*rect,0)


def pdf_lista(lista):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    lista=validar_lista(dados_lista(lista))
    pages=planejar(lista); stream=BytesIO(); pdf=Canvas(stream,pagesize=A4)
    W,H=A4; pdf.setTitle(lista.titulo)
    for page_number,page in enumerate(pages,1):
        title=Paragraph(escape(lista.titulo or 'Lista de Exercícios'),ParagraphStyle('titulo',fontName='Helvetica-Bold',fontSize=15,leading=18))
        _,height=title.wrap(W-60,60)
        if height>48: raise ValueError('O título é muito longo para o cabeçalho.')
        title.drawOn(pdf,30,H-22-height)
        for index,x,y,w,h,th,gh in page:
            grau,item=lista.itens[index]
            pdf.saveState()
            pdf.setStrokeColorRGB(.72,.76,.8); pdf.setLineWidth(.6); pdf.roundRect(x,y,w,h,5)
            p,_=paragrafo(grau,item,index+1,w); p.drawOn(pdf,x+10,y+h-12-th)
            if gh: desenhar_item(pdf,grau,item,(x+5,y+5,w-10,h-th-22))
            pdf.restoreState()
        pdf.setFillColorRGB(.3,.3,.3); pdf.setFont('Helvetica',8)
        pdf.drawRightString(W-30,22,f'Página {page_number} de {len(pages)}')
        pdf.showPage()
    pdf.save(); return stream.getvalue()


def salvar_lista(path,lista):
    path=Path(path)
    content=pdf_lista(lista)
    fd,tmp=tempfile.mkstemp(suffix='.pdf',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f: f.write(content)
        return publicar_par(tmp,path,None,dados_prontos=dados_lista(lista))
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
