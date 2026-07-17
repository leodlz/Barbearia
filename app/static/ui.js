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
    document.querySelectorAll('.admin-nav [data-view]').forEach(item => {
      item.classList.toggle('is-active', item === button);
    });
  });
});

(() => {
  const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  }[char]));

  const ensureToastRegion = () => {
    let region = document.querySelector('#toast-region');
    if (!region) {
      region = document.createElement('div');
      region.id = 'toast-region';
      region.className = 'toast-region';
      region.setAttribute('aria-live', 'polite');
      region.setAttribute('aria-label', 'Notificações');
      document.body.appendChild(region);
    }
    return region;
  };

  window.showToast = (message, type = 'success') => {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
    toast.textContent = message;
    ensureToastRegion().appendChild(toast);
    setTimeout(() => toast.classList.add('is-leaving'), 4200);
    setTimeout(() => toast.remove(), 4700);
  };

  window.confirmDialog = ({title = 'Confirmar ação', message = '', confirmText = 'Confirmar', cancelText = 'Voltar', danger = false} = {}) => new Promise(resolve => {
    const dialog = document.createElement('dialog');
    dialog.className = 'app-dialog';
    dialog.innerHTML = `<form method="dialog">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(message)}</p>
      <div class="dialog-actions">
        <button value="cancel" class="secondary-button" type="submit">${escapeHtml(cancelText)}</button>
        <button value="confirm" class="${danger ? 'danger-button' : ''}" type="submit">${escapeHtml(confirmText)}</button>
      </div>
    </form>`;
    document.body.appendChild(dialog);
    dialog.addEventListener('close', () => {
      resolve(dialog.returnValue === 'confirm');
      dialog.remove();
    }, {once: true});
    dialog.showModal();
    dialog.querySelector('button[value="cancel"]').focus();
  });
})();
