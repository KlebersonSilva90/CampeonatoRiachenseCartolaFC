const estadoDestaques = { campeonatos: [], rodadaAtual: 1 };
const formatadorDestaques = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function formatarPontos(valor) {
  return typeof valor === "number" ? formatadorDestaques.format(valor) : "—";
}

function definirTexto(id, texto) {
  const elemento = document.getElementById(id);
  if (elemento) elemento.textContent = texto;
}

function participantesDaRodada(campeonato, numeroRodada) {
  const rodada = campeonato.rodadas.find((item) => item.numero === numeroRodada);
  if (!rodada) return [];
  return rodada.partidas.flatMap((partida) => [
    { ...partida.mandante, adversario: partida.visitante, serie: campeonato.serie },
    { ...partida.visitante, adversario: partida.mandante, serie: campeonato.serie },
  ]);
}

function partidasDaRodada(campeonato, numeroRodada) {
  const rodada = campeonato.rodadas.find((item) => item.numero === numeroRodada);
  return (rodada?.partidas || []).map((partida) => ({ ...partida, serie: campeonato.serie }));
}

function statusRodadaGeral(numeroRodada) {
  let preenchidas = 0;
  let total = 0;
  estadoDestaques.campeonatos.forEach((campeonato) => {
    participantesDaRodada(campeonato, numeroRodada).forEach((participante) => {
      total += 1;
      if (typeof participante.pontuacao === "number") preenchidas += 1;
    });
  });
  if (preenchidas === 0) return "futura";
  if (preenchidas === total && total > 0) return "concluída";
  return "parcial";
}

function melhorParticipante(participantes) {
  return participantes
    .filter((item) => typeof item.pontuacao === "number")
    .sort((a, b) => b.pontuacao - a.pontuacao)[0] || null;
}

function renderizarMelhorGeral(melhor) {
  definirTexto("titulo-melhor-geral", melhor?.time || "Sem resultados");
  definirTexto("cartoleiro-melhor-geral", melhor?.cartoleiro || "—");
  definirTexto("pontuacao-melhor-geral", formatarPontos(melhor?.pontuacao));
  definirTexto("serie-melhor-geral", melhor ? `SÉRIE ${melhor.serie}` : "—");
}

function renderizarMelhoresPorSerie(numeroRodada) {
  const grade = document.getElementById("melhores-por-serie");
  if (!grade) return;
  grade.replaceChildren();
  estadoDestaques.campeonatos.forEach((campeonato) => {
    const melhor = melhorParticipante(participantesDaRodada(campeonato, numeroRodada));
    const artigo = document.createElement("article");
    artigo.className = "cartao-serie";
    const serie = document.createElement("span");
    serie.className = "selo-serie";
    serie.textContent = `SÉRIE ${campeonato.serie}`;
    const time = document.createElement("strong");
    time.textContent = melhor?.time || "Sem resultado";
    const cartoleiro = document.createElement("small");
    cartoleiro.textContent = melhor?.cartoleiro || "—";
    const pontos = document.createElement("b");
    pontos.textContent = formatarPontos(melhor?.pontuacao);
    artigo.append(serie, time, cartoleiro, pontos);
    grade.append(artigo);
  });
}

function descricaoPartida(partida) {
  return `${partida.mandante.time} ${formatarPontos(partida.mandante.pontuacao)} × ${formatarPontos(partida.visitante.pontuacao)} ${partida.visitante.time} · Série ${partida.serie}`;
}

