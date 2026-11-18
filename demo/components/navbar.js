/**
 * navbar.js — Componente de Barra de Navegação Superior (TopBar) Compartilhada
 * Injeta a barra padronizada em todas as páginas da demonstração da P2.
 */

const Navbar = (function () {
  return {
    render(options = {}) {
      const {
        brandTitle = 'Bookstore API &bull; Demonstração P2',
        brandSubtitle = 'Aluna: Roberta Souza &bull; Spec-Driven Development (SDD)',
        homeUrl = '../index.html',
        loginUrl = '01_login.html',
        targetElementId = null
      } = options;

      const isAuthed = Session.isAuthenticated();
      const role = Session.getRole();
      const user = Session.getUser();

      const roleBadgeHtml = isAuthed
        ? (role === 'ADMIN'
            ? `<span class="role-badge admin">🛡️ ADMIN</span>`
            : `<span class="role-badge seller">💼 SELLER</span>`)
        : `<span class="role-badge none">NÃO AUTENTICADO</span>`;

      const logoutBtnHtml = isAuthed
        ? `<button type="button" class="btn-logout" onclick="Navbar.logout('${loginUrl}')">🚪 Encerrar Sessão</button>`
        : '';

      const timerHtml = isAuthed
        ? `<div id="navbarTimerBadge" class="token-ttl-badge">TTL JWT: <span id="navbarTtlCountdown">15:00</span></div>`
        : '';

      const html = `
        <div class="topbar-brand">
          <a href="${homeUrl}" style="text-decoration:none; display:flex; align-items:center; gap:12px;">
            <span class="brand-icon">📚</span>
            <div>
              <div class="brand-title">${brandTitle}</div>
              <div class="brand-subtitle">${brandSubtitle}</div>
            </div>
          </a>
        </div>

        <div class="topbar-status-group">
          <div class="status-indicator" id="navbarApiStatus" title="Sonda real GET /health/ready">
            <span class="pulse-dot"></span>
            <span>API: CONECTANDO...</span>
          </div>

          ${timerHtml}
          <div>${roleBadgeHtml}</div>
          ${logoutBtnHtml}
        </div>
      `;

      let container;
      if (targetElementId) {
        container = document.getElementById(targetElementId);
      } else {
        container = document.querySelector('header.topbar');
        if (!container) {
          container = document.createElement('header');
          container.className = 'topbar';
          document.body.insertBefore(container, document.body.firstChild);
        }
      }

      container.innerHTML = html;

      // Sonda assíncrona ao vivo da saúde da API real (/health/ready)
      const apiUrl = Session.getApiUrl().replace(/\/$/, "");
      fetch(`${apiUrl}/health/ready`)
        .then(res => {
          const statusElem = document.getElementById('navbarApiStatus');
          if (statusElem) {
            if (res.ok) {
              statusElem.innerHTML = `<span class="pulse-dot"></span><span>API: PRONTA (200 OK)</span>`;
            } else {
              statusElem.innerHTML = `<span class="pulse-dot" style="background:#ef4444; box-shadow:none;"></span><span style="color:#fca5a5;">API: DEGRADADA (${res.status})</span>`;
            }
          }
        })
        .catch(() => {
          const statusElem = document.getElementById('navbarApiStatus');
          if (statusElem) {
            statusElem.innerHTML = `<span class="pulse-dot" style="background:#ef4444; box-shadow:none;"></span><span style="color:#fca5a5;">API: OFFLINE (PORTA 8000)</span>`;
          }
        });

      // Inicia temporizador se autenticado
      if (isAuthed) {
        const timerElem = document.getElementById('navbarTimerBadge');
        const countElem = document.getElementById('navbarTtlCountdown');

        Session.startTtlTimer((formatted, remaining) => {
          if (countElem) countElem.textContent = formatted;
          if (timerElem) {
            if (remaining <= 60) {
              timerElem.className = 'token-ttl-badge expired';
            } else if (remaining <= 300) {
              timerElem.className = 'token-ttl-badge warning';
            } else {
              timerElem.className = 'token-ttl-badge';
            }
          }
        });
      }
    },

    logout(redirectUrl = '01_login.html') {
      Session.clearSession();
      window.location.href = redirectUrl;
    }
  };
})();
