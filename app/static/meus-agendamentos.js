const lista = document.querySelector('#appointments');
const feedback = document.querySelector('#feedback');

const moeda = value => Number(value).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
const dataBr = value => value.split('-').reverse().join('/');
const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[char]));

function setFeedback(message, type = '') {
  feedback.textContent = message;
  feedback.className = `feedback ${type}`;
  if (message && window.showToast) window.showToast(message, type || 'success');
}

function appointmentDate(item) {
  return new Date(`${item.data}T${item.horario}`);
}

function classify(items) {
  const now = new Date();
  const active = ['agendado', 'confirmado'];
  const groups = {proximos: [], anteriores: [], cancelados: []};
  items.forEach(item => {
    if (item.status === 'cancelado') groups.cancelados.push(item);
    else if (active.includes(item.status) && appointmentDate(item) >= now) groups.proximos.push(item);
    else groups.anteriores.push(item);
  });
  groups.proximos.sort((a, b) => appointmentDate(a) - appointmentDate(b));
  groups.anteriores.sort((a, b) => appointmentDate(b) - appointmentDate(a));
  groups.cancelados.sort((a, b) => appointmentDate(b) - appointmentDate(a));
  return groups;
}

function card(item, highlight = false) {
  const canCancel = ['agendado', 'confirmado'].includes(item.status) && appointmentDate(item) >= new Date();
  return `<article class="appointment-card ${highlight ? 'next-card' : ''}">
    ${highlight ? '<p class="eyebrow">Próximo atendimento</p>' : ''}
    <span class="status-badge status-${escapeHtml(item.status)}">${escapeHtml(item.status)}</span>
    <h3>${escapeHtml(item.servico.nome)}</h3>
    <dl class="summary-list">
      <div><dt>Barbeiro</dt><dd>${escapeHtml(item.barbeiro.nome)}</dd></div>
      <div><dt>Data</dt><dd>${dataBr(item.data)} às ${item.horario.slice(0, 5)}</dd></div>
      <div><dt>Duração</dt><dd>${item.servico.duracao_minutos} min</dd></div>
      <div><dt>Valor</dt><dd>${moeda(item.preco_no_agendamento)}</dd></div>
    </dl>
    <small>Agendamento #${item.id}</small>
    ${canCancel ? `<button data-id="${item.id}" type="button" class="danger-button">Cancelar agendamento</button>` : ''}
  </article>`;
}

function render(items) {
  if (!items.length) {
    lista.innerHTML = '<article class="empty-state"><h2>Nenhum agendamento encontrado</h2><p>Quando você reservar um horário, ele aparecerá aqui.</p><a class="button" href="/agendar">Agendar agora</a></article>';
    return;
  }
  const groups = classify(items);
  lista.innerHTML = [
    ['Próximos', 'proximos'],
    ['Anteriores', 'anteriores'],
    ['Cancelados', 'cancelados'],
  ].map(([title, key]) => `<section class="appointment-group" aria-labelledby="${key}-title">
    <div class="section-heading compact-heading"><h2 id="${key}-title">${title}</h2><span>${groups[key].length}</span></div>
    <div class="cards-grid">${groups[key].map((item, index) => card(item, key === 'proximos' && index === 0)).join('') || '<article class="empty-state small-empty"><p>Nenhum item nesta categoria.</p></article>'}</div>
  </section>`).join('');
}

async function carregar() {
  lista.innerHTML = '<article class="empty-state"><div class="spinner" aria-hidden="true"></div><p>Carregando seus agendamentos...</p></article>';
  const response = await fetch('/api/clientes/me/agendamentos');
  if (response.status === 401) {
    location.href = '/acesso';
    return;
  }
  const itens = await response.json();
  render(itens);
}

lista.addEventListener('click', async event => {
  const id = event.target.dataset.id;
  if (!id) return;
  const ok = await window.confirmDialog({
    title: 'Cancelar agendamento',
    message: 'Este horário será liberado. Para outro atendimento, será necessário fazer um novo agendamento.',
    confirmText: 'Cancelar agendamento',
    cancelText: 'Manter horário',
    danger: true,
  });
  if (!ok) return;
  const response = await fetch(`/api/clientes/me/agendamentos/${id}/cancelar`, {method: 'PATCH'});
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    setFeedback(body.detail || 'Não foi possível cancelar este agendamento.', 'error');
    return;
  }
  setFeedback('Agendamento cancelado com sucesso.', 'success');
  carregar();
});

document.querySelector('#logout').onclick = async () => {
  await fetch('/api/clientes/logout', {method: 'POST'});
  location.href = '/acesso';
};

carregar();
