"""Contextos de PA; nenhum dado calculado vira dado fornecido."""


CENARIOS={
 'Treinamento de corrida ou natação': dict(
    intro='Uma atleta organizou um programa de {atividade} e registra a distância percorrida em cada dia de treino. O planejamento prevê uma alteração constante entre as distâncias de dois dias consecutivos.',
    medida='a distância percorrida',periodos=('dia',),unidades=('metros','quilômetros'),sentido=0),
 'Dinheiro guardado': dict(
    intro='Para realizar uma compra planejada, uma pessoa decidiu guardar dinheiro regularmente. O valor de cada depósito aumenta sempre pela mesma quantia em relação ao depósito anterior. Considere que não há juros nem retiradas.',
    medida='o valor depositado',periodos=('dia','mês'),unidades=('reais',),sentido=1,dinheiro=True),
 'Novos seguidores de um perfil': dict(
    intro='Uma criadora de conteúdo acompanha os novos seguidores recebidos por seu perfil em cada período. Essa quantidade aumenta sempre pelo mesmo número em relação ao período anterior. Considere os novos seguidores de cada período, e não o total acumulado do perfil.',
    medida='a quantidade de novos seguidores',periodos=('dia','mês'),unidades=('seguidores',),sentido=1,inteiro=True),
 'Assentos de um teatro ou cinema': dict(
    intro='Um teatro possui fileiras de assentos numeradas a partir do palco. Cada fileira tem sempre a mesma quantidade de assentos a mais que a anterior, ampliando gradualmente o número de lugares.',
    medida='a quantidade de assentos',periodos=('fileira',),unidades=('assentos',),sentido=1,inteiro=True),
 'Plantio de sementes': dict(
    intro='Uma equipe organizou um cronograma para ampliar uma horta. Conforme novos canteiros são preparados, a quantidade de sementes plantadas aumenta a cada dia, sempre pelo mesmo número em relação ao dia anterior.',
    medida='a quantidade de sementes plantadas',periodos=('dia',),unidades=('sementes',),sentido=1,inteiro=True),
 'Treinamento de um ciclista': dict(
    intro='Um ciclista elaborou um plano de treinamento e acompanha {medida} a cada dia. Seu planejamento prevê uma alteração constante dessa medida de um dia para o seguinte, durante o período considerado.',
    medida='a distância percorrida',periodos=('dia',),unidades=('quilômetros','minutos','horas'),sentido=0),
 'Leitura de um livro': dict(
    intro='Uma estudante estabeleceu metas diárias para concluir a leitura de um livro. A cada novo dia, a meta aumenta sempre pelo mesmo número de páginas. Considere que ela cumpre todas as metas e que há páginas suficientes para o período analisado.',
    medida='a quantidade de páginas lidas',periodos=('dia',),unidades=('páginas',),sentido=1,inteiro=True),
 'Produção de uma oficina': dict(
    intro='Uma oficina está ampliando gradualmente sua produção. Durante essa etapa, a quantidade de peças produzidas aumenta semanalmente, sempre pelo mesmo número de peças em relação à semana anterior.',
    medida='a quantidade de peças produzidas',periodos=('semana',),unidades=('peças',),sentido=1,inteiro=True),
 'Caixas empilhadas em camadas': dict(
    intro='Uma loja montou uma pilha de caixas para uma exposição. As camadas são numeradas de baixo para cima, começando pela base. Cada camada possui sempre a mesma quantidade de caixas a menos que a imediatamente abaixo.',
    medida='a quantidade de caixas',periodos=('camada',),unidades=('caixas',),sentido=-1,inteiro=True),
 'Economia no consumo de água': dict(
    intro='Durante uma campanha de economia, uma família acompanha seu consumo diário de água. Ao longo do período analisado, o consumo diminui sempre pela mesma quantidade de litros de um dia para o seguinte.',
    medida='o consumo de água',periodos=('dia',),unidades=('litros',),sentido=-1),
 'Parcelas de uma compra': dict(
    intro='Uma loja oferece um plano de pagamento sem entrada, composto por parcelas mensais decrescentes. Cada parcela custa sempre a mesma quantia a menos que a anterior. Considere que os pagamentos seguem o plano durante todo o período analisado.',
    medida='o valor da parcela',periodos=('parcela',),unidades=('reais',),sentido=-1,dinheiro=True),
}


def dados(t):
    if t.cenario not in CENARIOS: raise ValueError('Escolha um contexto de PA.')
    c=CENARIOS[t.cenario]
    if t.periodo not in c['periodos'] or t.unidade not in c['unidades']:
        raise ValueError('Escolha um período e uma unidade compatíveis com o contexto.')
    if t.atividade not in ('corrida','natação'): raise ValueError('Escolha corrida ou natação.')
    return c


def grandeza(t):
    if t.cenario=='Treinamento de um ciclista' and t.unidade in ('minutos','horas'):
        return 'o tempo de treino'
    return dados(t)['medida']


def validar(t,answer):
    from progressao import numero, posicao, resolver_soma
    c=dados(t)
    if t.tipo=='Soma dos termos':
        v={k:numero(t.valores[k]) for k in t.indicados.split(',')}
        first,r,n=resolver_soma(v,t.incognita,completa=True)
        last=first+(n-1)*r
    else:
        i=posicao(numero(t.valores['i'])); ai=numero(t.valores['ai'])
        j=posicao(answer if t.incognita=='j' else numero(t.valores['j']))
        r=answer if t.incognita=='r' else numero(t.valores['r'])
        first=ai-(i-1)*r
        last=first+(max(i,j)-1)*r
    if min(first,last)<=0:
        raise ValueError('As medidas devem ser positivas desde o primeiro período até os períodos indicados.')
    if r==0 or (c['sentido'] and r*c['sentido']<=0):
        raise ValueError('Use uma variação não nula e compatível com o aumento ou a redução descritos no contexto.')
    if c.get('inteiro') and (first.denominator!=1 or r.denominator!=1):
        raise ValueError('Este contexto exige quantidades inteiras, inclusive na variação entre períodos.')
    if c.get('dinheiro') and ((first*100).denominator!=1 or (r*100).denominator!=1):
        raise ValueError('Os valores monetários e suas variações devem ser múltiplos de um centavo.')


