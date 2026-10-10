"""Apoio ao professor; os resultados nunca são incluídos no PDF."""
from parabolas import Parabola
from numeros_exatos import ler
from contextos_quadraticas import validar


def calcular(campos):
    """Calcula mesmo que os valores ainda não sirvam ao contexto escolhido."""
    try:
        por_raizes=campos.get('modo','Coeficientes')=='Raízes e a'
        valores={k: (0 if por_raizes and k!='a' else ler(campos.get(k,''))[1]) for k in ('a','b','c')}
        q=Parabola(**valores,modo=campos.get('modo','Coeficientes'),
                   quantidade_raizes=campos.get('quantidade_raizes','2'),
                   raiz1=campos.get('raiz1',''),raiz2=campos.get('raiz2',''))
        xv,yv,roots=q.dados()
        fmt=lambda v: format(v,'.8g').replace('.',',')
        raizes=('Não há raízes reais.' if not roots else
                'Raiz dupla: '+fmt(roots[0]) if len(roots)==1 else
                'x₁ = '+fmt(roots[0])+'\nx₂ = '+fmt(roots[1]))
        resultado=f'{raizes}\n\nxv = {fmt(xv)}\nyv = {fmt(yv)}\nV = ({fmt(xv)}; {fmt(yv)})'
        resultado+=f'\n\na = {fmt(q.a)}; b = {fmt(q.b)}; c = {fmt(q.c)}'
        resultado+='\nSinal de a: '+('positivo (mínimo)' if q.a>0 else 'negativo (máximo)')
        resultado+='\nSinal de Δ: '+('negativo' if not roots else 'zero' if len(roots)==1 else 'positivo')
        q.apresentacao='Expressão da função'
        q.cenario=campos.get('cenario','Sem contexto')
        q.alvo_contexto=campos.get('alvo_contexto','xv e yv')
        q.eixo_contexto=campos.get('eixo_contexto','Distância horizontal')
        try:
            validar(q,xv,yv,roots)
            aviso='Valores compatíveis com o contexto.' if q.cenario!='Sem contexto' else ''
        except ValueError as exc:
            aviso='Ajuste para o contexto: '+str(exc)
        return resultado,aviso
    except (ValueError,OverflowError,TypeError) as exc:
        return 'Preencha os campos para calcular raízes e vértice.',str(exc)
