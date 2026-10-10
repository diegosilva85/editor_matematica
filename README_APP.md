# Criador de gráficos — retas, parábolas, triângulos e sólidos

## Salvar e reabrir documentos

Todo PDF gerado tem um JSON acompanhante no mesmo diretório e com o mesmo nome: `atividade.pdf` e `atividade.json`. Isso inclui as visualizações temporárias e a exportação direta de exemplo. O JSON contém somente as páginas incluídas naquele PDF, com títulos, colunas, coeficientes, pontos, opções de marcação, posições e medidas.

Clique em **Carregar JSON** para restaurar o documento nas abas correspondentes, editar e exportar novamente. O arquivo é validado antes da alteração. Se houver conteúdo aberto, o aplicativo pede confirmação para substituí-lo; abas ausentes do arquivo ficam vazias. Raízes e frações digitadas em medidas e coeficientes exponenciais são preservadas; coordenadas x são armazenadas como números. Não é necessário instalar novas dependências.

O formato usa `formato: criador-de-graficos`, `versao: 1` e uma lista `paginas`. PDFs antigos sem JSON não podem ser reconstruídos automaticamente.

## Funções exponenciais

A quinta aba permite até 8 gráficos por página, com 1 ou 2 por linha. Escolha `b · a^x` ou `a^x + b`, informe a e b e os valores de x a marcar. Coeficientes e pontos aceitam decimais, frações e raízes: `1/2`, `√2`, `sqrt(2)`, `-√3/3`. A base deve ser positiva e diferente de 1; no formato multiplicativo, b não pode ser zero. Os valores calculados nos eixos são apresentados como aproximações decimais quando necessário. As fórmulas não aparecem no PDF. A página pode ser exportada junto das outras abas.

As páginas de primeiro e segundo grau não têm campos de nome e data. O enunciado de primeiro grau pede a expressão da função; o de segundo grau pede c, raízes, xv, yv e os sinais de delta e de a.

## Geometria espacial

A quarta aba permite até 12 sólidos por página, com até 3 por linha. Selecione a figura para visualizar o desenho e seus campos. As medidas são em centímetros e aceitam raízes e frações, como nas questões de triângulos.

- Cubo e tetraedro regular: aresta.
- Prisma retangular: comprimento, largura e altura.
- Prisma triangular reto de base equilátera e prisma hexagonal reto de base regular: aresta da base e altura.
- Pirâmide reta de base quadrada: aresta da base e altura.
- Cilindro: raio ou diâmetro e altura.
- Cone: raio ou diâmetro e altura ou geratriz (maior que o raio).
- Esfera: raio ou diâmetro.

Cada letra do PDF inclui o nome do sólido. Os desenhos usam símbolos para identificar as medidas, cujos valores aparecem abaixo. Para 12 sólidos, use 3 colunas; combinações que deixam os quadros pequenos demais solicitam mais colunas. A página de sólidos também pode ser reunida às demais abas no mesmo PDF.

## Triângulos retângulos

Também é possível escolher **Teorema de Pitágoras**. Selecione o lado a calcular (Cateto 1, Cateto 2 ou Hipotenusa) e informe os dois lados restantes. O campo de ângulo fica desativado; o desenho é calculado pelas medidas e não exibe ângulo agudo nem o nome do método no PDF. Raízes e frações continuam disponíveis. Os dois valores e a escolha de x são preservados no JSON, e arquivos anteriores continuam compatíveis.

A terceira aba permite até 15 questões por página, com até 3 por linha. Informe um ângulo entre 0 e 90 graus, escolha seno, cosseno ou tangente, o lado conhecido e sua medida. O outro lado da razão escolhida é marcado como x: seno relaciona oposto e hipotenusa; cosseno relaciona adjacente e hipotenusa; tangente relaciona oposto e adjacente.

Selecione uma das seis posições clicando no desenho ou no botão abaixo dele: virado para direita ou esquerda, de cabeça para baixo para direita ou esquerda, hipotenusa apontada para cima ou para baixo. Nas duas últimas, a hipotenusa fica horizontal acima ou abaixo do vértice reto. O formato é calculado pelo ângulo informado, com escala uniforme: 45° produz catetos iguais. As miniaturas acompanham as alterações do ângulo. Os catetos são identificados em relação ao ângulo marcado, independentemente da posição. Seno, cosseno e tangente aparecem apenas na configuração; no PDF cada exercício é identificado somente pela letra.

Medidas aceitas: `5`, `2,5`, `2√3`, `sqrt(2)`, `√3/3`, `3/2`, `2√3/√2`. Use apenas valores positivos; expressões com somas e subtrações não são aceitas. No PDF, as frações são verticais e os radicais recebem uma barra. Nenhuma dependência adicional é necessária.

Quando mais de uma aba contém questões, a exportação oferece incluir todas as abas preenchidas ou apenas a aba atual. Cada aba ocupa uma página.

