"""Provas de dez questões: capa e páginas fixas com 4, 4 e 2 itens."""
from dataclasses import dataclass, field, asdict
from io import BytesIO
from pathlib import Path
from html import unescape
from xml.sax.saxutils import escape
import json
import os
import re
import tempfile
from listas import validar_lista, texto_questao, desenhar_item
from documentos import publicar_par

FORMATO='prova-de-matematica'


@dataclass
class QuestaoProva:
    modelo: object
    texto: str | None = None
    alternativas: list = field(default_factory=lambda:['']*5)


@dataclass
class Prova:
    titulo: str = 'PROVA DE MATEMÁTICA'
    escola: str = 'EREM Joaquim Távora'
    professor: str = 'Diego Silva'
    numero: str = '1'
    mensagem: str = 'Boa prova e que a força esteja com você!'
    itens: list = field(default_factory=list)


def texto_editavel(grau,modelo):
    texto=texto_questao(grau,modelo)
    texto=re.sub(r'<br\s*/?>','\n',texto,flags=re.I)
    texto=re.sub(r'<sub>(.*?)</sub>',r'_\1',texto)
    texto=re.sub(r'<super>(.*?)</super>',r'^\1',texto)
    return unescape(re.sub('<[^>]*>','',texto))


def dados_prova(prova):
    return dict(formato=FORMATO,versao=1,**{k:getattr(prova,k) for k in ('titulo','escola','professor','numero','mensagem')},
                itens=[dict(conteudo=g,dados=asdict(q.modelo),texto=q.texto,alternativas=q.alternativas) for g,q in prova.itens])


def validar_prova(dados,completa=False):
    try:
        if not isinstance(dados,dict) or dados.get('formato')!=FORMATO or type(dados.get('versao')) is not int or dados['versao']!=1:
            raise ValueError('Formato de prova não suportado.')
        meta={k:dados[k] for k in ('titulo','escola','professor','numero','mensagem')}
        for k,v in meta.items():
            if not isinstance(v,str) or len(v)>160 or (k!='mensagem' and not v.strip()):raise ValueError(f'Preencha {k} (até 160 caracteres).')
        if not re.fullmatch(r'[0-9]{1,6}',meta['numero']):raise ValueError('Use um número de prova de 1 a 6 algarismos.')
        entries=dados['itens']
        if not isinstance(entries,list) or len(entries)>10:raise ValueError('A prova comporta dez questões.')
        if completa and len(entries)!=10:raise ValueError('Acrescente exatamente dez questões para exportar a prova.')
        result=[]
        for i,e in enumerate(entries,1):
            model=validar_lista(dict(formato='lista-de-exercicios',versao=1,titulo='',colunas=1,por_pagina=1,itens=[e])).itens[0]
            texto=e['texto'];alts=e['alternativas']
            if texto is not None and (not isinstance(texto,str) or not texto.strip() or len(texto)>8000):raise ValueError(f'Questão {i}: enunciado inválido (até 8000 caracteres).')
            if not isinstance(alts,list) or len(alts)!=5 or any(not isinstance(a,str) or len(a)>1000 for a in alts):raise ValueError(f'Questão {i}: informe cinco alternativas de até 1000 caracteres.')
            if completa and any(not a.strip() for a in alts):raise ValueError(f'Questão {i}: preencha todas as alternativas, de a a e.')
            result.append((model[0],QuestaoProva(model[1],texto,list(alts))))
        return Prova(**meta,itens=result)
    except (KeyError,TypeError,AttributeError) as exc:raise ValueError('JSON de prova incompleto ou inválido.') from exc


def carregar_prova(path):
    path=Path(path)
    if path.stat().st_size>2_000_000:raise ValueError('JSON muito grande (máximo de 2 MB).')
    try:return validar_prova(json.loads(path.read_text(encoding='utf-8')))
    except (UnicodeError,json.JSONDecodeError) as exc:raise ValueError('JSON inválido.') from exc


