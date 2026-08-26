import unittest

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


if __name__ == "__main__":
    unittest.main()
