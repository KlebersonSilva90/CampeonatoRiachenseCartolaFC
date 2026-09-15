import unittest
from unittest.mock import patch

from atualizar_libertadores import RODADAS_GRUPOS, atualizar_confronto, recalcular_classificacao


class AtualizarLibertadoresTests(unittest.TestCase):
    def test_mapeamento_das_rodadas_dos_grupos(self):
        self.assertEqual({1: 23, 2: 24, 3: 25, 4: 26, 5: 27, 6: 28}, RODADAS_GRUPOS)

    @patch("atualizar_libertadores.time.sleep")
    @patch("atualizar_libertadores.pontuar_time")
    def test_rodada_anterior_reconsulta_historico(self, pontuar, _sleep):
        pontuar.side_effect = [105.84, 71.86]
        partida = {
            "mandante": {"time": "A", "pontuacao": None, "resultado": None},
            "visitante": {"time": "B", "pontuacao": None, "resultado": None},
        }
        anterior = {
            "mandante": {"time": "A", "pontuacao": 99.44},
            "visitante": {"time": "B", "pontuacao": 69.96},
            "status": "concluida",
        }
        status = atualizar_confronto(partida, anterior, 26, 27, False, {}, {}, set())
        self.assertEqual("concluida", status)
        self.assertEqual(105.84, partida["mandante"]["pontuacao"])
        self.assertEqual(71.86, partida["visitante"]["pontuacao"])

    def test_classificacao_obedece_criterios_definidos(self):
        def equipe(nome, pontos, resultado):
            return {"time": nome, "pontuacao": pontos, "resultado": resultado}

        data = {
            "grupos": [{
                "grupo": "A",
                "classificacao": [{"time": nome} for nome in ("A", "B", "C", "D")],
                "rodadas": [{
                    "partidas": [
                        {"mandante": equipe("A", 100, "V"), "visitante": equipe("B", 90, "D")},
                        {"mandante": equipe("C", 80, "E"), "visitante": equipe("D", 83, "E")},
                    ]
                }],
            }]
        }
        recalcular_classificacao(data)
        classificacao = data["grupos"][0]["classificacao"]
        self.assertEqual(["A", "D", "C", "B"], [item["time"] for item in classificacao])
        self.assertEqual("oitavas", classificacao[1]["destinoAtual"])
        self.assertEqual("copa-do-brasil", classificacao[2]["destinoAtual"])


if __name__ == "__main__":
    unittest.main()
