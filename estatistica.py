"""Tabelas estatísticas, cálculos ponderados exatos e geração com metas."""
from collections import Counter
from dataclasses import dataclass,field
from fractions import Fraction
from decimal import Decimal,localcontext
from xml.sax.saxutils import escape
import random
import time
from progressao import numero
from estatistica_multicolunas import TIPOS_MULTIPLOS,COMPARACAO,FALTANTE

# nome: identificação, medida, população, unidade, mínimo, máximo, passo
CONTEXTOS={
 'Notas de alunos': ('Aluno','Nota','alunos','pontos','0','10','0,5'),
 'Salários de funcionários': ('Funcionário','Salário (R$)','funcionários','reais','1000','10000','100'),
 'Glicose em amostras de sangue': ('Paciente','Glicose (mg/dL)','pacientes','mg/dL','50','200','1'),
 'Compras no mês': ('Dia','Gasto (R$)','dias observados','reais','0','500','10'),
 'Hábitos musicais': ('Participante','Escuta semanal (h)','participantes','horas','0','30','1'),
 'Livros lidos': ('Leitor','Livros no ano','leitores','livros','0','20','1'),
 'Temperaturas diárias': ('Dia','Temperatura (°C)','dias observados','graus Celsius','10','40','1'),
 'Tempo de deslocamento': ('Pessoa','Tempo (min)','pessoas','minutos','5','120','5'),
 'Produção de uma oficina': ('Dia','Peças produzidas','dias de produção','peças','0','100','1'),
 'Consumo de água': ('Residência','Consumo mensal (m³)','residências','metros cúbicos','0','50','1'),
 'Pontuação no basquete': ('Jogador','Pontos','jogadores','pontos','0','50','1')}
INTEIROS={'Livros lidos','Produção de uma oficina','Pontuação no basquete'}
TIPOS=('Simples','Frequência',*TIPOS_MULTIPLOS)
MEDIDAS=('media','moda','mediana')
NOMES={'media':'média','moda':'moda','mediana':'mediana'}


def fmt(x):
    x=Fraction(x)
    d=x.denominator
    for p in (2,5):
        while d%p==0: d//=p
    if d!=1: return str(x)
    with localcontext() as ctx:
        ctx.prec=60
        s=format(Decimal(x.numerator)/Decimal(x.denominator),'f')
    return (s.rstrip('0').rstrip('.') if '.' in s else s).replace('.',',')


