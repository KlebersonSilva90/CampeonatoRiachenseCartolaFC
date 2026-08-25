"""Extrai os dados públicos da Série A do arquivo XLSM para o site.

Uso: python tools/extrair_serie_a.py
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}


def column_number(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference).group(0)
    number = 0
    for letter in letters:
        number = number * 26 + ord(letter) - 64
    return number


def load_cells(path: Path, sheet_name: str) -> dict[tuple[int, int], object]:
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("m:si", NS):
                shared_strings.append("".join(node.text or "" for node in item.iterfind(".//m:t", NS)))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relation_id = None
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            if sheet.attrib.get("name") == sheet_name:
                relation_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
                break
        if not relation_id:
            raise ValueError(f"Aba {sheet_name!r} não encontrada em {path.name}")

        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = None
        for relation in relationships.findall("r:Relationship", REL_NS):
            if relation.attrib.get("Id") == relation_id:
                target = relation.attrib["Target"].lstrip("/")
                break
        if not target:
            raise ValueError(f"Arquivo XML da aba {sheet_name!r} não encontrado")
        sheet_path = target if target.startswith("xl/") else f"xl/{target}"
        sheet_root = ET.fromstring(archive.read(sheet_path))

        cells: dict[tuple[int, int], object] = {}
        for cell in sheet_root.findall(".//m:c", NS):
            reference = cell.attrib["r"]
            row = int(re.search(r"\d+", reference).group(0))
            col = column_number(reference)
            cell_type = cell.attrib.get("t")
            value_node = cell.find("m:v", NS)
            inline_node = cell.find("m:is", NS)
            if cell_type == "inlineStr" and inline_node is not None:
                value: object = "".join(node.text or "" for node in inline_node.iterfind(".//m:t", NS))
            elif value_node is None:
                value = None
            elif cell_type == "s":
                value = shared_strings[int(value_node.text)]
            elif cell_type in {"str", "e"}:
                value = value_node.text
            else:
                number = float(value_node.text)
                value = int(number) if number.is_integer() else round(number, 2)
            cells[(row, col)] = value
        return cells


def cell(cells: dict[tuple[int, int], object], row: int, col: int):
    return cells.get((row, col))


def match_result(left_score, right_score) -> tuple[str | None, str | None]:
    if not isinstance(left_score, (int, float)) or not isinstance(right_score, (int, float)):
        return None, None
    difference = round(left_score - right_score, 2)
    if difference >= 5:
        return "V", "D"
    if difference <= -5:
        return "D", "V"
    return "E", "E"


def standings_sort_key(team: dict) -> tuple:
    """Ordena pelos critérios do campeonato: P, V, saldo, PM e nome."""
    return (
        -team["pontos"],
        -team["vitorias"],
        -team["saldo"],
        -team["pontosMarcados"],
        team["time"].casefold(),
    )


def build_data(serie: str = "A") -> tuple[dict, Path]:
    serie = serie.upper()
    if serie not in {"A", "B", "C", "D", "E"}:
        raise ValueError("A série deve ser A, B, C, D ou E")
    source = ROOT / "planilhas" / f"Serie {serie}2.xlsm"
    output = ROOT / "dados" / f"serie-{serie.lower()}.json"
    if not source.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {source}")

    cells = load_cells(source, "Planilha3")
    standings = []
    for row in range(3, 23):
        team = cell(cells, row, 24)
        if not team:
            continue
        standings.append(
            {
                "posicao": 0,
                "time": team,
                "pontos": cell(cells, row, 25),
                "jogos": cell(cells, row, 26),
                "vitorias": cell(cells, row, 27),
                "empates": cell(cells, row, 28),
                "derrotas": cell(cells, row, 29),
                "pontosMarcados": cell(cells, row, 30),
                "pontosSofridos": cell(cells, row, 31),
                "saldo": cell(cells, row, 32),
                "media": cell(cells, row, 33),
            }
        )

    standings.sort(key=standings_sort_key)
    for position, team in enumerate(standings, start=1):
        team["posicao"] = position

    rounds = []
    for number in range(1, 20):
        header_row = 1 + (number - 1) * 12
        matches = []
        for row in range(header_row + 2, header_row + 12):
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
                        "naoEscalou": left_score == 0,
                    },
                    "visitante": {
                        "cartoleiro": cell(cells, row, 12),
                        "time": right_team,
                        "pontuacao": right_score,
                        "resultado": right_result,
                        "naoEscalou": right_score == 0,
                    },
                }
            )
        rounds.append({"numero": number, "partidas": matches})

    data = {
        "serie": serie,
        "fonte": source.name,
        "atualizadoEm": datetime.fromtimestamp(source.stat().st_mtime).isoformat(timespec="seconds"),
        "regraResultado": {"vitoriaDiferencaMinima": 5, "pontosVitoria": 3, "pontosEmpate": 1},
        "classificacao": standings,
        "rodadas": rounds,
    }
    return data, output


def validate_data(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    standings = data["classificacao"]
    rounds = data["rodadas"]

    if len(standings) != 20:
        errors.append(f"classificação possui {len(standings)} times; esperado: 20")
    names = [team["time"] for team in standings]
    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    if duplicate_names:
        errors.append(f"times duplicados: {', '.join(duplicate_names)}")
    if [team["posicao"] for team in standings] != list(range(1, len(standings) + 1)):
        errors.append("posições da classificação não são sequenciais")
    if standings != sorted(standings, key=standings_sort_key):
        errors.append("classificação não respeita os critérios de desempate")

    if len(rounds) != 19:
        errors.append(f"foram encontradas {len(rounds)} rodadas; esperado: 19")

    known_teams = set(names)
    aggregate = {
        name: {"j": 0, "v": 0, "e": 0, "d": 0, "pm": 0.0, "ps": 0.0}
        for name in known_teams
    }
    for round_data in rounds:
        matches = round_data["partidas"]
        if len(matches) != 10:
            errors.append(f"rodada {round_data['numero']} possui {len(matches)} confrontos; esperado: 10")
        for index, match in enumerate(matches, start=1):
            left = match["mandante"]
            right = match["visitante"]
            for side in (left, right):
                if side["time"] not in known_teams:
                    errors.append(
                        f"rodada {round_data['numero']}, jogo {index}: time desconhecido {side['time']!r}"
                    )
            left_has_score = isinstance(left["pontuacao"], (int, float))
            right_has_score = isinstance(right["pontuacao"], (int, float))
            if left_has_score != right_has_score:
                errors.append(
                    f"rodada {round_data['numero']}, jogo {index}: pontuação preenchida somente de um lado"
                )
            if not (left_has_score and right_has_score):
                continue
            if left["time"] not in aggregate or right["time"] not in aggregate:
                continue
            for team, opponent in ((left, right), (right, left)):
                stats = aggregate[team["time"]]
                stats["j"] += 1
                stats[team["resultado"].lower()] += 1
                stats["pm"] += team["pontuacao"]
                stats["ps"] += opponent["pontuacao"]

    tolerance = 0.011
    for team in standings:
        name = team["time"]
        if team["jogos"] != team["vitorias"] + team["empates"] + team["derrotas"]:
            errors.append(f"{name}: J não corresponde a V + E + D")
        if team["pontos"] != 3 * team["vitorias"] + team["empates"]:
            errors.append(f"{name}: pontos não correspondem a 3×V + E")
        if abs(team["saldo"] - (team["pontosMarcados"] - team["pontosSofridos"])) > tolerance:
            errors.append(f"{name}: saldo divergente")
        if team["jogos"] and abs(team["media"] - team["pontosMarcados"] / team["jogos"]) > tolerance:
            errors.append(f"{name}: média divergente")

        stats = aggregate.get(name)
        if not stats:
            continue
        comparisons = {
            "jogos": stats["j"], "vitorias": stats["v"], "empates": stats["e"],
            "derrotas": stats["d"], "pontosMarcados": stats["pm"], "pontosSofridos": stats["ps"],
        }
        for field, calculated in comparisons.items():
            if abs(team[field] - calculated) > tolerance:
                errors.append(f"{name}: {field} diverge dos confrontos")

    completed_rounds = sum(
        1 for round_data in rounds
        if round_data["partidas"] and all(
            isinstance(match["mandante"]["pontuacao"], (int, float))
            and isinstance(match["visitante"]["pontuacao"], (int, float))
            for match in round_data["partidas"]
        )
    )
    if completed_rounds == 0:
        warnings.append("nenhuma rodada possui todos os resultados preenchidos")
    return errors, warnings


def save_data(data: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(serie: str = "A") -> dict:
    data, output = build_data(serie)
    errors, warnings = validate_data(data)
    if errors:
        raise ValueError("; ".join(errors))
    save_data(data, output)
    print(f"Gerado: {output.relative_to(ROOT)} ({len(data['classificacao'])} times, {len(data['rodadas'])} rodadas)")
    for warning in warnings:
        print(f"Aviso: {warning}")
    return data


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "A")
