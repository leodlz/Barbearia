document.querySelectorAll('.top-nav').forEach(nav => {
  const toggle = nav.querySelector('.nav-toggle');
  const links = nav.querySelector('.nav-links');
  if (!toggle || !links) return;
  const close = () => {
    nav.classList.remove('nav-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Abrir menu');
    toggle.textContent = '☰';
  };
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
    toggle.textContent = open ? '×' : '☰';
  });
  links.addEventListener('click', event => {
    if (event.target.closest('a, button')) close();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') close();
  });
  window.matchMedia('(min-width: 901px)').addEventListener('change', event => {
    if (event.matches) close();
  });
});

document.querySelectorAll('.admin-nav [data-view]').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.admin-nav [data-view]').forEach(item => item.classList.toggle('is-active', item === button));
  });
});
