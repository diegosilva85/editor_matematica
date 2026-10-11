import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import Mock,patch
import pypdfium2 as pdfium
from provas import (Prova,QuestaoProva,dados_prova,validar_prova,pdf_prova,
                    salvar_prova,carregar_prova,salvar_rascunho,quadro,compor,capa)
from app_graficos import Funcao
from parabolas import Parabola
from progressao import Progressao
from geometria_plana import FiguraPlana
from estatistica import Estatistica
import test_documentos


def exemplo():
    fixture=test_documentos.DocumentosTests();fixture.setUp()
    modelos=[(g,q) for g,qs,_,_ in fixture.paginas for q in qs]
    modelos += [(6,Progressao()),(7,Estatistica()),(8,FiguraPlana()),(2,Parabola(1,-5,6,apresentacao='Expressão da função'))]
    return Prova(numero='23',itens=[(g,QuestaoProva(q,alternativas=['1/2','2√3','7,6','10','Nenhuma das anteriores'])) for g,q in modelos])


class ProvasTests(unittest.TestCase):
    def test_quadrados_nota_pm(self):
        from reportlab.lib.units import cm
        for tamanho in (1.5,2.4,3):
            p=Prova(tamanho_quadrados=tamanho);canvas=Mock();capa(canvas,p)
            self.assertEqual(canvas.rect.call_count,2)
            left,right=[c.args for c in canvas.rect.call_args_list]
            self.assertAlmostEqual(left[2],tamanho*cm);self.assertEqual(left[2],left[3])
            self.assertEqual(left[1],right[1]);self.assertLess(left[0]+left[2],right[0])
            self.assertEqual(validar_prova(dados_prova(p)),p)
        data=dados_prova(Prova());data.pop('tamanho_quadrados')
        self.assertEqual(validar_prova(data).tamanho_quadrados,3)
        for value in (True,0,4,float('nan'),'3'):
            data['tamanho_quadrados']=value
            with self.assertRaises(ValueError):validar_prova(data)

    def test_fontes_independentes_e_json_antigo(self):
        p=exemplo()
        for i,(g,q) in enumerate(p.itens):q.fonte=9 if i%2 else 12
        self.assertEqual(validar_prova(dados_prova(p)),p)
        for i in (0,1):
            g,q=p.itens[i];paragraph,_,alts,_=compor(g,q,i)
            self.assertEqual(paragraph.style.fontSize,q.fonte)
            self.assertTrue(all(a.style.fontSize==q.fonte for a,h in alts))
        data=dados_prova(p)
        for item in data['itens']:item.pop('fonte')
        self.assertTrue(all(q.fonte is None for g,q in validar_prova(data).itens))
        for value in (True,7,19,float('nan'),'12'):
            data=dados_prova(p);data['itens'][0]['fonte']=value
            with self.assertRaises(ValueError):validar_prova(data)

    def test_previa_temporaria_atualiza_prova_sem_salvar(self):
        from editor_provas import QuestaoProvaDialog
        d=QuestaoProvaDialog.__new__(QuestaoProvaDialog)
        d.editor=Mock();d.editor.lista=exemplo();d.index=5;d.timer=None;d.last=None
        d.window=Mock();d.preview=Mock();d.status=Mock()
        g,q=d.editor.lista.itens[5];editada=(g,replace(q,texto='Texto curto.',fonte=12))
        d.questao=Mock(return_value=editada)
        with patch('editor_provas.pdf_prova',return_value=b'pdf') as pdf:
            d.poll();self.assertEqual(pdf.call_args.args[0].itens[5],editada)
            d.editor.preview.mostrar.assert_called_once_with(b'pdf')
            self.assertEqual(d.preview.page,2)
            self.assertIsNone(d.editor.lista.itens[5][1].fonte)
        with patch('editor_provas.QuestaoDialog.fechar'):
            d.fechar();d.editor.atualizar.assert_called_once()

    def test_quatro_paginas_e_distribuicao(self):
        p=exemplo()
        p.itens=[(g,replace(q,texto=f'TEXTO{i+1} Qual é a resposta?')) for i,(g,q) in enumerate(p.itens)]
        with pdfium.PdfDocument(pdf_prova(p,True)) as doc:
            self.assertEqual(len(doc),4)
            for index,page in enumerate(doc):
                self.assertLess(page.get_width(),page.get_height())
                tp=page.get_textpage();text=tp.get_text_range();tp.close();page.close()
                if index==0:self.assertIn('Semana 23',text);self.assertNotIn('{23}',text);self.assertIn('Aluno:',text)
                else:
                    expected=(range(1,5),range(5,9),range(9,11))[index-1]
                    for i in range(1,11):self.assertEqual(f'TEXTO{i} ' in text,i in expected)
                    for label in 'abcde':self.assertEqual(text.count(label+')'),len(expected))

    def test_todos_conteudos_e_json(self):
        p=exemplo()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'prova.pdf';salvar_prova(path,p)
            self.assertEqual(carregar_prova(path.with_suffix('.json')),p)
            self.assertTrue(path.read_bytes().startswith(b'%PDF'))
        self.assertEqual(validar_prova(dados_prova(p)),p)

    def test_rascunhos_e_validacao(self):
        for quantidade in (0,1,9):
            p=replace(exemplo(),itens=exemplo().itens[:quantidade])
            with self.assertRaises(ValueError):validar_prova(dados_prova(p),True)
            with pdfium.PdfDocument(pdf_prova(p)) as doc:self.assertEqual(len(doc),4)
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'draft.json';salvar_rascunho(path,p);self.assertEqual(carregar_prova(path),p)
        p=exemplo();p.itens.append(p.itens[0])
        with self.assertRaises(ValueError):validar_prova(dados_prova(p))
        for key,value in [('numero','<1>'),('numero',''),('versao',True),('itens','erro')]:
            data=dados_prova(exemplo());data[key]=value
            with self.assertRaises(ValueError):validar_prova(data)
        data=dados_prova(exemplo());data['itens'][0]['alternativas']=['']*5
        validar_prova(data)
        with self.assertRaises(ValueError):validar_prova(data,True)

    def test_texto_livre_escape_e_limite(self):
        q=QuestaoProva(Progressao(),'Se x < 3 & y > 2, determine x².',['<3','>2','√2','1/2','7,6'])
        self.assertTrue(pdf_prova(Prova(itens=[(6,q)])).startswith(b'%PDF'))
        with self.assertRaisesRegex(ValueError,'não cabe'):compor(6,replace(q,texto='Enunciado longo. '*200),0)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'p.pdf';path.write_bytes(b'antigo')
            with self.assertRaises(ValueError):salvar_prova(path,Prova(itens=[(6,q)]))
            self.assertEqual(path.read_bytes(),b'antigo')

    def test_gabarito_e_marcas_fixas(self):
        canvas=Mock();capa(canvas,Prova())
        self.assertEqual(canvas.circle.call_count,51) # logotipo + 50 bolhas
        self.assertEqual(canvas.line.call_count,9) # identificação + 4 cantos de 2 traços
        self.assertEqual(quadro(0),quadro(4));self.assertEqual(quadro(0),quadro(8))

    def test_ordenacao_preserva_texto_e_alternativas(self):
        from editor_provas import EditorProva
        editor=EditorProva.__new__(EditorProva);editor.lista=exemplo();original=list(editor.lista.itens)
        editor.selecionado=lambda:0;editor.atualizar=Mock();editor.tree=Mock()
        editor.mover(1)
        self.assertEqual(editor.lista.itens[:2],original[1::-1])
        self.assertEqual(validar_prova(dados_prova(editor.lista)),editor.lista)

    def test_dialogo_texto_livre_e_insercao_com_progresso(self):
        from editor_provas import QuestaoProvaDialog
        d=QuestaoProvaDialog.__new__(QuestaoProvaDialog)
        d.aba=Mock();d.aba.pagina.return_value=(6,[Progressao()],1,'')
        d.texto=Mock();d.texto.get.return_value='Meu enunciado'
        d.personalizar=Mock();d.personalizar.get.return_value=True
        d.fonte=Mock();d.fonte.get.return_value='12'
        d.alternativas=[Mock() for _ in range(5)]
        for i,w in enumerate(d.alternativas):w.get.return_value=str(i)
        g,q=d.questao();self.assertEqual(q.texto,'Meu enunciado');self.assertEqual(q.alternativas,['0','1','2','3','4'])
        self.assertEqual(q.fonte,12)
        d.personalizar.get.return_value=False;self.assertIsNone(d.questao()[1].texto)
        d.index=None;d.timer=None;d.window=Mock();d.fechar=Mock();d.editor=Mock()
        d.editor.lista=Prova();d.editor.pending=None
        with patch('editor_provas.gerar_com_progresso',side_effect=lambda parent,task,**kw:task()) as progresso:
            d.confirmar();progresso.assert_called_once();d.editor.receber.assert_called_once();d.fechar.assert_called_once()
        self.assertEqual(d.editor.lista.itens,[]) # Só receber efetiva a alteração.
        d.editor.receber.reset_mock();d.fechar.reset_mock()
        with patch('editor_provas.gerar_com_progresso',side_effect=ValueError('Não cabe')),patch('editor_provas.messagebox.showerror') as erro:
            d.confirmar();erro.assert_called_once();d.editor.receber.assert_not_called();d.fechar.assert_not_called()
        self.assertFalse(d.editor._exportando)

    def test_modelo_permanece_editavel_com_texto_personalizado(self):
        p=exemplo();g,q=p.itens[0];q.texto='Texto que não deve ser sobrescrito';q.modelo.a=7
        restored=validar_prova(dados_prova(p))
        self.assertEqual(restored.itens[0][1].modelo.a,7)
        self.assertEqual(restored.itens[0][1].texto,q.texto)


if __name__=='__main__':unittest.main()
