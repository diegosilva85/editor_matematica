import unittest
from unittest.mock import Mock,patch
from editor_listas import QuestaoDialog,EditorLista
from listas import Lista
from progressao import Progressao


class InsercaoTests(unittest.TestCase):
    def dialogo(self):
        dialog=QuestaoDialog.__new__(QuestaoDialog)
        dialog.window=Mock();dialog.timer='timer';dialog.index=None
        dialog.editor=Mock();dialog.editor.lista=Lista();dialog.editor.pending='preview'
        dialog.questao=Mock(return_value=(6,Progressao()))
        dialog.status=Mock();dialog.add=Mock()
        return dialog

    def test_progresso_reutiliza_pdf(self):
        dialog=self.dialogo()
        with patch('progresso.gerar_com_progresso',side_effect=lambda parent,tarefa:tarefa()) as progresso,patch('editor_listas.pdf_lista',return_value=b'pdf') as pdf:
            dialog.confirmar()
        progresso.assert_called_once();pdf.assert_called_once()
        dialog.editor.receber.assert_called_once_with(dialog.questao.return_value,None,content=b'pdf')
        self.assertFalse(dialog.editor._exportando)
        self.assertEqual(dialog.editor.lista.itens,[])

    def test_erro_nao_acrescenta(self):
        dialog=self.dialogo()
        with patch('progresso.gerar_com_progresso',side_effect=ValueError('Inválido')),patch('editor_listas.messagebox.showerror') as erro:
            dialog.confirmar()
        dialog.editor.receber.assert_not_called()
        erro.assert_called_once()
        self.assertFalse(dialog.editor._exportando)
        dialog.window.after.assert_called_once()

    def test_receber_encaminha_previa(self):
        editor=EditorLista.__new__(EditorLista)
        editor.lista=Lista();editor.atualizar=Mock()
        item=(6,Progressao())
        editor.receber(item,content=b'pdf')
        self.assertEqual(editor.lista.itens,[item])
        editor.atualizar.assert_called_once_with(b'pdf')


if __name__=='__main__': unittest.main()
