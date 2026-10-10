import math
import unittest
from triangulos import POSICOES, vertices, Triangulo, PITAGORAS


class GeometriaTests(unittest.TestCase):
    def test_pitagoras(self):
        t=Triangulo(45,POSICOES[0],PITAGORAS,'','3','Hipotenusa','4')
        self.assertEqual(t.medidas_pitagoras()['Hipotenusa'],5)
        t.lado_x='Cateto 1'; t.valor2='5'
        self.assertAlmostEqual(t.medidas_pitagoras()['Cateto 1'],4)
        t.valor2='2'
        with self.assertRaises(ValueError): t.validar()

    def test_angulos_e_proporcoes_em_todas_as_posicoes(self):
        for angulo in (1,15,30,45,60,75,89):
            for posicao in POSICOES:
                with self.subTest(angulo=angulo,posicao=posicao):
                    r,a,b=vertices(posicao,angulo)
                    adj,opo,hip=math.dist(r,a),math.dist(r,b),math.dist(a,b)
                    self.assertAlmostEqual(adj*adj+opo*opo,hip*hip)
                    self.assertAlmostEqual(math.degrees(math.asin(opo/hip)),angulo)
                    self.assertAlmostEqual(opo/adj,math.tan(math.radians(angulo)))
                    if angulo==45: self.assertAlmostEqual(adj,opo)

    def test_hipotenusa_horizontal(self):
        for angulo in (30,45,60):
            for idx in (4,5):
                r,a,b=vertices(POSICOES[idx],angulo)
                self.assertAlmostEqual(a[1],b[1])
                self.assertEqual(a[1]>r[1],idx==4)


if __name__=='__main__':
    unittest.main()
