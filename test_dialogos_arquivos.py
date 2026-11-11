import unittest
from unittest.mock import Mock,call
from janelas import ocultar_arquivos_ocultos


class DialogosTests(unittest.TestCase):
    def test_linux_carrega_dialogo_antes_de_ocultar(self):
        root=Mock();root.tk.call.return_value='x11'
        ocultar_arquivos_ocultos(root)
        self.assertEqual(root.tk.method_calls,[
            call.call('tk','windowingsystem'),
            call.call('auto_load','::tk::dialog::file::'),
            call.setvar('::tk::dialog::file::showHiddenVar',0),
            call.setvar('::tk::dialog::file::showHiddenBtn',0)])

    def test_outros_sistemas_sem_variaveis_x11(self):
        root=Mock();root.tk.call.return_value='win32'
        ocultar_arquivos_ocultos(root);root.tk.setvar.assert_not_called()
