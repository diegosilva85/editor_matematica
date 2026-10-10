"""Observações repetidas por indivíduo e incógnitas resolvidas pela média."""
from collections import Counter
from dataclasses import replace
import random
import time
from html import escape

COMPARACAO='Comparação por linha'
FALTANTE='Valor faltante pela média'
TIPOS_MULTIPLOS=(COMPARACAO,FALTANTE)
# Identificação, nome de cada coluna de observações, texto contextual.
CONTEXTOS_MULTIPLOS={
 'Notas de alunos':('Aluno','Nota','Uma turma realizou avaliações com notas de zero a dez. A tabela reúne as notas de cada aluno, com o mesmo peso em todas as avaliações.'),
 'Pontuação no basquete':('Jogador','Partida','Uma equipe de basquete acompanhou os pontos marcados por seus jogadores em uma sequência de partidas. Cada linha da tabela reúne as pontuações de um jogador nas partidas observadas.'),
 'Salários de funcionários':('Funcionário','Mês','Uma empresa acompanhou a remuneração mensal de seus funcionários durante alguns meses, incluindo as variações de cada período. Os valores estão em reais.'),
 'Glicose em amostras de sangue':('Paciente','Coleta','Uma atividade escolar apresenta valores fictícios de glicose, em mg/dL, obtidos em várias coletas de cada paciente. Os dados servem somente ao estudo de estatística, sem interpretação clínica.'),
 'Compras no mês':('Pessoa','Dia','Algumas pessoas registraram seus gastos com compras, em reais, em determinados dias de um mês. Considere somente os dias apresentados na tabela.'),
 'Hábitos musicais':('Participante','Semana','Uma pesquisa acompanhou o tempo de escuta de música de cada participante durante várias semanas. Os números representam horas por semana, não os gêneros musicais preferidos.'),
 'Livros lidos':('Leitor','Mês','Uma biblioteca acompanhou quantos livros cada leitor concluiu em cada mês de um período. A tabela apresenta as quantidades mensais, e não os totais acumulados.'),
 'Temperaturas diárias':('Cidade','Dia','Estações meteorológicas registraram, em graus Celsius, a temperatura de várias cidades no mesmo horário em cada dia. Considere os dias apresentados.'),
 'Tempo de deslocamento':('Pessoa','Dia','Uma pesquisa acompanhou o tempo de deslocamento de cada pessoa até o trabalho durante alguns dias. Os tempos estão em minutos.'),
 'Produção de uma oficina':('Equipe','Dia','Uma oficina registrou quantas peças cada equipe produziu em vários dias de trabalho. A tabela permite comparar a produção das equipes no período observado.'),
 'Consumo de água':('Residência','Mês','Um levantamento acompanhou o consumo de água de algumas residências durante vários meses. Cada valor indica o consumo de um mês, em metros cúbicos.'),
}


def quantidade(q):
    if not isinstance(q.quantidade_medidas,str) or q.quantidade_medidas not in tuple(map(str,range(2,9))):
        raise ValueError('Escolha de 2 a 8 medidas por linha.')
    return int(q.quantidade_medidas)


def cabecalhos(q):
    n=quantidade(q);label,coluna,_=CONTEXTOS_MULTIPLOS[q.cenario]
    return [label]+[f'{coluna} {i+1}' for i in range(n)]+(['Média'] if q.tipo==FALTANTE else [])


def analisar(q):
    from estatistica import numero,conferir_valor,resumir
    n=quantidade(q);faltante=q.tipo==FALTANTE
    if q.tipo not in TIPOS_MULTIPLOS or q.cenario not in CONTEXTOS_MULTIPLOS: raise ValueError('Contexto ou formato inválido.')
    minimo=1 if faltante else 2
    if not isinstance(q.linhas,list) or not minimo<=len(q.linhas)<=20: raise ValueError(f'Use de {minimo} a 20 linhas.')
    labels=set();result=[];ocultos=0
    for i,row in enumerate(q.linhas,1):
        try:
            if not isinstance(row,(list,tuple)) or len(row)!=n+1+faltante or not all(isinstance(s,str) and len(s)<=80 for s in row):
                raise ValueError(f'Informe identificação, {n} medidas'+(' e média.' if faltante else '.'))
            label=row[0].strip()
            if not label or label in labels: raise ValueError('Use identificações preenchidas e distintas.')
            labels.add(label)
            desconhecido=faltante and row[n].strip() in ('','?','x','X')
            valores=[numero(s) for s in row[1:n if desconhecido else n+1]]
            for v in valores: conferir_valor(q.cenario,v)
            resposta=None
            if faltante:
                media=numero(row[-1])
                # A média pode ser fracionária mesmo em contagens inteiras.
                if abs(media)>1_000_000: raise ValueError('Média fora do intervalo permitido.')
                if desconhecido:
                    resposta=n*media-sum(valores)
                    conferir_valor(q.cenario,resposta)
                    valores.append(resposta);ocultos+=1
                elif sum(valores)/n!=media:
                    raise ValueError('A média informada não corresponde aos valores da linha completa.')
            resumo=resumir(Counter(valores))
            result.append(dict(nome=label,**resumo,resposta=resposta))
        except ValueError as exc: raise ValueError(f'Linha {i}: {exc}') from exc
    if faltante and not ocultos: raise ValueError('Deixe a última medida em branco (ou use ?) em pelo menos uma linha.')
    return result