function renderizarRodada(numeroRodada) {
  estadoDestaques.rodadaAtual = numeroRodada;
  const seletor = document.getElementById("seletor-rodada-home");
  if (seletor) seletor.value = String(numeroRodada);

  const participantes = estadoDestaques.campeonatos.flatMap((campeonato) =>
    participantesDaRodada(campeonato, numeroRodada));
  const partidas = estadoDestaques.campeonatos.flatMap((campeonato) =>
    partidasDaRodada(campeonato, numeroRodada)).filter((partida) =>
      typeof partida.mandante.pontuacao === "number" && typeof partida.visitante.pontuacao === "number");

  renderizarMelhorGeral(melhorParticipante(participantes));
  renderizarMelhoresPorSerie(numeroRodada);

  const vitorias = partidas.filter((partida) => partida.mandante.resultado === "V" || partida.visitante.resultado === "V");
  const empates = partidas.filter((partida) => partida.mandante.resultado === "E");
  const naoEscalados = participantes.filter((participante) => participante.naoEscalou);
  definirTexto("total-partidas", partidas.length);
  definirTexto("total-vitorias", vitorias.length);
  definirTexto("total-empates", empates.length);
  definirTexto("total-nao-escalou", naoEscalados.length);

  const maiorVitoria = [...vitorias].sort((a, b) =>
    Math.abs(b.mandante.pontuacao - b.visitante.pontuacao) - Math.abs(a.mandante.pontuacao - a.visitante.pontuacao))[0];
  const maisEquilibrado = [...partidas].sort((a, b) =>
    Math.abs(a.mandante.pontuacao - a.visitante.pontuacao) - Math.abs(b.mandante.pontuacao - b.visitante.pontuacao))[0];

  const vencedorMaior = maiorVitoria
    ? (maiorVitoria.mandante.resultado === "V" ? maiorVitoria.mandante : maiorVitoria.visitante)
    : null;
  definirTexto("maior-vitoria", vencedorMaior?.time || "—");
  definirTexto("detalhe-maior-vitoria", maiorVitoria ? descricaoPartida(maiorVitoria) : "Sem vitória registrada");
  definirTexto("mais-equilibrado", maisEquilibrado ? `${Math.abs(maisEquilibrado.mandante.pontuacao - maisEquilibrado.visitante.pontuacao).toFixed(2).replace(".", ",")} ponto(s)` : "—");
  definirTexto("detalhe-mais-equilibrado", maisEquilibrado ? descricaoPartida(maisEquilibrado) : "Sem resultado registrado");

  const painelNaoEscalados = document.getElementById("painel-nao-escalados");
  const listaNaoEscalados = document.getElementById("lista-nao-escalados");
  if (painelNaoEscalados && listaNaoEscalados) {
    listaNaoEscalados.replaceChildren();
    painelNaoEscalados.hidden = naoEscalados.length === 0;
    naoEscalados.forEach((participante) => {
      const item = document.createElement("li");
      item.textContent = `${participante.time} (${participante.cartoleiro}) · Série ${participante.serie}`;
      listaNaoEscalados.append(item);
    });
  }

  const status = document.getElementById("status-destaques");
  if (status) status.textContent = `${numeroRodada}ª rodada · ${statusRodadaGeral(numeroRodada)}`;
}

function criarSeletor() {
  const seletor = document.getElementById("seletor-rodada-home");
  if (!seletor) return;
  seletor.replaceChildren();
  for (let numero = 1; numero <= 19; numero += 1) {
    const opcao = document.createElement("option");
    opcao.value = numero;
    opcao.textContent = `${numero}ª RODADA — ${statusRodadaGeral(numero)}`;
    seletor.append(opcao);
  }
  seletor.addEventListener("change", () => renderizarRodada(Number(seletor.value)));
}

