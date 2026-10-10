"""Leitura restrita de números, frações e radicais, sem avaliar código."""
import re
import math
import sympy as sp


def ler(texto):
    if not isinstance(texto,str) or len(texto)>80:
        raise ValueError('Use até 80 caracteres para cada número.')
    s=texto.strip().replace(' ','').replace(',','.')
    s=re.sub(r'sqrt\((\d+(?:\.\d+)?)\)',r'√\1',s)
    number=r'(?:\d+(?:\.\d*)?|\.\d+)'
    term=rf'([+-]?)({number})?(?:\*?√({number}))?'
    def token(t):
        m=re.fullmatch(term,t)
        if not m or (m[2] is None and m[3] is None):
            raise ValueError('Use números, frações ou raízes: -1/2, 0,5, √2, 2√3/3 ou sqrt(2).')
        value=sp.Rational(m[2]) if m[2] is not None else sp.Integer(1)
        if m[3] is not None: value*=sp.sqrt(sp.Rational(m[3]))
        return -value if m[1]=='-' else value
    parts=s.split('/')
    if not 1<=len(parts)<=2: raise ValueError('Use uma única barra de fração.')
    value=token(parts[0])
    if len(parts)==2:
        denominator=token(parts[1])
        if denominator==0: raise ValueError('O denominador não pode ser zero.')
        value/=denominator
    value=sp.simplify(value)
    try: numeric=float(value)
    except (ValueError,OverflowError,TypeError): raise ValueError('Número fora do intervalo permitido.') from None
    if not math.isfinite(numeric) or (numeric==0 and value!=0):
        raise ValueError('Número fora do intervalo permitido.')
    return value,numeric


def rotulo(value):
    return str(value).replace('sqrt(', '√(').replace('**','^').replace('*','·')