Interface desktop em Python/Tkinter. Gera um PDF A4 com gráficos vetoriais, escalas individuais e quadros do mesmo tamanho. Nenhuma regra de função aparece no PDF.

## Aba de segundo grau

Em cada gráfico, escolha **Coeficientes** (a, b e c) ou **Raízes e a**. No segundo modo, informe a e uma ou duas raízes: uma raiz representa uma raiz dupla, com `f(x)=a(x-r)^2`; duas raízes representam `f(x)=a(x-r1)(x-r2)`. Os coeficientes b e c são calculados automaticamente, e suas entradas ficam desativadas. O modo, a quantidade de raízes e os valores informados são preservados no JSON. As opções de marcação continuam independentes do modo de entrada.

Escolha até 10 parábolas, com 1 ou 2 por linha, e clique em Criar documento. Preencha a, b e c (a diferente de zero). Cada gráfico tem quatro opções independentes: raízes reais, c no eixo y, xv no eixo x e yv no eixo y. As opções xv e yv desenham as respectivas projeções pontilhadas do vértice. A escala é automática e independe das opções marcadas. Raízes duplas aparecem uma vez; raízes não reais não são marcadas.

As abas mantêm seus dados separadamente. Quando ambas têm gráficos criados, Salvar PDF e Visualizar PDF perguntam se deve incluir as duas páginas. Sim gera primeiro a página de retas e depois a de parábolas; Não exporta somente a aba atual; Cancelar retorna à edição. Limpar aba remove os gráficos daquela aba após confirmação. O título pode ser definido por página.

## Executar neste computador

```bash
bash iniciar_app.sh
```

## Executar em outro computador

Instale Python 3 e Tkinter (no Ubuntu: pacote `python3-tk`). Instale a dependência e inicie:

```bash
python3 -m pip install -r requirements.txt
python3 app_graficos.py
```

## Uso

1. Escolha a quantidade de gráficos e de 1 a 3 colunas.
2. Clique em **Criar documento**.
3. Preencha `a` e `b` de cada função `y = ax + b`.
4. Escolha de 0 a 8 pontos e informe os valores de x; y é calculado automaticamente.
5. Clique em **Visualizar PDF** ou **Salvar PDF**.

Aceita vírgula ou ponto decimal. O coeficiente a não pode ser zero. É possível escolher até 15 gráficos por página, com tamanho automático; para 15, recomenda-se usar 3 colunas e 5 linhas. A quantidade de colunas pode ser alterada sem apagar os coeficientes. Clicar novamente em Criar documento substitui os campos após confirmação.

As marcações nos eixos correspondem aos pontos escolhidos. O zero na origem e a marcação do intercepto b só aparecem quando x = 0 estiver entre os pontos (outros pontos com y = 0 continuam sendo desenhados normalmente).

As retas são prolongadas dentro dos eixos; pontos vermelhos representam somente os x escolhidos. Os valores marcados têm até quatro algarismos significativos. Pontos muito próximos podem exigir ajustes de valores para evitar rótulos sobrepostos. A visualização abre no leitor de PDF do sistema e fica na pasta temporária.

Para gerar o exemplo sem abrir a interface:

```bash
python3 app_graficos.py --exemplo
```
# Questões contextuais de trigonometria

Na aba **Trigonometria**, cada questão permite escolher **Triângulo simples**
ou **Contextual**. Há 12 cenários ilustrados: avião, barco, escada, sombra,
observação de prédio, antena, chácara, rampa, pipa, cabo, teleférico e mergulho.
Escolha o ângulo, a medida conhecida e a medida pedida. Os campos aceitam
raízes e frações; olhos, mão e antena têm um campo de altura adicional.

As ilustrações contextuais são desenhos detalhados em preto e branco, armazenados
em `assets/contextos`, e não estão em escala. Mantenha essa pasta junto do app.
O editor e o PDF usam as mesmas imagens, preservando suas proporções. Quando houver
questões contextuais, o PDF usa até duas colunas e seis questões por página,
criando páginas adicionais automaticamente. Documentos apenas com triângulos
simples mantêm o limite de três colunas e 15 questões por página.
O JSON conserva os cenários e as escolhas; documentos antigos continuam aceitos.

O triângulo é sobreposto à ilustração na prévia e no PDF, com o ângulo e a
medida conhecida (em metros). Nenhum x, interrogação ou valor calculado identifica
o lado pedido. A ilustração e a sobreposição são esquemáticas, sem escala:
os valores indicados prevalecem sobre os ângulos aparentes da perspectiva.
Quando a medida conhecida é uma altura total, sua cota vai até o chão;
as alturas adicionais dos olhos, da mão e da antena permanecem no enunciado.
# Progressão aritmética

A aba **Progressão aritmética** permite até 12 questões, em uma ou duas colunas.
O modo **Sem contexto** oferece os seguintes tipos, com prévia do enunciado:

- **Termo geral:** descobrir o valor de um termo, a posição de um número ou a
  razão. Informe a posição e o valor do termo de referência; os demais campos
  aparecem conforme a incógnita. Para a razão, informe dois termos em posições
  diferentes. Para a posição, informe os dois valores de termos e a razão.
