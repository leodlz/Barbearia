const loginForm = document.querySelector('#login-form');
const registerForm = document.querySelector('#register-form');
const recoveryForm = document.querySelector('#recovery-form');
const feedback = document.querySelector('#feedback');
let recoveryStep = 1;

function setFeedback(message, type = '') {
  feedback.textContent = message;
  feedback.className = `feedback ${type}`;
  if (message && window.showToast) window.showToast(message, type || 'success');
}

function mostrar(nome) {
  loginForm.classList.toggle('hidden', nome !== 'login');
  registerForm.classList.toggle('hidden', nome !== 'register');
  recoveryForm.classList.toggle('hidden', nome !== 'recovery');
  document.querySelector('#tab-login').classList.toggle('active', nome === 'login');
  document.querySelector('#tab-register').classList.toggle('active', nome === 'register');
  document.querySelector('#tab-login').setAttribute('aria-selected', String(nome === 'login'));
  document.querySelector('#tab-register').setAttribute('aria-selected', String(nome === 'register'));
  setFeedback('');
}

document.querySelector('#tab-login').onclick = () => mostrar('login');
document.querySelector('#tab-register').onclick = () => mostrar('register');
document.querySelector('#forgot-button').onclick = () => mostrar('recovery');
document.querySelector('#recovery-back').onclick = () => mostrar('login');

document.querySelectorAll('[data-toggle-password]').forEach(button => {
  button.addEventListener('click', () => {
    const input = document.querySelector(button.dataset.togglePassword);
    const visible = input.type === 'text';
    input.type = visible ? 'password' : 'text';
    button.textContent = visible ? 'Mostrar' : 'Ocultar';
    button.setAttribute('aria-label', visible ? 'Mostrar senha' : 'Ocultar senha');
  });
});

async function post(url, dados) {
  const response = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(dados)});
  const body = response.status === 204 ? {} : await response.json();
  if (!response.ok) {
    const detalhe = Array.isArray(body.detail) ? body.detail[0]?.msg : body.detail;
    throw Error((detalhe || 'Confira os dados informados.').replace('Value error, ', ''));
  }
  return body;
}

async function enviar(form, url, dados) {
  if (!form.reportValidity()) return;
  const botao = form.querySelector('button[type=submit],button:not([type])');
  botao.disabled = true;
  botao.dataset.originalText = botao.textContent;
  botao.textContent = 'Aguarde...';
  try {
    await post(url, dados);
    location.href = '/agendar';
  } catch (error) {
    setFeedback(error.message, 'error');
  } finally {
    botao.disabled = false;
    botao.textContent = botao.dataset.originalText;
  }
}

loginForm.onsubmit = event => {
  event.preventDefault();
  enviar(loginForm, '/api/clientes/login', {
    cpf: document.querySelector('#login-cpf').value.trim(),
    senha: document.querySelector('#login-senha').value,
  });
};

registerForm.onsubmit = event => {
  event.preventDefault();
  enviar(registerForm, '/api/clientes/registro', {
    nome: document.querySelector('#nome').value.trim(),
    telefone: document.querySelector('#telefone').value.trim(),
    cpf: document.querySelector('#registro-cpf').value.trim(),
    senha: document.querySelector('#registro-senha').value,
  });
};

recoveryForm.onsubmit = async event => {
  event.preventDefault();
  if (!recoveryForm.reportValidity()) return;
  const button = document.querySelector('#recovery-submit');
  button.disabled = true;
  try {
    if (recoveryStep === 1) {
      const body = await post('/api/clientes/recuperacao/solicitar', {cpf: document.querySelector('#recovery-cpf').value.trim()});
      recoveryStep = 2;
      document.querySelector('#recovery-confirm').classList.remove('hidden');
      document.querySelector('#recovery-code').required = true;
      document.querySelector('#recovery-password').required = true;
      document.querySelector('#recovery-password-confirm').required = true;
      button.textContent = 'Alterar senha';
      setFeedback(body.codigo_teste ? `Ambiente simulado — código: ${body.codigo_teste}` : body.mensagem, 'success');
    } else {
      await post('/api/clientes/recuperacao/confirmar', {
        cpf: document.querySelector('#recovery-cpf').value.trim(),
        codigo: document.querySelector('#recovery-code').value,
        nova_senha: document.querySelector('#recovery-password').value,
        confirmar_nova_senha: document.querySelector('#recovery-password-confirm').value,
      });
      recoveryStep = 1;
      mostrar('login');
      setFeedback('Senha alterada. Entre com a nova senha.', 'success');
    }
  } catch (error) {
    setFeedback(error.message, 'error');
  } finally {
    button.disabled = false;
  }
};
