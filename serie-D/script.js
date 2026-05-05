const telas = [
  // 1ª fase
  { tipo: "grupo", nome: "grupo-a" },
  { tipo: "grupo", nome: "grupo-b" },
  { tipo: "grupo", nome: "grupo-c" },
  { tipo: "grupo", nome: "grupo-d" },

  // 2ª fase (grupos)
  { tipo: "segunda-fase", nome: "grupo-a" },
  { tipo: "segunda-fase", nome: "grupo-b" },
  { tipo: "segunda-fase", nome: "grupo-c" },
  { tipo: "segunda-fase", nome: "grupo-d" },

  // mata-mata
  { tipo: "mata-mata" },
];

const fasesMataMata = ["quartas", "semi", "final"];

let telaAtual = 0;
let faseAtual = 0;

const tituloGrupo = document.getElementById("titulo-grupo");
const imgClassificacao = document.getElementById("imagem-classificacao");
const imgRodadas = document.getElementById("imagem-rodadas");

function atualizarGrupo() {
  const tela = telas[telaAtual];

  // 🟢 1ª FASE
  if (tela.tipo === "grupo") {
    tituloGrupo.innerText =
      "1ª FASE - " + tela.nome.replace("grupo-", "GRUPO ").toUpperCase();

    imgClassificacao.src = `${tela.nome}/classificacao.png`;
    imgRodadas.src = `${tela.nome}/rodadas.png`;
    imgRodadas.style.display = "block";

    faseAtual = 0;
  }

  // 🔵 2ª FASE (grupos)
  else if (tela.tipo === "segunda-fase") {
    tituloGrupo.innerText =
      "2ª FASE - " + tela.nome.replace("grupo-", "GRUPO ").toUpperCase();

    imgClassificacao.src = `segunda-fase/${tela.nome}/classificacao.png`;
    imgRodadas.src = `segunda-fase/${tela.nome}/rodadas.png`;
    imgRodadas.style.display = "block";

    faseAtual = 0;
  }

  // 🔴 MATA-MATA
  else if (tela.tipo === "mata-mata") {
    const fase = fasesMataMata[faseAtual];

    tituloGrupo.innerText = `MATA-MATA - ${fase.toUpperCase()}`;

    imgClassificacao.src = `mata-mata/${fase}.png`;
    imgRodadas.style.display = "none";
  }
}

function trocarGrupo(direcao) {
  const tela = telas[telaAtual];

  // 🔴 controle interno do mata-mata
  if (tela.tipo === "mata-mata") {
    faseAtual += direcao;

    if (faseAtual >= 0 && faseAtual < fasesMataMata.length) {
      atualizarGrupo();
      return;
    }

    if (faseAtual < 0) {
      telaAtual--;
    } else {
      telaAtual++;
    }

    faseAtual = 0;
  } else {
    telaAtual += direcao;
  }

  // loop
  if (telaAtual < 0) telaAtual = telas.length - 1;
  if (telaAtual >= telas.length) telaAtual = 0;

  atualizarGrupo();
}

// init
atualizarGrupo();

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
    trocarGrupo(-1);
  } else if (distancia < -limite) {
    trocarGrupo(1);
  }
}
