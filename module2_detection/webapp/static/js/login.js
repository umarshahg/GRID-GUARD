// webapp/static/js/login.js
// ─────────────────────────────────────────────────────────────
// Login page — simple UX enhancements
// ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {

  const form     = document.querySelector('.login-form');
  const btn      = document.querySelector('.btn-login');
  const emailInp = document.getElementById('email');
  const passInp  = document.getElementById('password');

  // Auto-focus email field
  if (emailInp) emailInp.focus();

  // Button loading state on submit
  if (form) {
    form.addEventListener('submit', () => {
      btn.textContent = 'Authenticating...';
      btn.disabled    = true;
      btn.style.opacity = '0.7';
    });
  }

  // Input glow on focus
  [emailInp, passInp].forEach(inp => {
    if (!inp) return;
    inp.addEventListener('focus', () => {
      inp.parentElement.style.filter = 'drop-shadow(0 0 6px rgba(0,198,255,0.2))';
    });
    inp.addEventListener('blur', () => {
      inp.parentElement.style.filter = '';
    });
  });

  // Demo credential quick-fill on click
  const hints = document.querySelectorAll('.login-box p[style*="mono"]');
  hints.forEach(hint => {
    hint.style.cursor = 'pointer';
    hint.title = 'Click to fill';
    hint.addEventListener('click', () => {
      const parts = hint.textContent.split(' / ');
      if (parts.length === 2 && emailInp && passInp) {
        emailInp.value = parts[0].trim();
        passInp.value  = parts[1].trim();
        emailInp.dispatchEvent(new Event('input'));
      }
    });
  });

});