function normalizarChaveAlerta(texto) {
  return String(texto || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .trim()
    .replace(/\s+/g, " ");
}

function chaveAlertaReincidencia(serie, time) {
  return `${String(serie || "").toUpperCase()}|${normalizarChaveAlerta(time)}`;
}

function reincidentesSemEscalar(campeonatos, contatosReconhecidos = {}, limite = 5) {
  const registros = new Map();
  campeonatos.forEach((campeonato) => {
    campeonato.rodadas.forEach((rodada) => {
      rodada.partidas.forEach((partida) => {
        [partida.mandante, partida.visitante].forEach((equipe) => {
          if (!(equipe.naoEscalou === true || equipe.pontuacao === 0)) return;
          const chave = chaveAlertaReincidencia(campeonato.serie, equipe.time);
          const registro = registros.get(chave) || {
            serie: campeonato.serie,
            time: equipe.time,
            cartoleiro: equipe.cartoleiro || "Cartoleiro não informado",
            quantidade: 0,
          };
          registro.quantidade += 1;
          registros.set(chave, registro);
        });
      });
    });
  });
  return [...registros.values()]
    .map((registro) => {
      const chave = chaveAlertaReincidencia(registro.serie, registro.time);
      const reconhecidas = Math.max(0, Number(contatosReconhecidos[chave]?.ocorrenciasReconhecidas) || 0);
      return {
        ...registro,
        reconhecidas,
        novasOcorrencias: Math.max(0, registro.quantidade - reconhecidas),
      };
    })
    .filter((registro) => registro.novasOcorrencias >= limite)
    .sort((a, b) => b.novasOcorrencias - a.novasOcorrencias || a.time.localeCompare(b.time, "pt-BR"));
}

async function carregarContatosReconhecidos() {
  try {
    const resposta = await fetch(`dados/alertas-nao-escalados.json?t=${Date.now()}`, { cache: "no-store" });
    if (!resposta.ok) return {};
    const dados = await resposta.json();
    return dados.contatos || {};
  } catch (erro) {
    console.warn("Não foi possível carregar os contatos já registrados:", erro);
    return {};
  }
}

async function configurarAlertaReincidencia() {
  const dialogo = document.getElementById("alerta-reincidencia-nao-escalados");
  const mensagens = document.getElementById("mensagens-alerta-reincidencia");
  const fechar = document.getElementById("fechar-alerta-reincidencia");
  const confirmar = document.getElementById("confirmar-alerta-reincidencia");
  if (!dialogo || !mensagens) return;

  const contatosReconhecidos = await carregarContatosReconhecidos();
  const reincidentes = reincidentesSemEscalar(estadoDestaques.campeonatos, contatosReconhecidos);
  if (reincidentes.length === 0) return;
  mensagens.replaceChildren(...reincidentes.map((registro) => {
    const mensagem = document.createElement("p");
    mensagem.textContent = `${registro.cartoleiro.toUpperCase()}, ENTRE EM CONTATO POIS SEU TIME ${registro.time.toUpperCase()} FICOU 5 VEZES OU MAIS SEM ESCALAR.`;
    const detalhe = document.createElement("small");
    detalhe.textContent = `Série ${registro.serie} · ${registro.novasOcorrencias} nova(s) ocorrência(s) · ${registro.quantidade} no total`;
    const item = document.createElement("article");
    item.append(mensagem, detalhe);
    return item;
  }));

  const fecharDialogo = () => dialogo.close();
  fechar?.addEventListener("click", fecharDialogo);
  confirmar?.addEventListener("click", fecharDialogo);
  dialogo.addEventListener("click", (evento) => {
    if (evento.target === dialogo) fecharDialogo();
  });
  if (typeof dialogo.showModal === "function") dialogo.showModal();
  else dialogo.setAttribute("open", "");
}

async function carregarDestaques() {
  const urls = ["a", "b", "c", "d", "e"].map((serie) => `dados/serie-${serie}.json`);
  try {
    const respostas = await Promise.all(urls.map((url) => fetch(url)));
    const falha = respostas.find((resposta) => !resposta.ok);
    if (falha) throw new Error(`HTTP ${falha.status}`);
    estadoDestaques.campeonatos = await Promise.all(respostas.map((resposta) => resposta.json()));
    criarSeletor();
    let ultimaConcluida = 1;
    for (let numero = 1; numero <= 19; numero += 1) {
      if (statusRodadaGeral(numero) === "concluída") ultimaConcluida = numero;
    }
    renderizarRodada(ultimaConcluida);
    await configurarAlertaReincidencia();
  } catch (erro) {
    definirTexto("status-destaques", "Não foi possível carregar os dados dos campeonatos.");
    console.error("Erro ao carregar os melhores da rodada:", erro);
  }
}

document.addEventListener("DOMContentLoaded", carregarDestaques);
