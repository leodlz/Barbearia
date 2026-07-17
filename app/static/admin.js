const content = document.querySelector('#admin-content');
const feedback = document.querySelector('#admin-feedback');
const title = document.querySelector('#view-title');
let servicos = [];
let barbeiros = [];
let agendaQuery = '';

const h = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[char]));
const money = value => Number(value).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
const requestJson = (method, data) => ({method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});

function setFeedback(message, type = '') {
  feedback.textContent = message;
  feedback.className = `feedback ${type}`;
  if (message && window.showToast) window.showToast(message, type || 'success');
}

function loading(message = 'Carregando informações...') {
  content.innerHTML = `<article class="empty-state"><div class="spinner" aria-hidden="true"></div><p>${h(message)}</p></article>`;
}

async function api(url, options, withMeta = false) {
  const response = await fetch(url, options);
  if (response.status === 401 || response.status === 403) {
    location.href = '/admin/login';
    throw Error('Você não tem permissão para acessar esta área.');
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw Error(body.detail || 'Não foi possível concluir.');
  return withMeta ? {body, response} : body;
}

async function executar(action, successMessage) {
  setFeedback('');
  try {
    await action();
    if (successMessage) setFeedback(successMessage, 'success');
  } catch (error) {
    setFeedback(error.message, 'error');
  }
}

async function carregarCatalogo() {
  [servicos, barbeiros] = await Promise.all([api('/api/admin/servicos'), api('/api/admin/barbeiros')]);
}

async function dashboard() {
  title.textContent = 'Dashboard';
  loading();
  const data = await api('/api/admin/dashboard');
  const labels = {
    agendamentos_hoje: 'agendamentos hoje',
    proximos_atendimentos: 'próximos atendimentos',
    servicos_ativos: 'serviços ativos',
    barbeiros_ativos: 'barbeiros ativos',
    cancelamentos: 'cancelamentos',
  };
  content.innerHTML = `<div class="summary-grid">${Object.entries(data).map(([key, value]) => `<article><strong>${value}</strong><span>${h(labels[key] || key.replaceAll('_', ' '))}</span></article>`).join('')}</div>
    <section class="surface-card admin-welcome">
      <p class="eyebrow">Ações rápidas</p>
      <h2>Operação do dia</h2>
      <div class="action-group">
        <button data-view-shortcut="agenda">Ver agenda</button>
        <button data-view-shortcut="servicos" class="secondary-button">Gerenciar serviços</button>
        <button data-view-shortcut="barbeiros" class="secondary-button">Gerenciar barbeiros</button>
      </div>
    </section>`;
}

async function agenda(query = '') {
  title.textContent = 'Agendamentos';
  agendaQuery = query;
  loading('Carregando agenda...');
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
  </form>
  <section id="client-link-panel"></section>
  <p class="result-count">${total} registro(s) · página ${paginaAtual} de ${totalPaginas}.</p>
  <div class="admin-list agenda-list">${itens.map(item => `<article>
    <div>
      <span class="status-badge status-${h(item.status)}">${h(item.status)}</span>
      <strong>${h(item.data)} às ${h(item.horario.slice(0, 5))}</strong>
      <span>${h(item.cliente)} · ${h(item.telefone)}</span>
      <small>${h(item.servico)} · ${h(item.barbeiro)} · ${money(item.preco)}</small>
    </div>
    <div class="action-group">
      ${item.cliente_id === null ? `<button data-link-client="${item.id}" class="secondary-button">Vincular cliente</button>` : ''}
      <select aria-label="Status do agendamento" data-status="${item.id}">${['agendado', 'confirmado', 'cancelado', 'concluido', 'faltou'].map(status => `<option ${status === item.status ? 'selected' : ''}>${status}</option>`).join('')}</select>
    </div>
  </article>`).join('') || '<article class="empty-state"><h3>Nenhum agendamento encontrado</h3><p>Ajuste os filtros ou aguarde novos horários.</p></article>'}</div>
  <nav class="pagination"><button data-page="${paginaAtual - 1}" ${paginaAtual <= 1 ? 'disabled' : ''}>Anterior</button><button data-page="${paginaAtual + 1}" ${paginaAtual >= totalPaginas ? 'disabled' : ''}>Próxima</button></nav>`;
  const atuais = new URLSearchParams(query.replace(/^\?/, ''));
  for (const [key, value] of atuais) {
    const field = content.querySelector(`[name="${key}"]`);
    if (field) field.value = value;
  }
}

function abrirVinculo(agendamentoId) {
  document.querySelector('#client-link-panel').innerHTML = `<article class="settings-card">
    <strong>Vincular agendamento #${agendamentoId}</strong>
    <form id="client-search-form" data-appointment-id="${agendamentoId}">
      <label>Nome ou telefone do cliente<input id="client-search" minlength="2" required></label>
      <button>Buscar cliente</button>
      <button type="button" class="secondary-button" data-close-link>Cancelar</button>
    </form>
    <div id="client-search-results"></div>
  </article>`;
  document.querySelector('#client-search').focus();
}

function formularioServico(item = {}) {
  return `<form id="service-form" class="inline-form management-form" data-id="${item.id || ''}">
    <label>Nome<input id="sn" value="${h(item.nome)}" required></label>
    <label>Descrição<input id="sd" value="${h(item.descricao)}"></label>
    <label>Preço<input id="sp" type="number" step=".01" min=".01" value="${h(item.preco)}" required></label>
    <label>Minutos<input id="st" type="number" min="1" max="480" value="${h(item.duracao_minutos)}" required></label>
    <button>${item.id ? 'Atualizar' : 'Cadastrar'}</button>
    ${item.id ? '<button type="button" class="secondary-button" data-cancel-edit>Cancelar</button>' : ''}
  </form>`;
}

async function telaServicos(editId) {
  title.textContent = 'Serviços';
  loading('Carregando serviços...');
  servicos = await api('/api/admin/servicos');
  const editado = servicos.find(item => item.id === Number(editId));
  content.innerHTML = `${formularioServico(editado)}
    <div class="section-tools"><p class="result-count">${servicos.length} serviço(s) cadastrado(s).</p></div>
    <div class="admin-list management-list">${servicos.map(item => `<article>
      <div>
        <span class="status-badge ${item.ativo ? 'status-confirmado' : 'status-cancelado'}">${item.ativo ? 'Ativo' : 'Inativo'}</span>
        <strong>${h(item.nome)}</strong>
        <span>${h(item.descricao || 'Sem descrição')}</span>
        <small>${money(item.preco)} · ${item.duracao_minutos} min</small>
      </div>
      <div class="action-group">
        <button data-edit-service="${item.id}">Editar</button>
        <button data-service="${item.id}" data-action="${item.ativo ? 'desativar' : 'ativar'}" class="${item.ativo ? 'danger-button' : 'secondary-button'}">${item.ativo ? 'Desativar' : 'Ativar'}</button>
      </div>
    </article>`).join('') || '<article class="empty-state"><h3>Nenhum serviço cadastrado</h3><p>Crie o primeiro serviço para liberar agendamentos.</p></article>'}</div>`;
}

function formularioBarbeiro(item = {}) {
  const ids = new Set((item.servicos || []).map(servico => servico.id));
  const quantidade = ids.size;
  const resumo = quantidade ? `${quantidade} serviço${quantidade > 1 ? 's' : ''} selecionado${quantidade > 1 ? 's' : ''}` : 'Selecionar serviços';
  return `<form id="barber-form" class="inline-form management-form" data-id="${item.id || ''}">
    <label>Nome<input id="bn" value="${h(item.nome)}" required></label>
    <label>Descrição<input id="bd" value="${h(item.descricao)}"></label>
    <label class="service-picker-label">Serviços
      <details class="service-picker">
        <summary><span data-service-summary>${resumo}</span><span class="picker-chevron" aria-hidden="true">⌄</span></summary>
        <div class="service-options">${servicos.map(servico => `<label class="service-option"><input type="checkbox" value="${servico.id}" data-service-option ${ids.has(servico.id) ? 'checked' : ''}><span>${h(servico.nome)}</span></label>`).join('') || '<p class="service-empty">Nenhum serviço cadastrado.</p>'}</div>
      </details>
    </label>
    <button>${item.id ? 'Atualizar' : 'Cadastrar'}</button>
    ${item.id ? '<button type="button" class="secondary-button" data-cancel-edit>Cancelar</button>' : ''}
  </form>`;
}

async function telaBarbeiros(editId) {
  title.textContent = 'Barbeiros';
  loading('Carregando barbeiros...');
  await carregarCatalogo();
  const editado = barbeiros.find(item => item.id === Number(editId));
  content.innerHTML = `${formularioBarbeiro(editado)}
    <div class="admin-list management-list barber-management">${barbeiros.map(item => `<article>
      <div class="barber-row">
        <div class="avatar" aria-hidden="true">${h(item.nome).slice(0, 2).toUpperCase()}</div>
        <div>
          <span class="status-badge ${item.ativo ? 'status-confirmado' : 'status-cancelado'}">${item.ativo ? 'Ativo' : 'Inativo'}</span>
          <strong>${h(item.nome)}</strong>
          <span>${item.servicos.map(servico => h(servico.nome)).join(' · ') || 'Sem serviços associados'}</span>
        </div>
      </div>
      <div class="action-group">
        <button data-edit-barber="${item.id}">Editar</button>
        <button data-barber="${item.id}" data-action="${item.ativo ? 'desativar' : 'ativar'}" class="${item.ativo ? 'danger-button' : 'secondary-button'}">${item.ativo ? 'Desativar' : 'Ativar'}</button>
      </div>
    </article>`).join('') || '<article class="empty-state"><h3>Nenhum barbeiro cadastrado</h3><p>Cadastre barbeiros e associe serviços.</p></article>'}</div>`;
}

async function seguranca() {
  title.textContent = 'Segurança';
  loading();
  const master = await api('/api/admin/me');
  content.innerHTML = `<article class="settings-card">
    <p>Usuário conectado: <strong>${h(master.usuario)}</strong></p>
    <form id="password-form">
      <label>Senha atual<input id="current-password" type="password" required autocomplete="current-password"></label>
      <label>Nova senha<input id="new-password" type="password" minlength="8" required autocomplete="new-password"></label>
      <label>Confirmar nova senha<input id="confirm-password" type="password" minlength="8" required autocomplete="new-password"></label>
      <button>Alterar senha</button>
    </form>
  </article>`;
}

const views = {dashboard, agenda, servicos: telaServicos, barbeiros: telaBarbeiros, seguranca};

document.querySelector('.admin-nav').addEventListener('click', event => {
  const view = event.target.dataset.view;
  if (view) executar(() => views[view]());
});

content.addEventListener('change', async event => {
  if (event.target.matches('[data-service-option]')) {
    const picker = event.target.closest('.service-picker');
    const quantidade = picker.querySelectorAll('[data-service-option]:checked').length;
    picker.querySelector('[data-service-summary]').textContent = quantidade ? `${quantidade} serviço${quantidade > 1 ? 's' : ''} selecionado${quantidade > 1 ? 's' : ''}` : 'Selecionar serviços';
    return;
  }
  if (!event.target.dataset.status) return;
  const status = event.target.value;
  if (['cancelado', 'faltou'].includes(status)) {
    const ok = await window.confirmDialog({
      title: 'Alterar status',
      message: `Confirmar mudança para ${status}? Esta informação aparecerá no histórico.`,
      confirmText: 'Alterar status',
      cancelText: 'Voltar',
      danger: true,
    });
    if (!ok) {
      await agenda(agendaQuery);
      return;
    }
  }
  executar(() => api(`/api/admin/agendamentos/${event.target.dataset.status}/status`, requestJson('PATCH', {status})), 'Status atualizado.');
});

content.addEventListener('click', async event => {
  const target = event.target.closest('button');
  if (!target) return;
  if (target.dataset.viewShortcut) executar(() => views[target.dataset.viewShortcut]());
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
  if (target.dataset.service) {
    const ok = target.dataset.action === 'desativar' ? await window.confirmDialog({title: 'Desativar serviço', message: 'O serviço ficará indisponível para novos agendamentos. Registros históricos serão preservados.', confirmText: 'Desativar', cancelText: 'Voltar', danger: true}) : true;
    if (!ok) return;
    executar(async () => {
      const result = await api(`/api/admin/servicos/${target.dataset.service}/${target.dataset.action}`, {method: 'PATCH'});
      await telaServicos();
      setFeedback(`Serviço atualizado. ${result.agendamentos_futuros} agendamento(s) futuro(s) preservado(s).`, 'success');
    });
  }
  if (target.dataset.barber) {
    const ok = target.dataset.action === 'desativar' ? await window.confirmDialog({title: 'Desativar barbeiro', message: 'O barbeiro deixará de aparecer para novos horários. Agendamentos futuros podem exigir revisão.', confirmText: 'Desativar', cancelText: 'Voltar', danger: true}) : true;
    if (!ok) return;
    executar(async () => {
      const result = await api(`/api/admin/barbeiros/${target.dataset.barber}/${target.dataset.action}`, {method: 'PATCH'});
      await telaBarbeiros();
      setFeedback(`Barbeiro atualizado. ${result.agendamentos_futuros} agendamento(s) para revisão.`, 'success');
    });
  }
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
    const servicoIds = [...event.target.querySelectorAll('[data-service-option]:checked')].map(option => Number(option.value));
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
