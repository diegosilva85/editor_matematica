"""Composição compacta de questões do acervo, inteiras e sem gabarito."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from boss_enem import preparar_imagem
from acervo_enem import PDF_LOCK, salvar_json

LARGURA=A4[0]-20*mm
ALTURA=A4[1]-30*mm
GAP=4*mm
LEGENDA=14


def encaixar(itens,escala):
    paginas=[]
    for item in sorted(itens,key=lambda i:i['altura'],reverse=True):
        s=min(escala,LARGURA/item['largura'],(ALTURA-LEGENDA)/item['altura'])
        w,h=item['largura']*s,item['altura']*s+LEGENDA
        # Colunas com largura estável: diferenças de poucos pixels nos recortes
        # não devem impedir que outra questão caiba logo abaixo.
        faixa=(LARGURA-GAP)/2 if w<=(LARGURA-GAP)/2 else LARGURA
        opcoes=[]
        for p,pagina in enumerate(paginas):
            for r,(x,y,rw,rh) in enumerate(pagina['livres']):
                if faixa<=rw+1e-6 and h<=rh+1e-6:
                    opcoes.append((rw*rh-w*h,p,r))
        if opcoes:
            _,p,r=min(opcoes)
        else:
            paginas.append(dict(livres=[(0,0,LARGURA,ALTURA)],itens=[]))
            p,r=len(paginas)-1,0
        pagina=paginas[p];x,y,rw,rh=pagina['livres'].pop(r)
        pagina['itens'].append(dict(item=item,x=x,y=y,largura=w,altura=h,escala=s))
        # Partições disjuntas: coluna direita completa + espaço sob a questão.
        if rw-faixa>GAP:pagina['livres'].append((x+faixa+GAP,y,rw-faixa-GAP,rh))
        if rh-h>GAP:pagina['livres'].append((x,y+h+GAP,faixa,rh-h-GAP))
    return paginas


def gerar_lista(questoes,provas,progresso=lambda n,total:None):
    if not questoes:raise ValueError('Selecione pelo menos uma questão.')
    itens=[]
    for n,q in enumerate(questoes):
        im,p=preparar_imagem(q,provas[q['prova']])
        itens.append(dict(q=q,imagem=im,largura=p['largura']/p['escala'],altura=p['altura']/p['escala']))
        progresso(n+1,len(questoes))
    # Só reduz mais se isso efetivamente economizar páginas.
    paginas=min((encaixar(itens,s) for s in (1,.95,.9,.85,.8)),key=len)
    out=BytesIO();pdf=canvas.Canvas(out,pagesize=A4);pdf.setTitle('Lista de exercícios — Enem')
    ordem=[];numero=0
    for n,pagina in enumerate(paginas,1):
        pdf.setFont('Helvetica-Bold',12);pdf.drawString(10*mm,A4[1]-12*mm,'Lista de exercícios - Enem')
        pdf.setFont('Helvetica',9);pdf.drawRightString(A4[0]-10*mm,6*mm,f'{n} / {len(paginas)}')
        for bloco in sorted(pagina['itens'],key=lambda b:(b['x'],b['y'])):
            numero+=1;q=bloco['item']['q'];ordem.append(q)
            x=10*mm+bloco['x'];topo=A4[1]-20*mm-bloco['y']
            pdf.setFont('Helvetica-Bold',8)
            pdf.drawString(x,topo-9,f"{numero}. Enem {q['ano']} | {q['prova']} | Q{q['numero']}")
            h=bloco['altura']-LEGENDA
            pdf.drawImage(ImageReader(bloco['item']['imagem']),x,topo-LEGENDA-h,bloco['largura'],h)
        pdf.showPage()
    pdf.save();dados=out.getvalue();previews=[]
    import pypdfium2 as pdfium
    with PDF_LOCK,pdfium.PdfDocument(dados) as doc:
        for page in doc:
            bitmap=page.render(scale=1.1)
            try:previews.append(bitmap.to_pil().convert('RGB').copy())
            finally:bitmap.close();page.close()
    return dados,previews,ordem


def salvar_lista(destino,dados,questoes,provas):
    from pathlib import Path
    path=Path(destino)
    path.write_bytes(dados)
    salvar_json(path.with_suffix('.json'),dict(tipo='lista_enem',versao=1,questoes=questoes,
        provas=[provas[k] for k in dict.fromkeys(q['prova'] for q in questoes)]))


def abrir_preview(parent,dados,previews,questoes,provas,ao_salvar):
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    from PIL import ImageTk
    win=tk.Toplevel(parent);win.title('Lista de exercícios — Enem');win.geometry('850x900')
    win.transient(parent);win.grab_set()
    nav=ttk.Frame(win,padding=10);nav.pack(fill='x');pagina=[0]
    area=tk.Canvas(win,background='#ddd')
    y=ttk.Scrollbar(win,command=area.yview);x=ttk.Scrollbar(win,orient='horizontal',command=area.xview)
    x.pack(side='bottom',fill='x');y.pack(side='right',fill='y');area.pack(fill='both',expand=True)
    area.configure(yscrollcommand=y.set,xscrollcommand=x.set)
    def mostrar(delta=0):
        pagina[0]=max(0,min(len(previews)-1,pagina[0]+delta));im=previews[pagina[0]]
        area.delete('all');area._photo=ImageTk.PhotoImage(im)
        area.create_image(10,10,image=area._photo,anchor='nw')
        area.configure(scrollregion=(0,0,im.width+20,im.height+20));area.yview_moveto(0)
        rotulo.configure(text=f"Página {pagina[0]+1} de {len(previews)} | {len(questoes)} questões")
        anterior.configure(state='normal' if pagina[0] else 'disabled')
        proxima.configure(state='normal' if pagina[0]<len(previews)-1 else 'disabled')
    anterior=ttk.Button(nav,text='◀ Anterior',command=lambda:mostrar(-1));anterior.pack(side='left')
    proxima=ttk.Button(nav,text='Próxima ▶',command=lambda:mostrar(1));proxima.pack(side='left',padx=5)
    rotulo=ttk.Label(nav);rotulo.pack(side='left',padx=10)
    def salvar():
        destino=filedialog.asksaveasfilename(parent=win,title='Salvar lista',defaultextension='.pdf',
            initialfile='lista_enem.pdf',filetypes=[('PDF','*.pdf')])
        if not destino:return
        try:salvar_lista(destino,dados,questoes,provas)
        except OSError as exc:messagebox.showerror('Salvar lista',str(exc),parent=win);return
        ao_salvar(questoes);win.destroy()
        messagebox.showinfo('Lista salva','PDF e JSON salvos. A seleção foi liberada para uma nova lista.',parent=parent)
    ttk.Button(nav,text='Salvar lista',command=salvar).pack(side='right')
    area.bind('<MouseWheel>',lambda e:area.yview_scroll(-int(e.delta/120),'units'))
    area.bind('<Button-4>',lambda e:area.yview_scroll(-3,'units'))
    area.bind('<Button-5>',lambda e:area.yview_scroll(3,'units'))
    mostrar()
