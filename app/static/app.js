const form = document.querySelector("#booking-form");
const servicoSelect = document.querySelector("#servico");
const barbeiroSelect = document.querySelector("#barbeiro");
const dataInput = document.querySelector("#data");
const horarioSelect = document.querySelector("#horario");
const clienteInput = document.querySelector("#cliente");
const feedback = document.querySelector("#feedback");
const submitButton = form.querySelector("button");

let barbeiros = [];

const hoje = new Date();
const hojeLocal = new Date(hoje.getTime() - hoje.getTimezoneOffset() * 60000);
dataInput.min = hojeLocal.toISOString().slice(0, 10);

function preencherSelect(elemento, itens, placeholder, texto) {
  elemento.innerHTML = `<option value="">${placeholder}</option>`;
  itens.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id ?? item;
    option.textContent = texto(item);
    elemento.appendChild(option);
  });
}

async function obterJson(url, options) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || "Não foi possível concluir a solicitação.");
  }
  return body;
}

async function carregarCatalogo() {
  try {
    const [servicos, barbeirosAtivos] = await Promise.all([
      obterJson("/servicos?somente_ativos=true"),
      obterJson("/barbeiros?somente_ativos=true"),
    ]);
    barbeiros = barbeirosAtivos;
    preencherSelect(servicoSelect, servicos, "Escolha o serviço", (servico) =>
      `${servico.nome} · ${servico.duracao_minutos} min · R$ ${servico.preco}`
    );
  } catch (error) {
    mostrarFeedback(error.message, "error");
  }
}

servicoSelect.addEventListener("change", () => {
  const servicoId = Number(servicoSelect.value);
  const compativeis = barbeiros.filter((barbeiro) =>
    barbeiro.servicos.some((servico) => servico.id === servicoId)
  );
  preencherSelect(barbeiroSelect, compativeis, "Escolha o barbeiro", (item) => item.nome);
  barbeiroSelect.disabled = !servicoId || compativeis.length === 0;
  dataInput.disabled = true;
  horarioSelect.disabled = true;
});

barbeiroSelect.addEventListener("change", () => {
  dataInput.disabled = !barbeiroSelect.value;
  horarioSelect.disabled = true;
});

dataInput.addEventListener("change", async () => {
  horarioSelect.disabled = true;
  preencherSelect(horarioSelect, [], "Consultando horários…", String);
  if (!dataInput.value) return;

  const params = new URLSearchParams({
    barbeiro_id: barbeiroSelect.value,
    servico_id: servicoSelect.value,
    data: dataInput.value,
  });

  try {
    const disponibilidade = await obterJson(`/disponibilidade?${params}`);
    preencherSelect(
      horarioSelect,
      disponibilidade.horarios,
      disponibilidade.horarios.length ? "Escolha o horário" : "Sem horários disponíveis",
      (horario) => horario.slice(0, 5)
    );
    horarioSelect.disabled = disponibilidade.horarios.length === 0;
  } catch (error) {
    mostrarFeedback(error.message, "error");
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  mostrarFeedback("Confirmando seu horário…");

  try {
    const agendamento = await obterJson("/agendamentos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cliente: clienteInput.value.trim(),
        barbeiro_id: Number(barbeiroSelect.value),
        servico_id: Number(servicoSelect.value),
        data: dataInput.value,
        horario: horarioSelect.value,
      }),
    });
    mostrarFeedback(
      `Agendamento #${agendamento.id} confirmado com ${agendamento.barbeiro.nome}.`,
      "success"
    );
    clienteInput.value = "";
    dataInput.dispatchEvent(new Event("change"));
  } catch (error) {
    mostrarFeedback(error.message, "error");
  } finally {
    submitButton.disabled = false;
  }
});

function mostrarFeedback(mensagem, tipo = "") {
  feedback.textContent = mensagem;
  feedback.className = `feedback ${tipo}`;
}

carregarCatalogo();
