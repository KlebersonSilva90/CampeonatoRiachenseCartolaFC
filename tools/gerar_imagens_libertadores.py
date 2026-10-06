"""Gera PNGs dos grupos e das fases eliminatórias da Libertadores."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from PIL import ImageDraw

from gerar_imagens import (
    ALTURA,
    CORES,
    LARGURA,
    fonte,
    fundo_degrade,
    pontos,
    texto_centralizado,
    texto_limitado,
)


ROOT = Path(__file__).resolve().parents[1]
ARQUIVO_DADOS = ROOT / "dados" / "libertadores.json"

FONTES = {
    "marca": fonte(26, True),
    "titulo": fonte(43, True),
    "subtitulo": fonte(22),
    "secao": fonte(20, True),
    "cabecalho": fonte(13, True),
    "tabela": fonte(17),
    "tabela_bold": fonte(17, True),
    "rodada": fonte(15, True),
    "time": fonte(15, True),
    "placar": fonte(16, True),
    "rodape": fonte(16),
    "time_mata_mata": fonte(19, True),
    "placar_mata_mata": fonte(18, True),
    "rotulo_mata_mata": fonte(12, True),
}

FASES_MATA_MATA = {
    "oitavas": "oitavas",
    "oitavas-de-final": "oitavas",
    "quartas": "quartas",
    "quartas-de-final": "quartas",
    "semifinais": "semifinais",
    "semi": "semifinais",
    "final": "final",
}


def carregar_dados() -> dict:
    if not ARQUIVO_DADOS.exists():
        raise SystemExit(f"Dados não encontrados: {ARQUIVO_DADOS}")
    return json.loads(ARQUIVO_DADOS.read_text(encoding="utf-8"))


def cor_classificacao(equipe: dict) -> str:
    destino = equipe.get("destinoAtual")
    if destino == "oitavas":
        return CORES["acesso"]
    if destino == "copa-do-brasil":
        return "#FFE7A6"
    return CORES["rebaixamento"]


def cor_resultado(equipe: dict) -> str:
    if equipe.get("resultado") == "V":
        return CORES["vencedor"]
    if equipe.get("resultado") == "E":
        return CORES["empate"]
    return CORES["texto"]


def desenhar_classificacao(draw: ImageDraw.ImageDraw, grupo: dict) -> None:
    x1, y1, x2, y2 = 43, 260, LARGURA - 43, 523
    draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=CORES["cartao"], outline="#8B5A13", width=2)
    draw.text((x1 + 16, y1 - 25), "CLASSIFICAÇÃO", font=FONTES["secao"], fill=CORES["texto"], anchor="lm")
    colunas = [
        ("POS", 58), ("TIME", 420), ("PTS", 64), ("J", 50),
        ("V", 50), ("E", 50), ("D", 50), ("PP", 92), ("SALDO", 100),
    ]
    altura_cabecalho = 39
    altura_linha = 55
    x = x1 + 14
    for titulo, largura in colunas:
        ancora = "lm" if titulo == "TIME" else "mm"
        px = x + (7 if titulo == "TIME" else largura // 2)
        draw.text((px, y1 + altura_cabecalho // 2), titulo, font=FONTES["cabecalho"], fill=CORES["texto_suave"], anchor=ancora)
        x += largura

    for indice, equipe in enumerate(grupo["classificacao"]):
        topo = y1 + altura_cabecalho + indice * altura_linha
        centro = topo + altura_linha // 2
        draw.rectangle((x1 + 2, topo, x2 - 2, topo + altura_linha), fill=cor_classificacao(equipe))
        valores = [
            f"{equipe['posicao']}º", equipe["time"], str(equipe["pontos"]), str(equipe["jogos"]),
            str(equipe["vitorias"]), str(equipe["empates"]), str(equipe["derrotas"]),
            pontos(equipe["pontosPro"]), pontos(equipe["saldo"]),
        ]
        x = x1 + 14
        for (titulo, largura), valor in zip(colunas, valores):
            if titulo == "TIME":
                valor = texto_limitado(draw, valor, largura - 18, FONTES["tabela_bold"])
                draw.text((x + 7, centro), valor, font=FONTES["tabela_bold"], fill=CORES["texto"], anchor="lm")
            else:
                draw.text((x + largura // 2, centro), valor, font=FONTES["tabela"], fill=CORES["texto"], anchor="mm")
            x += largura


def desenhar_rodada(draw: ImageDraw.ImageDraw, rodada: dict, caixa: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = caixa
    draw.rounded_rectangle(caixa, radius=15, fill=CORES["cartao"], outline="#9A681E", width=2)
    cartola = rodada.get("rodadaCartola")
    titulo = f"{rodada['numero']}ª RODADA"
    if cartola:
        titulo += f" • CARTOLA {cartola}"
    texto_centralizado(draw, ((x1 + x2) // 2, y1 + 17), titulo, FONTES["rodada"], CORES["texto_suave"])

    for indice, partida in enumerate(rodada["partidas"]):
        centro_y = y1 + 53 + indice * 43
        mandante, visitante = partida["mandante"], partida["visitante"]
        nome1 = texto_limitado(draw, mandante["time"], 160, FONTES["time"])
        nome2 = texto_limitado(draw, visitante["time"], 160, FONTES["time"])
        draw.text((x1 + 13, centro_y), nome1, font=FONTES["time"], fill=cor_resultado(mandante), anchor="lm")
        draw.text((x2 - 13, centro_y), nome2, font=FONTES["time"], fill=cor_resultado(visitante), anchor="rm")
        placar = f"{pontos(mandante.get('pontuacao'))} × {pontos(visitante.get('pontuacao'))}"
        texto_centralizado(draw, ((x1 + x2) // 2, centro_y), placar, FONTES["placar"], CORES["texto"])


def gerar_grupo(dados: dict, grupo: dict, destino: Path) -> None:
    imagem = fundo_degrade()
    draw = ImageDraw.Draw(imagem)
    draw.rectangle((0, 0, LARGURA, 118), fill="#D96B00")
    texto_centralizado(draw, (LARGURA // 2, 42), "CAMPEONATO RIACHENSE CARTOLA FC", FONTES["marca"], CORES["branco"])
    texto_centralizado(draw, (LARGURA // 2, 169), "LIBERTADORES", FONTES["titulo"], CORES["texto"])
    texto_centralizado(draw, (LARGURA // 2, 216), f"GRUPO {grupo['grupo']} • CLASSIFICAÇÃO E JOGOS", FONTES["subtitulo"], CORES["texto"])

    desenhar_classificacao(draw, grupo)
    draw.text((43, 557), "RESULTADOS", font=FONTES["secao"], fill=CORES["texto"], anchor="lm")
    margem, gap_x, gap_y = 43, 14, 13
    largura_card = (LARGURA - 2 * margem - gap_x) // 2
    altura_card = 128
    inicio_y = 580
    for indice, rodada in enumerate(grupo["rodadas"]):
        coluna, linha = indice % 2, indice // 2
        x1 = margem + coluna * (largura_card + gap_x)
        y1 = inicio_y + linha * (altura_card + gap_y)
        desenhar_rodada(draw, rodada, (x1, y1, x1 + largura_card, y1 + altura_card))

    draw.rounded_rectangle((43, 1015, LARGURA - 43, 1062), radius=12, fill="#F3E2BD")
    texto_centralizado(
        draw, (LARGURA // 2, 1038),
        "1º e 2º: oitavas • 3º: Copa do Brasil • vencedor em vermelho",
        FONTES["rodape"], CORES["texto_suave"],
    )
    try:
        atualizado = datetime.fromisoformat(dados.get("atualizadoEm", "")).strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        atualizado = "data não informada"
    texto_centralizado(draw, (LARGURA // 2, ALTURA - 27), f"Dados atualizados em {atualizado}", FONTES["rodape"], CORES["texto_suave"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(destino, "PNG", optimize=True)


def cor_time_mata_mata(partida: dict, nome: str) -> str:
    if partida.get("empatadoNoAgregado"):
        return CORES["empate"]
    if partida.get("vencedor") == nome:
        return CORES["vencedor"]
    return CORES["texto"]


def desenhar_confronto_mata_mata(
    draw: ImageDraw.ImageDraw,
    partida: dict,
    caixa: tuple[int, int, int, int],
) -> None:
    x1, y1, x2, y2 = caixa
    draw.rounded_rectangle(caixa, radius=15, fill=CORES["cartao"], outline="#9A681E", width=2)
    colunas_x = (x2 - 166, x2 - 104, x2 - 38)
    for x, rotulo in zip(colunas_x, ("IDA", "VOLTA", "TOTAL")):
        draw.text((x, y1 + 15), rotulo, font=FONTES["rotulo_mata_mata"], fill=CORES["texto_suave"], anchor="mm")

    altura = y2 - y1
    linhas_y = (y1 + altura * 0.38, y1 + altura * 0.76)
    for y, lado, nome in (
        (linhas_y[0], "time1", partida.get("time1") or "A definir"),
        (linhas_y[1], "time2", partida.get("time2") or "A definir"),
    ):
        nome_exibido = texto_limitado(draw, nome, (x2 - x1) - 210, FONTES["time_mata_mata"])
        draw.text((x1 + 15, y), nome_exibido, font=FONTES["time_mata_mata"], fill=cor_time_mata_mata(partida, nome), anchor="lm")
        valores = (
            pontos(partida.get("ida", {}).get(lado)),
            pontos(partida.get("volta", {}).get(lado)),
            pontos(partida.get("agregado", {}).get(lado)),
        )
        for x, valor in zip(colunas_x, valores):
            draw.text((x, y), valor, font=FONTES["placar_mata_mata"], fill=CORES["texto"], anchor="mm")


def gerar_mata_mata(dados: dict, fase: dict, destino: Path) -> None:
    imagem = fundo_degrade()
    draw = ImageDraw.Draw(imagem)
    draw.rectangle((0, 0, LARGURA, 118), fill="#D96B00")
    texto_centralizado(draw, (LARGURA // 2, 42), "CAMPEONATO RIACHENSE CARTOLA FC", FONTES["marca"], CORES["branco"])
    texto_centralizado(draw, (LARGURA // 2, 171), "LIBERTADORES", FONTES["titulo"], CORES["texto"])
    rodadas = fase.get("rodadasCartola", [])
    subtitulo = f"{fase['nome'].upper()} • IDA E VOLTA"
    if len(rodadas) == 2:
        subtitulo += f" • RODADAS {rodadas[0]} E {rodadas[1]}"
    texto_centralizado(draw, (LARGURA // 2, 219), subtitulo, FONTES["subtitulo"], CORES["texto"])

    partidas = fase.get("partidas", [])
    colunas = 2
    linhas = max((len(partidas) + colunas - 1) // colunas, 1)
    inicio_y, fim_y = 275, 1220
    margem, gap_x, gap_y = 43, 16, 18
    largura_card = (LARGURA - 2 * margem - gap_x) // 2
    altura_card = min(205, (fim_y - inicio_y - gap_y * (linhas - 1)) // linhas)
    for indice, partida in enumerate(partidas):
        coluna, linha = indice % colunas, indice // colunas
        x1 = margem + coluna * (largura_card + gap_x)
        y1 = inicio_y + linha * (altura_card + gap_y)
        desenhar_confronto_mata_mata(draw, partida, (x1, y1, x1 + largura_card, y1 + altura_card))

    try:
        atualizado = datetime.fromisoformat(dados.get("atualizadoEm", "")).strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        atualizado = "data não informada"
    texto_centralizado(draw, (LARGURA // 2, 1324), f"Dados atualizados em {atualizado}", FONTES["rodape"], CORES["texto_suave"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(destino, "PNG", optimize=True)


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera imagens dos grupos e do mata-mata da Libertadores.")
    parser.add_argument("grupos", nargs="*", help="Grupos A a H; omita para gerar todos")
    parser.add_argument("--fase", choices=sorted(FASES_MATA_MATA), help="Fase eliminatória a gerar")
    parser.add_argument("--saida", default=str(ROOT / "imagens-geradas"), help="Diretório dos PNGs")
    return parser.parse_args()


def main() -> int:
    args = argumentos()
    dados = carregar_dados()
    saida = Path(args.saida).resolve()
    if args.fase:
        fase_id = FASES_MATA_MATA[args.fase]
        fases = {fase["id"]: fase for fase in dados.get("mataMata", [])}
        fase = fases.get(fase_id)
        if not fase:
            raise SystemExit(f"Fase não encontrada nos dados: {fase_id}")
        destino = saida / f"libertadores-{fase_id}.png"
        gerar_mata_mata(dados, fase, destino)
        print(f"Gerado: {destino}")
        return 0
    solicitados = [grupo.upper() for grupo in args.grupos] or list("ABCDEFGH")
    invalidos = [grupo for grupo in solicitados if grupo not in "ABCDEFGH"]
    if invalidos:
        raise SystemExit("Grupos inválidos: " + ", ".join(invalidos))
    grupos = {grupo["grupo"]: grupo for grupo in dados["grupos"]}
    for letra in solicitados:
        destino = saida / f"libertadores-grupo-{letra.lower()}.png"
        gerar_grupo(dados, grupos[letra], destino)
        print(f"Gerado: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