- **Soma dos termos:** escolha descobrir a₁, aₙ, n, Sₙ ou a razão e marque os dados que
  aparecerão. É necessário fornecer dados que determinem uma resposta única; seleções
  insuficientes ou inconsistentes são sinalizadas antes da exportação.

Aceita negativos, decimais e frações. Posições e quantidades são inteiros
positivos. A resposta não aparece no PDF. Os dados são preservados no JSON,
e esta aba pode ser exportada junto com as outras cinco abas.

### Contextos de termo geral

Escolha **Termo geral → Contextual** e um dos 11 cenários. Há opções de
corrida/natação, dia/mês para depósitos e seguidores, e distância ou duração
para o treino do ciclista. A incógnita continua sendo valor, posição ou razão.
Use razão positiva para aumento e negativa para redução; os cenários têm
validação de quantidades positivas, itens inteiros e valores monetários em centavos.
Somente os dados fornecidos entram no enunciado; não há gabarito no PDF.

Documentos com contextos de PA usam até duas colunas e seis questões por página,
com paginação automática. Todas as escolhas são preservadas no JSON, e documentos
antigos continuam funcionando. Os mesmos cenários também estão disponíveis para
**Soma dos termos**, com os totais adequados a cada situação. A razão pode ser
fornecida no enunciado ou escolhida como incógnita.

## Editor de listas mistas

Na aba **2º grau**, a apresentação **Expressão da função** cria questões sem
gráfico, exibindo `f(x) = ax² + bx + c`. Marque **Raízes reais** e/ou
**Coordenadas do vértice** para definir o que será pedido. A entrada continua
aceitando coeficientes ou raízes e coeficiente a (uma raiz significa raiz dupla).
O modo também está disponível no editor de listas e é preservado no JSON.
Documentos antigos continuam abrindo no modo gráfico.
Coeficientes e raízes aceitam frações, decimais com vírgula e radicais:
`-1/2`, `0,5`, `√2`, `2√3/3`, `1/√2` e `sqrt(2)`. No modo por raízes,
a expressão expandida mantém valores exatos. A notação digitada nos coeficientes
é preservada. Atualize as dependências para instalar o cálculo simbólico:
`python -m pip install -r requirements.txt`.

Clique em **Criar Lista**, fora das abas, para abrir **Nova Lista de Exercícios**.
As abas tradicionais continuam funcionando de forma independente.

1. Defina o título, de 1 a 3 questões por linha e o máximo de 1 a 12 por página.
2. Clique em **Acrescentar questão**, escolha o conteúdo e preencha o formulário
   já utilizado nas abas. A prévia à direita acompanha as alterações.
3. Clique em **Acrescentar à lista**. Para continuar, use **Acrescentar outra questão**.
4. Na lista principal, selecione uma questão para editar, remover ou mover com
   as setas. A prévia permite navegar pelas páginas e ampliar/reduzir.
5. **Salvar PDF + JSON** gera os dois arquivos. **Carregar JSON**, nessa janela,
   reabre listas mistas e também importa documentos antigos criados nas abas.

A ordem das questões é preservada, com numeração contínua. Cada linha tem
quadros alinhados; textos extensos aumentam a altura e podem fazer a página
conter menos questões que o limite escolhido. Questões não são divididas entre
páginas. O PDF usa gráficos vetoriais e a prévia é renderizada do próprio PDF.

Para habilitar as prévias internas, atualize as dependências no ambiente virtual:

```bash
python -m pip install -r requirements.txt
```

As prévias usam `pypdfium2` (não exigem Poppler instalado no computador).

### Contextos de funções quadráticas

Em **2º grau → Expressão da função**, escolha um contexto ou mantenha
**Sem contexto** para a questão literal. Os nove cenários incluem chute do
goleiro, saque de vôlei, jato de água, lucro por quantidade vendida, lucro ao
longo dos dias, terreno com cerca, receita de ingressos, temperatura de uma
câmara fria e cabo suspenso.

Escolha a pergunta: **Raízes**, **xv**, **yv** ou **xv e yv**. Nos lançamentos,
é possível definir x como distância horizontal ou tempo. Os coeficientes
continuam sendo informados diretamente ou por raízes e a; o app verifica
a concavidade e a coerência básica dos valores com o contexto escolhido.

**Incluir imagem** é opcional e fica habilitado nos quatro cenários com arte:
goleiro, vôlei, jato de água e cabo. As ilustrações não estão em escala e não
são recalculadas a partir dos coeficientes. Vôlei e goleiro usam as versões
revisadas com trajetória. Todas as escolhas ficam no JSON e também funcionam
no editor de listas e em sua prévia. Na aba tradicional, prefira até quatro
questões por página quando houver imagens; se o conteúdo não couber, o app
pede menos questões ou uma coluna, sem cortar o texto. No editor de listas,
a paginação se ajusta automaticamente.
