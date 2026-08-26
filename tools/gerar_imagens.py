"""Gera cards PNG da classificação e da última rodada concluída.

Exemplos:
    python tools/gerar_imagens.py E
    python tools/gerar_imagens.py --serie A --saida imagens-geradas
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as error:  # pragma: no cover - depende do ambiente do usuário
    raise SystemExit("Pillow não está instalado. Execute: python -m pip install Pillow") from error


ROOT = Path(__file__).resolve().parents[1]
LARGURA = 1080
ALTURA = 1350
MARGEM = 54

CORES = {
    "cartao": "#FFF9EB",
    "texto": "#2B1A08",
    "texto_suave": "#765A36",
    "linha": "#E4D2AD",
    "lider": "#FFD447",
    "acesso": "#CFE8FF",
    "rebaixamento": "#FFD5D5",
    "vencedor": "#B21E24",
    "empate": "#1769AA",
    "neutro": "#554B40",
    "branco": "#FFFFFF",
}

CORES_DEGRADE = (
    (239, 104, 24),   # laranja
    (255, 202, 40),   # amarelo
    (255, 250, 238),  # branco quente
)


def fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    nomes = [
        "C:/Windows/Fonts/arialbd.ttf" if negrito else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if negrito else "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrito else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for nome in nomes:
        if Path(nome).exists():
            return ImageFont.truetype(nome, tamanho)
    return ImageFont.load_default(size=tamanho)


FONTES = {
    "marca": fonte(26, True),
    "titulo": fonte(48, True),
    "subtitulo": fonte(23),
    "cabecalho": fonte(18, True),
    "cabecalho_compacto": fonte(13, True),
    "linha": fonte(19),
    "linha_bold": fonte(19, True),
    "linha_compacta": fonte(17),
    "linha_compacta_bold": fonte(17, True),
    "time": fonte(24, True),
    "cartoleiro": fonte(17),
    "placar": fonte(28, True),
    "rodape": fonte(16),
}


def texto_centralizado(draw: ImageDraw.ImageDraw, xy: tuple[int, int], texto: str, font, fill: str) -> None:
    draw.text(xy, texto, font=font, fill=fill, anchor="mm")


def fundo_degrade() -> Image.Image:
    """Cria um degradê diagonal laranja → amarelo → branco."""
    imagem = Image.new("RGB", (LARGURA, ALTURA))
    pixels = imagem.load()
    laranja, amarelo, branco = CORES_DEGRADE
    for y in range(ALTURA):
        vertical = y / (ALTURA - 1)
        for x in range(LARGURA):
            diagonal = (x / (LARGURA - 1) + vertical) / 2
            if diagonal < 1 / 2:
                inicio, fim, fator = laranja, amarelo, diagonal * 2
            else:
                inicio, fim, fator = amarelo, branco, (diagonal - 1 / 2) * 2
            pixels[x, y] = tuple(round(a + (b - a) * fator) for a, b in zip(inicio, fim))
    return imagem


def texto_limitado(draw: ImageDraw.ImageDraw, texto: str, largura: int, font) -> str:
    if draw.textlength(texto, font=font) <= largura:
        return texto
    reduzido = texto
    while reduzido and draw.textlength(reduzido + "…", font=font) > largura:
        reduzido = reduzido[:-1]
    return reduzido.rstrip() + "…"


def pontos(valor) -> str:
    if not isinstance(valor, (int, float)):
        return "—"
    return f"{valor:.2f}".replace(".", ",")


def carregar_dados(serie: str) -> dict:
    arquivo = ROOT / "dados" / f"serie-{serie.lower()}.json"
    if not arquivo.exists():
        raise SystemExit(f"Dados não encontrados: {arquivo}")
    return json.loads(arquivo.read_text(encoding="utf-8"))


def ultima_rodada_concluida(dados: dict) -> dict:
    concluidas = []
    for rodada in dados["rodadas"]:
        partidas = rodada.get("partidas", [])
        if partidas and all(
            isinstance(partida["mandante"].get("pontuacao"), (int, float))
            and isinstance(partida["visitante"].get("pontuacao"), (int, float))
            for partida in partidas
        ):
            concluidas.append(rodada)
    if not concluidas:
        raise SystemExit("Nenhuma rodada concluída foi encontrada.")
    return concluidas[-1]


def nova_imagem(titulo: str, subtitulo: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    imagem = fundo_degrade()
    draw = ImageDraw.Draw(imagem)
    draw.rectangle((0, 0, LARGURA, 118), fill="#D96B00")
    texto_centralizado(draw, (LARGURA // 2, 42), "CAMPEONATO RIACHENSE CARTOLA FC", FONTES["marca"], CORES["branco"])
    texto_centralizado(draw, (LARGURA // 2, 178), titulo, FONTES["titulo"], CORES["texto"])
    texto_centralizado(draw, (LARGURA // 2, 222), subtitulo, FONTES["subtitulo"], CORES["texto"])
    return imagem, draw


def rodape(draw: ImageDraw.ImageDraw, atualizado_em: str) -> None:
    try:
        data = datetime.fromisoformat(atualizado_em).strftime("%d/%m/%Y às %H:%M")
    except (TypeError, ValueError):
        data = str(atualizado_em or "data não informada")
    texto_centralizado(draw, (LARGURA // 2, ALTURA - 27), f"Dados atualizados em {data}", FONTES["rodape"], CORES["texto_suave"])


def gerar_classificacao(dados: dict, destino: Path) -> None:
    serie = dados["serie"]
    imagem, draw = nova_imagem(f"CLASSIFICAÇÃO • SÉRIE {serie}", "Tabela atual após a última rodada concluída")
    x1, y1, x2, y2 = MARGEM, 270, LARGURA - MARGEM, ALTURA - 62
    draw.rounded_rectangle((x1, y1, x2, y2), radius=24, fill=CORES["cartao"], outline="#8B5A13", width=3)

    colunas = [
        ("POS", 58), ("TIME", 268), ("PONTOS", 66), ("JOGOS", 58),
        ("V", 44), ("E", 44), ("D", 44), ("PP", 88), ("PC", 88),
        ("SALDO", 88), ("MÉDIA", 82),
    ]
    altura_cabecalho = 48
    altura_linha = 48
    x = x1 + 18
    for titulo, largura in colunas:
        ancora = "lm" if titulo == "TIME" else "mm"
        px = x + (8 if titulo == "TIME" else largura // 2)
        draw.text((px, y1 + altura_cabecalho // 2), titulo, font=FONTES["cabecalho_compacto"], fill=CORES["texto_suave"], anchor=ancora)
        x += largura
    draw.line((x1 + 16, y1 + altura_cabecalho, x2 - 16, y1 + altura_cabecalho), fill=CORES["linha"], width=2)

    classificacao = dados["classificacao"]
    primeira_rebaixada = len(classificacao) - 3
    for indice, time in enumerate(classificacao):
        topo = y1 + altura_cabecalho + indice * altura_linha
        centro = topo + altura_linha // 2
        posicao = time["posicao"]
        if posicao == 1:
            cor_linha = CORES["lider"]
        elif serie != "A" and posicao <= 4:
            cor_linha = CORES["acesso"]
        elif posicao >= primeira_rebaixada:
            cor_linha = CORES["rebaixamento"]
        else:
            cor_linha = CORES["cartao"]
        draw.rectangle((x1 + 3, topo, x2 - 3, topo + altura_linha), fill=cor_linha)
        if indice < len(classificacao) - 1:
            draw.line((x1 + 16, topo + altura_linha, x2 - 16, topo + altura_linha), fill=CORES["linha"], width=1)

        valores = [
            f"{posicao}º", time["time"], str(time["pontos"]), str(time["jogos"]),
            str(time["vitorias"]), str(time["empates"]), str(time["derrotas"]),
            pontos(time["pontosMarcados"]), pontos(time["pontosSofridos"]),
            pontos(time["saldo"]), pontos(time["media"]),
        ]
        x = x1 + 18
        for coluna, ((titulo, largura), valor) in enumerate(zip(colunas, valores)):
            if titulo == "TIME":
                valor = texto_limitado(draw, valor, largura - 18, FONTES["linha_compacta_bold"])
                draw.text((x + 8, centro), valor, font=FONTES["linha_compacta_bold"], fill=CORES["texto"], anchor="lm")
            else:
                draw.text((x + largura // 2, centro), valor, font=FONTES["linha_compacta_bold"] if coluna < 3 else FONTES["linha_compacta"], fill=CORES["texto"], anchor="mm")
            x += largura

    rodape(draw, dados.get("atualizadoEm"))
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(destino, "PNG", optimize=True)


def cor_resultado(equipe: dict) -> str:
    if equipe.get("resultado") == "V":
        return CORES["vencedor"]
    if equipe.get("resultado") == "E":
        return CORES["empate"]
    return CORES["neutro"]


def gerar_rodada(dados: dict, rodada: dict, destino: Path) -> None:
    imagem, draw = nova_imagem(f"RESULTADOS • SÉRIE {dados['serie']}", f"{rodada['numero']}ª rodada do campeonato")
    inicio_y = 272
    altura_card = 91
    espaco = 11
    x1, x2 = MARGEM, LARGURA - MARGEM
    meio = LARGURA // 2

    for indice, partida in enumerate(rodada["partidas"]):
        y1 = inicio_y + indice * (altura_card + espaco)
        y2 = y1 + altura_card
        draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=CORES["cartao"], outline="#9A681E", width=2)
        mandante = partida["mandante"]
        visitante = partida["visitante"]
        cor_mandante = cor_resultado(mandante)
        cor_visitante = cor_resultado(visitante)

        nome_mandante = texto_limitado(draw, mandante["time"], 330, FONTES["time"])
        nome_visitante = texto_limitado(draw, visitante["time"], 330, FONTES["time"])
        draw.text((x1 + 22, y1 + 29), nome_mandante, font=FONTES["time"], fill=cor_mandante, anchor="lm")
        draw.text((x2 - 22, y1 + 29), nome_visitante, font=FONTES["time"], fill=cor_visitante, anchor="rm")
        draw.text((x1 + 22, y1 + 64), mandante.get("cartoleiro") or "", font=FONTES["cartoleiro"], fill=CORES["texto_suave"], anchor="lm")
        draw.text((x2 - 22, y1 + 64), visitante.get("cartoleiro") or "", font=FONTES["cartoleiro"], fill=CORES["texto_suave"], anchor="rm")

        placar = f"{pontos(mandante['pontuacao'])}  ×  {pontos(visitante['pontuacao'])}"
        draw.text((meio, y1 + 45), placar, font=FONTES["placar"], fill=CORES["texto"], anchor="mm")

    draw.rounded_rectangle((MARGEM, 1294, LARGURA - MARGEM, 1323), radius=12, fill="#F3E2BD")
    texto_centralizado(draw, (LARGURA // 2, 1308), "Vencedor em vermelho • Empate em azul", FONTES["rodape"], CORES["texto_suave"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(destino, "PNG", optimize=True)


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera PNGs da classificação e da última rodada.")
    parser.add_argument("serie_posicional", nargs="?", help="Série A, B, C, D ou E")
    parser.add_argument("--serie", dest="serie_opcao", help="Série A, B, C, D ou E")
    parser.add_argument("--saida", default=str(ROOT / "imagens-geradas"), help="Diretório dos PNGs")
    return parser.parse_args()


def main() -> int:
    args = argumentos()
    serie = (args.serie_opcao or args.serie_posicional or "E").strip().upper().replace("SÉRIE", "").replace("SERIE", "").strip()
    if serie not in {"A", "B", "C", "D", "E"}:
        raise SystemExit("Informe uma série válida: A, B, C, D ou E.")

    dados = carregar_dados(serie)
    rodada = ultima_rodada_concluida(dados)
    saida = Path(args.saida).resolve()
    classificacao = saida / f"serie-{serie.lower()}-classificacao.png"
    resultados = saida / f"serie-{serie.lower()}-rodada-{rodada['numero']}.png"
    gerar_classificacao(dados, classificacao)
    gerar_rodada(dados, rodada, resultados)
    print(f"Gerado: {classificacao}")
    print(f"Gerado: {resultados}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
