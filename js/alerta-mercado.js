const API_STATUS_MERCADO = "https://api.cartola.globo.com/mercado/status";

function pluralMercado(valor, singular, plural) {
  return `${valor} ${valor === 1 ? singular : plural}`;
}

function tempoRestanteMercado(milissegundos) {
  const totalMinutos = Math.max(0, Math.floor(milissegundos / 60000));
  const dias = Math.floor(totalMinutos / 1440);
  const horas = Math.floor((totalMinutos % 1440) / 60);
  const minutos = totalMinutos % 60;
  const partes = [];
  if (dias) partes.push(pluralMercado(dias, "dia", "dias"));
  if (horas) partes.push(pluralMercado(horas, "hora", "horas"));
  if (minutos || !partes.length) partes.push(pluralMercado(minutos, "minuto", "minutos"));
  if (partes.length === 1) return partes[0];
  return `${partes.slice(0, -1).join(", ")} e ${partes.at(-1)}`;
}

function dataFechamentoMercado(fechamento) {
  if (typeof fechamento?.timestamp === "number") {
    return new Date(fechamento.timestamp * 1000);
  }
  if (!fechamento) return null;
  return new Date(
    fechamento.ano,
    Number(fechamento.mes) - 1,
    fechamento.dia,
    fechamento.hora,
    fechamento.minuto,
  );
}

function formatarFechamentoMercado(data) {
  const dia = new Intl.DateTimeFormat("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    timeZone: "America/Sao_Paulo",
  }).format(data);
  const hora = new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Sao_Paulo",
  }).format(data);
  return `${dia}, às ${hora}`;
}

function criarMensagemMercado(dados) {
  const rodada = dados.nome_rodada || `Rodada ${dados.rodada_atual || "atual"}`;
  const fechamento = dataFechamentoMercado(dados.fechamento);
  if (dados.status_mercado !== 1) {
    return `🔒 O mercado da ${rodada.toLowerCase()} está fechado.`;
  }
  if (!fechamento || Number.isNaN(fechamento.getTime())) {
    return `⚠️ O mercado da ${rodada.toLowerCase()} está aberto, mas o horário de fechamento não foi informado.`;
  }
  const restante = fechamento.getTime() - Date.now();
  if (restante <= 0) return `⚠️ O horário previsto para o fechamento da ${rodada.toLowerCase()} já passou.`;
  return `⚠️ Atenção, cartoleiros! O mercado da ${rodada.toLowerCase()} fecha ${formatarFechamentoMercado(fechamento)}. Faltam ${tempoRestanteMercado(restante)}. Não esqueçam de escalar o time!`;
}

async function consultarMercado() {
  const botao = document.getElementById("consultar-mercado");
  const mensagem = document.getElementById("mensagem-mercado");
  if (!botao || !mensagem) return;
  botao.disabled = true;
  botao.textContent = "CONSULTANDO…";
  mensagem.classList.remove("erro");
  mensagem.textContent = "Consultando o Cartola…";
  try {
    const resposta = await fetch(API_STATUS_MERCADO, { cache: "no-store" });
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
    mensagem.textContent = criarMensagemMercado(await resposta.json());
  } catch (erro) {
    mensagem.classList.add("erro");
    mensagem.textContent = "Não foi possível consultar o Cartola agora. Tente novamente em alguns instantes.";
    console.error("Erro ao consultar o mercado do Cartola:", erro);
  } finally {
    botao.disabled = false;
    botao.textContent = "GERAR MENSAGEM";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("consultar-mercado")?.addEventListener("click", consultarMercado);
});
