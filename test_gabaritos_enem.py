import json
import tempfile
import unittest
from collections import Counter
from acervo_enem import ASSETS,carregar_acervo,rotulo_gabarito,salvar_conteudos
from importar_gabaritos_enem import extrair_respostas


class GabaritosEnemTests(unittest.TestCase):
    def test_todas_as_questoes_tem_resposta_oficial(self):
        fontes,questoes=carregar_acervo()
        gs=json.loads((ASSETS/'gabaritos.json').read_text(encoding='utf-8'))['provas']
        self.assertEqual(set(gs),{p['id'] for p in fontes})
        self.assertEqual(len(questoes),1035)
        for q in questoes:
            self.assertIn(q['gabarito'],('A','B','C','D','E','Anulada'))
            self.assertEqual(q['gabarito'],gs[q['prova']]['respostas'][str(q['numero'])])
            self.assertTrue(q['gabarito_url'].startswith('https://download.inep.gov.br/'))
        self.assertEqual(Counter(q['gabarito'] for q in questoes)['Anulada'],6)
        for pid,g in gs.items():
            self.assertEqual(len(g['respostas']),45);self.assertEqual(len(g['sha256']),64)
            esperado=13 if pid in ('2015-ppl','2016-ppl') else 17 if pid=='2018-ppl' else 5
            self.assertEqual(g['caderno'],esperado)

    def test_amostras_de_aplicacoes_e_anuladas(self):
        _,questoes=carregar_acervo();q={q['id']:q for q in questoes}
        for id,letra in {'2015-ppl-136':'A','2016-regular-136':'C',
                         '2016-segunda-136':'B','2016-ppl-136':'E'}.items():
            self.assertEqual(q[id]['gabarito'],letra)
        for id in ('2018-regular-150','2020-regular-141','2021-regular-178',
                   '2022-regular-175','2023-regular-177','2025-regular-178'):
            self.assertEqual(q[id]['gabarito'],'Anulada')
            self.assertEqual(rotulo_gabarito(q[id]),'Gabarito oficial: Anulada')
        self.assertEqual(rotulo_gabarito({}),'Gabarito oficial: Não disponível')

    def test_revisar_conteudo_nao_muda_gabarito(self):
        with tempfile.TemporaryDirectory() as d:
            salvar_conteudos('2016-segunda-136',['Estatística'],d)
            q=next(q for q in carregar_acervo(d)[1] if q['id']=='2016-segunda-136')
            self.assertTrue(q['revisado']);self.assertEqual(q['gabarito'],'B')

    def test_extracao_exige_45_respostas_unicas(self):
        s='\n'.join(f'{n} A' for n in range(136,181))
        respostas=extrair_respostas(s.replace('150 A','150 Anulada'))
        self.assertEqual(respostas['150'],'Anulada')
        self.assertEqual(extrair_respostas(s.replace('136 A','136\r\nA'))['136'],'A')
        for invalido in (s.replace('150 A','150 X'),s+'\n150 B',s.replace('180 A','')):
            with self.assertRaises(ValueError):extrair_respostas(invalido)


if __name__=='__main__':unittest.main()
