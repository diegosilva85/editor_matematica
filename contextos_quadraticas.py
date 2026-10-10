"""Contextos de expressões quadráticas e suas ilustrações opcionais."""
from pathlib import Path

CENARIOS = ('Sem contexto', 'Chute do goleiro', 'Saque de vôlei', 'Jato de água',
            'Lucro por quantidade vendida', 'Lucro ao longo dos dias',
            'Terreno com cerca', 'Receita de ingressos', 'Temperatura de uma câmara fria',
            'Cabo suspenso')
ALVOS = ('Raízes', 'xv', 'yv', 'xv e yv')
EIXOS = ('Distância horizontal', 'Tempo')
PROJETEIS = CENARIOS[1:4]
IMAGENS = {'Chute do goleiro': 'chute_goleiro-v2.png', 'Saque de vôlei': 'saque_volei-v2.png',
           'Jato de água': 'jato_agua.png', 'Cabo suspenso': 'cabo_suspenso.png'}


def orientacao(cenario):
    if cenario=='Sem contexto':
        return 'Use a diferente de zero. Você pode informar coeficientes ou uma raiz dupla / duas raízes reais.'
    if cenario=='Cabo suspenso':
        return ('Cabo acima do solo: a > 0, xv ≥ 0 e yv > 0. Isso exige Δ < 0: não há raízes reais. '
                'Use Coeficientes, não Raízes e a. Exemplo: a = 1, b = -6, c = 13 → V = (3; 4). '
                'Com duas raízes reais o ponto mais baixo fica no solo ou abaixo dele; por isso esse modo não serve a este cenário.')
    if cenario=='Temperatura de uma câmara fria':
        return ('Use a > 0 e xv ≥ 0 para um mínimo após o início. yv pode ser negativo. '
                'Exemplo: a = 1, b = -6, c = 5 (raízes 1 e 5). Para perguntar raízes, deve existir uma raiz real não negativa.')
    base=('Use a < 0, xv ≥ 0 e yv > 0 para um máximo no domínio do contexto. '
          'Exemplo: a = -1, b = 6, c = 0; ou a = -1 com raízes 0 e 6. '
          'No modo por raízes, use duas distintas cuja média seja não negativa. ')
    if cenario in PROJETEIS:
        return base+'c é a altura inicial: use c ≥ 0. Exemplo de lançamento acima do solo: a = -1, b = 4, c = 5 (raízes -1 e 5).'
    return base+'Se pedir raízes, deve haver ao menos uma raiz real não negativa. x representa '+{
        'Lucro por quantidade vendida':'milhares de unidades vendidas.',
        'Lucro ao longo dos dias':'dias desde o início da campanha.',
        'Terreno com cerca':'uma dimensão em metros; considere somente área positiva.',
        'Receita de ingressos':'o preço em reais; considere preços e receita não negativos.'}[cenario]


def imagem(q):
    if q.apresentacao != 'Expressão da função' or not q.incluir_imagem or q.cenario not in IMAGENS:
        return None
    return Path(__file__).resolve().parent / 'assets' / 'contextos_quadraticas' / IMAGENS[q.cenario]


def validar(q, xv, yv, roots):
    if q.cenario not in CENARIOS or q.alvo_contexto not in ALVOS or q.eixo_contexto not in EIXOS:
        raise ValueError('Contexto, pergunta ou variável inválida.')
    if type(q.incluir_imagem) is not bool:
        raise ValueError('A opção de incluir imagem deve ser verdadeira ou falsa.')
    if q.apresentacao != 'Expressão da função' or q.cenario == 'Sem contexto':
        return
    minimo = q.cenario in ('Cabo suspenso', 'Temperatura de uma câmara fria')
    if q.cenario=='Cabo suspenso' and q.modo=='Raízes e a':
        raise ValueError('Cabo acima do solo não tem raízes reais. Troque para Coeficientes; exemplo: a=1, b=-6, c=13.')
    if (minimo and q.a < 0) or (not minimo and q.a > 0):
        raise ValueError('Use a > 0 para este mínimo.' if minimo else 'Use a < 0 para este máximo.')
    if q.cenario != 'Temperatura de uma câmara fria' and yv <= 0:
        raise ValueError('yv deve ser maior que zero. '+('No cabo, aumente c até c > b²/(4a).' if q.cenario=='Cabo suspenso' else 'Ajuste os coeficientes para obter um máximo positivo.'))
    if xv < 0:
        raise ValueError('O vértice deve corresponder a uma distância, tempo ou quantidade não negativa.')
    if q.alvo_contexto == 'Raízes' and q.cenario != 'Cabo suspenso' and not any(r >= 0 for r in roots):
        raise ValueError('Este contexto precisa de pelo menos uma raiz real não negativa.')


