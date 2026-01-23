const grupos = [
  "grupo-a",
  "grupo-b",
  "grupo-c",
  "grupo-d",
  "grupo-e",
  "grupo-f",
  "grupo-g",
  "grupo-h",
];

let grupoAtual = 0;

const tituloGrupo = document.getElementById("titulo-grupo");
const imgClassificacao = document.getElementById("imagem-classificacao");
const imgRodadas = document.getElementById("imagem-rodadas");

function atualizarGrupo() {
  const pasta = grupos[grupoAtual];

  tituloGrupo.innerText = pasta.replace("grupo-", "GRUPO ").toUpperCase();

  imgClassificacao.src = `${pasta}/classificacao.png`;
  imgRodadas.src = `${pasta}/rodadas.png`;
}

function trocarGrupo(direcao) {
  grupoAtual += direcao;

  if (grupoAtual < 0) grupoAtual = grupos.length - 1;
  if (grupoAtual >= grupos.length) grupoAtual = 0;

  atualizarGrupo();
}

atualizarGrupo();

// inicializa na primeira carga
atualizarGrupo();

//swipe inicio
let startX = 0;
let endX = 0;

const areaSwipe = document.querySelector(".conteudo-serie");

areaSwipe.addEventListener("touchstart", (e) => {
  startX = e.touches[0].clientX;
});

areaSwipe.addEventListener("touchend", (e) => {
  endX = e.changedTouches[0].clientX;
  handleSwipe();
});

function handleSwipe() {
  const distancia = endX - startX;

  // sensibilidade do swipe (quanto maior, mais difícil)
  const limite = 50;

  if (distancia > limite) {
    // swipe para direita
    trocarGrupo(-1);
  } else if (distancia < -limite) {
    // swipe para esquerda
    trocarGrupo(1);
  }
}
