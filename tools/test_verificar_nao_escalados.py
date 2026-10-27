import unittest

from registrar_contato import chave_registro, resumir_times
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

    def test_contato_reinicia_contagem_e_alerta_retorna_apos_cinco_novas(self):
        ocorrencias = [
            {"serie": "E", "time": "Águia FC", "cartoleiro": "Ana"}
            for _ in range(9)
        ]
        chave = chave_registro("E", "Aguia FC")
        contatos = {"contatos": {chave: {"ocorrenciasReconhecidas": 9}}}

        reconhecido = resumir_times(ocorrencias, contatos)[0]
        self.assertEqual(0, reconhecido["novas"])

        ocorrencias.extend(
            {"serie": "E", "time": "Águia FC", "cartoleiro": "Ana"}
            for _ in range(5)
        )
        reincidente = resumir_times(ocorrencias, contatos)[0]
        self.assertEqual(5, reincidente["novas"])
        self.assertEqual(14, reincidente["total"])


if __name__ == "__main__":
    unittest.main()
