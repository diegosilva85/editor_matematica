from queue import Queue
import tkinter as tk
import unittest
from unittest.mock import Mock,patch
from interface_enem import JanelaEnem
from acervo_enem import carregar_acervo


class InterfaceEnemTests(unittest.TestCase):
    def setUp(self):
        self.tcl=tk.Tcl();self.w=object.__new__(JanelaEnem);w=self.w
        w.fontes,w.questoes=carregar_acervo();w.provas={p['id']:p for p in w.fontes}
        for k,value in [('ano','Todos'),('prova','Todas'),('conteudo','Todos'),('busca',''),('numero_pagina','1'),('status','')]:
            setattr(w,k,tk.StringVar(master=self.tcl,value=value))
        for name in ('cards','canvas','anterior','proxima','paginas','contagem','combo_prova','executor','after'):
            setattr(w,name,Mock())
        w.cards.winfo_children.return_value=[];w.canvas.winfo_width.return_value=800
        w.fila=Queue();w.geracao=0;w.pagina=0;w.futuro=None;w.baixando=False
        w.opcoes={'Todas':'','2015 regular':'2015-regular'}
        w.selecionadas={};w.seletores={};w.botao_lista=Mock()
        w._w='.';w.tk=self.tcl.tk;w.master=self.tcl
        self.patches=[patch('interface_enem.ttk.'+name,Mock()) for name in ('LabelFrame','Frame','Label','Button','Checkbutton')]
        for p in self.patches:p.start();self.addCleanup(p.stop)

    def test_filtros_paginacao_e_ultima_pagina(self):
        w=self.w;w.prova.set('2015 regular');w.aplicar()
        self.assertEqual(len(w.resultados),45);self.assertEqual(len(w.slots),4)
        w.mudar(99);self.assertEqual(w.pagina,11);self.assertEqual(len(w.slots),1)
        w.proxima.configure.assert_called_with(state='disabled')
        w.numero_pagina.set('2');w.ir_pagina();self.assertEqual(w.pagina,1)
        w.busca.set('nao existe este texto 123456789');w.aplicar()
        self.assertEqual(w.resultados,[]);self.assertEqual(w.numero_pagina.get(),'1')

    def test_resposta_antiga_nao_atualiza_preview_atual(self):
        w=self.w;w.aplicar();token=w.geracao;w.mudar(1)
        w.fila.put(('imagem',token,0,'erro antigo'))
        w.consultar();w.slots[0].configure.assert_not_called()
        w.fila.put(('imagem',w.geracao,0,'PDF ausente'))
        w.consultar();w.slots[0].configure.assert_called_with(text='PDF ausente',wraplength=500)

    def test_troca_ano_atualiza_provas(self):
        w=self.w;w.ano.set('2016');w.trocar_ano()
        self.assertEqual(len(w.opcoes),4);self.assertEqual(len(w.resultados),135)

    def test_selecao_persiste_filtros_e_limpa_apos_salvar(self):
        w=self.w;q=w.questoes[0];w.selecionar(q,True);w.selecionar(q,True)
        self.assertEqual(len(w.selecionadas),1)
        w.ano.set('2025');w.trocar_ano();self.assertIn(q['id'],w.selecionadas)
        w.ano.set('Todos');w.trocar_ano();self.assertTrue(w.seletores[q['id']].get())
        w.lista_salva([q]);self.assertEqual(w.selecionadas,{})
        self.assertFalse(w.seletores[q['id']].get())


if __name__=='__main__':unittest.main()
