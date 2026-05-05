const fases = [
  "primeira-fase",
  "segunda-fase",
  "terceira-fase",
  "oitavas",
  "quartas",
  "semi",
  "final",
];

let faseAtual = 0;

const tituloFase = document.getElementById("titulo-fase");
const imgFase = document.getElementById("imagem-fase");

function atualizarFase() {
  const fase = fases[faseAtual];

  tituloFase.innerText = formatarNome(fase);
  imgFase.src = `${fase}.png`;
}

function trocarFase(direcao) {
  faseAtual += direcao;

  if (faseAtual < 0) faseAtual = fases.length - 1;
  if (faseAtual >= fases.length) faseAtual = 0;

  atualizarFase();
}

function formatarNome(fase) {
  return fase
    .replace("-", " ")
    .toUpperCase()
    .replace("PRIMEIRA FASE", "PRIMEIRA FASE")
    .replace("SEGUNDA FASE", "SEGUNDA FASE")
    .replace("TERCEIRA FASE", "TERCEIRA FASE")
    .replace("OITAVAS", "OITAVAS DE FINAL")
    .replace("QUARTAS", "QUARTAS DE FINAL")
    .replace("SEMI", "SEMI FINAL")
    .replace("FINAL", "FINAL");
}

// init
atualizarFase();

// SWIPE
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
  const limite = 50;

  if (distancia > limite) {
    trocarFase(-1);
  } else if (distancia < -limite) {
    trocarFase(1);
  }
}
