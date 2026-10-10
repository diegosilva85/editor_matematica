"""Cenários exclusivos para interpretação das raízes de uma quadrática."""
CENARIOS = ('Bola lançada verticalmente', 'Lucro nulo de uma empresa',
            'Temperatura igual a zero', 'Arco da entrada de um parque',
            'Encontro de dois ciclistas', 'Nível de um reservatório')
IMAGENS = dict(zip((CENARIOS[0],CENARIOS[3],CENARIOS[4],CENARIOS[5]),
                  ('bola_vertical.png','arco_entrada.png','dois_ciclistas.png','reservatorio_nivel.png')))

TEXTOS = {
 CENARIOS[0]: ('Durante um treino, um atleta lança uma bola verticalmente para cima. Após subir, ela desce até atingir o solo.',
              'A altura em relação ao solo, em metros, é modelada por {f}, em que x é o tempo, em segundos, desde o lançamento.',
              'Determine as raízes da função e identifique após quantos segundos a bola atinge o solo. Explique por que uma das raízes não corresponde a um instante desse movimento.'),
 CENARIOS[1]: ('Uma pequena empresa produz e vende determinado produto. Seu resultado financeiro depende da receita obtida com as vendas e dos custos de produção.',
              'O lucro é modelado por {f}, em milhares de reais, sendo x a quantidade vendida, em centenas de unidades.',
              'Determine as raízes e indique as quantidades de produtos, em unidades, para as quais a empresa não tem lucro nem prejuízo.'),
 CENARIOS[2]: ('Durante um ciclo de funcionamento, um sensor acompanha a temperatura de uma câmara fria. Ela diminui e, após atingir seu menor valor, volta a aumentar.',
              'A temperatura, em graus Celsius, é modelada por {f}, em que x é o tempo, em horas, desde o início do acompanhamento. O ciclo observado abrange as duas passagens por zero grau Celsius.',
              'Em quais instantes a temperatura da câmara fria é igual a zero grau Celsius?'),
 CENARIOS[3]: ('A entrada de um parque possui um arco cujo contorno interno pode ser aproximado por uma parábola. Suas duas extremidades encontram o chão.',
              'A altura do contorno em relação ao chão, em metros, é dada por {f}, em que x é a posição horizontal, em metros, medida a partir de uma referência à esquerda da entrada. Considere o trecho acima do chão.',
              'Determine as posições em que o arco encontra o chão e calcule a largura da entrada entre esses pontos.'),
 CENARIOS[4]: ('Dois ciclistas percorrem uma pista no mesmo sentido. Um observador acompanha suas posições durante um intervalo que inclui dois encontros.',
              'A diferença entre a posição do primeiro e a do segundo é dada por {f}, em metros, sendo x o tempo em segundos desde o início da observação. Valores positivos indicam que o primeiro está à frente; valores negativos indicam o contrário.',
              'Em quais instantes os dois ciclistas estão na mesma posição?'),
 CENARIOS[5]: ('Após a abertura de uma comporta, o nível de um reservatório diminui e, posteriormente, volta a subir devido à entrada de água.',
              'A diferença entre o nível da água e uma marca de referência é dada por {f}, em centímetros, em que x é o tempo em horas. A observação começa antes da primeira passagem pela marca e termina depois da segunda.',
              'Em quais instantes a água está exatamente na altura da marca de referência? Valores negativos da função indicam nível abaixo da marca.')}


def orientacao(c):
    if c==CENARIOS[0]:
        return 'Use a < 0, b > 0 e c > 0: lançamento para cima, acima do solo. As raízes devem ter sinais opostos, com média positiva. Exemplo: a=-5, b=15, c=20; ou a=-5 e raízes -1 e 4.'
    exemplos={CENARIOS[1]:'a=-1, b=14, c=-40; raízes 4 e 10',
              CENARIOS[2]:'a=1, b=-8, c=12; raízes 2 e 6',
              CENARIOS[3]:'a=-1, b=10, c=-16; raízes 2 e 8',
              CENARIOS[4]:'a=1, b=-7, c=10; raízes 2 e 5',
              CENARIOS[5]:'a=1, b=-7, c=6; raízes 1 e 6'}
    sinal=('a < 0' if c in (CENARIOS[1],CENARIOS[3]) else
           'a > 0' if c in (CENARIOS[2],CENARIOS[5]) else 'a diferente de zero')
    return f'Use {sinal} e duas raízes reais, distintas e positivas. No modo Coeficientes, Δ deve ser positivo. Exemplo: {exemplos[c]}. No modo Raízes e a, informe essas duas raízes e o mesmo a.'


def validar(q, roots):
    if q.alvo_contexto!='Raízes':
        raise ValueError('Este cenário pertence ao grupo Raízes, não ao grupo Vértice.')
    c=q.cenario
    if len(roots)!=2:
        raise ValueError('Este enunciado precisa de duas raízes reais distintas (Δ > 0).')
    if c==CENARIOS[0]:
        if not (q.a<0 and q.b>0 and q.c>0 and roots[0]<0<roots[1]):
            raise ValueError('Para o lançamento vertical, use a < 0, b > 0 e c > 0; exemplo: -5, 15, 20.')
        return
    if not all(r>0 for r in roots):
        raise ValueError('Use duas raízes positivas, para que os dois eventos façam sentido no contexto.')
    if c in (CENARIOS[1],CENARIOS[3]) and q.a>=0:
        raise ValueError('Use a < 0: a curva deve ter concavidade para baixo.')
    if c in (CENARIOS[2],CENARIOS[5]) and q.a<=0:
        raise ValueError('Use a > 0: a grandeza diminui e depois aumenta.')


def enunciado(q):
    intro,modelo,pergunta=TEXTOS[q.cenario]
    return intro+' '+modelo.format(f='<b>'+q.expressao()+'</b>')+' '+pergunta
