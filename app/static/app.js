const form = document.querySelector('#booking-form');
const servicoInput = document.querySelector('#servico');
const barbeiroInput = document.querySelector('#barbeiro');
const dataInput = document.querySelector('#data');
const horarioInput = document.querySelector('#horario');
const clienteInput = document.querySelector('#cliente');
const feedback = document.querySelector('#feedback');
const serviceOptions = document.querySelector('#service-options');
const barberOptions = document.querySelector('#barber-options');
const timeGrid = document.querySelector('#time-grid');
const backButton = document.querySelector('#back-step');
const nextButton = document.querySelector('#next-step');
const successScreen = document.querySelector('#success-screen');
const successDetails = document.querySelector('#success-details');

let currentStep = 0;
let cliente = null;
let servicos = [];
let barbeiros = [];
let horarios = [];

const money = value => Number(value).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
const dateBr = value => value ? value.split('-').reverse().join('/') : '';
const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[char]));

const selectedService = () => servicos.find(item => item.id === Number(servicoInput.value));
const selectedBarber = () => barbeiros.find(item => item.id === Number(barbeiroInput.value));

async function obterJson(url, options) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || 'Não foi possível concluir a solicitação.');
  return body;
}

async function carregarCliente() {
  const response = await fetch('/api/clientes/me');
  if (!response.ok) {
    location.href = '/acesso';
    return;
  }
  cliente = await response.json();
  clienteInput.value = cliente.nome;
  atualizarResumo();
}

document.querySelector('#logout').addEventListener('click', async () => {
  await fetch('/api/clientes/logout', {method: 'POST'});
  location.href = '/acesso';
});

const hoje = new Date();
const hojeLocal = new Date(hoje.getTime() - hoje.getTimezoneOffset() * 60000);
dataInput.min = hojeLocal.toISOString().slice(0, 10);

function setLoading(container, count = 4) {
  container.innerHTML = Array.from({length: count}, () => '<article class="choice-card skeleton-card"><span></span><span></span><span></span></article>').join('');
}

function mostrarFeedback(mensagem, tipo = '') {
  feedback.textContent = mensagem;
  feedback.className = `feedback ${tipo}`;
  if (mensagem && window.showToast) window.showToast(mensagem, tipo || 'success');
}

function renderServicos() {
  serviceOptions.innerHTML = servicos.map(servico => `<button type="button" class="choice-card" data-service="${servico.id}" aria-pressed="${servicoInput.value === String(servico.id)}">
    <span class="choice-check" aria-hidden="true">✓</span>
    <p class="eyebrow">${servico.duracao_minutos} min</p>
    <h3>${escapeHtml(servico.nome)}</h3>
    <p>${escapeHtml(servico.descricao || 'Serviço profissional com horário reservado.')}</p>
    <strong>${money(servico.preco)}</strong>
  </button>`).join('') || '<article class="empty-state"><h3>Nenhum serviço ativo</h3><p>Cadastre serviços no painel master antes de agendar.</p></article>';
}

function renderBarbeiros() {
  const serviceId = Number(servicoInput.value);
  const compativeis = barbeiros.filter(barbeiro => barbeiro.servicos.some(servico => servico.id === serviceId));
  barberOptions.innerHTML = compativeis.map(barbeiro => `<button type="button" class="choice-card barber-choice" data-barber="${barbeiro.id}" aria-pressed="${barbeiroInput.value === String(barbeiro.id)}">
    <span class="choice-check" aria-hidden="true">✓</span>
    <div class="avatar" aria-hidden="true">${escapeHtml(barbeiro.nome).slice(0, 2).toUpperCase()}</div>
    <h3>${escapeHtml(barbeiro.nome)}</h3>
    <p>${escapeHtml(barbeiro.descricao || 'Disponível para o serviço selecionado.')}</p>
  </button>`).join('') || '<article class="empty-state"><h3>Nenhum barbeiro para este serviço</h3><p>Escolha outro serviço ou associe um barbeiro no painel master.</p></article>';
}

function renderHorarios(loading = false) {
  if (loading) {
    timeGrid.innerHTML = Array.from({length: 8}, () => '<button type="button" class="time-button skeleton-line" disabled></button>').join('');
    return;
  }
  timeGrid.innerHTML = horarios.map(horario => `<button type="button" class="time-button ${horarioInput.value === horario ? 'selected' : ''}" data-time="${horario}" aria-pressed="${horarioInput.value === horario}">${horario.slice(0, 5)}</button>`).join('') || '<article class="empty-state"><h3>Nenhum horário disponível nesta data</h3><p>Escolha outra data para continuar.</p></article>';
}

function atualizarResumo() {
  const servico = selectedService();
  const barbeiro = selectedBarber();
  const values = {
    cliente: cliente?.nome || 'Carregando...',
    servico: servico?.nome || 'Escolha um serviço',
    barbeiro: barbeiro?.nome || 'Escolha um barbeiro',
    data: dataInput.value ? dateBr(dataInput.value) : 'Escolha uma data',
    horario: horarioInput.value ? horarioInput.value.slice(0, 5) : 'Escolha um horário',
    duracao: servico ? `${servico.duracao_minutos} min` : '-',
    preco: servico ? money(servico.preco) : '-',
  };
  Object.entries(values).forEach(([key, value]) => {
    document.querySelector(`[data-summary="${key}"]`).textContent = value;
  });
}

