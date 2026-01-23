const grupos = [
  "Grupo A",
  "Grupo B",
  "Grupo C",
  "Grupo D",
  "Grupo E",
  "Grupo F",
  "Grupo G",
  "Grupo H",
];

let grupoAtual = 0;

const tituloGrupo = document.getElementById("titulo-grupo");
const imgClassificacao = document.getElementById("imagem-classificacao");
const imgRodadas = document.getElementById("imagem-rodadas");

function atualizarGrupo() {
  const grupo = grupos[grupoAtual];

  tituloGrupo.innerText = grupo.toUpperCase();
  imgClassificacao.src = `${grupo}/classificacao.png`;
  imgRodadas.src = `${grupo}/rodadas.png`;
}

function trocarGrupo(direcao) {
  grupoAtual += direcao;

  if (grupoAtual < 0) grupoAtual = grupos.length - 1;
  if (grupoAtual >= grupos.length) grupoAtual = 0;

  atualizarGrupo();
}

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
