const estadoLibertadores = { dados: null };
const formatadorLibertadores = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function formatarPontos(valor) {
  return typeof valor === "number" ? formatadorLibertadores.format(valor) : "—";
}

function criarElemento(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) elemento.className = classe;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

function statusRodada(rodada) {
  if (rodada.concluida) return "concluída";
  const pontuacoes = rodada.partidas.flatMap((partida) => [
    partida.mandante.pontuacao,
    partida.visitante.pontuacao,
  ]);
  if (pontuacoes.some((valor) => typeof valor === "number")) return "parcial";
  return "futura";
}

function classeDestino(destino) {
  if (destino === "oitavas") return "libertadores-oitavas";
  if (destino === "copa-do-brasil") return "libertadores-copa";
  return "libertadores-eliminado";
}

function criarTabelaGrupo(grupo) {
  const container = criarElemento("div", "libertadores-tabela-container");
  container.tabIndex = 0;
  container.setAttribute("aria-label", `Classificação do Grupo ${grupo.grupo}; deslize horizontalmente para ver todas as colunas`);
  const tabela = criarElemento("table", "libertadores-tabela");
  const legenda = criarElemento("caption", "sr-only", `Classificação atual do Grupo ${grupo.grupo}`);
  const cabecalho = document.createElement("thead");
  const linhaCabecalho = document.createElement("tr");
  [
    ["#", "Posição"], ["TIME", "Time"], ["PTS", "Pontos"], ["J", "Jogos"],
    ["V", "Vitórias"], ["E", "Empates"], ["D", "Derrotas"],
    ["PP", "Pontos pró"], ["PC", "Pontos contra"], ["SG", "Saldo"],
  ].forEach(([texto, titulo]) => {
    const th = criarElemento("th", "", texto);
    th.scope = "col";
    th.title = titulo;
    linhaCabecalho.append(th);
  });
  cabecalho.append(linhaCabecalho);

  const corpo = document.createElement("tbody");
  grupo.classificacao.forEach((time) => {
    const linha = document.createElement("tr");
    linha.className = classeDestino(time.destinoAtual);
    linha.title = time.destinoAtual === "oitavas"
      ? "Zona de classificação para as oitavas"
      : time.destinoAtual === "copa-do-brasil"
        ? "Zona de classificação para a Copa do Brasil"
        : "Zona de eliminação";
    const valores = [
      `${time.posicao}º`, time.time, time.pontos, time.jogos, time.vitorias,
      time.empates, time.derrotas, formatarPontos(time.pontosPro),
      formatarPontos(time.pontosContra), formatarPontos(time.saldo),
    ];
    valores.forEach((valor, indice) => {
      const td = criarElemento("td", "", String(valor));
      if (indice === 1) td.className = "libertadores-time";
      linha.append(td);
    });
    corpo.append(linha);
  });
  tabela.append(legenda, cabecalho, corpo);
  container.append(tabela);
  return container;
}

function criarEquipeRodada(equipe) {
  const bloco = criarElemento("div", "libertadores-equipe");
  if (equipe.resultado === "V") bloco.classList.add("vencedor");
  if (equipe.resultado === "E") bloco.classList.add("empate");
  const textos = criarElemento("div", "libertadores-equipe-textos");
  textos.append(
    criarElemento("strong", "", equipe.time || "A definir"),
    criarElemento("span", "", equipe.cartoleiro || "Cartoleiro não informado"),
  );
  bloco.append(textos, criarElemento("b", "libertadores-placar", formatarPontos(equipe.pontuacao)));
  return bloco;
}

function renderizarJogosGrupo(grupo, numeroRodada, painel) {
  const rodada = grupo.rodadas.find((item) => item.numero === Number(numeroRodada));
  const lista = painel.querySelector(".libertadores-jogos-lista");
  lista.replaceChildren();
  if (!rodada?.partidas.length) {
    lista.append(criarElemento("p", "estado-dados", "Confrontos ainda não cadastrados."));
    return;
  }
  rodada.partidas.forEach((partida) => {
    const jogo = criarElemento("article", "libertadores-jogo");
    jogo.append(
      criarEquipeRodada(partida.mandante),
      criarElemento("span", "libertadores-versus", "×"),
      criarEquipeRodada(partida.visitante),
    );
    lista.append(jogo);
  });
}

function criarPainelJogos(grupo, idPainel) {
  const painel = criarElemento("div", "libertadores-jogos");
  painel.id = idPainel;
  painel.hidden = true;
  const seletor = document.createElement("select");
  seletor.className = "seletor-rodada libertadores-seletor";
  seletor.setAttribute("aria-label", `Selecionar rodada do Grupo ${grupo.grupo}`);
  grupo.rodadas.forEach((rodada) => {
    const opcao = document.createElement("option");
    opcao.value = rodada.numero;
    opcao.textContent = `${rodada.numero}ª RODADA — ${statusRodada(rodada)}`;
    seletor.append(opcao);
  });
  const ultimaConcluida = [...grupo.rodadas].reverse().find((rodada) => rodada.concluida);
  seletor.value = String(ultimaConcluida?.numero || 1);
  const lista = criarElemento("div", "libertadores-jogos-lista");
  painel.append(seletor, lista);
  seletor.addEventListener("change", () => renderizarJogosGrupo(grupo, seletor.value, painel));
  renderizarJogosGrupo(grupo, seletor.value, painel);
  return painel;
}