function canAdvance(step = currentStep) {
  if (step === 0) return Boolean(servicoInput.value);
  if (step === 1) return Boolean(barbeiroInput.value);
  if (step === 2) return Boolean(dataInput.value);
  if (step === 3) return Boolean(horarioInput.value);
  return true;
}

function setStep(step) {
  currentStep = Math.max(0, Math.min(4, step));
  document.querySelectorAll('[data-step]').forEach(panel => panel.classList.toggle('is-active', Number(panel.dataset.step) === currentStep));
  document.querySelectorAll('[data-step-indicator]').forEach(item => {
    const index = Number(item.dataset.stepIndicator);
    item.classList.toggle('is-active', index === currentStep);
    item.classList.toggle('is-complete', index < currentStep);
  });
  backButton.disabled = currentStep === 0;
  nextButton.classList.toggle('hidden', currentStep === 4);
  nextButton.disabled = !canAdvance();
  if (currentStep === 1) renderBarbeiros();
  if (currentStep === 3 && dataInput.value) carregarHorarios();
  atualizarResumo();
}

async function carregarCatalogo() {
  setLoading(serviceOptions, 4);
  try {
    [servicos, barbeiros] = await Promise.all([
      obterJson('/servicos?somente_ativos=true'),
      obterJson('/barbeiros?somente_ativos=true'),
    ]);
    renderServicos();
  } catch (error) {
    serviceOptions.innerHTML = `<article class="empty-state"><h3>Catálogo indisponível</h3><p>${escapeHtml(error.message)}</p></article>`;
    mostrarFeedback(error.message, 'error');
  }
}

async function carregarHorarios() {
  if (!dataInput.value || !servicoInput.value || !barbeiroInput.value) return;
  renderHorarios(true);
  horarioInput.value = '';
  nextButton.disabled = true;
  const params = new URLSearchParams({
    barbeiro_id: barbeiroInput.value,
    servico_id: servicoInput.value,
    data: dataInput.value,
  });
  try {
    const disponibilidade = await obterJson(`/disponibilidade?${params}`);
    horarios = disponibilidade.horarios;
    renderHorarios();
  } catch (error) {
    timeGrid.innerHTML = `<article class="empty-state"><h3>Erro ao consultar horários</h3><p>${escapeHtml(error.message)}</p></article>`;
    mostrarFeedback(error.message, 'error');
  } finally {
    atualizarResumo();
  }
}

serviceOptions.addEventListener('click', event => {
  const button = event.target.closest('[data-service]');
  if (!button) return;
  servicoInput.value = button.dataset.service;
  barbeiroInput.value = '';
  dataInput.value = '';
  horarioInput.value = '';
  horarios = [];
  renderServicos();
  atualizarResumo();
  setStep(1);
});

barberOptions.addEventListener('click', event => {
  const button = event.target.closest('[data-barber]');
  if (!button) return;
  barbeiroInput.value = button.dataset.barber;
  dataInput.value = '';
  horarioInput.value = '';
  horarios = [];
  renderBarbeiros();
  atualizarResumo();
  setStep(2);
});

dataInput.addEventListener('change', () => {
  horarioInput.value = '';
  horarios = [];
  atualizarResumo();
  nextButton.disabled = !canAdvance();
  if (currentStep >= 3) carregarHorarios();
});

timeGrid.addEventListener('click', event => {
  const button = event.target.closest('[data-time]');
  if (!button) return;
  horarioInput.value = button.dataset.time;
  renderHorarios();
  atualizarResumo();
  setStep(4);
});

backButton.addEventListener('click', () => setStep(currentStep - 1));
nextButton.addEventListener('click', () => {
  if (!canAdvance()) return;
  setStep(currentStep + 1);
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!form.reportValidity() || !canAdvance(3)) return;
  const ok = await window.confirmDialog({
    title: 'Confirmar agendamento',
    message: `Reservar ${selectedService()?.nome} com ${selectedBarber()?.nome} em ${dateBr(dataInput.value)} às ${horarioInput.value.slice(0, 5)}?`,
    confirmText: 'Confirmar',
    cancelText: 'Revisar',
  });
  if (!ok) return;

  const submitButton = document.querySelector('#confirm-booking');
  submitButton.disabled = true;
  mostrarFeedback('Confirmando seu horário...');

  try {
    const agendamento = await obterJson('/api/clientes/agendamentos', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        barbeiro_id: Number(barbeiroInput.value),
        servico_id: Number(servicoInput.value),
        data: dataInput.value,
        horario: horarioInput.value,
      }),
    });
    const servico = agendamento.servico || selectedService();
    successDetails.innerHTML = `<dl>
      <div><dt>Serviço</dt><dd>${escapeHtml(servico.nome)}</dd></div>
      <div><dt>Barbeiro</dt><dd>${escapeHtml(agendamento.barbeiro.nome)}</dd></div>
      <div><dt>Data</dt><dd>${dateBr(agendamento.data)}</dd></div>
      <div><dt>Horário</dt><dd>${agendamento.horario.slice(0, 5)}</dd></div>
      <div><dt>Agendamento</dt><dd>#${agendamento.id}</dd></div>
    </dl>`;
    document.querySelector('.booking-layout').classList.add('hidden');
    document.querySelector('.booking-intro').classList.add('hidden');
    successScreen.classList.remove('hidden');
    mostrarFeedback('Agendamento confirmado com sucesso.', 'success');
  } catch (error) {
    mostrarFeedback(error.message, 'error');
    if (error.message.includes('reservado')) carregarHorarios();
  } finally {
    submitButton.disabled = false;
  }
});

carregarCatalogo();
carregarCliente();
setStep(0);
