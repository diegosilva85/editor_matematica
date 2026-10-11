"""Notação matemática simples, sem eval, desenhada como vetores no PDF."""
import re
from reportlab.platypus import Flowable
from reportlab.pdfbase.pdfmetrics import stringWidth


class Parser:
    def __init__(self,text):self.text=text;self.i=0;self.math=False
    def espacos(self):
        while self.i<len(self.text) and self.text[self.i] in ' \t':self.i+=1
    def atom(self,depth=0):
        if depth>12:raise ValueError('Expressão matemática muito aninhada; simplifique os agrupamentos.')
        self.espacos();start=self.i
        if self.i>=len(self.text):raise SyntaxError
        c=self.text[self.i]
        if c in '+-':
            self.i+=1;return ('row',[('text',c),self.atom(depth+1)])
        if c in '({':
            self.i+=1;node=self.expr(depth+1);self.espacos()
            if self.i>=len(self.text) or self.text[self.i]!=(')' if c=='(' else '}'):raise SyntaxError
            self.i+=1
            return ('group',node,c)
        m=re.match(r'(?:\d+(?:[.,]\d+)?|(?:√)?[A-Za-zα-ωΑ-Ω]+|√\d+(?:[.,]\d+)?)',self.text[self.i:])
        if not m:raise SyntaxError
        self.i+=len(m[0]);return ('text',self.text[start:self.i])
    def power(self,depth=0):
        node=self.atom(depth);end=self.i;self.espacos()
        if self.i<len(self.text) and self.text[self.i]=='^':
            self.i+=1
            try:exponent=self.power(depth+1)
            except SyntaxError:self.i=end;return node
            self.math=True;return ('power',node,ungroup(exponent))
        self.i=end;return node
    def fraction(self,depth=0):
        node=self.power(depth)
        while True:
            end=self.i;self.espacos()
            m=re.match(r'over(?![A-Za-z_])',self.text[self.i:])
            if not m:self.i=end;return node
            self.i+=4
            try:denominator=self.power(depth)
            except SyntaxError:self.i=end;return node
            node=('fraction',ungroup(node),ungroup(denominator));self.math=True
    def expr(self,depth=0):
        nodes=[self.fraction(depth)]
        while True:
            end=self.i;self.espacos()
            if self.i>=len(self.text) or self.text[self.i] not in '+-*=÷/':self.i=end;break
            op=self.text[self.i];self.i+=1
            try:right=self.fraction(depth)
            except SyntaxError:self.i=end;break
            if op=='*':self.math=True
            nodes += [('text',' · ' if op=='*' else f' {op} '),right]
        return nodes[0] if len(nodes)==1 else ('row',nodes)


def ungroup(node):return node[1] if node[0]=='group' else node


def partes(text):
    result=[];plain='';i=0
    while i<len(text):
        if text[i].isspace():plain+=text[i];i+=1;continue
        p=Parser(text);p.i=i
        try:node=p.expr()
        except SyntaxError:node=None
        if node is not None and p.math:
            if plain:result.append(plain);plain=''
            result.append(node);i=p.i
        else:plain+=text[i];i+=1
    if plain:result.append(plain)
    return result


def caixa(node,size):
    """Retorna largura, altura acima/abaixo da linha de base e operações vetoriais."""
    kind=node[0]
    if kind=='text':
        text=node[1];return stringWidth(text,'Helvetica',size),size*.85,size*.23,[('text',0,0,size,text)]
    if kind=='group':
        return caixa(('row',[('text',node[2]),node[1],('text',')' if node[2]=='(' else '}')]),size)
    if kind=='row':
        w=0;a=d=0;ops=[]
        for child in node[1]:
            cw,ca,cd,co=caixa(child,size);ops+=mover(co,w,0);w+=cw;a=max(a,ca);d=max(d,cd)
        return w,a,d,ops
    if kind=='power':
        w,a,d,ops=caixa(node[1],size);ew,ea,ed,eo=caixa(node[2],size*.72)
        lift=max(size*.55,a*.65)
        return w+ew,max(a,lift+ea),max(d,ed-lift),ops+mover(eo,w,lift)
    nw,na,nd,no=caixa(node[1],size*.86);dw,da,dd,do=caixa(node[2],size*.86)
    w=max(nw,dw)+size*.45;axis=size*.25;gap=size*.18
    ny=axis+gap+nd;dy=axis-gap-da
    return w,ny+na,max(0,dd-dy),mover(no,(w-nw)/2,ny)+mover(do,(w-dw)/2,dy)+[('line',0,axis,w,axis)]


def mover(ops,x,y):
    return [('text',op[1]+x,op[2]+y,*op[3:]) if op[0]=='text' else ('line',op[1]+x,op[2]+y,op[3]+x,op[4]+y) for op in ops]


class AlternativaMatematica(Flowable):
    def __init__(self,label,text,style):
        super().__init__();self.style=style;self.label=label;self.parts=partes(text)
    def wrap(self,width,height):
        size=self.style.fontSize;indent=stringWidth(self.label+') ','Helvetica-Bold',size)
        tokens=[]
        for part in self.parts:
            if isinstance(part,str):
                for word in re.findall(r'\n|[^\S\n]+|[^\s]+',part):
                    if word=='\n':tokens.append(None)
                    else:
                        # Long prose words may wrap; a mathematical expression stays whole.
                        chunk=''
                        for char in word:
                            if chunk and stringWidth(chunk+char,'Helvetica',size)>width-indent:
                                tokens.append(caixa(('text',chunk),size));chunk=''
                            chunk+=char
                        if chunk:tokens.append(caixa(('text',chunk),size))
            else:tokens.append(caixa(part,size))
        rows=[];row=[];used=indent
        def finish():
            nonlocal row,used
            rows.append((row,max([size*.85]+[b[1] for x,b in row]),max([size*.23]+[b[2] for x,b in row])))
            row=[];used=indent
        for box in tokens:
            if box is None:finish();continue
            if box[0]>width-indent+.01:raise ValueError('Expressão matemática muito larga. Reduza a fonte ou simplifique a alternativa.')
            if used+box[0]>width and row:finish()
            row.append((used,box));used+=box[0]
        if row or not rows:finish()
        self.rows=rows;self.width=width
        self.height=sum(max(self.style.leading,a+d+size*.2) for _,a,d in rows)
        return width,self.height
    def draw(self):
        pdf=self.canv;size=self.style.fontSize;top=self.height
        for i,(row,a,d) in enumerate(self.rows):
            baseline=top-a
            if i==0:pdf.setFont('Helvetica-Bold',size);pdf.drawString(0,baseline,self.label+')')
            for x,box in row:
                for op in box[3]:
                    if op[0]=='text':pdf.setFont('Helvetica',op[3]);pdf.drawString(x+op[1],baseline+op[2],op[4])
                    else:pdf.setLineWidth(max(.45,size*.045));pdf.line(x+op[1],baseline+op[2],x+op[3],baseline+op[4])
            top-=max(self.style.leading,a+d+size*.2)
