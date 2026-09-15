"""Atualiza automaticamente grupos e mata-mata da Libertadores pelo Cartola FC."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from atualizar_copa_do_brasil import indice_mapeamentos, obter_pontos_historicos
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
from extrair_libertadores import (
    OUTPUT,
    build_data,
    group_destination,
    standings_sort_key,
    validate_data,
)
from extrair_serie_a import match_result


RODADAS_GRUPOS = {numero: 22 + numero for numero in range(1, 7)}


def participantes(data: dict) -> list[dict]:
    encontrados = {}
    for grupo in data["grupos"]:
        cartoleiros = {
            equipe["time"]: equipe.get("cartoleiro", "")
            for rodada in grupo["rodadas"]
            for partida in rodada["partidas"]
            for equipe in (partida["mandante"], partida["visitante"])
        }
        for equipe in grupo["classificacao"]:
            encontrados[equipe["time"]] = {
                "time": equipe["time"],
                "cartoleiro": cartoleiros.get(equipe["time"], ""),
            }
    return list(encontrados.values())


def garantir_mapeamentos(data: dict, mapa: dict) -> tuple[dict, list[str]]:
    indice = indice_mapeamentos(mapa)
    nao_localizados = []
    for participante in participantes(data):
        nome = participante["time"]
        chave = f"LIB|{nome}"
        if mapa["times"].get(chave, {}).get("timeId"):
            continue
        existentes = indice.get(normalizar(nome), [])
        ids = {item.get("timeId") for item in existentes if item.get("timeId")}
        if len(ids) == 1:
            cadastro = next(item for item in existentes if item.get("timeId") in ids)
        else:
            cadastro = localizar_time(nome, participante.get("cartoleiro", ""))
            time.sleep(0.12)
        mapa["times"][chave] = cadastro or {"timeId": None, "slug": None, "nomeCartola": None}
        if not cadastro or not cadastro.get("timeId"):
            nao_localizados.append(nome)
    return mapa, nao_localizados


def pontuar_time(nome, rodada, rodada_atual, mercado_fechado, mapa, parciais, clubes_encerrados):
    time_id = mapa["times"].get(f"LIB|{nome}", {}).get("timeId")
    if not time_id:
        return None
    if rodada == rodada_atual and mercado_fechado:
        escalacao = consultar(f"/time/id/{time_id}") or {}
        return calcular_pontuacao(escalacao, parciais, clubes_encerrados)
    if rodada < rodada_atual:
        return obter_pontos_historicos(time_id, rodada)
    return None


def pode_preservar(rodada: int, rodada_atual: int, anterior_status: str, valores: list) -> bool:
    return (
        rodada < rodada_atual - 1
        and anterior_status == "concluida"
        and all(isinstance(valor, (int, float)) for valor in valores)
    )


def atualizar_confronto(
    partida, anterior, rodada, rodada_atual, mercado_fechado, mapa, parciais, clubes_encerrados
) -> str:
    if rodada > rodada_atual or (rodada == rodada_atual and not mercado_fechado):
        partida["status"] = "aguardando"
        return "aguardando"
    mesmos_times = anterior and all(
        anterior.get(lado, {}).get("time") == partida.get(lado, {}).get("time")
        for lado in ("mandante", "visitante")
    )
    valores_anteriores = [
        (anterior or {}).get(lado, {}).get("pontuacao") for lado in ("mandante", "visitante")
    ]
    if mesmos_times and pode_preservar(
        rodada, rodada_atual, (anterior or {}).get("status", ""), valores_anteriores
    ):
        for lado, valor in zip(("mandante", "visitante"), valores_anteriores):
            partida[lado]["pontuacao"] = valor
        status = "concluida"
    else:
        historico_confirmado = rodada < rodada_atual
        for lado in ("mandante", "visitante"):
            try:
                valor = pontuar_time(
                    partida[lado]["time"], rodada, rodada_atual, mercado_fechado,
                    mapa, parciais, clubes_encerrados,
                )
            except (HTTPError, URLError, TimeoutError, ValueError):
                valor = None
            time.sleep(0.12)
            if rodada < rodada_atual and valor is None:
                historico_confirmado = False
            if valor is None:
                valor = (anterior or {}).get(lado, {}).get("pontuacao")
            partida[lado]["pontuacao"] = valor
        status = "concluida" if historico_confirmado else "parcial"
        if rodada == rodada_atual:
            status = "parcial"

    mandante, visitante = partida["mandante"], partida["visitante"]
    resultado_mandante, resultado_visitante = match_result(
        mandante.get("pontuacao"), visitante.get("pontuacao")
    )
    mandante["resultado"] = resultado_mandante
    visitante["resultado"] = resultado_visitante
    partida["status"] = status
    return status


def confronto_anterior_grupo(anterior: dict, grupo: str, numero: int, indice: int):
    grupo_anterior = next((item for item in anterior.get("grupos", []) if item.get("grupo") == grupo), None)
    rodada = next(
        (item for item in (grupo_anterior or {}).get("rodadas", []) if item.get("numero") == numero), None
    )
    partidas = (rodada or {}).get("partidas", [])
    return partidas[indice] if indice < len(partidas) else None


def recalcular_classificacao(data: dict) -> None:
    classificados_oitavas = []
    classificados_copa = []
    for grupo in data["grupos"]:
        nomes = [equipe["time"] for equipe in grupo["classificacao"]]
        tabela = {
            nome: {
                "time": nome, "pontos": 0, "jogos": 0, "vitorias": 0, "empates": 0,
                "derrotas": 0, "pontosPro": 0.0, "pontosContra": 0.0, "saldo": 0.0, "media": 0.0,
            }
            for nome in nomes
        }
        for rodada in grupo["rodadas"]:
            for partida in rodada["partidas"]:
                mandante, visitante = partida["mandante"], partida["visitante"]
                if not all(isinstance(equipe.get("pontuacao"), (int, float)) for equipe in (mandante, visitante)):
                    continue
                for equipe, adversario in ((mandante, visitante), (visitante, mandante)):
                    linha = tabela[equipe["time"]]
                    linha["jogos"] += 1
                    linha["pontosPro"] += equipe["pontuacao"]
                    linha["pontosContra"] += adversario["pontuacao"]
                    if equipe.get("resultado") == "V":
                        linha["vitorias"] += 1
                        linha["pontos"] += 3
                    elif equipe.get("resultado") == "E":
                        linha["empates"] += 1
                        linha["pontos"] += 1
                    else:
                        linha["derrotas"] += 1
        classificacao = []
        for linha in tabela.values():
            linha["pontosPro"] = round(linha["pontosPro"], 2)
            linha["pontosContra"] = round(linha["pontosContra"], 2)
            linha["saldo"] = round(linha["pontosPro"] - linha["pontosContra"], 2)
            linha["media"] = round(linha["pontosPro"] / linha["jogos"], 2) if linha["jogos"] else 0
            classificacao.append(linha)
        classificacao.sort(key=standings_sort_key)
        for posicao, equipe in enumerate(classificacao, start=1):
            equipe["posicao"] = posicao
            equipe["destinoAtual"] = group_destination(posicao)
        grupo["classificacao"] = classificacao
        classificados_oitavas.extend(
            {"grupo": grupo["grupo"], "time": equipe["time"], "posicao": equipe["posicao"]}
            for equipe in classificacao[:2]
        )
        classificados_copa.append(
            {"grupo": grupo["grupo"], "time": classificacao[2]["time"], "posicao": 3}
        )
    data["classificacaoAtual"] = {"oitavas": classificados_oitavas, "copaDoBrasil": classificados_copa}


def partida_anterior_mata(anterior: dict, fase_id: str, indice: int):
    fase = next((item for item in anterior.get("mataMata", []) if item.get("id") == fase_id), None)
    partidas = (fase or {}).get("partidas", [])
    return partidas[indice] if indice < len(partidas) else None


def atualizar_perna_mata(
    partida, perna, rodada, rodada_atual, mercado_fechado, mapa, parciais, clubes_encerrados, anterior
) -> None:
    dados = partida[perna]
    if rodada > rodada_atual or (rodada == rodada_atual and not mercado_fechado):
        dados["status"] = "aguardando"
        return
    anterior_perna = (anterior or {}).get(perna, {})
    mesmos_times = anterior and all(anterior.get(lado) == partida.get(lado) for lado in ("time1", "time2"))
    valores = [anterior_perna.get(lado) for lado in ("time1", "time2")]
    if mesmos_times and pode_preservar(rodada, rodada_atual, anterior_perna.get("status", ""), valores):
        dados.update({"time1": valores[0], "time2": valores[1], "status": "concluida"})
        return
    historico_confirmado = rodada < rodada_atual
    for lado in ("time1", "time2"):
        try:
            valor = pontuar_time(
                partida[lado], rodada, rodada_atual, mercado_fechado,
                mapa, parciais, clubes_encerrados,
            )
        except (HTTPError, URLError, TimeoutError, ValueError):
            valor = None
        time.sleep(0.12)
        if rodada < rodada_atual and valor is None:
            historico_confirmado = False
        dados[lado] = valor if valor is not None else anterior_perna.get(lado)
    dados["status"] = "concluida" if historico_confirmado else "parcial"
    if rodada == rodada_atual:
        dados["status"] = "parcial"


def finalizar_mata(partida: dict) -> None:
    ida, volta = partida["ida"], partida["volta"]
    completo = all(
        isinstance(perna.get(lado), (int, float))
        for perna in (ida, volta) for lado in ("time1", "time2")
    )
    if completo:
        total1 = round(ida["time1"] + volta["time1"], 2)
        total2 = round(ida["time2"] + volta["time2"], 2)
        partida["agregado"] = {"time1": total1, "time2": total2}
    else:
        total1 = total2 = None
        partida["agregado"] = {"time1": None, "time2": None}
    concluido = completo and ida.get("status") == volta.get("status") == "concluida"
    partida["vencedor"] = None
    partida["empatadoNoAgregado"] = bool(concluido and total1 == total2)
    if concluido and total1 != total2:
        partida["vencedor"] = partida["time1"] if total1 > total2 else partida["time2"]
    if concluido:
        partida["status"] = "aguardando-desempate" if partida["empatadoNoAgregado"] else "concluido"
    elif ida.get("status") in {"parcial", "concluida"} or volta.get("status") == "parcial":
        partida["status"] = "em-andamento"
    else:
        partida["status"] = "agendado"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data, _, _ = build_data()
    erros, _ = validate_data(data)
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
    if mercado_fechado and 23 <= rodada_atual <= 36:
        parciais = mapa_parciais(consultar("/atletas/pontuados"))
        clubes_encerrados = clubes_com_partida_encerrada(consultar(f"/partidas/{rodada_atual}") or {})

    for grupo in data["grupos"]:
        for rodada in grupo["rodadas"]:
            rodada_cartola = RODADAS_GRUPOS[rodada["numero"]]
            statuses = []
            for indice, partida in enumerate(rodada["partidas"]):
                anterior_partida = confronto_anterior_grupo(
                    anterior, grupo["grupo"], rodada["numero"], indice
                )
                statuses.append(atualizar_confronto(
                    partida, anterior_partida, rodada_cartola, rodada_atual, mercado_fechado,
                    mapa, parciais, clubes_encerrados,
                ))
            rodada["rodadaCartola"] = rodada_cartola
            rodada["concluida"] = bool(statuses) and all(status == "concluida" for status in statuses)
            rodada["status"] = (
                "concluida" if rodada["concluida"]
                else ("parcial" if "parcial" in statuses else "aguardando")
            )

    recalcular_classificacao(data)

    for fase in data["mataMata"]:
        rodadas = fase.get("rodadasCartola", [])
        if len(rodadas) != 2:
            continue
        for indice, partida in enumerate(fase["partidas"]):
            anterior_partida = partida_anterior_mata(anterior, fase["id"], indice)
            atualizar_perna_mata(
                partida, "ida", rodadas[0], rodada_atual, mercado_fechado,
                mapa, parciais, clubes_encerrados, anterior_partida,
            )
            atualizar_perna_mata(
                partida, "volta", rodadas[1], rodada_atual, mercado_fechado,
                mapa, parciais, clubes_encerrados, anterior_partida,
            )
            finalizar_mata(partida)

    data["cartola"] = {
        "rodadaAtual": rodada_atual,
        "mercadoFechado": mercado_fechado,
        "bolaRolando": bool(mercado.get("bola_rolando")),
        "rodadasGrupos": RODADAS_GRUPOS,
    }
    data["avisos"] = [f"Time ainda não localizado no Cartola: {nome}" for nome in nao_localizados]
    alterado = salvar_estado_se_mudou(OUTPUT, data)
    print(f"{'Gerado' if alterado else 'Sem alterações'}: {OUTPUT.relative_to(OUTPUT.parents[1])}")
    print(f"Rodada do Cartola: {rodada_atual or 'não informada'}")
    if nao_localizados:
        print("AVISO: sem identificação: " + ", ".join(nao_localizados))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
