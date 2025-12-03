let rodadaAtual = 1;
let totalRodadas = 19; // altere se sua liga tiver menos

function trocarRodada(direcao) {
  rodadaAtual += direcao;

  if (rodadaAtual < 1) rodadaAtual = totalRodadas;
  if (rodadaAtual > totalRodadas) rodadaAtual = 1;

  document.getElementById("titulo-rodada").innerText = rodadaAtual + "ª RODADA";

  document.getElementById("imagem-rodada").src =
    "rodadas/rodada" + rodadaAtual + ".png";
}