def enunciado(q):
    c=q.cenario
    if c in PROJETEIS:
        intro={'Chute do goleiro': 'Durante uma partida de futebol, um goleiro chuta a bola, que descreve uma trajetória curva até voltar ao gramado.',
               'Saque de vôlei': 'Em um treino de vôlei, um atleta realiza um saque. Após deixar a mão do jogador, a bola sobe e depois desce em direção à quadra adversária.',
               'Jato de água': 'Em uma fonte ornamental, um bico lança um jato de água para cima. A água descreve uma trajetória curva antes de atingir o nível do solo.'}[c]
        temporal=q.eixo_contexto=='Tempo'
        significado=('o tempo, em segundos, decorrido desde o lançamento' if temporal else
                     'a distância horizontal, em metros, medida a partir do ponto de lançamento')
        definicao=f'A altura em relação ao solo, em metros, é modelada por {{f}}, em que x representa {significado}. Considere apenas a parte do movimento acima do solo.'
        pedidos={'Raízes': 'Determine as raízes reais do modelo e identifique a raiz não negativa correspondente ao retorno ao solo.',
                 'xv': 'Determine '+('o instante em que' if temporal else 'a distância horizontal na qual')+' a altura máxima é atingida.',
                 'yv': 'Determine a altura máxima atingida.',
                 'xv e yv': 'Determine a altura máxima e '+('o instante em que ela é atingida.' if temporal else 'a distância horizontal na qual ela é atingida.')}
    else:
        dados={
          'Lucro por quantidade vendida': (
            'Uma empresa estuda como a venda de um produto afeta seu resultado financeiro. O modelo considera a receita obtida e os custos da operação.',
            'O lucro, em reais, é dado por {f}, em que x representa a quantidade vendida, em milhares de unidades.',
            'a quantidade vendida que proporciona o maior lucro', 'o lucro máximo', 'as quantidades vendidas para as quais não há lucro nem prejuízo'),
          'Lucro ao longo dos dias': (
            'Durante uma campanha comercial, uma loja acompanha a evolução de seu lucro diário. Para analisar o período, a equipe utiliza um modelo quadrático.',
            'O lucro diário, em reais, é dado por {f}, em que x é o tempo, em dias, desde o início da campanha. Considere o tempo como uma variável contínua.',
            'o instante da campanha em que o lucro diário é máximo', 'o maior lucro diário previsto', 'os instantes em que o lucro diário é zero'),
          'Terreno com cerca': (
            'Uma família planeja cercar um terreno retangular. Ao variar uma das dimensões, a área disponível para plantio muda conforme o modelo a seguir.',
            'A área, em metros quadrados, é dada por {f}, em que x é uma das dimensões do terreno, em metros. Para um terreno utilizável, considere x positivo e área positiva.',
            'a dimensão x que permite obter a maior área', 'a maior área possível', 'os valores de x que anulam a área e representam os limites do modelo'),
          'Receita de ingressos': (
            'A organização de um espetáculo analisa a relação entre o preço dos ingressos e a arrecadação. Preços maiores podem reduzir a procura, conforme o modelo adotado.',
            'A receita, em reais, é dada por {f}, em que x representa o preço de um ingresso, em reais. Considere os preços não negativos para os quais a receita não é negativa.',
            'o preço que maximiza a receita', 'a receita máxima', 'os preços para os quais a receita é zero'),
          'Temperatura de uma câmara fria': (
            'Durante um ciclo de funcionamento, um sensor acompanha a temperatura de uma câmara fria. A temperatura diminui e, após atingir seu menor valor, volta a aumentar.',
            'A temperatura, em graus Celsius, é modelada por {f}, em que x é o tempo, em horas, desde o início da observação.',
            'o instante em que a temperatura é mínima', 'a menor temperatura atingida', 'os instantes em que a temperatura é de zero grau Celsius'),
          'Cabo suspenso': (
            'Um cabo está suspenso entre dois suportes. Para este exercício, seu perfil é aproximado por uma parábola, com um ponto mais baixo entre as extremidades.',
            'A altura do cabo em relação ao solo, em metros, é dada por {f}, em que x é a distância horizontal, em metros, medida a partir de uma referência fixa. Considere o trecho entre os suportes contendo o vértice.',
            'a posição horizontal do ponto mais baixo do cabo', 'a menor altura do cabo em relação ao solo', 'as posições em que o modelo prevê altura zero')}
        intro,definicao,x,y,r=dados[c]
        pedidos={'Raízes': f'Determine as raízes reais e interprete {r}. Desconsidere valores negativos de x.',
                 'xv': f'Determine {x}.', 'yv': f'Determine {y}.', 'xv e yv': f'Determine {x} e {y}.'}
        if c=='Cabo suspenso':
            pedidos['Raízes']='Investigue se a função possui raízes reais e explique o que isso indica sobre a possibilidade de o cabo tocar o solo.'
    return intro+' '+definicao.format(f='<b>'+q.expressao()+'</b>')+' '+pedidos[q.alvo_contexto]


def desenhar_imagem(pdf,q,rect):
    path=imagem(q)
    if path:
        x,y,w,h=rect
        pdf.drawImage(str(path),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
