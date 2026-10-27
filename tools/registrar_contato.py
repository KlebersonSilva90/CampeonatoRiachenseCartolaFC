"""Registra contatos realizados com times reincidentes sem escalação.

Uso:
    python tools/registrar_contato.py --listar
    python tools/registrar_contato.py --serie E --time "Vermeiras FC"
    python tools/registrar_contato.py --cartoleiro "Wesley"
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from verificar_nao_escalados import encontrar_nao_escalados


ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "dados"
ARQUIVO_CONTATOS = DADOS / "alertas-nao-escalados.json"
SERIES = tuple("ABCDE")
LIMITE = 5


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    sem_acentos = "".join(letra for letra in texto if not unicodedata.combining(letra))
    return " ".join(sem_acentos.casefold().split())


def chave_registro(serie: str, time: str) -> str:
    return f"{serie.upper()}|{normalizar(time)}"


def carregar_contatos(arquivo: Path = ARQUIVO_CONTATOS) -> dict:
    if not arquivo.exists():
        return {"versao": 1, "atualizadoEm": None, "contatos": {}}
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    dados.setdefault("versao", 1)
    dados.setdefault("atualizadoEm", None)
    dados.setdefault("contatos", {})
    return dados


def carregar_ocorrencias() -> list[dict]:
    ocorrencias = []
    for serie in SERIES:
        arquivo = DADOS / f"serie-{serie.lower()}.json"
        data = json.loads(arquivo.read_text(encoding="utf-8"))
        ocorrencias.extend(encontrar_nao_escalados(data))
    return ocorrencias


def resumir_times(ocorrencias: list[dict], contatos: dict) -> list[dict]:
    registros: dict[str, dict] = {}
    for ocorrencia in ocorrencias:
        chave = chave_registro(ocorrencia["serie"], ocorrencia["time"])
        registro = registros.setdefault(
            chave,
            {
                "chave": chave,
                "serie": ocorrencia["serie"],
                "time": ocorrencia["time"],
                "cartoleiro": ocorrencia["cartoleiro"],
                "total": 0,
            },
        )
        registro["total"] += 1

    reconhecidos = contatos.get("contatos", {})
    for registro in registros.values():
        contato = reconhecidos.get(registro["chave"], {})
        registro["reconhecidas"] = max(0, int(contato.get("ocorrenciasReconhecidas", 0)))
        registro["novas"] = max(0, registro["total"] - registro["reconhecidas"])
    return sorted(
        registros.values(),
        key=lambda item: (-item["novas"], item["serie"], normalizar(item["time"])),
    )


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lista alertas pendentes ou registra o contato com um participante."
    )
    acao = parser.add_mutually_exclusive_group(required=True)
    acao.add_argument("--listar", action="store_true", help="Lista alertas ainda pendentes.")
    acao.add_argument("--time", help="Nome do time cujo contato foi realizado.")
    acao.add_argument("--cartoleiro", help="Nome do cartoleiro cujo contato foi realizado.")
    parser.add_argument("--serie", choices=SERIES, type=str.upper, help="Restringe a busca a uma série.")
    return parser.parse_args()


def selecionar(registros: list[dict], args: argparse.Namespace) -> dict:
    candidatos = registros
    if args.serie:
        candidatos = [item for item in candidatos if item["serie"] == args.serie]
    if args.time:
        procurado = normalizar(args.time)
        candidatos = [item for item in candidatos if normalizar(item["time"]) == procurado]
    if args.cartoleiro:
        procurado = normalizar(args.cartoleiro)
        candidatos = [item for item in candidatos if normalizar(item["cartoleiro"]) == procurado]
    if not candidatos:
        raise SystemExit("Nenhum participante encontrado com os dados informados.")
    if len(candidatos) > 1:
        encontrados = ", ".join(f"Série {item['serie']} · {item['time']}" for item in candidatos)
        raise SystemExit(f"Mais de um participante encontrado ({encontrados}). Informe também --serie.")
    return candidatos[0]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = argumentos()
    contatos = carregar_contatos()
    registros = resumir_times(carregar_ocorrencias(), contatos)

    if args.listar:
        pendentes = [item for item in registros if item["novas"] >= LIMITE]
        if not pendentes:
            print("Nenhum contato pendente no momento.")
            return 0
        print("CONTATOS PENDENTES")
        for item in pendentes:
            print(
                f"  Série {item['serie']} | {item['time']} ({item['cartoleiro']}) | "
                f"{item['novas']} nova(s), {item['total']} no total"
            )
        return 0

    selecionado = selecionar(registros, args)
    if selecionado["novas"] < LIMITE:
        raise SystemExit(
            f"{selecionado['time']} possui somente {selecionado['novas']} nova(s) ocorrência(s); "
            f"o alerta é exibido a partir de {LIMITE}."
        )

    agora = datetime.now(timezone.utc).isoformat()
    contatos["contatos"][selecionado["chave"]] = {
        "serie": selecionado["serie"],
        "time": selecionado["time"],
        "cartoleiro": selecionado["cartoleiro"],
        "ocorrenciasReconhecidas": selecionado["total"],
        "contatoRegistradoEm": agora,
    }
    contatos["atualizadoEm"] = agora
    ARQUIVO_CONTATOS.write_text(
        json.dumps(contatos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Contato registrado: Série {selecionado['serie']} · {selecionado['time']} "
        f"({selecionado['cartoleiro']}). Contagem reiniciada após {selecionado['total']} ocorrência(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