function criarCardGrupo(grupo) {
  const card = criarElemento("article", "libertadores-grupo");
  const cabecalho = criarElemento("header", "libertadores-grupo-cabecalho");
  const titulo = criarElemento("h3", "", `GRUPO ${grupo.grupo}`);
  cabecalho.append(titulo);
  const idPainel = `jogos-grupo-${grupo.grupo.toLowerCase()}`;
  const botao = criarElemento("button", "libertadores-botao-jogos", "VER JOGOS");
  botao.type = "button";
  botao.setAttribute("aria-expanded", "false");
  botao.setAttribute("aria-controls", idPainel);
  const painel = criarPainelJogos(grupo, idPainel);
  botao.addEventListener("click", () => {
    const abrir = painel.hidden;
    painel.hidden = !abrir;
    botao.setAttribute("aria-expanded", String(abrir));
    botao.textContent = abrir ? "OCULTAR JOGOS" : "VER JOGOS";
  });
  card.append(cabecalho, criarTabelaGrupo(grupo), botao, painel);
  return card;
}

function renderizarGrupos(grupos) {
  const grade = document.getElementById("grade-grupos");
  grade.replaceChildren(...grupos.map(criarCardGrupo));
}

function definirEstadoSecao(botao, conteudo, abrir, nome) {
  conteudo.hidden = !abrir;
  botao.setAttribute("aria-expanded", String(abrir));
  botao.firstChild.textContent = `${abrir ? "RECOLHER" : "EXPANDIR"} ${nome} `;
  botao.querySelector("span").textContent = abrir ? "−" : "+";
}

function configurarAlternanciaGrupos() {
  const botao = document.getElementById("alternar-grupos");
  const grade = document.getElementById("grade-grupos");
  if (!botao || !grade) return;
  botao.addEventListener("click", () => {
    definirEstadoSecao(botao, grade, grade.hidden, "GRUPOS");
  });
}

function configurarAlternanciaMataMata() {
  const botao = document.getElementById("alternar-mata-mata");
  const fases = document.getElementById("fases-mata-mata");
  if (!botao || !fases) return;
  botao.addEventListener("click", () => {
    definirEstadoSecao(botao, fases, fases.hidden, "MATA-MATA");
  });
}

function aplicarEstadoInicial(dados) {
  const mataMataIniciado = dados.mataMata.some((fase) => fase.partidas.length > 0);
  definirEstadoSecao(
    document.getElementById("alternar-grupos"),
    document.getElementById("grade-grupos"),
    !mataMataIniciado,
    "GRUPOS",
  );
  definirEstadoSecao(
    document.getElementById("alternar-mata-mata"),
    document.getElementById("fases-mata-mata"),
    mataMataIniciado,
    "MATA-MATA",
  );
}

function criarConfrontoMataMata(partida) {
  const confronto = criarElemento("article", "libertadores-confronto");
  const linha = (time, ida, volta, agregado, vencedor) => {
    const item = criarElemento("div", vencedor ? "classificado" : "");
    item.append(
      criarElemento("strong", "", time || "A definir"),
      criarElemento("span", "", formatarPontos(ida)),
      criarElemento("span", "", formatarPontos(volta)),
      criarElemento("b", "", formatarPontos(agregado)),
    );
    return item;
  };
  confronto.append(
    linha(partida.time1, partida.ida.time1, partida.volta.time1, partida.agregado.time1, partida.vencedor === partida.time1),
    linha(partida.time2, partida.ida.time2, partida.volta.time2, partida.agregado.time2, partida.vencedor === partida.time2),
  );
  return confronto;
}

function renderizarMataMata(fases) {
  const container = document.getElementById("fases-mata-mata");
  container.replaceChildren();
  fases.forEach((fase) => {
    const card = criarElemento("article", "libertadores-fase");
    const cabecalho = criarElemento("header", "");
    cabecalho.append(
      criarElemento("h3", "", fase.nome.toUpperCase()),
      criarElemento("span", "", fase.rodadasCartola.length ? `Rodadas ${fase.rodadasCartola.join("–")}` : "A definir"),
    );
    card.append(cabecalho);
    if (!fase.partidas.length) {
      card.append(criarElemento("p", "libertadores-aguardando", "Aguardando definição dos confrontos"));
    } else {
      const rotulos = criarElemento("div", "libertadores-confronto-rotulos");
      rotulos.innerHTML = "<span>TIME</span><span>IDA</span><span>VOLTA</span><span>AGREGADO</span>";
      card.append(rotulos, ...fase.partidas.map(criarConfrontoMataMata));
    }
    container.append(card);
  });
}

async function carregarLibertadores() {
  const status = document.getElementById("status-dados");
  const erro = document.getElementById("erro-libertadores");
  try {
    const resposta = await fetch(document.body.dataset.dadosUrl || "../dados/libertadores.json");
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
    const dados = await resposta.json();
    estadoLibertadores.dados = dados;
    renderizarGrupos(dados.grupos);
    renderizarMataMata(dados.mataMata);
    aplicarEstadoInicial(dados);
    const atualizado = new Date(dados.atualizadoEm);
    status.textContent = `Dados da planilha · atualizados em ${atualizado.toLocaleString("pt-BR")}`;
  } catch (error) {
    status.textContent = "Não foi possível carregar os dados da Libertadores.";
    erro.hidden = false;
    erro.textContent = "Confira se dados/libertadores.json foi gerado e acesse o site por um servidor local.";
    console.error("Erro ao carregar a Libertadores:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  configurarAlternanciaGrupos();
  configurarAlternanciaMataMata();
  carregarLibertadores();
});
