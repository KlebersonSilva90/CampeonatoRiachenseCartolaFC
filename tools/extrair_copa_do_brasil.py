"""Extrai a chave da Copa do Brasil para ``dados/copa-do-brasil.json``.

Uso: python tools/extrair_copa_do_brasil.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from extrair_serie_a import ROOT, load_cells


SOURCE = ROOT / "planilhas" / "Copa do Brasil.xlsx"
OUTPUT = ROOT / "dados" / "copa-do-brasil.json"


def pares(inicio: int, fim: int, passo: int) -> list[tuple[int, int]]:
    return [(linha, linha + 1) for linha in range(inicio, fim + 1, passo)]


PHASES = (
    {
        "id": "primeira-fase", "nome": "Primeira fase", "rodadas": [24, 25], "expected": 32,
        "left": {"team": 2, "ida": 3, "volta": 4, "rows": pares(18, 78, 4)},
        "right": {"team": 78, "ida": 77, "volta": 76, "rows": pares(18, 78, 4)},
    },
    {
        "id": "segunda-fase", "nome": "Segunda fase", "rodadas": [26, 27], "expected": 16,
        "left": {"team": 8, "ida": 9, "volta": 10, "rows": pares(20, 76, 8)},
        "right": {"team": 72, "ida": 71, "volta": 70, "rows": pares(20, 76, 8)},
    },
    {
        "id": "terceira-fase", "nome": "Terceira fase", "rodadas": [28, 29], "expected": 8,
        "left": {"team": 14, "ida": 15, "volta": 16, "rows": pares(24, 72, 16)},
        "right": {"team": 66, "ida": 65, "volta": 64, "rows": pares(24, 72, 16)},
    },
    {
        "id": "oitavas", "nome": "Oitavas de final", "rodadas": [30, 31], "expected": 8,
        "left": {"team": 20, "ida": 21, "volta": 22, "rows": pares(24, 72, 16)},
        "right": {"team": 60, "ida": 59, "volta": 58, "rows": pares(24, 72, 16)},
    },
    {
        "id": "quartas", "nome": "Quartas de final", "rodadas": [32, 33], "expected": 4,
        "left": {"team": 26, "ida": 27, "volta": 28, "rows": [(32, 33), (65, 66)]},
        "right": {"team": 54, "ida": 53, "volta": 52, "rows": [(32, 33), (65, 66)]},
    },
    {
        "id": "semifinais", "nome": "Semifinais", "rodadas": [34, 35], "expected": 2,
        "left": {"team": 32, "ida": 33, "volta": 34, "rows": [(49, 50)]},
        "right": {"team": 48, "ida": 47, "volta": 46, "rows": [(49, 50)]},
    },
)


def valor(cells: dict[tuple[int, int], object], row: int, col: int):
    return cells.get((row, col))


def pontuacao(cells, row: int, col: int):
    numero = valor(cells, row, col)
    # A planilha usa zero como marcador de campo ainda não preenchido.
    return float(numero) if isinstance(numero, (int, float)) and numero != 0 else None


def criar_partida(cells, config: dict, rows: tuple[int, int]) -> dict | None:
    row1, row2 = rows
    time1 = valor(cells, row1, config["team"])
    time2 = valor(cells, row2, config["team"])
    if not time1 and not time2:
        return None
    return {
        "time1": time1,
        "time2": time2,
        "ida": {
            "rodadaCartola": None,
            "time1": pontuacao(cells, row1, config["ida"]),
            "time2": pontuacao(cells, row2, config["ida"]),
            "status": "planilha",
        },
        "volta": {
            "rodadaCartola": None,
            "time1": pontuacao(cells, row1, config["volta"]),
            "time2": pontuacao(cells, row2, config["volta"]),
            "status": "planilha",
        },
        "agregado": {"time1": None, "time2": None},
        "vencedor": None,
        "empatadoNoAgregado": False,
        "status": "agendado",
    }


def finalizar_partida(partida: dict, rodadas: list[int]) -> None:
    partida["ida"]["rodadaCartola"] = rodadas[0]
    partida["volta"]["rodadaCartola"] = rodadas[1]
    ida = partida["ida"]
    volta = partida["volta"]
    numeros = (ida["time1"], ida["time2"], volta["time1"], volta["time2"])
    if all(isinstance(item, (int, float)) for item in numeros):
        agregado1 = round(ida["time1"] + volta["time1"], 2)
        agregado2 = round(ida["time2"] + volta["time2"], 2)
        partida["agregado"] = {"time1": agregado1, "time2": agregado2}
        if ida.get("status") == "concluida" and volta.get("status") == "concluida":
            if agregado1 > agregado2:
                partida["vencedor"] = partida["time1"]
            elif agregado2 > agregado1:
                partida["vencedor"] = partida["time2"]
            else:
                partida["empatadoNoAgregado"] = True


def extrair_fases(cells) -> list[dict]:
    fases = []
    for fase in PHASES:
        partidas = []
        for lado in ("left", "right"):
            config = fase[lado]
            for rows in config["rows"]:
                partida = criar_partida(cells, config, rows)
                if partida:
                    finalizar_partida(partida, fase["rodadas"])
                    partidas.append(partida)
        fases.append({
            "id": fase["id"],
            "nome": fase["nome"],
            "rodadasCartola": fase["rodadas"],
            "quantidadeEsperada": fase["expected"],
            "partidas": partidas,
        })

    # A final ocupa o centro da chave. As pontuações serão preenchidas pelo
    # atualizador automático nas rodadas 36 e 37.
    time1 = valor(cells, 49, 38)
    time2 = valor(cells, 49, 42)
    final = {
        "id": "final",
        "nome": "Final",
        "rodadasCartola": [36, 37],
        "quantidadeEsperada": 1,
        "partidas": [],
    }
    if time1 or time2:
        partida = {
            "time1": time1, "time2": time2,
            "ida": {"rodadaCartola": 36, "time1": None, "time2": None, "status": "aguardando"},
            "volta": {"rodadaCartola": 37, "time1": None, "time2": None, "status": "aguardando"},
            "agregado": {"time1": None, "time2": None},
            "vencedor": None, "empatadoNoAgregado": False, "status": "agendado",
        }
        final["partidas"].append(partida)
    fases.append(final)
    return fases


def build_data() -> tuple[dict, Path]:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {SOURCE}")
    cells_times = load_cells(SOURCE, "TIMES")
    cells_jogos = load_cells(SOURCE, "Jogos")
    times = []
    for row in range(2, 82):
        cartoleiro = valor(cells_times, row, 3)
        nome = valor(cells_times, row, 4)
        if nome:
            times.append({"cartoleiro": cartoleiro or "", "time": nome})
    data = {
        "competicao": "Copa do Brasil",
        "fonte": SOURCE.name,
        "atualizadoEm": datetime.fromtimestamp(SOURCE.stat().st_mtime).isoformat(timespec="seconds"),
        "regulamento": {
            "participantes": 64,
            "mataMata": "ida-e-volta",
            "final": "ida-e-volta",
            "rodadaInicial": 24,
            "rodadaFinal": 37,
            "desempateAgregado": "pendente",
        },
        "times": times,
        "fases": extrair_fases(cells_jogos),
        "avisos": [],
    }
    return data, OUTPUT


def validar(data: dict) -> list[str]:
    erros = []
    nomes = [item["time"] for item in data["times"]]
    if len(nomes) != 64:
        erros.append(f"foram encontrados {len(nomes)} times; esperado: 64")
    repetidos = sorted({nome for nome in nomes if nomes.count(nome) > 1}, key=str.casefold)
    if repetidos:
        erros.append("times duplicados: " + ", ".join(repetidos))
    primeira = data["fases"][0]["partidas"]
    if len(primeira) != 32:
        erros.append(f"a primeira fase possui {len(primeira)} confrontos; esperado: 32")
    inscritos = set(nomes)
    chave = [time for partida in primeira for time in (partida["time1"], partida["time2"]) if time]
    desconhecidos = sorted(set(chave) - inscritos, key=str.casefold)
    ausentes = sorted(inscritos - set(chave), key=str.casefold)
    if desconhecidos:
        erros.append("times da chave fora da aba TIMES: " + ", ".join(desconhecidos))
    if ausentes:
        erros.append("times da aba TIMES ausentes da primeira fase: " + ", ".join(ausentes))
    return erros


def salvar(data: dict, output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\r\n") as destino:
        destino.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data, output = build_data()
    erros = validar(data)
    if erros:
        print("Extração cancelada:")
        for erro in erros:
            print(f"  ERRO: {erro}")
        return 1
    salvar(data, output)
    print(f"Gerado: {output.relative_to(ROOT)}")
    print(f"Times: {len(data['times'])} | confrontos da primeira fase: {len(data['fases'][0]['partidas'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