def enunciado(t):
    from progressao import numero, formatar_entrada
    c=dados(t); medida=grandeza(t)
    feminino=t.periodo in ('fileira','semana','camada','parcela')
    ordinal='ª' if feminino else 'º'; em='Na' if feminino else 'No'
    def f(key):
        return formatar_entrada(t.valores[key])
    intro=c['intro'].format(atividade=t.atividade,medida=medida)
    if t.tipo=='Soma dos termos':
        return enunciado_soma(t,intro,medida)
    text=f'{intro} {em} {f("i")}{ordinal} {t.periodo}, {medida} foi de {f("ai")} {t.unidade}.'
    if t.incognita=='r':
        text+=f' {em} {f("j")}{ordinal} {t.periodo}, foi de {f("aj")} {t.unidade}.'
        text+=f' Determine a variação de {"uma" if feminino else "um"} {t.periodo} para {"a" if feminino else "o"} seguinte, em {t.unidade}, indicando se houve aumento ou redução.'
    else:
        r=numero(t.valores['r'])
        magnitude=formatar_entrada(t.valores['r'],modulo=True)
        text+=f' A cada {t.periodo}, essa medida {"aumenta" if r>0 else "diminui"} em {magnitude} {t.unidade} em relação à anterior.'
        if t.incognita=='aj':
            text+=f' Qual será {medida} {"na" if feminino else "no"} {f("j")}{ordinal} {t.periodo}?'
        else:
            text+=f' Em qual {t.periodo} {medida} será de {f("aj")} {t.unidade}?'
    return text


def enunciado_soma(t,intro,medida):
    from progressao import numero, formatar_entrada
    totals={
        'Treinamento de corrida ou natação':'a distância total percorrida',
        'Dinheiro guardado':'o total de dinheiro guardado',
        'Novos seguidores de um perfil':'o total de novos seguidores recebidos',
        'Assentos de um teatro ou cinema':'o total de assentos',
        'Plantio de sementes':'o total de sementes plantadas',
        'Treinamento de um ciclista':('o tempo total de treino' if t.unidade in ('minutos','horas') else 'a distância total percorrida'),
        'Leitura de um livro':'o total de páginas lidas',
        'Produção de uma oficina':'o total de peças produzidas',
        'Caixas empilhadas em camadas':'o total de caixas empilhadas',
        'Economia no consumo de água':'o total de água consumida',
        'Parcelas de uma compra':'o valor total pago',
    }
    total=totals[t.cenario]
    feminine=t.periodo in ('fileira','semana','camada','parcela')
    first='na primeira' if feminine else 'no primeiro'
    last='na última' if feminine else 'no último'
    plural={'dia':'dias','mês':'meses','fileira':'fileiras','semana':'semanas',
            'camada':'camadas','parcela':'parcelas'}[t.periodo]
    scope=f'Considerando {"as" if feminine else "os"} {plural} consecutiv{ "as" if feminine else "os"}, desde {"a primeira" if feminine else "o primeiro"} {t.periodo},'
    selected=set(t.indicados.split(','))
    def f(k): return formatar_entrada(t.valores[k])
    parts=[intro]
    if 'a1' in selected: parts.append(f'{medida.capitalize()} {first} {t.periodo} foi de {f("a1")} {t.unidade}.')
    if 'an' in selected: parts.append(f'{medida.capitalize()} {last} {t.periodo} foi de {f("an")} {t.unidade}.')
    if 'n' in selected: parts.append(f'Foram considerad{"as" if feminine else "os"} {f("n")} {plural} consecutiv{"as" if feminine else "os"}, a partir {"da primeira" if feminine else "do primeiro"} {t.periodo}.')
    if 'r' in selected:
        r=numero(t.valores['r'])
        magnitude=formatar_entrada(t.valores['r'],modulo=True)
        parts.append(f'A cada {t.periodo}, essa medida {"aumenta" if r>0 else "diminui"} em {magnitude} {t.unidade} em relação à anterior.')
    if 'sn' in selected:
        parts.append(f'{total.capitalize()} no conjunto considerado foi de {f("sn")} {t.unidade}.' if 'n' in selected
                     else f'{scope} {total} foi de {f("sn")} {t.unidade}.')
    asks={
        'sn':(f'Determine {total} no conjunto considerado.' if 'n' in selected
              else f'{scope} determine {total}.'),
        'a1':f'Determine {medida} {first} {t.periodo}, em {t.unidade}.',
        'an':f'Determine {medida} {last} {t.periodo} do conjunto considerado, em {t.unidade}.',
        'n':f'Quant{"as" if feminine else "os"} {plural} foram considerad{"as" if feminine else "os"} para atingir esse total?',
        'r':f'Determine a variação de {"uma" if feminine else "um"} {t.periodo} para {"a" if feminine else "o"} seguinte, em {t.unidade}, indicando se houve aumento ou redução.',
    }
    parts.append(asks[t.incognita])
    return ' '.join(parts)
