let rodadaAtual = 1;
let totalRodadas = 19;
let navegando = false; // ✅ bloqueio de multi-clique

function trocarRodada(direcao) {
  rodadaAtual += direcao;

  if (rodadaAtual < 1) rodadaAtual = totalRodadas;
  if (rodadaAtual > totalRodadas) rodadaAtual = 1;

  document.getElementById("titulo-rodada").innerText = rodadaAtual + "ª RODADA";

  document.getElementById("imagem-rodada").src =
    "rodadas/rodada" + rodadaAtual + ".png";
}

window.addEventListener("DOMContentLoaded", () => {
  const splash = document.getElementById("splash");
  const splashImg = document.getElementById("splashImg");
  const site = document.getElementById("site");
  const links = document.querySelectorAll(".menu a[data-splash]");

  const nextSplash = sessionStorage.getItem("nextSplash");

  /* ============================= */
  /* ===== PRELOAD INTELIGENTE ===== */
  /* ============================= */

  function preloadImagem(src) {
    if (!src) return;
    const img = new Image();
    img.src = src;
  }

  /* ============================= */
  /* ===== SPLASH AO ENTRAR ===== */
  /* ============================= */

  if (splash && site) {
    // 🔥 veio de outra página
    if (nextSplash && splashImg) {
      splashImg.src = nextSplash;
      sessionStorage.removeItem("nextSplash");

      splash.style.display = "flex";
      splash.classList.remove("hide");

      // 🎬 ativa zoom cinematográfico
      requestAnimationFrame(() => {
        splash.classList.add("show");
      });

      setTimeout(() => {
        splash.classList.add("hide");

        setTimeout(() => {
          splash.style.display = "none";
          site.classList.add("show");
        }, 700);
      }, 1000);
    }
    // 🔹 splash inicial (home)
    else {
      setTimeout(() => {
        splash.classList.add("hide");

        setTimeout(() => {
          splash.style.display = "none";
          site.classList.add("show");
        }, 700);
      }, 1800);
    }
  }

  /* ============================= */
  /* ===== CLIQUE NO MENU ===== */
  /* ============================= */

  links.forEach((link) => {
    const img = link.dataset.splash;
    preloadImagem(img); // ✅ preload ao iniciar

    link.addEventListener("click", (e) => {
      if (navegando) return; // 🚫 bloqueia multi-clique
      navegando = true;

      e.preventDefault();

      const url = link.href;
      const splashToUse = img || "/img/Capa.png";

      sessionStorage.setItem("nextSplash", splashToUse);

      if (splash && splashImg) {
        splashImg.src = splashToUse;
        splash.style.display = "flex";
        splash.classList.remove("hide");

        requestAnimationFrame(() => {
          splash.classList.add("show");
        });
      }

      setTimeout(() => {
        window.location.href = url;
      }, 750);
    });
  });
});
