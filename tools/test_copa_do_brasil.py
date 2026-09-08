import unittest
from unittest.mock import patch

from atualizar_copa_do_brasil import atualizar_perna
from extrair_copa_do_brasil import build_data, finalizar_partida, validar


class CopaDoBrasilTests(unittest.TestCase):
    def test_planilha_tem_64_times_e_32_confrontos_iniciais(self):
        data, _ = build_data()
        self.assertEqual([], validar(data))
        self.assertEqual(64, len(data["times"]))
        self.assertEqual(32, len(data["fases"][0]["partidas"]))

    def test_calendario_termina_com_final_ida_e_volta(self):
        data, _ = build_data()
        self.assertEqual([24, 25], data["fases"][0]["rodadasCartola"])
        self.assertEqual([36, 37], data["fases"][-1]["rodadasCartola"])
        self.assertEqual("ida-e-volta", data["regulamento"]["final"])

    def test_vencedor_so_e_definido_apos_a_volta_concluida(self):
        partida = {
            "time1": "A", "time2": "B",
            "ida": {"time1": 100.0, "time2": 90.0, "status": "concluida"},
            "volta": {"time1": 80.0, "time2": 95.0, "status": "parcial"},
            "agregado": {"time1": None, "time2": None},
            "vencedor": None, "empatadoNoAgregado": False,
        }
        finalizar_partida(partida, [24, 25])
        self.assertEqual({"time1": 180.0, "time2": 185.0}, partida["agregado"])
        self.assertIsNone(partida["vencedor"])
        partida["volta"]["status"] = "concluida"
        finalizar_partida(partida, [24, 25])
        self.assertEqual("B", partida["vencedor"])

    @patch("atualizar_copa_do_brasil.time.sleep")
    @patch("atualizar_copa_do_brasil.obter_pontos_historicos")
    def test_rodada_anterior_reconsulta_historico(self, obter_pontos, _sleep):
        obter_pontos.side_effect = [105.84, 71.86]
        partida = {
            "time1": "SC Tello",
            "time2": "SeguimeuPAAL",
            "ida": {"time1": None, "time2": None, "status": "planilha"},
        }
        anterior = {
            "time1": "SC Tello",
            "time2": "SeguimeuPAAL",
            "ida": {"time1": 99.44, "time2": 69.96, "status": "concluida"},
        }
        mapa = {"times": {
            "CB|SC Tello": {"timeId": 1},
            "CB|SeguimeuPAAL": {"timeId": 2},
        }}

        atualizar_perna(partida, "ida", 26, 27, False, mapa, {}, set(), anterior)

        self.assertEqual(105.84, partida["ida"]["time1"])
        self.assertEqual(71.86, partida["ida"]["time2"])
        self.assertEqual("concluida", partida["ida"]["status"])

    @patch("atualizar_copa_do_brasil.time.sleep")
    @patch("atualizar_copa_do_brasil.obter_pontos_historicos", return_value=None)
    def test_falha_no_historico_nao_congela_parcial(self, _obter_pontos, _sleep):
        partida = {
            "time1": "A", "time2": "B",
            "ida": {"time1": None, "time2": None, "status": "planilha"},
        }
        anterior = {
            "time1": "A", "time2": "B",
            "ida": {"time1": 90.0, "time2": 80.0, "status": "parcial"},
        }
        mapa = {"times": {"CB|A": {"timeId": 1}, "CB|B": {"timeId": 2}}}

        atualizar_perna(partida, "ida", 26, 27, False, mapa, {}, set(), anterior)

        self.assertEqual(90.0, partida["ida"]["time1"])
        self.assertEqual(80.0, partida["ida"]["time2"])
        self.assertEqual("parcial", partida["ida"]["status"])


if __name__ == "__main__":
    unittest.main()
