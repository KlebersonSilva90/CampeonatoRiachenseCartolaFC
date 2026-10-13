"""Lista pontuações iguais a zero nas planilhas das Séries A a E.

Uso:
    python tools/verificar_nao_escalados.py
    python tools/verificar_nao_escalados.py --series A C E
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from extrair_serie_a import build_data


SERIES = tuple("ABCDE")


def encontrar_nao_escalados(data: dict) -> list[dict]:
    ocorrencias = []
    for rodada in data.get("rodadas", []):
        for numero_jogo, partida in enumerate(rodada.get("partidas", []), start=1):
            for lado in ("mandante", "visitante"):
                equipe = partida.get(lado, {})
                pontuacao = equipe.get("pontuacao")
                if (
                    isinstance(pontuacao, (int, float))
                    and not isinstance(pontuacao, bool)
                    and pontuacao == 0
                ):
                    ocorrencias.append(
                        {
                            "serie": data.get("serie"),
                            "rodada": rodada.get("numero"),
                            "jogo": numero_jogo,
                            "time": equipe.get("time") or "Time não informado",
                            "cartoleiro": equipe.get("cartoleiro") or "Cartoleiro não informado",
                        }
                    )
    return ocorrencias


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verifica nas planilhas os times com pontuação igual a zero."
    )
    parser.add_argument(
        "--series",
        nargs="+",
        choices=SERIES,
        type=str.upper,
        default=list(SERIES),
        help="Séries a verificar; por padrão, A B C D E.",
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = argumentos()
    todas = []
    for serie in args.series:
        data, _ = build_data(serie)
        ocorrencias = encontrar_nao_escalados(data)
        todas.extend(ocorrencias)
        print(f"\nSÉRIE {serie}: {len(ocorrencias)} ocorrência(s)")
        for item in ocorrencias:
            print(
                f"  Rodada {item['rodada']:>2} | {item['time']} "
                f"({item['cartoleiro']})"
            )

    print("\nRESUMO POR TIME")
    if not todas:
        print("  Nenhuma pontuação igual a zero foi encontrada.")
        return 0
    contagem = Counter((item["serie"], item["time"]) for item in todas)
    for (serie, time), quantidade in sorted(
        contagem.items(), key=lambda item: (-item[1], item[0][0], item[0][1].casefold())
    ):
        print(f"  Série {serie} | {time}: {quantidade} vez(es)")
    print(f"\nTOTAL: {len(todas)} ocorrência(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
