"""Gera cards PNG das fases da Copa do Brasil.

Exemplos:
    python tools/gerar_imagens_copa.py 1 2
    python tools/gerar_imagens_copa.py --fases primeira-fase segunda-fase
"""

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
ARQUIVO_DADOS = ROOT / "dados" / "copa-do-brasil.json"

FASES = {
    "1": "primeira-fase",
    "2": "segunda-fase",
    "primeira": "primeira-fase",
    "segunda": "segunda-fase",
    "primeira-fase": "primeira-fase",
    "segunda-fase": "segunda-fase",
}

FONTES_COPA = {
    "marca": fonte(26, True),
    "titulo": fonte(44, True),
    "subtitulo": fonte(22),
    "fase": fonte(17, True),
    "time_grande": fonte(19, True),
    "time_compacto": fonte(15, True),
    "placar_grande": fonte(18, True),
    "placar_compacto": fonte(14, True),
    "rotulo": fonte(12, True),
    "rodape": fonte(16),
}


def carregar_dados() -> dict:
    if not ARQUIVO_DADOS.exists():
        raise SystemExit(f"Dados não encontrados: {ARQUIVO_DADOS}")
    return json.loads(ARQUIVO_DADOS.read_text(encoding="utf-8"))


def cor_time(partida: dict, nome: str) -> str:
    if partida.get("empatadoNoAgregado"):
        return CORES["empate"]
    if partida.get("vencedor") == nome:
        return CORES["vencedor"]
    return CORES["texto"]


def placares(partida: dict, lado: str) -> tuple[str, str, str]:
    ida = pontos(partida.get("ida", {}).get(lado))
    volta = pontos(partida.get("volta", {}).get(lado))
    agregado = pontos(partida.get("agregado", {}).get(lado))
    return ida, volta, agregado


def desenhar_card(
    draw: ImageDraw.ImageDraw,
    partida: dict,
    caixa: tuple[int, int, int, int],
    compacto: bool,
) -> None:
    x1, y1, x2, y2 = caixa
    draw.rounded_rectangle(caixa, radius=13, fill=CORES["cartao"], outline="#9A681E", width=2)
    time_font = FONTES_COPA["time_compacto"] if compacto else FONTES_COPA["time_grande"]
    placar_font = FONTES_COPA["placar_compacto"] if compacto else FONTES_COPA["placar_grande"]
    nome_largura = (x2 - x1) - (176 if compacto else 205)

    time1 = texto_limitado(draw, partida.get("time1") or "A definir", nome_largura, time_font)
    time2 = texto_limitado(draw, partida.get("time2") or "A definir", nome_largura, time_font)
    altura = y2 - y1
    linha1 = y1 + altura * 0.34
    linha2 = y1 + altura * 0.72
    draw.text((x1 + 14, linha1), time1, font=time_font, fill=cor_time(partida, partida.get("time1")), anchor="lm")
    draw.text((x1 + 14, linha2), time2, font=time_font, fill=cor_time(partida, partida.get("time2")), anchor="lm")

    colunas_x = (x2 - (142 if compacto else 166), x2 - (88 if compacto else 104), x2 - (32 if compacto else 38))
    if not compacto:
        for x, rotulo in zip(colunas_x, ("IDA", "VOLTA", "TOTAL")):
            draw.text((x, y1 + 13), rotulo, font=FONTES_COPA["rotulo"], fill=CORES["texto_suave"], anchor="mm")

    for linha, lado in ((linha1, "time1"), (linha2, "time2")):
        for x, valor in zip(colunas_x, placares(partida, lado)):
            draw.text((x, linha), valor, font=placar_font, fill=CORES["texto"], anchor="mm")


def gerar_fase(dados: dict, fase: dict, destino: Path) -> None:
    imagem = fundo_degrade()
    draw = ImageDraw.Draw(imagem)
    draw.rectangle((0, 0, LARGURA, 118), fill="#D96B00")
    texto_centralizado(draw, (LARGURA // 2, 42), "CAMPEONATO RIACHENSE CARTOLA FC", FONTES_COPA["marca"], CORES["branco"])
    texto_centralizado(draw, (LARGURA // 2, 171), "COPA DO BRASIL", FONTES_COPA["titulo"], CORES["texto"])
    rodadas = fase.get("rodadasCartola", [])
    subtitulo = f"{fase['nome'].upper()} • IDA E VOLTA"
    if len(rodadas) == 2:
        subtitulo += f" • RODADAS {rodadas[0]} E {rodadas[1]}"
    texto_centralizado(draw, (LARGURA // 2, 219), subtitulo, FONTES_COPA["subtitulo"], CORES["texto"])

    partidas = fase.get("partidas", [])
    colunas = 2
    linhas = (len(partidas) + colunas - 1) // colunas
    inicio_y, fim_y = 258, 1285
    gap_x, gap_y = 14, 7
    margem = 42
    largura_card = (LARGURA - 2 * margem - gap_x) // 2
    altura_card = (fim_y - inicio_y - gap_y * max(linhas - 1, 0)) // max(linhas, 1)
    compacto = linhas > 10

    for indice, partida in enumerate(partidas):
        coluna = indice % colunas
        linha = indice // colunas
        x1 = margem + coluna * (largura_card + gap_x)
        y1 = inicio_y + linha * (altura_card + gap_y)
        desenhar_card(draw, partida, (x1, y1, x1 + largura_card, y1 + altura_card), compacto)

    try:
        atualizado = datetime.fromisoformat(dados.get("atualizadoEm", "")).strftime("%d/%m/%Y às %H:%M")
    except ValueError:
        atualizado = "data não informada"
    texto_centralizado(draw, (LARGURA // 2, 1324), f"Dados atualizados em {atualizado}", FONTES_COPA["rodape"], CORES["texto_suave"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(destino, "PNG", optimize=True)


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera PNGs das fases da Copa do Brasil.")
    parser.add_argument("fases_posicionais", nargs="*", help="Fases 1 e 2")
    parser.add_argument("--fases", nargs="+", dest="fases_opcao", help="IDs das fases")
    parser.add_argument("--saida", default=str(ROOT / "imagens-geradas"), help="Diretório dos PNGs")
    return parser.parse_args()


def main() -> int:
    args = argumentos()
    solicitadas = args.fases_opcao or args.fases_posicionais or ["1", "2"]
    ids = []
    for valor in solicitadas:
        fase_id = FASES.get(valor.strip().lower())
        if not fase_id:
            raise SystemExit(f"Fase inválida: {valor}. Informe 1, 2, primeira-fase ou segunda-fase.")
        if fase_id not in ids:
            ids.append(fase_id)

    dados = carregar_dados()
    fases = {fase["id"]: fase for fase in dados.get("fases", [])}
    saida = Path(args.saida).resolve()
    for fase_id in ids:
        fase = fases.get(fase_id)
        if not fase:
            raise SystemExit(f"Fase não encontrada nos dados: {fase_id}")
        destino = saida / f"copa-do-brasil-{fase_id}.png"
        gerar_fase(dados, fase, destino)
        print(f"Gerado: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
