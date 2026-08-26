const formatadorCopa = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function criarElemento(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) elemento.className = classe;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

function formatarPontos(valor) {
  return typeof valor === "number" ? formatadorCopa.format(valor) : "—";
}

function definirEstadoFase(botao, conteudo, abrir) {
  conteudo.hidden = !abrir;
  botao.setAttribute("aria-expanded", String(abrir));
  botao.firstChild.textContent = `${abrir ? "RECOLHER" : "EXPANDIR"} FASE `;
  botao.querySelector("span").textContent = abrir ? "−" : "+";
}

function criarLinhaConfronto(partida, lado) {
  const time = partida[lado] || "A definir";
  const agregado = partida.agregado?.[lado];
  const linha = criarElemento("div", "");
  if (partida.vencedor && partida.vencedor === partida[lado]) linha.classList.add("classificado");
  if (partida.status === "em-andamento" && typeof agregado === "number") {
    const outro = lado === "time1" ? "time2" : "time1";
    if (agregado > (partida.agregado?.[outro] ?? Number.POSITIVE_INFINITY)) {
      linha.classList.add("copa-lider-parcial");
    }
  }
  linha.append(
    criarElemento("strong", "", time),
    criarElemento("span", "", formatarPontos(partida.ida?.[lado])),
    criarElemento("span", "", formatarPontos(partida.volta?.[lado])),
    criarElemento("b", "", formatarPontos(agregado)),
  );
  return linha;
}

function criarConfronto(partida) {
  const confronto = criarElemento("article", "libertadores-confronto copa-confronto");
  const rotulos = criarElemento("div", "libertadores-confronto-rotulos");
  rotulos.innerHTML = "<span>TIME</span><span>IDA</span><span>VOLTA</span><span>AGREGADO</span>";
  confronto.append(rotulos, criarLinhaConfronto(partida, "time1"), criarLinhaConfronto(partida, "time2"));
  return confronto;
}

function criarFase(fase, rodadaAtual, indice) {
  const card = criarElemento("article", "libertadores-fase copa-fase");
  const cabecalho = criarElemento("header", "");
  const informacoes = criarElemento("div", "copa-fase-titulos");
  informacoes.append(
    criarElemento("h3", "", fase.nome.toUpperCase()),
    criarElemento("span", "", `Rodadas ${fase.rodadasCartola.join("–")}`),
  );
  const faseAtual = fase.rodadasCartola.includes(rodadaAtual);
  const idConteudo = `conteudo-fase-${indice}`;
  const botao = criarElemento("button", "copa-alternar-fase", "");
  botao.type = "button";
  botao.setAttribute("aria-controls", idConteudo);
  botao.append(document.createTextNode("EXPANDIR FASE "), criarElemento("span", "", "+"));
  cabecalho.append(informacoes, botao);
  if (faseAtual) card.classList.add("copa-fase-atual");
  const conteudo = criarElemento("div", "copa-fase-conteudo");
  conteudo.id = idConteudo;
  if (!fase.partidas.length) {
    conteudo.append(criarElemento("p", "libertadores-aguardando", "Aguardando definição dos confrontos"));
    card.append(cabecalho, conteudo);
    definirEstadoFase(botao, conteudo, faseAtual);
    botao.addEventListener("click", () => definirEstadoFase(botao, conteudo, conteudo.hidden));
    return card;
  }
  const grade = criarElemento("div", "copa-confrontos-grade");
  grade.append(...fase.partidas.map(criarConfronto));
  conteudo.append(grade);
  card.append(cabecalho, conteudo);
  definirEstadoFase(botao, conteudo, faseAtual);
  botao.addEventListener("click", () => definirEstadoFase(botao, conteudo, conteudo.hidden));
  return card;
}

function renderizarFases(dados) {
  const container = document.getElementById("fases-copa");
  const rodadaAtual = dados.cartola?.rodadaAtual || 0;
  container.replaceChildren(...dados.fases.map((fase, indice) => criarFase(fase, rodadaAtual, indice)));
}

async function carregarCopa() {
  const status = document.getElementById("status-dados");
  const erro = document.getElementById("erro-copa");
  const avisos = document.getElementById("avisos-copa");
  try {
    const resposta = await fetch(document.body.dataset.dadosUrl || "../dados/copa-do-brasil.json");
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
    const dados = await resposta.json();
    renderizarFases(dados);
    const atualizado = new Date(dados.atualizadoEm);
    const origem = dados.cartola?.mercadoFechado ? "pontuações parciais" : "dados consolidados";
    status.textContent = `${origem} · atualizados em ${atualizado.toLocaleString("pt-BR")}`;
    if (dados.avisos?.length) {
      avisos.hidden = false;
      avisos.textContent = dados.avisos.join(" ");
    }
  } catch (error) {
    status.textContent = "Não foi possível carregar os dados da Copa do Brasil.";
    erro.hidden = false;
    erro.textContent = "Execute o atualizador da Copa do Brasil e acesse o site por um servidor local.";
    console.error("Erro ao carregar a Copa do Brasil:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  carregarCopa();
});
