const grupos = [
  "grupo-a",
  "grupo-b",
  "grupo-c",
  "grupo-d",
  "grupo-e",
  "grupo-f",
  "grupo-g",
  "grupo-h",
  "mata-mata",
];

const fasesMataMata = ["oitavas", "quartas", "semi", "final"];

let grupoAtual = 0;
let faseAtual = 0;

const tituloGrupo = document.getElementById("titulo-grupo");
const imgClassificacao = document.getElementById("imagem-classificacao");
const imgRodadas = document.getElementById("imagem-rodadas");

function atualizarGrupo() {
  const pasta = grupos[grupoAtual];

  if (pasta === "mata-mata") {
    const fase = fasesMataMata[faseAtual];

    tituloGrupo.innerText = `MATA-MATA - ${fase.toUpperCase()}`;

    imgClassificacao.src = `mata-mata/${fase}.png`;
    imgRodadas.style.display = "none"; // esconde segunda imagem
  } else {
    tituloGrupo.innerText = pasta.replace("grupo-", "GRUPO ").toUpperCase();

    imgClassificacao.src = `${pasta}/classificacao.png`;
    imgRodadas.src = `${pasta}/rodadas.png`;
    imgRodadas.style.display = "block";

    // sempre que sair do mata-mata, resetar fase
    faseAtual = 0;
  }
}

function trocarGrupo(direcao) {
  const atual = grupos[grupoAtual];

  if (atual === "mata-mata") {
    faseAtual += direcao;

    // continua navegando dentro do mata-mata
    if (faseAtual >= 0 && faseAtual < fasesMataMata.length) {
      atualizarGrupo();
      return;
    }

    // saiu das fases → vai para próximo grupo
    if (faseAtual < 0) {
      grupoAtual--;
    } else {
      grupoAtual++;
    }

    faseAtual = 0;
  } else {
    grupoAtual += direcao;
  }

  // controle circular
  if (grupoAtual < 0) grupoAtual = grupos.length - 1;
  if (grupoAtual >= grupos.length) grupoAtual = 0;

  atualizarGrupo();
}

// inicialização
atualizarGrupo();

// swipe
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
    trocarGrupo(-1);
  } else if (distancia < -limite) {
    trocarGrupo(1);
  }
}
