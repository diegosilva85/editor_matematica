"""Conferência numérica exclusiva do editor, sem alterar questões ou PDFs."""
import math
from app_graficos import Funcao,numero
from exponenciais import Exponencial,TIPOS,coeficiente
from triangulos import Triangulo,PITAGORAS,medida


def fmt(v):
    if not math.isfinite(v):raise ValueError('Resultado fora do intervalo numérico. Reduza os valores.')
    return format(v,'.8g').replace('.',',')


def reta(c):
    q=Funcao(numero(c['a']),numero(c['b']),[numero(v) for v in c['xs']]);q.validar()
    rows=[f'f(x) = ({fmt(q.a)})·x + ({fmt(q.b)})',
          f'Raiz: x = {fmt(-q.b/q.a)}',f'Interseção com y: (0; {fmt(q.b)})',
          'Crescente.' if q.a>0 else 'Decrescente.']
    rows += [f'x = {fmt(x)} → y = {fmt(q.a*x+q.b)}' for x in q.xs]
    return '\n'.join(rows)+'\nA raiz é −b/a; b é o valor de f(0).'


def exponencial(c):
    q=Exponencial(c['tipo'],c['a'],c['b'],[coeficiente(v) for v in c['xs']]);q.validar()
    a,b=q.parametros();multiplicativa=q.tipo==TIPOS[0]
    crescente=(a>1)==(b>0) if multiplicativa else a>1
    rows=[f'f(x) = ({q.b})·({q.a})^x' if multiplicativa else f'f(x) = ({q.a})^x + ({q.b})',
          'Crescente.' if crescente else 'Decrescente.',f'f(0) = {fmt(q.y(0))}',
          f'Assíntota horizontal: y = {fmt(0 if multiplicativa else b)}']
    if not multiplicativa and b<0:
        rows.append(f'Raiz: x = ln(−b)/ln(a) = {fmt(math.log(-b)/math.log(a))}')
    else:rows.append('Não possui raiz real.')
    rows.append(('Imagem: y > 0.' if b>0 else 'Imagem: y < 0.') if multiplicativa else f'Imagem: y > {fmt(b)}.')
    rows += [f'x = {fmt(x)} → y = {fmt(q.y(x))}' for x in q.xs]
    return '\n'.join(rows)+'\nUse a > 0 e a ≠ 1. No formato b·a^x, b ≠ 0.'


def triangulo(c):
    contextual=c['apresentacao']=='Contextual'
    angle=45 if c['razao']==PITAGORAS and not contextual else numero(c['angulo'])
    q=Triangulo(angle,**{k:c[k] for k in ('posicao','razao','conhecido','valor','lado_x','valor2','apresentacao','cenario','dado_contexto','pedido_contexto','altura_extra')})
    q.validar()
    if q.razao==PITAGORAS and not contextual:
        d=q.medidas_pitagoras();a=d['Cateto 1'];o=d['Cateto 2'];h=d['Hipotenusa']
        rows=[f'{key} = {fmt(v)}' for key,v in d.items()]
        rows += [f'Lado solicitado ({q.lado_x}): {fmt(d[q.lado_x])}',
                 f'Ângulos agudos: {fmt(math.degrees(math.atan2(o,a)))}° e {fmt(math.degrees(math.atan2(a,o)))}°',
                 'Relação: hipotenusa² = cateto 1² + cateto 2².']
    else:
        s=math.sin(math.radians(angle));co=math.cos(math.radians(angle))
        extra=0;names=('Cateto adjacente','Cateto oposto','Hipotenusa')
        if contextual:
            from contextos import CENARIOS,EXTRAS
            names=CENARIOS[q.cenario][1];known=names.index(q.dado_contexto);asked=names.index(q.pedido_contexto)
            extra=medida(q.altura_extra)[1] if q.cenario in EXTRAS else 0
        else:known=names.index(q.conhecido);asked=names.index(q.incognita)
        value=medida(q.valor)[1]-(extra if known==1 else 0)
        h=value/(co,s,1)[known];a=h*co;o=h*s
        values=(a,o+extra,h)
        rows=[f'{name} = {fmt(v)}'+(' m' if contextual else '') for name,v in zip(names,values)]
        rows += [f'Medida solicitada: {fmt(values[asked])}',
                 f'sen({fmt(angle)}°) = {fmt(s)}; cos = {fmt(co)}; tan = {fmt(s/co)}',
                 'sen = oposto/hipotenusa; cos = adjacente/hipotenusa; tan = oposto/adjacente.']
        if extra:rows.append(f'Cateto vertical do triângulo = {fmt(o)} m. Altura total = cateto vertical + {fmt(extra)} m.')
    unidade='m' if contextual else 'unid.'
    rows += [f'Área do triângulo = {fmt(a*o/2)} {unidade}²; perímetro = {fmt(a+o+h)} {unidade}.']
    return '\n'.join(rows)


def calcular(tipo,campos):
    try:return {'reta':reta,'exponencial':exponencial,'triangulo':triangulo}[tipo](campos),True
    except (ValueError,KeyError,TypeError,OverflowError,ZeroDivisionError) as exc:
        return 'Confira os dados: '+str(exc),False
