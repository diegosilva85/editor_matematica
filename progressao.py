"""Questões de PA com ou sem contexto; aritmética exata, sem avaliação de código."""
from dataclasses import dataclass, field
from fractions import Fraction
import math
import re
from itertools import combinations

TIPOS=('Termo geral','Soma dos termos')
ALVOS={TIPOS[0]:{'aj':'Valor de um termo','j':'Posição de um número','r':'Razão'},
       TIPOS[1]:{'a1':'Primeiro termo (a₁)','an':'Último termo (aₙ)',
                 'n':'Quantidade de termos (n)','sn':'Soma (Sₙ)','r':'Razão (r)'}}
PADRAO={'i':'1','ai':'2','j':'10','aj':'29','r':'3',
        'a1':'2','an':'29','n':'10','sn':'155'}
DADOS_SOMA={**ALVOS[TIPOS[1]],'r':'Razão (r)'}


def resolver_soma(v, alvo, completa=False):
    """Resolve apenas os dados fornecidos, rejeitando ambiguidades e conflitos."""
    def raizes(a,b,c):
        if a==0: return {-c/b} if b else set()
        d=b*b-4*a*c
        if d<0: return set()
        p=math.isqrt(d.numerator); q=math.isqrt(d.denominator)
        if p*p!=d.numerator or q*q!=d.denominator: return set()
        s=Fraction(p,q)
        return {(-b+s)/(2*a),(-b-s)/(2*a)}
    if 'n' in v:
        candidates={Fraction(posicao(v['n']))}
    else:
        candidates=set()
        if {'a1','an','sn'}<=v.keys() and v['a1']+v['an']:
            candidates.add(2*v['sn']/(v['a1']+v['an']))
        if {'a1','an','r'}<=v.keys() and v['r']:
            candidates.add(1+(v['an']-v['a1'])/v['r'])
        if {'a1','r','sn'}<=v.keys():
            candidates |= raizes(v['r'],2*v['a1']-v['r'],-2*v['sn'])
        if {'an','r','sn'}<=v.keys():
            candidates |= raizes(-v['r'],2*v['an']+v['r'],-2*v['sn'])
    answers=set()
    progressions=set()
    for n in candidates:
        if n.denominator!=1 or not 1<=n<=1_000_000: continue
        coefficients={'a1':(Fraction(1),Fraction(0)), 'an':(Fraction(1),n-1),
                      'sn':(n,n*(n-1)/2), 'r':(Fraction(0),Fraction(1))}
        equations=[(*coefficients[k],value) for k,value in v.items() if k!='n']
        for (a,b,c),(d,e,f) in combinations(equations,2):
            det=a*e-b*d
            if not det: continue
            first=(c*e-b*f)/det; reason=(a*f-c*d)/det
            complete={'a1':first,'an':first+(n-1)*reason,'n':n,
                      'sn':n*(2*first+(n-1)*reason)/2,'r':reason}
            if all(complete[k]==value for k,value in v.items()):
                answers.add(complete[alvo])
                progressions.add((first,reason,n))
        # With one term, the reason is irrelevant to all four sum targets.
        if n==1 and alvo!='r':
            terms=[v[k] for k in ('a1','an','sn') if k in v]
            if terms and len(set(terms))==1:
                answers.add(n if alvo=='n' else terms[0])
    if len(answers)!=1:
        raise ValueError('Os dados devem determinar uma única resposta. Confira os valores e indique dados suficientes (inclusive a razão, se necessário).')
    if completa:
        if len(progressions)!=1:
            raise ValueError('Para o contexto, informe dados que determinem a progressão e sua variação.')
        return progressions.pop()
    return answers.pop()


def numero(text):
    if not isinstance(text,str) or len(text)>40:
        raise ValueError('Use números ou frações com até 40 caracteres.')
    text=text.strip().replace(',','.')
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+|\d+/[+-]?\d+)',text):
        raise ValueError('Use números ou frações, como -3, 2,5 ou 1/2.')
    try: return Fraction(text)
    except (ValueError,ZeroDivisionError,OverflowError):
        raise ValueError('Use números ou frações, como -3, 2,5 ou 1/2.') from None


def posicao(value):
    if value.denominator!=1 or not 1<=value<=1_000_000:
        raise ValueError('A posição/quantidade deve ser um inteiro positivo, até 1000000.')
    return int(value)


def formatar(value):
    return str(value.numerator) if value.denominator==1 else f'{value.numerator}/{value.denominator}'


def formatar_entrada(text,modulo=False):
    """Preserva a notação digitada sem mudar a aritmética interna exata."""
    numero(text)
    result=text.strip()
    return result.lstrip('+-') if modulo else result


