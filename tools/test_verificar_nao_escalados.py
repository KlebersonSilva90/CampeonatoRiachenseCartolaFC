import unittest

from verificar_nao_escalados import encontrar_nao_escalados


class VerificarNaoEscaladosTest(unittest.TestCase):
    def test_encontra_apenas_zero_numerico(self):
        data = {
            "serie": "A",
            "rodadas": [
                {
                    "numero": 1,
                    "partidas": [
                        {
                            "mandante": {"time": "Time Zero", "cartoleiro": "Ana", "pontuacao": 0},
                            "visitante": {"time": "Time Positivo", "cartoleiro": "Beto", "pontuacao": 80.5},
                        },
                        {
                            "mandante": {"time": "Time Vazio", "cartoleiro": "Caio", "pontuacao": None},
                            "visitante": {"time": "Time Texto", "cartoleiro": "Dora", "pontuacao": "0"},
                        },
                    ],
                }
            ],
        }

        encontrados = encontrar_nao_escalados(data)

        self.assertEqual(1, len(encontrados))
        self.assertEqual("Time Zero", encontrados[0]["time"])
        self.assertEqual(1, encontrados[0]["rodada"])


if __name__ == "__main__":
    unittest.main()
