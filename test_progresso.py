import unittest
from queue import Queue
from threading import Thread,Event
from progresso import executar_tarefa


class ProgressoTests(unittest.TestCase):
    def test_resultado(self):
        fila=Queue()
        executar_tarefa(lambda:'PDF salvo',fila)
        self.assertEqual(fila.get_nowait(),(True,'PDF salvo'))

    def test_erro(self):
        fila=Queue(); erro=OSError('Sem permissão para salvar')
        def falhar(): raise erro
        executar_tarefa(falhar,fila)
        sucesso,resultado=fila.get_nowait()
        self.assertFalse(sucesso); self.assertIs(resultado,erro)

    def test_nao_bloqueia_chamador(self):
        fila=Queue(); liberar=Event(); entrou=Event()
        def tarefa():
            entrou.set(); liberar.wait(2); return 42
        worker=Thread(target=executar_tarefa,args=(tarefa,fila))
        worker.start()
        try:
            self.assertTrue(entrou.wait(1))
            self.assertTrue(fila.empty())
        finally:
            liberar.set(); worker.join(3)
        self.assertEqual(fila.get_nowait(),(True,42))


if __name__=='__main__': unittest.main()
