"""Extrai e valida a Libertadores da planilha XLSM para o site.

Uso: python tools/extrair_libertadores.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from extrair_serie_a import ROOT, load_cells, match_result


SOURCE = ROOT / "planilhas" / "LIBERTADORES.xlsm"
OUTPUT = ROOT / "dados" / "libertadores.json"
GROUPS = tuple("ABCDEFGH")
GROUP_ROUND_HEADER_ROWS = (1, 6, 11, 16, 21, 26)
KNOCKOUT_PHASES = (
    {"id": "oitavas", "nome": "Oitavas de final", "rows": range(15, 23), "expected": 8, "title_row": 12},
    {"id": "quartas", "nome": "Quartas de final", "rows": range(38, 42), "expected": 4, "title_row": 35},
    {"id": "semifinais", "nome": "Semifinais", "rows": range(57, 59), "expected": 2, "title_row": 54},
    {"id": "final", "nome": "Final", "rows": range(75, 76), "expected": 1, "title_row": 71},
)


def cell(cells: dict[tuple[int, int], object], row: int, col: int):
    return cells.get((row, col))


def is_score(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def standings_sort_key(team: dict) -> tuple:
    return (
        -team["pontos"],
        -team["vitorias"],
        -team["saldo"],
        -team["pontosPro"],
    )


def group_destination(position: int) -> str:
    if position <= 2:
        return "oitavas"
    if position == 3:
        return "copa-do-brasil"
    return "eliminado"


def extract_group(letter: str) -> dict:
    cells = load_cells(SOURCE, f"GRUPO {letter}")
    standings = []
    for row in range(3, 7):
        team = cell(cells, row, 24)
        if not team:
            continue
        games = cell(cells, row, 26) or 0
        points_for = cell(cells, row, 30) or 0
        standings.append(
            {
                "posicao": 0,
                "time": team,
                "pontos": cell(cells, row, 25) or 0,
                "jogos": games,
                "vitorias": cell(cells, row, 27) or 0,
                "empates": cell(cells, row, 28) or 0,
                "derrotas": cell(cells, row, 29) or 0,
                "pontosPro": points_for,
                "pontosContra": cell(cells, row, 31) or 0,
                "saldo": cell(cells, row, 32) or 0,
                "media": round(points_for / games, 2) if games else 0,
            }
        )

    standings.sort(key=standings_sort_key)
    for position, team in enumerate(standings, start=1):
        team["posicao"] = position
        team["destinoAtual"] = group_destination(position)

    rounds = []
    for number, header_row in enumerate(GROUP_ROUND_HEADER_ROWS, start=1):
        matches = []
        for row in (header_row + 2, header_row + 3):
            left_team = cell(cells, row, 7)
            right_team = cell(cells, row, 11)
            if not left_team and not right_team:
                continue
            left_score = cell(cells, row, 8)
            right_score = cell(cells, row, 10)
            left_result, right_result = match_result(left_score, right_score)
            matches.append(
                {
                    "mandante": {
                        "cartoleiro": cell(cells, row, 6),
                        "time": left_team,
                        "pontuacao": left_score,
                        "resultado": left_result,
                    },
                    "visitante": {
                        "cartoleiro": cell(cells, row, 12),
                        "time": right_team,
                        "pontuacao": right_score,
                        "resultado": right_result,
                    },
                }
            )
        completed = bool(matches) and all(
            is_score(match["mandante"]["pontuacao"]) and is_score(match["visitante"]["pontuacao"])
            for match in matches
        )
        rounds.append({"numero": number, "concluida": completed, "partidas": matches})

    return {"grupo": letter, "classificacao": standings, "rodadas": rounds}


def round_numbers(title) -> list[int]:
    return [int(number) for number in re.findall(r"\d+", str(title or ""))]


def knockout_match(cells, row: int) -> dict | None:
    left_team = cell(cells, row, 1)
    right_team = cell(cells, row, 9)
    if not left_team and not right_team:
        return None

    first_leg_left = cell(cells, row, 2)
    first_leg_right = cell(cells, row, 8)
    second_leg_left = cell(cells, row, 3)
    second_leg_right = cell(cells, row, 7)
    first_complete = is_score(first_leg_left) and is_score(first_leg_right)
    second_complete = is_score(second_leg_left) and is_score(second_leg_right)
    complete = first_complete and second_complete

    left_aggregate = round(first_leg_left + second_leg_left, 2) if complete else None
    right_aggregate = round(first_leg_right + second_leg_right, 2) if complete else None
    winner = None
    tied = False
    if complete:
        if left_aggregate > right_aggregate:
            winner = left_team
        elif right_aggregate > left_aggregate:
            winner = right_team
        else:
            tied = True

    if complete:
        status = "concluido" if winner else "aguardando-desempate"
    elif first_complete or second_complete:
        status = "em-andamento"
    else:
        status = "agendado"

    return {
        "time1": left_team,
        "time2": right_team,
        "ida": {"time1": first_leg_left, "time2": first_leg_right},
        "volta": {"time1": second_leg_left, "time2": second_leg_right},
        "agregado": {"time1": left_aggregate, "time2": right_aggregate},
        "vencedor": winner,
        "empatadoNoAgregado": tied,
        "status": status,
    }


def extract_knockout(known_teams: set[str]) -> tuple[list[dict], list[str]]:
    cells = load_cells(SOURCE, "mata mata")
    phases = []
    warnings = []
    for config in KNOCKOUT_PHASES:
        extracted = [knockout_match(cells, row) for row in config["rows"]]
        matches = [match for match in extracted if match]
        unknown = sorted(
            {
                team
                for match in matches
                for team in (match["time1"], match["time2"])
                if team and team not in known_teams
            },
            key=str.casefold,
        )
        ignored = bool(unknown)
        if ignored:
            warnings.append(
                f"{config['nome']}: conteúdo antigo ignorado; times fora da edição atual: {', '.join(unknown)}"
            )
            matches = []
        phases.append(
            {
                "id": config["id"],
                "nome": config["nome"],
                "rodadasCartola": round_numbers(cell(cells, config["title_row"], 1)),
                "quantidadeEsperada": config["expected"],
                "status": "aguardando" if not matches else "definido",
                "conteudoAntigoIgnorado": ignored,
                "partidas": matches,
            }
        )
    return phases, warnings


def build_data() -> tuple[dict, Path, list[str]]:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {SOURCE}")

    groups = [extract_group(letter) for letter in GROUPS]
    known_teams = {
        team["time"]
        for group in groups
        for team in group["classificacao"]
    }
    knockout, warnings = extract_knockout(known_teams)

    current_round_of_16 = []
    current_copa_brasil = []
    for group in groups:
        current_round_of_16.extend(
            {"grupo": group["grupo"], "time": team["time"], "posicao": team["posicao"]}
            for team in group["classificacao"][:2]
        )
        third = group["classificacao"][2]
        current_copa_brasil.append({"grupo": group["grupo"], "time": third["time"], "posicao": 3})

    data = {
        "competicao": "Libertadores",
        "fonte": SOURCE.name,
        "atualizadoEm": datetime.fromtimestamp(SOURCE.stat().st_mtime).isoformat(timespec="seconds"),
        "regulamento": {
            "grupos": 8,
            "timesPorGrupo": 4,
            "classificadosOitavasPorGrupo": 2,
            "classificadosCopaDoBrasilPorGrupo": 1,
            "posicaoCopaDoBrasil": 3,
            "mataMata": "ida-e-volta",
            "vitoriaDiferencaMinima": 5,
            "pontosVitoria": 3,
            "pontosEmpate": 1,
            "criteriosClassificacao": ["pontos", "vitorias", "saldo", "pontosPro"],
        },
        "grupos": groups,
        "classificacaoAtual": {
            "oitavas": current_round_of_16,
            "copaDoBrasil": current_copa_brasil,
        },
        "mataMata": knockout,
        "avisos": warnings,
    }
    return data, OUTPUT, warnings


def validate_data(data: dict) -> tuple[list[str], list[str]]:
    errors = []
    warnings = list(data.get("avisos", []))
    groups = data["grupos"]
    if len(groups) != 8:
        errors.append(f"foram encontrados {len(groups)} grupos; esperado: 8")

    all_names = []
    tolerance = 0.011
    for group in groups:
        letter = group["grupo"]
        standings = group["classificacao"]
        rounds = group["rodadas"]
        names = [team["time"] for team in standings]
        all_names.extend(names)
        if len(standings) != 4:
            errors.append(f"Grupo {letter}: possui {len(standings)} times; esperado: 4")
        if len(set(names)) != len(names):
            errors.append(f"Grupo {letter}: possui times duplicados")
        if standings != sorted(standings, key=standings_sort_key):
            errors.append(f"Grupo {letter}: classificação fora de ordem")
        if [team["posicao"] for team in standings] != list(range(1, len(standings) + 1)):
            errors.append(f"Grupo {letter}: posições não sequenciais")
        if len(rounds) != 6:
            errors.append(f"Grupo {letter}: possui {len(rounds)} rodadas; esperado: 6")

        aggregate = {name: {"j": 0, "v": 0, "e": 0, "d": 0, "pp": 0.0, "pc": 0.0} for name in names}
        pair_counts = {}
        for round_data in rounds:
            if len(round_data["partidas"]) != 2:
                errors.append(
                    f"Grupo {letter}, rodada {round_data['numero']}: possui {len(round_data['partidas'])} jogos; esperado: 2"
                )
            for match in round_data["partidas"]:
                left = match["mandante"]
                right = match["visitante"]
                if left["time"] not in aggregate or right["time"] not in aggregate:
                    errors.append(f"Grupo {letter}: confronto contém time desconhecido")
                    continue
                pair = tuple(sorted((left["time"], right["time"]), key=str.casefold))
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
                left_has_score = is_score(left["pontuacao"])
                right_has_score = is_score(right["pontuacao"])
                if left_has_score != right_has_score:
                    errors.append(f"Grupo {letter}: confronto com pontuação preenchida somente de um lado")
                if not (left_has_score and right_has_score):
                    continue
                for team, opponent in ((left, right), (right, left)):
                    stats = aggregate[team["time"]]
                    stats["j"] += 1
                    stats[team["resultado"].lower()] += 1
                    stats["pp"] += team["pontuacao"]
                    stats["pc"] += opponent["pontuacao"]

        if pair_counts and (len(pair_counts) != 6 or any(count != 2 for count in pair_counts.values())):
            errors.append(f"Grupo {letter}: tabela não contém os seis pares em ida e volta")

        for team in standings:
            name = team["time"]
            if team["jogos"] != team["vitorias"] + team["empates"] + team["derrotas"]:
                errors.append(f"Grupo {letter}, {name}: J não corresponde a V + E + D")
            if team["pontos"] != 3 * team["vitorias"] + team["empates"]:
                errors.append(f"Grupo {letter}, {name}: pontos não correspondem a 3×V + E")
            if abs(team["saldo"] - (team["pontosPro"] - team["pontosContra"])) > tolerance:
                errors.append(f"Grupo {letter}, {name}: saldo divergente")
            stats = aggregate[name]
            comparisons = {
                "jogos": stats["j"], "vitorias": stats["v"], "empates": stats["e"],
                "derrotas": stats["d"], "pontosPro": stats["pp"], "pontosContra": stats["pc"],
            }
            for field, calculated in comparisons.items():
                if abs(team[field] - calculated) > tolerance:
                    errors.append(f"Grupo {letter}, {name}: {field} diverge dos confrontos")

    duplicates = sorted({name for name in all_names if all_names.count(name) > 1}, key=str.casefold)
    if duplicates:
        errors.append(f"times repetidos entre grupos: {', '.join(duplicates)}")

    for phase in data["mataMata"]:
        if phase["partidas"] and len(phase["partidas"]) != phase["quantidadeEsperada"]:
            errors.append(
                f"{phase['nome']}: possui {len(phase['partidas'])} confrontos; esperado: {phase['quantidadeEsperada']}"
            )
    return errors, warnings


def save_data(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data, output, _ = build_data()
    errors, warnings = validate_data(data)
    if errors:
        print("Extração cancelada:")
        for error in errors:
            print(f"  ERRO: {error}")
        return 1
    save_data(data, output)
    completed = {
        group["grupo"]: sum(round_data["concluida"] for round_data in group["rodadas"])
        for group in data["grupos"]
    }
    print(f"Gerado: {output.relative_to(ROOT)}")
    print("Rodadas concluídas por grupo: " + ", ".join(f"{group}={count}" for group, count in completed.items()))
    for warning in warnings:
        print(f"AVISO: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
