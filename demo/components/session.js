/**
 * session.js — Gerenciador de Estado de Autenticação e Sessão (Bookstore API)
 * Centraliza tokens JWT, Refresh Token, claims e temporizador TTL no sessionStorage.
 */

const Session = (function () {
  const KEYS = {
    ACCESS_TOKEN: 'bookstore_access_token',
    REFRESH_TOKEN: 'bookstore_refresh_token',
    USER: 'bookstore_user',
    ROLE: 'bookstore_role',
    EXPIRES_AT: 'bookstore_expires_at',
    REQUEST_ID: 'bookstore_request_id',
    API_URL: 'bookstore_api_url',
    SELECTED_CLIENT: 'bookstore_selected_client',
    DRAFT_SALE: 'bookstore_draft_sale',
    LAST_SALE: 'bookstore_last_sale'
  };

  function decodeJwt(token) {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      return null;
    }
  }

  return {
    saveSession({ accessToken, refreshToken, user, role, expiresIn = 900, requestId, apiUrl }) {
      if (accessToken) sessionStorage.setItem(KEYS.ACCESS_TOKEN, accessToken);
      if (refreshToken) sessionStorage.setItem(KEYS.REFRESH_TOKEN, refreshToken);
      if (user) sessionStorage.setItem(KEYS.USER, JSON.stringify(user));

      // Resolve role a partir do user, token ou fallback
      let resolvedRole = role;
      if (!resolvedRole && accessToken) {
        const claims = decodeJwt(accessToken);
        if (claims && claims.role) resolvedRole = claims.role;
      }
      if (!resolvedRole && user && user.role) resolvedRole = user.role;
      if (resolvedRole) sessionStorage.setItem(KEYS.ROLE, resolvedRole);

      const expiresAt = Date.now() + expiresIn * 1000;
      sessionStorage.setItem(KEYS.EXPIRES_AT, expiresAt.toString());

      if (requestId) sessionStorage.setItem(KEYS.REQUEST_ID, requestId);
      if (apiUrl) sessionStorage.setItem(KEYS.API_URL, apiUrl);
    },

    clearSession() {
      sessionStorage.removeItem(KEYS.ACCESS_TOKEN);
      sessionStorage.removeItem(KEYS.REFRESH_TOKEN);
      sessionStorage.removeItem(KEYS.USER);
      sessionStorage.removeItem(KEYS.ROLE);
      sessionStorage.removeItem(KEYS.EXPIRES_AT);
      sessionStorage.removeItem(KEYS.REQUEST_ID);
      sessionStorage.removeItem(KEYS.SELECTED_CLIENT);
      sessionStorage.removeItem(KEYS.DRAFT_SALE);
      sessionStorage.removeItem(KEYS.LAST_SALE);
    },

    isAuthenticated() {
      const token = sessionStorage.getItem(KEYS.ACCESS_TOKEN);
      const expiresAt = parseInt(sessionStorage.getItem(KEYS.EXPIRES_AT) || '0', 10);
      return Boolean(token && Date.now() < expiresAt);
    },

    requireAuth(loginRedirectUrl = '01_login.html') {
      if (!this.isAuthenticated()) {
        window.location.href = loginRedirectUrl;
        return false;
      }
      return true;
    },

    getAccessToken() {
      return sessionStorage.getItem(KEYS.ACCESS_TOKEN);
    },

    getRefreshToken() {
      return sessionStorage.getItem(KEYS.REFRESH_TOKEN);
    },

    getUser() {
      const u = sessionStorage.getItem(KEYS.USER);
      if (!u) return null;
      try { return JSON.parse(u); } catch { return null; }
    },

    getRole() {
      return sessionStorage.getItem(KEYS.ROLE) || 'SELLER';
    },

    getRequestId() {
      return sessionStorage.getItem(KEYS.REQUEST_ID) || '8NV1c7Q4TCYGcsuPch8I';
    },

    setRequestId(id) {
      if (id) sessionStorage.setItem(KEYS.REQUEST_ID, id);
    },

    getApiUrl() {
      return sessionStorage.getItem(KEYS.API_URL) || 'http://localhost:8000';
    },

    decodeJwt(token) {
      return decodeJwt(token);
    },

    getJwtClaims() {
      const token = this.getAccessToken();
      return token ? decodeJwt(token) : null;
    },

    getTimeRemainingSeconds() {
      const expiresAt = parseInt(sessionStorage.getItem(KEYS.EXPIRES_AT) || '0', 10);
      const remaining = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
      return remaining;
    },

    setSelectedClient(client) {
      if (client) sessionStorage.setItem(KEYS.SELECTED_CLIENT, JSON.stringify(client));
    },

    getSelectedClient() {
      const data = sessionStorage.getItem(KEYS.SELECTED_CLIENT);
      if (!data) return null;
      try { return JSON.parse(data); } catch { return null; }
    },

    clearSelectedClient() {
      sessionStorage.removeItem(KEYS.SELECTED_CLIENT);
    },

    setDraftSale(sale) {
      if (sale) sessionStorage.setItem(KEYS.DRAFT_SALE, JSON.stringify(sale));
    },

    getDraftSale() {
      const data = sessionStorage.getItem(KEYS.DRAFT_SALE);
      if (!data) return null;
      try { return JSON.parse(data); } catch { return null; }
    },

    clearDraftSale() {
      sessionStorage.removeItem(KEYS.DRAFT_SALE);
    },

    setLastSale(sale) {
      if (sale) sessionStorage.setItem(KEYS.LAST_SALE, JSON.stringify(sale));
    },

    getLastSale() {
      const data = sessionStorage.getItem(KEYS.LAST_SALE);
      if (!data) return null;
      try { return JSON.parse(data); } catch { return null; }
    },

    clearLastSale() {
      sessionStorage.removeItem(KEYS.LAST_SALE);
    },

    startTtlTimer(callback) {
      function tick() {
        const total = Session.getTimeRemainingSeconds();
        const mins = Math.floor(total / 60);
        const secs = total % 60;
        const formatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        callback(formatted, total);
      }
      tick();
      return setInterval(tick, 1000);
    }
  };
})();