def quadro(index):
    from reportlab.lib.pagesizes import A4
    W,H=A4;w=(W-72)/2;h=(H-98)/2
    slot=index%4
    return 30+(slot%2)*(w+12),H-58-(slot//2)*(h+12)-h,w,h


def compor(g,q,index):
    """Mede antes de desenhar; nunca corta ou empurra itens para outra página."""
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY
    _,_,w,h=quadro(index)
    text=texto_questao(g,q.modelo) if q.texto is None else escape(q.texto).replace('\n','<br/>')
    graphic=True
    if g==6:graphic=False
    elif g==2 and q.modelo.apresentacao=='Expressão da função':
        from contextos_quadraticas import imagem
        graphic=bool(imagem(q.modelo))
    elif g==4 and q.modelo.modalidade=='Relação de Euler':
        from euler import imagem
        graphic=bool(imagem(q.modelo))
    elif g==4 and q.modelo.cenario!='Sem contexto':graphic=q.modelo.incluir_imagem
    elif g==8:graphic=q.modelo.incluir_imagem
    for size in (10,9.5,9):
        style=ParagraphStyle('prova',fontName='Helvetica',fontSize=size,leading=size*1.22,alignment=TA_JUSTIFY)
        p=Paragraph(f'<b>{index+1}.</b> '+text,style);_,th=p.wrap(w-20,10000)
        alternatives=[]
        for label,value in zip('abcde',q.alternativas):
            a=Paragraph(f'<b>{label})</b> '+escape(value).replace('\n','<br/>'),style)
            _,ah=a.wrap(w-20,10000);alternatives.append((a,ah))
        ah=sum(height+3 for _,height in alternatives)
        gh=0
        if graphic:
            if g==7:
                from estatistica import tabela
                _,gh=tabela(q.modelo,w-20).wrap(w-20,10000)
                gh+=12
            else:gh=min(160,h-30-th-ah-12)
        if th+ah+gh+42<=h and (not graphic or g==7 or gh>=110):return p,th,alternatives,gh
    raise ValueError(f'Questão {index+1} não cabe no quadro da prova. Encurte o enunciado/alternativas, reduza a tabela ou retire a imagem opcional. A prova permanece com quatro páginas.')


def capa(pdf,p):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    W,H=A4
    def linha(text,x,y,w,size=14):
        para=Paragraph(escape(text),ParagraphStyle('capa',fontName='Helvetica',fontSize=size,leading=size*1.3))
        _,h=para.wrap(w,1000)
        if h>size*2.7:raise ValueError('Texto da capa muito longo. Encurte escola, professor, título ou mensagem.')
        para.drawOn(pdf,x,y-h)
    pdf.setLineWidth(1.2);pdf.circle(65,H-107,22);pdf.setFont('Helvetica-Bold',16);pdf.drawCentredString(65,H-113,'JT')
    linha(p.escola,103,H-93,W-148,16)
    linha('Aluno:',45,H-188,70);pdf.line(101,H-210,W-45,H-210)
    linha('Data: ____ / ____ / ______',45,H-237,W-90)
    linha('Professor: '+p.professor,45,H-279,W-90)
    linha(p.titulo,45,H-350,W-90,20)
    linha('Semana {'+p.numero+'}',45,H-408,W-90,17)
    linha('GABARITO',45,350,W-90,16)
    linha('Preencha apenas uma alternativa por questão.',45,321,W-90,10)
    # Quatro marcas em L de geometria fixa, reservadas para futura leitura óptica.
    x0,x1,y0,y1=39,W-39,63,285
    pdf.setLineWidth(2)
    for x,sx in ((x0,1),(x1,-1)):
        for y,sy in ((y0,1),(y1,-1)):
            pdf.line(x,y,x+14*sx,y);pdf.line(x,y,x,y+14*sy)
    start=100;step=(W-160)/9
    pdf.setFont('Helvetica-Bold',11);pdf.setLineWidth(.8)
    for j in range(10):pdf.drawCentredString(start+j*step,263,str(j+1))
    for i,label in enumerate('abcde'):
        y=234-i*33
        pdf.drawString(57,y-4,label)
        for j in range(10):pdf.circle(start+j*step,y,7)


def pdf_prova(prova,completa=False):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    prova=validar_prova(dados_prova(prova),completa)
    planos=[compor(g,q,i) for i,(g,q) in enumerate(prova.itens)]
    stream=BytesIO();pdf=Canvas(stream,pagesize=A4);W,H=A4;pdf.setTitle(prova.titulo)
    capa(pdf,prova);pdf.showPage()
    for page,(start,end) in enumerate(((0,4),(4,8),(8,10)),2):
        pdf.setFont('Helvetica-Bold',11);pdf.drawString(30,H-30,'Matemática - Semana {'+prova.numero+'}')
        for i in range(start,min(end,len(prova.itens))):
            g,q=prova.itens[i];x,y,w,h=quadro(i);p,th,alts,gh=planos[i]
            pdf.saveState();pdf.setLineWidth(.5);pdf.setStrokeGray(.5);pdf.rect(x,y,w,h)
            cursor=y+h-10;p.drawOn(pdf,x+10,cursor-th);cursor-=th+8
            if gh:
                desenhar_item(pdf,g,q.modelo,(x+5,cursor-gh,w-10,gh));cursor-=gh+8
            for a,ah in alts:a.drawOn(pdf,x+10,cursor-ah);cursor-=ah+3
            pdf.restoreState()
        if page==4 and prova.mensagem:
            p=Paragraph(escape(prova.mensagem),ParagraphStyle('fim',fontName='Helvetica-Oblique',fontSize=16,leading=22,alignment=1))
            _,height=p.wrap(W-100,200);p.drawOn(pdf,50,180-height)
        pdf.setFont('Helvetica',8);pdf.drawRightString(W-30,20,f'{page}/4');pdf.showPage()
    pdf.save();return stream.getvalue()


def salvar_prova(path,prova):
    path=Path(path);content=pdf_prova(prova,completa=True)
    fd,tmp=tempfile.mkstemp(suffix='.pdf',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(content)
        return publicar_par(tmp,path,None,dados_prontos=dados_prova(prova))
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def salvar_rascunho(path,prova):
    dados=dados_prova(prova);validar_prova(dados)
    path=Path(path);fd,tmp=tempfile.mkstemp(suffix='.json',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(dados,f,ensure_ascii=False,indent=2)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
