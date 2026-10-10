"""Cálculos e orientações de PA exclusivos do editor."""
from progressao import numero,formatar,resolver_soma,ALVOS
from contextos_pa import dados


def calcular(q):
    try:
        c=dados(q)
        sentido={1:'positiva (aumenta)',-1:'negativa (diminui)',0:'não nula; pode aumentar ou diminuir'}[c['sentido']]
        dica=f'Use posições inteiras positivas e razão {sentido}. As medidas devem permanecer positivas desde o primeiro período.'
        if c.get('inteiro'): dica+=' Quantidades e razão precisam ser inteiras.'
        if c.get('dinheiro'): dica+=' Use valores e variações em múltiplos de R$ 0,01.'
        if q.tipo=='Soma dos termos': dica+=' Marque dados suficientes para determinar uma única PA; não forneça a incógnita.'
        else: dica+=' Para descobrir a posição, o número deve pertencer à PA. Para descobrir a razão, informe duas posições distintas.'
    except ValueError as exc:
        dica=str(exc)
    if q.apresentacao!='Contextual':
        dica='Use posições inteiras positivas. aₙ = a₁ + (n−1)r; Sₙ = n(a₁+aₙ)/2. Forneça dados suficientes e não informe a incógnita.'
    try:
        resposta=q.resolver()
        linhas=[f'{ALVOS[q.tipo][q.incognita]} = {formatar(resposta)}']
        if q.tipo=='Termo geral':
            i=numero(q.valores['i']); ai=numero(q.valores['ai'])
            r=resposta if q.incognita=='r' else numero(q.valores['r'])
            j=resposta if q.incognita=='j' else numero(q.valores['j'])
            primeiro=ai-(i-1)*r
            linhas += [f'Primeiro termo = {formatar(primeiro)}',f'Razão = {formatar(r)}',
                       f'Termo na posição {formatar(j)} = {formatar(primeiro+(j-1)*r)}']
        else:
            v={k:numero(q.valores[k]) for k in q.indicados.split(',')}
            primeiro,r,n=resolver_soma(v,q.incognita,completa=True)
            ultimo=primeiro+(n-1)*r
            linhas += [f'a₁ = {formatar(primeiro)}; aₙ = {formatar(ultimo)}',
                       f'n = {formatar(n)}; r = {formatar(r)}',f'Sₙ = {formatar(n*(primeiro+ultimo)/2)}']
        resultado='\n'.join(linhas)
        try:
            q.validar(); aviso='Valores válidos.' if q.apresentacao!='Contextual' else 'Valores compatíveis com o contexto.'
        except ValueError as exc: aviso=('Ajuste para o contexto: ' if q.apresentacao=='Contextual' else 'Confira os dados: ')+str(exc)
        return resultado,aviso,dica
    except (ValueError,KeyError,ZeroDivisionError) as exc:
        return 'Preencha os dados para calcular.',str(exc),dica