def resumir(contagens):
    total=sum(contagens.values())
    if total<=0: raise ValueError('Informe ao menos uma observação.')
    def ordem(pos):
        acumulado=0
        for v,f in sorted(contagens.items()):
            acumulado+=f
            if acumulado>=pos: return v
    media=sum(v*f for v,f in contagens.items())/total
    mediana=(ordem((total+1)//2)+ordem((total+2)//2))/2
    maior=max(contagens.values())
    # Convenção escolar: todos os valores igualmente frequentes = amodal.
    modas=[] if len(contagens)>1 and len(set(contagens.values()))==1 else sorted(v for v,f in contagens.items() if f==maior)
    return dict(media=media,mediana=mediana,modas=modas,total=total)


def conferir_valor(cenario,v):
    if abs(v)>1_000_000: raise ValueError('Use valores de magnitude até 1000000.')
    if cenario!='Temperaturas diárias' and v<0: raise ValueError('Este contexto não aceita valores negativos.')
    if cenario=='Notas de alunos' and not 0<=v<=10: raise ValueError('As notas devem estar entre 0 e 10.')
    if cenario in INTEIROS and v.denominator!=1: raise ValueError('Livros, peças e pontos devem ser quantidades inteiras.')
    if cenario in ('Salários de funcionários','Compras no mês') and (v*100).denominator!=1:
        raise ValueError('Valores monetários devem ser múltiplos de um centavo.')


@dataclass
class Estatistica:
    tipo: str = 'Simples'
    cenario: str = 'Notas de alunos'
    linhas: list = field(default_factory=lambda:[['Aluno 1','6'],['Aluno 2','7'],['Aluno 3','7'],['Aluno 4','8'],['Aluno 5','9']])
    pedir_media: bool = True
    pedir_moda: bool = True
    pedir_mediana: bool = True
    meta_media: str = ''
    meta_moda: str = ''
    meta_mediana: str = ''
    minimo: str = '0'
    maximo: str = '10'
    passo: str = '0,5'
    observacoes: str = '15'
    quantidade_medidas: str = '4'

    def contagens(self):
        if self.tipo not in TIPOS or self.cenario not in CONTEXTOS: raise ValueError('Escolha o tipo de tabela e o contexto.')
        if not isinstance(self.linhas,list) or not 2<=len(self.linhas)<=20: raise ValueError('Use de 2 a 20 linhas.')
        counts=Counter(); labels=set()
        for linha in self.linhas:
            if not isinstance(linha,(list,tuple)) or len(linha)!=2 or not all(isinstance(s,str) and len(s)<=80 for s in linha):
                raise ValueError('Cada linha deve conter dois campos textuais de até 80 caracteres.')
            x,y=linha
            if self.tipo=='Simples':
                if not x.strip() or x.strip() in labels: raise ValueError('Preencha identificações não repetidas na primeira coluna.')
                labels.add(x.strip()); v=numero(y); f=1
            else:
                v=numero(x); f=numero(y)
                if f.denominator!=1 or not 1<=f<=100000: raise ValueError('Frequências devem ser inteiros de 1 a 100000.')
                if v in counts: raise ValueError('Agrupe valores iguais em uma única linha de frequência.')
                f=int(f)
            conferir_valor(self.cenario,v); counts[v]+=f
        return counts

    def validar(self):
        if self.tipo in TIPOS_MULTIPLOS:
            from estatistica_multicolunas import analisar
            analisar(self)
        else:self.contagens()
        if any(type(getattr(self,'pedir_'+k)) is not bool for k in MEDIDAS): raise ValueError('Seleções inválidas.')
        if self.tipo==COMPARACAO:
            if not (self.pedir_media or self.pedir_mediana):raise ValueError('Selecione maior média e/ou maior mediana.')
        elif self.tipo!=FALTANTE and not any(getattr(self,'pedir_'+k) for k in MEDIDAS): raise ValueError('Selecione média, moda ou mediana.')
        for k in ('meta_media','meta_moda','meta_mediana','minimo','maximo','passo','observacoes','quantidade_medidas'):
            if not isinstance(getattr(self,k),str) or len(getattr(self,k))>80: raise ValueError('Configuração de geração inválida.')

    def resumo(self):
        if self.tipo in TIPOS_MULTIPLOS:
            from estatistica_multicolunas import analisar
            return analisar(self)
        return resumir(self.contagens())

    def cabecalhos(self):
        if self.tipo in TIPOS_MULTIPLOS:
            from estatistica_multicolunas import cabecalhos
            return cabecalhos(self)
        c=CONTEXTOS[self.cenario]
        return (c[0],c[1]) if self.tipo=='Simples' else (c[1],'Frequência')

    def enunciado(self):
        self.validar()
        if self.tipo in TIPOS_MULTIPLOS:
            from estatistica_multicolunas import enunciado
            return enunciado(self)
        c=CONTEXTOS[self.cenario]
        intro={
          'Notas de alunos':'Uma turma realizou uma avaliação com notas de zero a dez.',
          'Salários de funcionários':'Uma empresa levantou os salários mensais de seus funcionários.',
          'Glicose em amostras de sangue':'Uma atividade escolar utiliza dados fictícios de glicose em amostras de sangue. Os dados servem apenas ao estudo de estatística, sem interpretação clínica.',
          'Compras no mês':'Uma pessoa registrou o total gasto em compras em alguns dias de um mês. Considere somente os dias observados.',
          'Hábitos musicais':'Uma pesquisa sobre hábitos musicais registrou quantas horas cada participante escuta música por semana. Analise o tempo de escuta, não os gêneros musicais preferidos.',
          'Livros lidos':'Uma biblioteca pesquisou quantos livros seus leitores concluíram no último ano.',
          'Temperaturas diárias':'Uma estação registrou a temperatura no mesmo horário em dias de um período de observação.',
          'Tempo de deslocamento':'Uma pesquisa registrou o tempo de deslocamento de algumas pessoas até o trabalho.',
          'Produção de uma oficina':'Uma oficina registrou a quantidade de peças produzidas em cada dia de um período.',
          'Consumo de água':'Um levantamento registrou o consumo mensal de água de algumas residências.',
          'Pontuação no basquete':'Uma equipe registrou os pontos marcados por seus jogadores em uma partida de basquete.'}[self.cenario]
        desc=('Cada linha apresenta uma observação individual.' if self.tipo=='Simples' else
              f'A frequência indica quantos {c[2]} apresentaram cada valor; considere essas repetições nos cálculos.')
        pedidos=[NOMES[k] for k in MEDIDAS if getattr(self,'pedir_'+k)]
        pedido=', '.join(pedidos[:-1])+' e '+pedidos[-1] if len(pedidos)>1 else pedidos[0]
        return intro+' '+desc+' Com base na tabela, determine '+pedido+'.'


def apoio(q):
    if q.tipo in TIPOS_MULTIPLOS:
        from estatistica_multicolunas import apoio
        return apoio(q)
    dica='Média: soma dos valores dividida pelo total de observações. Mediana: posições centrais dos valores ordenados. '
    dica+='Na frequência, cada valor é repetido conforme sua frequência. ' if q.tipo=='Frequência' else 'A primeira coluna identifica observações; os cálculos usam somente a segunda. '
    dica+='Moda: valor(es) mais frequente(s). Frequências todas iguais: amodal (convenção adotada).'
    if q.cenario in INTEIROS: dica+=' Use quantidades inteiras.'
    if q.cenario=='Notas de alunos': dica+=' Notas de 0 a 10.'
    try:
        s=q.resumo()
        texto=f'N = {s["total"]}\nMédia = {fmt(s["media"])}\nMediana = {fmt(s["mediana"])}\nModa = '+(', '.join(map(fmt,s['modas'])) if s['modas'] else 'amodal')
        avisos=[]
        for key in MEDIDAS:
            raw=getattr(q,'meta_'+key)
            if raw.strip():
                target=numero(raw)
                ok=s['modas']==[target] if key=='moda' else s[key]==target
                avisos.append(f'Meta de {NOMES[key]}: '+('atingida' if ok else 'não atingida'))
        return texto+'\n'+'; '.join(avisos),dica
    except ValueError as exc: return 'Ajuste necessário: '+str(exc),dica


def gerar(q,quantidade,seed=None,_deadline=None):
    """Busca limitada; só devolve uma tabela se todas as metas forem exatas."""
    if type(quantidade) is not int or not 2<=quantidade<=20: raise ValueError('Escolha de 2 a 20 linhas.')
    if q.tipo not in TIPOS or q.cenario not in CONTEXTOS: raise ValueError('Contexto ou tipo inválido.')
    if q.tipo in TIPOS_MULTIPLOS:
        from estatistica_multicolunas import gerar
        return gerar(q,quantidade,seed)
    lo,hi,step=map(numero,(q.minimo,q.maximo,q.passo))
    if step<=0 or hi<=lo: raise ValueError('Use mínimo menor que máximo e passo positivo.')
    conferir_valor(q.cenario,lo);conferir_valor(q.cenario,hi)
    if q.cenario in INTEIROS and (lo.denominator!=1 or step.denominator!=1): raise ValueError('Neste contexto, use passo inteiro.')
    if q.cenario in ('Salários de funcionários','Compras no mês') and (step*100).denominator!=1: raise ValueError('Use passo em centavos inteiros.')
    slots=int((hi-lo)//step)+1
    if slots>10001: raise ValueError('Use até 10001 valores possíveis: aumente o passo ou reduza o intervalo.')
    goals={k:numero(getattr(q,'meta_'+k)) for k in MEDIDAS if getattr(q,'meta_'+k).strip()}
    if any(not lo<=v<=hi for v in goals.values()): raise ValueError('As metas devem estar entre o mínimo e o máximo.')
    if 'moda' in goals and (goals['moda']-lo)%step: raise ValueError('A moda precisa ser um valor possível no passo escolhido.')
    total=Fraction(quantidade) if q.tipo=='Simples' else numero(q.observacoes)
    if total.denominator!=1: raise ValueError('O total de observações deve ser inteiro.')
    total=int(total)
    if not quantidade<=total<=200: raise ValueError('Use total de observações entre a quantidade de linhas e 200.')
    if q.tipo=='Frequência' and slots<quantidade: raise ValueError('O intervalo não contém valores distintos suficientes para as linhas.')
    if 'media' in goals and (goals['media']*total-lo*total)%step:
        raise ValueError('A média não é possível com este total e passo. Ajuste o passo ou o total de observações.')
    rng=random.Random(seed); grid=[lo+i*step for i in range(slots)]; end=min(time.monotonic()+5,_deadline) if _deadline is not None else time.monotonic()+5
    def satisfaz(vals,weights):
        counts=Counter()
        for v,w in zip(vals,weights): counts[v]+=w
        if q.tipo=='Frequência' and len(counts)!=quantidade: return None
        if any(v<lo or v>hi or (v-lo)%step for v in counts): return None
        s=resumir(counts)
        if any((s['modas']!=[v] if k=='moda' else s[k]!=v) for k,v in goals.items()): return None
        return counts
    for tentativa in range(16000):
        if time.monotonic()>end: break
        if q.tipo=='Simples':
            vals=[rng.choice(grid) for _ in range(total)]; weights=[1]*total
            if 'moda' in goals:
                for i in range(rng.randint(2,total)): vals[i]=goals['moda']
        else:
            vals=rng.sample(grid,quantidade); weights=[1]*quantidade
            if 'moda' in goals: vals[0]=goals['moda']
            for _ in range(total-quantidade): weights[rng.randrange(quantidade)]+=1
            if 'moda' in goals:
                idx=max(range(quantidade),key=lambda i:weights[i])
                weights[0],weights[idx]=weights[idx],weights[0]
        # Impõe a mediana na(s) posição(ões) central(is), antes de ajustar a soma.
        if 'mediana' in goals:
            order=sorted(range(len(vals)),key=lambda i:vals[i]); acc=0; middle=[]
            for i in order:
                old=acc;acc+=weights[i]
                if any(old<p<=acc for p in ((total+1)//2,(total+2)//2)): middle.append(i)
            if len(middle)==1: vals[middle[0]]=goals['mediana']
            else: vals[middle[1]]=2*goals['mediana']-vals[middle[0]]
        candidates=[vals]
        if 'media' in goals:
            delta=goals['media']*total-sum(v*w for v,w in zip(vals,weights))
            candidates=[]
            for i in rng.sample(range(len(vals)),len(vals)):
                candidate=vals.copy();candidate[i]+=delta/weights[i];candidates.append(candidate)
        for candidate in candidates:
            counts=satisfaz(candidate,weights)
            if counts is None: continue
            if q.tipo=='Frequência': rows=[[fmt(v),str(f)] for v,f in sorted(counts.items())]
            else:
                rng.shuffle(candidate)
                label=CONTEXTOS[q.cenario][0]
                rows=[[q.linhas[i][0] if i<len(q.linhas) and q.tipo=='Simples' else f'{label} {i+1}',fmt(v)] for i,v in enumerate(candidate)]
            from dataclasses import replace
            replace(q,linhas=rows).validar()
            return rows
    raise ValueError('Não encontrei uma tabela com todas as metas na busca limitada. Isso não prova impossibilidade. Tente novamente, ajuste o passo/intervalo, as metas, as linhas ou o total de observações. A tabela atual foi preservada.')


def tabela(q,width):
    from reportlab.platypus import Table,TableStyle,Paragraph
    from reportlab.lib.styles import ParagraphStyle
    multi=q.tipo in TIPOS_MULTIPLOS
    style=ParagraphStyle('celula',fontName='Helvetica',fontSize=8 if multi else 9,leading=10 if multi else 11)
    rows=[list(row) for row in q.linhas]
    if q.tipo==FALTANTE:
        n=int(q.quantidade_medidas)
        for row in rows:
            if row[n].strip() in ('','?','x','X'):row[n]='?'
    data=[list(q.cabecalhos())]+rows
    cells=[[Paragraph(escape(v),style) for v in row] for row in data]
    cols=len(data[0])
    widths=[width*.25]+[width*.75/(cols-1)]*(cols-1) if multi else [width*.53,width*.47]
    table=Table(cells,colWidths=widths,hAlign='CENTER')
    table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,'#707070'),('BACKGROUND',(0,0),(-1,0),'#eeeeee'),
                              ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    return table


def desenhar_pagina(pdf,items,colunas,titulo):
    from listas import Lista,planejar,paragrafo
    from reportlab.lib.pagesizes import A4
    W,H=A4
    lista=Lista(titulo or 'Estatística',colunas,4,[(7,q) for q in items])
    for numero_pagina,page in enumerate(planejar(lista)):
        if numero_pagina: pdf.showPage()
        pdf.setFont('Helvetica-Bold',16);pdf.drawCentredString(W/2,H-38,lista.titulo[:70])
        for index,x,y,w,h,th,gh in page:
            q=items[index];p,_=paragrafo(7,q,index+1,w)
            pdf.setStrokeGray(.65);pdf.roundRect(x,y,w,h,5)
            p.drawOn(pdf,x+10,y+h-12-th)
            t=tabela(q,w-20);_,ht=t.wrap(w-20,10000);t.drawOn(pdf,x+10,y+h-th-22-ht)