@dataclass
class Progressao:
    tipo: str = 'Termo geral'
    incognita: str = 'aj'
    valores: dict = field(default_factory=lambda:dict(PADRAO))
    indicados: str = 'a1,an,n'
    apresentacao: str = 'Sem contexto'
    cenario: str = 'Treinamento de corrida ou natação'
    periodo: str = 'dia'
    unidade: str = 'metros'
    atividade: str = 'corrida'

    def resolver(self):
        if self.tipo not in ALVOS or self.incognita not in ALVOS[self.tipo]:
            raise ValueError('Escolha o tipo da questão e o que deseja descobrir.')
        def get(k):
            if k not in self.valores: raise ValueError(f'Informe o valor de {k}.')
            return numero(self.valores[k])
        if self.tipo==TIPOS[0]:
            i=posicao(get('i')); ai=get('ai')
            if self.incognita=='aj':
                j=posicao(get('j'))
                return ai+(j-i)*get('r')
            if self.incognita=='r':
                j=posicao(get('j'))
                if j==i: raise ValueError('Use duas posições diferentes para determinar a razão.')
                return (get('aj')-ai)/(j-i)
            r=get('r')
            if r==0: raise ValueError('Razão zero não permite determinar uma posição única.')
            answer=Fraction(i)+(get('aj')-ai)/r
            posicao(answer)
            return answer
        selected=self.indicados.split(',') if self.indicados else []
        if len(selected)!=len(set(selected)) or any(k not in DADOS_SOMA for k in selected):
            raise ValueError('Seleção de dados da soma inválida.')
        if self.incognita in selected: raise ValueError('A incógnita não pode ser fornecida no enunciado.')
        v={k:get(k) for k in selected}
        return resolver_soma(v,self.incognita)

    def validar(self):
        answer=self.resolver()
        if self.apresentacao not in ('Sem contexto','Contextual'):
            raise ValueError('Escolha a apresentação da questão.')
        if self.apresentacao=='Contextual':
            from contextos_pa import validar
            validar(self,answer)

    def enunciado(self):
        self.validar()
        if self.apresentacao=='Contextual':
            from contextos_pa import enunciado
            return enunciado(self)
        def f(k): return formatar_entrada(self.valores[k])
        if self.tipo==TIPOS[0]:
            ref=f'a<sub>{f("i")}</sub> = {f("ai")}'
            if self.incognita=='r':
                return f'Em uma progressão aritmética, {ref} e a<sub>{f("j")}</sub> = {f("aj")}. Determine a razão dessa progressão.'
            if self.incognita=='aj':
                return f'Em uma progressão aritmética, {ref} e a razão é {f("r")}. Determine o valor de a<sub>{f("j")}</sub>.'
            return f'Em uma progressão aritmética, {ref} e a razão é {f("r")}. Qual é a posição do número {f("aj")} nessa progressão?'
        names={'a1':'o primeiro termo é','an':'o último termo é',
               'n':'a quantidade de termos é','sn':'a soma dos termos é','r':'a razão é'}
        parts=[f'{names[k]} {f(k)}' for k in DADOS_SOMA if k in self.indicados.split(',')]
        ask={'a1':'o primeiro termo','an':'o último termo','n':'a quantidade de termos',
             'sn':'a soma desses termos','r':'a razão dessa progressão'}[self.incognita]
        dados=', '.join(parts[:-1])+' e '+parts[-1] if len(parts)>1 else parts[0]
        return 'Em uma progressão aritmética, '+dados+f'. Determine {ask}.'


def desenhar_pagina(pdf,items,colunas,titulo):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.platypus import Paragraph
    if not 1<=len(items)<=12 or colunas not in (1,2):
        raise ValueError('Use de 1 a 12 questões de PA, com até 2 por linha.')
    contextual=any(t.apresentacao=='Contextual' for t in items)
    capacity=colunas*3 if contextual else 12
    W,H=A4
    for start in range(0,len(items),capacity):
        if start: pdf.showPage()
        batch=items[start:start+capacity]; rows=math.ceil(len(batch)/colunas)
        cw=(W-60-(colunas-1)*12)/colunas; ch=(H-95)/rows
        pdf.setFillGray(0); pdf.setFont('Helvetica-Bold',16)
        pdf.drawCentredString(W/2,H-35,(titulo or 'Progressão aritmética')[:65])
        pdf.setFont('Helvetica',9); pdf.drawString(30,H-53,'Resolva as questões a seguir.')
        for i,item in enumerate(batch):
            x=30+i%colunas*(cw+12); y=H-70-(i//colunas+1)*ch
            pdf.setStrokeGray(.65); pdf.setLineWidth(.6); pdf.roundRect(x,y+8,cw,ch-14,5)
            style=ParagraphStyle('pa',fontName='Helvetica',fontSize=10,leading=14,alignment=TA_JUSTIFY)
            for size in (10,9.5,9):
                style.fontSize=size; style.leading=size+3
                p=Paragraph(f'<b>({chr(97+start+i)})</b> '+item.enunciado(),style)
                _,height=p.wrap(cw-22,ch-30)
                if height<=ch-30: break
            if height>ch-30: raise ValueError('O texto não cabe. Use uma coluna ou menos questões.')
            p.drawOn(pdf,x+11,y+ch-18-height)