def vencedores(q):
    rows=analisar(q)
    return {key:[r['nome'] for r in rows if r[key]==max(v[key] for v in rows)] for key in ('media','mediana')}


def enunciado(q):
    intro=CONTEXTOS_MULTIPLOS[q.cenario][2]
    if q.tipo==FALTANTE:
        return enunciado_faltante(q)
    medidas=[]
    if q.pedir_media: medidas.append('média aritmética')
    if q.pedir_mediana: medidas.append('mediana')
    pedido=' e a '.join(medidas)
    return intro+' Calcule a '+pedido+' de cada linha e identifique quem apresenta o maior valor em cada medida solicitada. Se houver empate, indique todos os envolvidos.'


def enunciado_faltante(q):
    """Metas narrativas, sem inserir a resposta calculada no enunciado."""
    from estatistica import numero
    n=quantidade(q)
    textos={
        'Notas de alunos':('As avaliações têm notas de zero a dez e o mesmo peso. A coluna Média indica a média mínima exigida para aprovação em cada caso.', 'Qual é a nota mínima necessária na última avaliação para obter aprovação?'),
        'Pontuação no basquete':('Cada jogador pretende alcançar, ao final das partidas apresentadas, a média de pontos do maior pontuador de seu campeonato, indicada na coluna Média.', 'Quantos pontos deve marcar na última partida para alcançar exatamente essa média?'),
        'Salários de funcionários':('Uma empresa planeja a remuneração de seus funcionários no período apresentado, em reais. A coluna Média indica a remuneração mensal média planejada para cada funcionário.', 'Qual deverá ser a remuneração do último mês para atingir essa média no período?'),
        'Glicose em amostras de sangue':('Uma atividade escolar apresenta coletas fictícias de glicose, em mg/dL. O resultado da última coleta foi apagado, mas a média das coletas foi preservada na coluna Média. Os dados não têm finalidade clínica.', 'Qual era o resultado da última coleta para que as amostras apresentassem essa média?'),
        'Compras no mês':('Um planejamento de compras estabelece um gasto médio diário, em reais, indicado na coluna Média. Considere apenas os dias da tabela.', 'Quanto deverá ser gasto no último dia para que o gasto médio seja exatamente o planejado?'),
        'Hábitos musicais':('Uma pesquisa registrou as horas semanais de escuta de música. A coluna Média informa a média semanal do período, mas o registro da última semana está incompleto.', 'Quantas horas de música foram ouvidas na última semana para que a média fosse a informada?'),
        'Livros lidos':('Um desafio de leitura estabelece para cada leitor uma meta de livros lidos por mês, em média, indicada na coluna Média. As quantidades da tabela são mensais, não acumuladas.', 'Quantos livros deverão ser concluídos no último mês para atingir exatamente a média do desafio?'),
        'Temperaturas diárias':('Estações meteorológicas mediram a temperatura, em graus Celsius, no mesmo horário durante os dias apresentados. A média do período foi preservada na coluna Média, mas falta a última medição.', 'Qual foi a temperatura registrada no último dia para que a média do período fosse a informada?'),
        'Tempo de deslocamento':('Uma pesquisa registrou o tempo de deslocamento até o trabalho, em minutos, nos dias apresentados. A coluna Média informa o tempo médio do período, mas falta o registro do último dia.', 'Quanto tempo durou o deslocamento no último dia para que a média fosse a informada?'),
        'Produção de uma oficina':('Uma oficina definiu para cada equipe uma meta de produção média diária, indicada na coluna Média. A tabela mostra a quantidade de peças produzidas a cada dia.', 'Quantas peças deverão ser produzidas no último dia para atingir exatamente a média planejada?'),
        'Consumo de água':('Um levantamento registrou o consumo mensal de água, em metros cúbicos. A coluna Média informa o consumo médio do período, mas o registro do último mês está incompleto.', 'Qual foi o consumo de água no último mês para que a média fosse a informada?'),
    }
    intro,pergunta=textos[q.cenario]
    if len(q.linhas)==1:
        row=q.linhas[0]
        referencia=f' Para {escape(row[0])}, considere {n} registros e média de {escape(row[-1])}.'
    else:
        referencia=f' Considere os {n} registros de cada linha e responda somente aos casos indicados por ?.'
        # Com a mesma referência, todos os jogadores podem pertencer ao mesmo campeonato.
        if q.cenario=='Pontuação no basquete' and len({numero(r[-1]) for r in q.linhas})==1:
            intro=intro.replace('de seu campeonato','do campeonato')
    return intro+referencia+' '+pergunta


