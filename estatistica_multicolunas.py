"""Observações repetidas por indivíduo e incógnitas resolvidas pela média."""
from collections import Counter
from dataclasses import replace
import random
import time

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
    if not isinstance(q.linhas,list) or not 2<=len(q.linhas)<=20: raise ValueError('Use de 2 a 20 linhas.')
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
        return intro+' A última coluna informa a média aritmética exata das '+str(quantidade(q))+' medidas de cada linha. Determine cada valor indicado por ?, usando a média fornecida.'
    medidas=[]
    if q.pedir_media: medidas.append('média aritmética')
    if q.pedir_mediana: medidas.append('mediana')
    pedido=' e a '.join(medidas)
    return intro+' Calcule a '+pedido+' de cada linha e identifique quem apresenta o maior valor em cada medida solicitada. Se houver empate, indique todos os envolvidos.'


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
    if type(total) is not int or not 2<=total<=20: raise ValueError('Escolha de 2 a 20 linhas.')
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
