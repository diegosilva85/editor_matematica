"""Limpeza conservadora dos espaços externos dos recortes do caderno."""


def aparar_branco(im,horizontal=True):
    mascara=im.convert('L').point(lambda p:255 if p<250 else 0)
    linhas=[y for y in range(im.height) if mascara.crop((0,y,im.width,y+1)).getbbox()]
    if len(linhas)>1:
        intervalos=[i for i in range(len(linhas)-1) if linhas[i+1]-linhas[i]>1]
        if intervalos:
            inicio=intervalos[-1]+1;rodape=linhas[inicio:]
            # Régua isolada, abaixo do conteúdo: tolerâncias proporcionais à
            # resolução, para a mesma limpeza na prévia e no PDF de impressão.
            if (len(rodape)<=max(2,im.width*.01)
                    and rodape[0]-linhas[inicio-1]>max(20,im.width*.07)
                    and max(mascara.crop((0,y,im.width,y+1)).histogram()[255]
                            for y in rodape)>.85*im.width):
                im=im.crop((0,0,im.width,min(im.height,linhas[inicio-1]+7)))
                mascara=mascara.crop((0,0,im.width,im.height))
    caixa=mascara.getbbox()
    if caixa is None:return im
    l,t,r,b=caixa;folga=max(2,round(im.width*.008))
    return im.crop((max(0,l-folga) if horizontal else 0,max(0,t-folga),
                    min(im.width,r+folga) if horizontal else im.width,min(im.height,b+folga)))