def apoio(q):
    from estatistica import fmt
    dica=('Cada linha é um conjunto independente. Todas as medidas têm o mesmo peso. '
          'A mediana exige ordenar os valores de cada linha. Empates são aceitos e todos os envolvidos são indicados. '
          'As metas opcionais do gerador são aplicadas a cada linha, não à tabela inteira.')
    if q.tipo==FALTANTE:
        dica=('Última medida faltante = número de medidas × média informada − soma das medidas conhecidas. '
              'Deixe somente a última medida em branco ou digite ?. A coluna Média deve estar preenchida. '
              'A média é exata, não arredondada; a resposta deve respeitar o contexto. '
              'Na geração, a meta de média prevalece; se estiver vazia, usa-se a média preenchida em cada linha.')
    try:
        q.validar();rows=analisar(q)
        if q.tipo==FALTANTE:
            text='\n'.join(r['nome']+': '+('valor faltante = '+fmt(r['resposta']) if r['resposta'] is not None else 'linha completa conferida') for r in rows)
        else:
            text='\n'.join(f'{r["nome"]}: média {fmt(r["media"])}; mediana {fmt(r["mediana"])}' for r in rows)
            for key,nome in (('media','média'),('mediana','mediana')):
                if getattr(q,'pedir_'+key):
                    maior=max(r[key] for r in rows);nomes=[r['nome'] for r in rows if r[key]==maior]
                    text+=f'\nMaior {nome}: '+', '.join(nomes)+f' ({fmt(maior)})'+(' - empate' if len(nomes)>1 else '')
        return text,dica
    except ValueError as exc: return 'Ajuste necessário: '+str(exc),dica


def redimensionar(q,total,anteriores):
    """Preserva rótulos e colunas existentes; mantém a incógnita no fim."""
    from estatistica import CONTEXTOS,fmt,numero
    n=quantidade(q);label=CONTEXTOS_MULTIPLOS[q.cenario][0]
    padrao=fmt((numero(CONTEXTOS[q.cenario][4])+numero(CONTEXTOS[q.cenario][5]))/2)
    rows=[]
    for i in range(total):
        old=anteriores[i] if i<len(anteriores) else []
        nome=old[0] if old else f'{label} {i+1}'
        media=old[-1] if old and q.tipo==FALTANTE else padrao
        vals=list(old[1:-1] if q.tipo==FALTANTE else old[1:])
        oculto=q.tipo==FALTANTE and (not vals or vals[-1].strip() in ('','?','x','X'))
        if oculto and vals:vals.pop()
        size=n-1 if oculto else n
        vals=(vals+[padrao]*size)[:size]
        if oculto:vals.append('')
        rows.append([nome]+vals+([media] if q.tipo==FALTANTE else []))
    return rows


def gerar(q,total,seed=None):
    from estatistica import Estatistica,gerar as gerar_simples,fmt,numero
    minimo=1 if q.tipo==FALTANTE else 2
    if type(total) is not int or not minimo<=total<=20: raise ValueError(f'Escolha de {minimo} a 20 linhas.')
    n=quantidade(q);rng=random.Random(seed);deadline=time.monotonic()+5
    label=CONTEXTOS_MULTIPLOS[q.cenario][0];rows=[]
    for i in range(total):
        old=q.linhas[i] if i<len(q.linhas) else []
        media=q.meta_media
        if q.tipo==FALTANTE and not media.strip() and len(old)==n+2:media=old[-1]
        base=Estatistica(cenario=q.cenario,meta_media=media,meta_moda=q.meta_moda,
                         meta_mediana=q.meta_mediana,minimo=q.minimo,maximo=q.maximo,passo=q.passo)
        dados=gerar_simples(base,n,seed=rng.randrange(2**32),_deadline=deadline)
        vals=[row[1] for row in dados]
        nome=old[0] if old else f'{label} {i+1}'
        if q.tipo==FALTANTE:
            media_texto=media if media.strip() else fmt(sum(map(numero,vals))/n)
            vals[-1]='';vals.append(media_texto)
        rows.append([nome]+vals)
    replace(q,linhas=rows).validar()
    return rows
