const content = document.querySelector('#admin-content');
const feedback = document.querySelector('#admin-feedback');
const title = document.querySelector('#view-title');
let servicos = [];
let barbeiros = [];
let agendaQuery = '';

const h = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[char]));
const money = value => Number(value).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
const requestJson = (method, data) => ({method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});

async function api(url, options, withMeta = false) {
  const response = await fetch(url, options);
  if (response.status === 401 || response.status === 403) {
    location.href = '/admin/login';
    throw Error('Sem permissão');
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw Error(body.detail || 'Não foi possível concluir.');
  return withMeta ? {body, response} : body;
}

async function executar(action, successMessage) {
  feedback.className = 'feedback';
  try {
    await action();
    feedback.textContent = successMessage || feedback.textContent;
    if (successMessage) feedback.classList.add('success');
  } catch (error) {
    feedback.textContent = error.message;
    feedback.classList.add('error');
  }
}

async function carregarCatalogo() {
  [servicos, barbeiros] = await Promise.all([api('/api/admin/servicos'), api('/api/admin/barbeiros')]);
}

async function dashboard() {
  title.textContent = 'Dashboard';
  const data = await api('/api/admin/dashboard');
  content.innerHTML = `<div class="summary-grid">${Object.entries(data).map(([key, value]) => `<article><strong>${value}</strong><span>${h(key.replaceAll('_', ' '))}</span></article>`).join('')}</div>`;
}

async function agenda(query = '') {
  title.textContent = 'Agendamentos';
  agendaQuery = query;
  await carregarCatalogo();
  const separador = query ? '&' : '?';
  const {body: itens, response} = await api(`/api/admin/agendamentos${query}${separador}por_pagina=20`, undefined, true);
  const total = Number(response.headers.get('X-Total-Count') || itens.length);
  const paginaAtual = Number(response.headers.get('X-Page') || 1);
  const totalPaginas = Math.max(1, Math.ceil(total / 20));
  content.innerHTML = `<form id="agenda-filters" class="filter-form">
    <label>Data<input name="data" type="date"></label>
    <label>Barbeiro<select name="barbeiro_id"><option value="">Todos</option>${barbeiros.map(item => `<option value="${item.id}">${h(item.nome)}</option>`).join('')}</select></label>
    <label>Serviço<select name="servico_id"><option value="">Todos</option>${servicos.map(item => `<option value="${item.id}">${h(item.nome)}</option>`).join('')}</select></label>
    <label>Status<select name="status"><option value="">Todos</option>${['agendado', 'confirmado', 'cancelado', 'concluido', 'faltou'].map(status => `<option>${status}</option>`).join('')}</select></label>
    <label>Cliente ou telefone<input name="busca" placeholder="Buscar"></label>
    <label>Ordenar por<select name="ordenar"><option value="data">Data</option><option value="horario">Horário</option><option value="cliente">Cliente</option><option value="status">Status</option></select></label>
    <label>Direção<select name="direcao"><option value="asc">Crescente</option><option value="desc">Decrescente</option></select></label>
    <button type="submit">Filtrar</button><button type="reset" class="secondary-button">Limpar</button>
  </form><section id="client-link-panel"></section><p>${total} registro(s) · página ${paginaAtual} de ${totalPaginas}.</p><div class="admin-list">${itens.map(item => `<article><strong>${h(item.data)} ${h(item.horario.slice(0, 5))} — ${h(item.cliente)}</strong><span>${h(item.telefone)} · ${h(item.servico)} · ${h(item.barbeiro)} · ${money(item.preco)}</span>${item.cliente_id === null ? `<button data-link-client="${item.id}">Vincular cliente</button>` : ''}<select aria-label="Status do agendamento" data-status="${item.id}">${['agendado', 'confirmado', 'cancelado', 'concluido', 'faltou'].map(status => `<option ${status === item.status ? 'selected' : ''}>${status}</option>`).join('')}</select></article>`).join('') || '<p>Nenhum agendamento encontrado.</p>'}</div><nav class="pagination"><button data-page="${paginaAtual - 1}" ${paginaAtual <= 1 ? 'disabled' : ''}>Anterior</button><button data-page="${paginaAtual + 1}" ${paginaAtual >= totalPaginas ? 'disabled' : ''}>Próxima</button></nav>`;
  const atuais = new URLSearchParams(query.replace(/^\?/, ''));
  for (const [key, value] of atuais) if (content.querySelector(`[name="${key}"]`)) content.querySelector(`[name="${key}"]`).value = value;
}

function abrirVinculo(agendamentoId) {
  document.querySelector('#client-link-panel').innerHTML = `<article class="settings-card"><strong>Vincular agendamento #${agendamentoId}</strong><form id="client-search-form" data-appointment-id="${agendamentoId}"><label>Nome ou telefone do cliente<input id="client-search" minlength="2" required></label><button>Buscar cliente</button><button type="button" class="secondary-button" data-close-link>Cancelar</button></form><div id="client-search-results"></div></article>`;
  document.querySelector('#client-search').focus();
}

function formularioServico(item = {}) {
  return `<form id="service-form" class="inline-form" data-id="${item.id || ''}"><input id="sn" placeholder="Nome" value="${h(item.nome)}" required><input id="sd" placeholder="Descrição" value="${h(item.descricao)}"><input id="sp" type="number" step=".01" min=".01" placeholder="Preço" value="${h(item.preco)}" required><input id="st" type="number" min="1" max="480" placeholder="Minutos" value="${h(item.duracao_minutos)}" required><button>${item.id ? 'Atualizar' : 'Cadastrar'}</button>${item.id ? '<button type="button" class="secondary-button" data-cancel-edit>Cancelar</button>' : ''}</form>`;
}

async function telaServicos(editId) {
  title.textContent = 'Serviços';
  servicos = await api('/api/admin/servicos');
  const editado = servicos.find(item => item.id === Number(editId));
  content.innerHTML = `${formularioServico(editado)}<div class="admin-list">${servicos.map(item => `<article><strong>${h(item.nome)} <span class="status-badge">${item.ativo ? 'Ativo' : 'Inativo'}</span></strong><span>${money(item.preco)} · ${item.duracao_minutos} min</span><div class="action-group"><button data-edit-service="${item.id}">Editar</button><button data-service="${item.id}" data-action="${item.ativo ? 'desativar' : 'ativar'}">${item.ativo ? 'Desativar' : 'Ativar'}</button></div></article>`).join('')}</div>`;
}

function formularioBarbeiro(item = {}) {
  const ids = new Set((item.servicos || []).map(servico => servico.id));
  return `<form id="barber-form" class="inline-form" data-id="${item.id || ''}"><input id="bn" placeholder="Nome" value="${h(item.nome)}" required><input id="bd" placeholder="Descrição" value="${h(item.descricao)}"><label>Serviços<select id="bs" multiple size="${Math.min(Math.max(servicos.length, 2), 6)}">${servicos.map(servico => `<option value="${servico.id}" ${ids.has(servico.id) ? 'selected' : ''}>${h(servico.nome)}</option>`).join('')}</select></label><button>${item.id ? 'Atualizar' : 'Cadastrar'}</button>${item.id ? '<button type="button" class="secondary-button" data-cancel-edit>Cancelar</button>' : ''}</form>`;
}

async function telaBarbeiros(editId) {
  title.textContent = 'Barbeiros';
  await carregarCatalogo();
  const editado = barbeiros.find(item => item.id === Number(editId));
  content.innerHTML = `${formularioBarbeiro(editado)}<div class="admin-list">${barbeiros.map(item => `<article><strong>${h(item.nome)} <span class="status-badge">${item.ativo ? 'Ativo' : 'Inativo'}</span></strong><span>${item.servicos.map(servico => h(servico.nome)).join(', ') || 'Sem serviços'}</span><div class="action-group"><button data-edit-barber="${item.id}">Editar serviços</button><button data-barber="${item.id}" data-action="${item.ativo ? 'desativar' : 'ativar'}">${item.ativo ? 'Desativar' : 'Ativar'}</button></div></article>`).join('')}</div>`;
}

async function seguranca() {
  title.textContent = 'Segurança';
  const master = await api('/api/admin/me');
  content.innerHTML = `<article class="settings-card"><p>Usuário conectado: <strong>${h(master.usuario)}</strong></p><form id="password-form"><label>Senha atual<input id="current-password" type="password" required autocomplete="current-password"></label><label>Nova senha<input id="new-password" type="password" minlength="8" required autocomplete="new-password"></label><label>Confirmar nova senha<input id="confirm-password" type="password" minlength="8" required autocomplete="new-password"></label><button>Alterar senha</button></form></article>`;
}

const views = {dashboard, agenda, servicos: telaServicos, barbeiros: telaBarbeiros, seguranca};
document.querySelector('.admin-nav').addEventListener('click', event => {
  const view = event.target.dataset.view;
  if (view) executar(() => views[view]());
});

content.addEventListener('change', event => {
  if (!event.target.dataset.status) return;
  executar(() => api(`/api/admin/agendamentos/${event.target.dataset.status}/status`, requestJson('PATCH', {status: event.target.value})), 'Status atualizado.');
});

content.addEventListener('click', event => {
  const target = event.target;
  if (target.dataset.editService) telaServicos(target.dataset.editService);
  if (target.dataset.editBarber) telaBarbeiros(target.dataset.editBarber);
  if (target.dataset.linkClient) abrirVinculo(target.dataset.linkClient);
  if (target.dataset.page) {
    const params = new URLSearchParams(agendaQuery.replace(/^\?/, ''));
    params.set('pagina', target.dataset.page);
    executar(() => agenda(`?${params}`));
  }
  if (target.hasAttribute('data-close-link')) document.querySelector('#client-link-panel').innerHTML = '';
  if (target.dataset.clientChoice) executar(async () => {
    await api(`/api/admin/agendamentos/${target.dataset.appointmentId}/cliente`, requestJson('PUT', {cliente_id: Number(target.dataset.clientChoice)}));
    await agenda();
  }, 'Cliente vinculado ao agendamento.');
  if (target.hasAttribute('data-cancel-edit')) title.textContent === 'Serviços' ? telaServicos() : telaBarbeiros();
  if (target.dataset.service) executar(async () => {
    const result = await api(`/api/admin/servicos/${target.dataset.service}/${target.dataset.action}`, {method: 'PATCH'});
    await telaServicos();
    feedback.textContent = `Serviço atualizado. ${result.agendamentos_futuros} agendamento(s) futuro(s) preservado(s).`;
  });
  if (target.dataset.barber) executar(async () => {
    const result = await api(`/api/admin/barbeiros/${target.dataset.barber}/${target.dataset.action}`, {method: 'PATCH'});
    await telaBarbeiros();
    feedback.textContent = `Barbeiro atualizado. ${result.agendamentos_futuros} agendamento(s) para revisão.`;
  });
});

content.addEventListener('reset', event => {
  if (event.target.id === 'agenda-filters') setTimeout(() => agenda(), 0);
});

content.addEventListener('submit', event => {
  event.preventDefault();
  if (event.target.id === 'agenda-filters') {
    const params = new URLSearchParams(new FormData(event.target));
    for (const [key, value] of [...params]) if (!value) params.delete(key);
    executar(() => agenda(params.size ? `?${params}` : ''));
  }
  if (event.target.id === 'client-search-form') executar(async () => {
    const encontrados = await api(`/api/admin/clientes?busca=${encodeURIComponent(document.querySelector('#client-search').value)}`);
    document.querySelector('#client-search-results').innerHTML = encontrados.map(cliente => `<button type="button" class="secondary-button client-choice" data-client-choice="${cliente.id}" data-appointment-id="${event.target.dataset.appointmentId}">${h(cliente.nome)} · ${h(cliente.telefone)}</button>`).join('') || '<p>Nenhum cliente encontrado.</p>';
  });
  if (event.target.id === 'service-form') executar(async () => {
    const data = {nome: document.querySelector('#sn').value, descricao: document.querySelector('#sd').value || null, preco: document.querySelector('#sp').value, duracao_minutos: Number(document.querySelector('#st').value)};
    const id = event.target.dataset.id;
    await api(id ? `/api/admin/servicos/${id}` : '/servicos', requestJson(id ? 'PUT' : 'POST', data));
    await telaServicos();
  }, 'Serviço salvo.');
  if (event.target.id === 'barber-form') executar(async () => {
    const servicoIds = [...document.querySelector('#bs').selectedOptions].map(option => Number(option.value));
    const data = {nome: document.querySelector('#bn').value, descricao: document.querySelector('#bd').value || null, servico_ids: servicoIds};
    const id = event.target.dataset.id;
    if (id) {
      await api(`/api/admin/barbeiros/${id}`, requestJson('PUT', data));
    } else {
      const criado = await api('/barbeiros', requestJson('POST', {nome: data.nome, descricao: data.descricao}));
      await api(`/api/admin/barbeiros/${criado.id}`, requestJson('PUT', data));
    }
    await telaBarbeiros();
  }, 'Barbeiro salvo.');
  if (event.target.id === 'password-form') executar(async () => {
    await api('/api/admin/senha', requestJson('PUT', {senha_atual: document.querySelector('#current-password').value, nova_senha: document.querySelector('#new-password').value, confirmar_nova_senha: document.querySelector('#confirm-password').value}));
    event.target.reset();
  }, 'Senha alterada com segurança.');
});

document.querySelector('#admin-logout').addEventListener('click', async () => {
  await fetch('/api/admin/logout', {method: 'POST'});
  location.href = '/admin/login';
});

executar(() => dashboard());
