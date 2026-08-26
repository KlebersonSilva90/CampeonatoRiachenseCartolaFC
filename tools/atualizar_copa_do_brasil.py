"""Atualiza a chave e as pontuações automáticas da Copa do Brasil.

Uso: python tools/atualizar_copa_do_brasil.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from atualizar_parciais import (
    ARQUIVO_MAPA,
    calcular_pontuacao,
    carregar_mapa,
    clubes_com_partida_encerrada,
    consultar,
    localizar_time,
    mapa_parciais,
    normalizar,
    salvar,
    salvar_estado_se_mudou,
)
from extrair_copa_do_brasil import OUTPUT, build_data, finalizar_partida, validar


def indice_mapeamentos(mapa: dict) -> dict[str, list[dict]]:
    indice: dict[str, list[dict]] = {}
    for chave, cadastro in mapa.get("times", {}).items():
        if not cadastro or not cadastro.get("timeId"):
            continue
        nome = chave.split("|", 1)[-1]
        indice.setdefault(normalizar(nome), []).append(cadastro)
    return indice


def garantir_mapeamentos(data: dict, mapa: dict) -> tuple[dict, list[str]]:
    indice = indice_mapeamentos(mapa)
    nao_localizados = []
    for participante in data["times"]:
        nome = participante["time"]
        chave = f"CB|{nome}"
        if mapa["times"].get(chave, {}).get("timeId"):
            continue
        existentes = indice.get(normalizar(nome), [])
        ids = {item.get("timeId") for item in existentes}
        if len(ids) == 1:
            cadastro = next(item for item in existentes if item.get("timeId") in ids)
        else:
            cadastro = localizar_time(nome, participante.get("cartoleiro", ""))
            time.sleep(0.12)
        mapa["times"][chave] = cadastro or {"timeId": None, "slug": None, "nomeCartola": None}
        if not cadastro or not cadastro.get("timeId"):
            nao_localizados.append(nome)
    return mapa, nao_localizados


def obter_pontos_historicos(time_id: int, rodada: int):
    resposta = consultar(f"/time/id/{time_id}/{rodada}") or {}
    pontos = resposta.get("pontos")
    return round(float(pontos), 2) if isinstance(pontos, (int, float)) else None


def partida_anterior(anterior: dict, fase_id: str, indice: int):
    fase = next((item for item in anterior.get("fases", []) if item.get("id") == fase_id), None)
    if not fase or indice >= len(fase.get("partidas", [])):
        return None
    return fase["partidas"][indice]


def pontuacao_preservada(anterior_partida, perna: str, lado: str):
    if not anterior_partida:
        return None
    return anterior_partida.get(perna, {}).get(lado)


def atualizar_perna(
    partida: dict,
    perna: str,
    rodada: int,
    rodada_atual: int,
    mercado_fechado: bool,
    mapa: dict,
    parciais: dict,
    clubes_encerrados: set,
    anterior_partida: dict | None,
) -> None:
    dados_perna = partida[perna]
    if rodada > rodada_atual or (rodada == rodada_atual and not mercado_fechado):
        dados_perna["status"] = "aguardando"
        return
    anterior_perna = (anterior_partida or {}).get(perna, {})
    mesmos_times = anterior_partida and all(
        anterior_partida.get(lado) == partida.get(lado) for lado in ("time1", "time2")
    )
    if (
        rodada < rodada_atual
        and mesmos_times
        and anterior_perna.get("status") == "concluida"
        and all(isinstance(anterior_perna.get(lado), (int, float)) for lado in ("time1", "time2"))
    ):
        dados_perna.update({
            "time1": anterior_perna["time1"],
            "time2": anterior_perna["time2"],
            "status": "concluida",
        })
        return
    for lado in ("time1", "time2"):
        nome = partida.get(lado)
        if not nome:
            continue
        cadastro = mapa["times"].get(f"CB|{nome}", {})
        time_id = cadastro.get("timeId")
        pontos = None
        if time_id:
            try:
                if rodada == rodada_atual and mercado_fechado:
                    escalacao = consultar(f"/time/id/{time_id}") or {}
                    pontos = calcular_pontuacao(escalacao, parciais, clubes_encerrados)
                elif rodada < rodada_atual:
                    pontos = obter_pontos_historicos(time_id, rodada)
            except (HTTPError, URLError, TimeoutError, ValueError):
                pontos = None
            time.sleep(0.12)
        if pontos is None:
            pontos = pontuacao_preservada(anterior_partida, perna, lado)
        dados_perna[lado] = pontos
    dados_perna["status"] = "parcial" if rodada == rodada_atual else "concluida"


def atualizar_status_partida(partida: dict) -> None:
    finalizar_partida(partida, [partida["ida"]["rodadaCartola"], partida["volta"]["rodadaCartola"]])
    ida = partida["ida"]
    volta = partida["volta"]
    if volta["status"] == "concluida":
        partida["status"] = "aguardando-desempate" if partida["empatadoNoAgregado"] else "concluido"
    elif ida["status"] in {"parcial", "concluida"} or volta["status"] == "parcial":
        partida["status"] = "em-andamento"
    else:
        partida["status"] = "agendado"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data, _ = build_data()
    erros = validar(data)
    if erros:
        print("Atualização cancelada:")
        for erro in erros:
            print(f"  ERRO: {erro}")
        return 1

    anterior = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    mercado = consultar("/mercado/status") or {}
    rodada_atual = int(mercado.get("rodada_atual") or 0)
    mercado_fechado = mercado.get("status_mercado") == 2
    mapa = carregar_mapa()
    antes = json.dumps(mapa.get("times", {}), ensure_ascii=False, sort_keys=True)
    mapa, nao_localizados = garantir_mapeamentos(data, mapa)
    if json.dumps(mapa["times"], ensure_ascii=False, sort_keys=True) != antes:
        mapa["atualizadoEm"] = datetime.now(timezone.utc).isoformat()
        salvar(ARQUIVO_MAPA, mapa)

    parciais = {}
    clubes_encerrados = set()
    if mercado_fechado and 24 <= rodada_atual <= 37:
        parciais = mapa_parciais(consultar("/atletas/pontuados"))
        partidas_cartola = consultar(f"/partidas/{rodada_atual}") or {}
        clubes_encerrados = clubes_com_partida_encerrada(partidas_cartola)

    for fase in data["fases"]:
        ida, volta = fase["rodadasCartola"]
        for indice, partida in enumerate(fase["partidas"]):
            anterior_partida = partida_anterior(anterior, fase["id"], indice)
            atualizar_perna(partida, "ida", ida, rodada_atual, mercado_fechado, mapa, parciais, clubes_encerrados, anterior_partida)
            atualizar_perna(partida, "volta", volta, rodada_atual, mercado_fechado, mapa, parciais, clubes_encerrados, anterior_partida)
            atualizar_status_partida(partida)

    data["cartola"] = {
        "rodadaAtual": rodada_atual,
        "mercadoFechado": mercado_fechado,
        "bolaRolando": bool(mercado.get("bola_rolando")),
    }
    data["avisos"] = [f"Time ainda não localizado no Cartola: {nome}" for nome in nao_localizados]
    alterado = salvar_estado_se_mudou(OUTPUT, data)
    print(
        f"{'Gerado' if alterado else 'Sem alterações'}: "
        f"{OUTPUT.relative_to(OUTPUT.parents[1])}"
    )
    print(f"Rodada do Cartola: {rodada_atual or 'não informada'}")
    if nao_localizados:
        print("AVISO: sem identificação: " + ", ".join(nao_localizados))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
