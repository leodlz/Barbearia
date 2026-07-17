const serviceList = document.querySelector('#home-services');
const barberList = document.querySelector('#home-barbers');

const money = value => Number(value).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[char]));

function skeleton(container, count) {
  container.innerHTML = Array.from({length: count}, () => '<article class="feature-card skeleton-card"><span></span><span></span><span></span></article>').join('');
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw Error('Não foi possível carregar as informações agora.');
  return response.json();
}

async function loadHome() {
  skeleton(serviceList, 3);
  skeleton(barberList, 3);
  try {
    const [services, barbers] = await Promise.all([
      getJson('/servicos?somente_ativos=true'),
      getJson('/barbeiros?somente_ativos=true'),
    ]);

    serviceList.innerHTML = services.slice(0, 6).map(service => `<article class="feature-card">
      <p class="eyebrow">${escapeHtml(service.duracao_minutos)} min</p>
      <h3>${escapeHtml(service.nome)}</h3>
      <p>${escapeHtml(service.descricao || 'Atendimento cuidadoso, acabamento limpo e horário reservado para você.')}</p>
      <strong>${money(service.preco)}</strong>
    </article>`).join('') || '<article class="empty-state"><h3>Nenhum serviço ativo</h3><p>Cadastre serviços no painel master para exibi-los aqui.</p></article>';

    barberList.innerHTML = barbers.slice(0, 6).map(barber => `<article class="feature-card barber-card">
      <div class="avatar" aria-hidden="true">${escapeHtml(barber.nome).slice(0, 2).toUpperCase()}</div>
      <h3>${escapeHtml(barber.nome)}</h3>
      <p>${escapeHtml(barber.descricao || 'Profissional disponível para os serviços associados.')}</p>
      <small>${barber.servicos?.length ? barber.servicos.map(service => escapeHtml(service.nome)).join(' · ') : 'Serviços a definir'}</small>
    </article>`).join('') || '<article class="empty-state"><h3>Nenhum barbeiro ativo</h3><p>Cadastre barbeiros no painel master para exibi-los aqui.</p></article>';
  } catch (error) {
    serviceList.innerHTML = `<article class="empty-state"><h3>Serviços indisponíveis</h3><p>${escapeHtml(error.message)}</p></article>`;
    barberList.innerHTML = `<article class="empty-state"><h3>Barbeiros indisponíveis</h3><p>${escapeHtml(error.message)}</p></article>`;
  }
}

loadHome();
