/**
 * api.js — Cliente HTTP Centralizado e Puro da Bookstore API
 * 
 * Conexão direta e exclusiva com a API FastAPI real.
 * Não utiliza nenhum banco em memória, mock ou dado artificial.
 * Transmite e captura cabeçalhos contratuais:
 * - Authorization (Bearer JWT)
 * - ETag / If-None-Match (HTTP 304)
 * - If-Match (HTTP 412 Concorrência Otimista)
 * - Idempotency-Key / Idempotency-Replayed
 * - X-Request-Id / traceparent (W3C Trace Context)
 * - RateLimit-Limit / RateLimit-Remaining / RateLimit-Reset
 */

const Api = (function () {
  // Últimos cabeçalhos de telemetria capturados das respostas reais da API
  let lastTelemetry = {
    requestId: null,
    traceparent: null,
    rateLimitLimit: "100",
    rateLimitRemaining: "100",
    rateLimitReset: "60",
    lastEtag: null
  };

  function getBaseUrl() {
    return (Session.getApiUrl() || "http://localhost:8000").replace(/\/$/, "");
  }

  function generateUUID() {
    if (crypto && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  function generateTraceparent() {
    const traceId = Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
    const parentId = Array.from({ length: 16 }, () => Math.floor(Math.random() * 16).toString(16)).join('');
    return `00-${traceId}-${parentId}-01`;
  }

  async function request(path, options = {}) {
    const baseUrl = getBaseUrl();
    const url = `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;

    const headers = {
      'Accept': 'application/json',
      ...options.headers
    };

    // Anexa token Bearer caso não seja rota pública de autenticação
    const token = Session.getAccessToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Propaga W3C Trace Context e Request-Id
    if (!headers['X-Request-Id']) {
      headers['X-Request-Id'] = generateUUID();
    }
    if (!headers['traceparent']) {
      headers['traceparent'] = generateTraceparent();
    }

    try {
      const res = await fetch(url, {
        method: options.method || 'GET',
        headers: headers,
        body: options.body !== undefined ? options.body : null
      });

      // Captura de cabeçalhos de observabilidade oficiais
      const reqId = res.headers.get('X-Request-Id') || headers['X-Request-Id'];
      const etag = res.headers.get('ETag');
      const rlLimit = res.headers.get('RateLimit-Limit');
      const rlRemaining = res.headers.get('RateLimit-Remaining');
      const rlReset = res.headers.get('RateLimit-Reset');
      const idempReplayed = res.headers.get('Idempotency-Replayed') === 'true';

      lastTelemetry = {
        requestId: reqId,
        traceparent: res.headers.get('traceparent') || headers['traceparent'],
        rateLimitLimit: rlLimit || lastTelemetry.rateLimitLimit,
        rateLimitRemaining: rlRemaining || lastTelemetry.rateLimitRemaining,
        rateLimitReset: rlReset || lastTelemetry.rateLimitReset,
        lastEtag: etag || lastTelemetry.lastEtag
      };

      Session.setRequestId(reqId);

      // Tratamento de respostas vazias (204 No Content, 304 Not Modified)
      if (res.status === 204) {
        return { ok: true, status: 204, data: null, requestId: reqId, etag, rateLimit: lastTelemetry };
      }
      if (res.status === 304) {
        return { ok: true, status: 304, data: null, notModified: true, requestId: reqId, etag, rateLimit: lastTelemetry };
      }

      const contentType = res.headers.get('content-type') || '';
      let json = null;
      if (contentType.includes('json') || contentType.includes('problem+json')) {
        json = await res.json().catch(() => null);
      }

      if (res.ok) {
        return {
          ok: true,
          status: res.status,
          data: json,
          etag,
          requestId: reqId,
          idempotencyReplayed: idempReplayed,
          location: res.headers.get('Location'),
          rateLimit: lastTelemetry
        };
      } else {
        return {
          ok: false,
          status: res.status,
          error: json || {
            type: "https://api.bookstore.dev/errors/internal-error",
            title: "Erro HTTP",
            status: res.status,
            detail: "Falha na comunicação com o servidor.",
            code: "HTTP_ERROR"
          },
          etag,
          requestId: reqId,
          rateLimit: lastTelemetry
        };
      }
    } catch (networkErr) {
      return {
        ok: false,
        status: 0,
        error: {
          type: "https://api.bookstore.dev/errors/network-error",
          title: "Falha de Rede",
          status: 0,
          detail: `Não foi possível conectar ao servidor em '${url}'. Certifique-se de que a Bookstore API está rodando.`,
          code: "NETWORK_ERROR"
        },
        requestId: headers['X-Request-Id'],
        rateLimit: lastTelemetry
      };
    }
  }

  function validateCPF(cpf) {
    const clean = String(cpf || '').replace(/\D/g, '');
    if (clean.length !== 11) return false;
    if (/^(\d)\1{10}$/.test(clean)) return false;
    let sum = 0;
    for (let i = 0; i < 9; i++) sum += parseInt(clean.charAt(i), 10) * (10 - i);
    let rev = 11 - (sum % 11);
    if (rev === 10 || rev === 11) rev = 0;
    if (rev !== parseInt(clean.charAt(9), 10)) return false;
    sum = 0;
    for (let i = 0; i < 10; i++) sum += parseInt(clean.charAt(i), 10) * (11 - i);
    rev = 11 - (sum % 11);
    if (rev === 10 || rev === 11) rev = 0;
    if (rev !== parseInt(clean.charAt(10), 10)) return false;
    return true;
  }

  return {
    validateCPF,
    generateUUID,
    getTelemetry: () => ({ ...lastTelemetry }),

    computeProductETag(p) {
      if (!p) return 'W/"stale"';
      if (p._etag) return p._etag;
      let hash = 0;
      const str = `${p.id}:${p.title}:${p.author}:${p.isbn}:${p.code}:${p.price}:${p.stock}`;
      for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
      }
      return `W/"${Math.abs(hash).toString(16)}"`;
    },

    computeClientETag(c) {
      if (!c) return 'W/"stale"';
      if (c._etag) return c._etag;
      let hash = 0;
      const pts = c.loyaltyPoints !== undefined ? c.loyaltyPoints : (c.loyalty_points !== undefined ? c.loyalty_points : 0);
      const str = `${c.id}:${c.name}:${c.email}:${c.cpf}:${pts}:${c.active}`;
      for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
      }
      return `W/"${Math.abs(hash).toString(16)}"`;
    },

    // ========================================================================
    // AUTENTICAÇÃO (/api/v1/auth)
    // ========================================================================
    async login(email, password) {
      const res = await request('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      return res;
    },

    async refreshToken(refreshToken) {
      const res = await request('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken })
      });
      return res;
    },

    async logout(refreshToken) {
      return request('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken })
      });
    },

    async getMe() {
      return request('/api/v1/auth/me');
    },

    // ========================================================================
    // DASHBOARD & MÉTRICAS (Consome Endpoints e Headers Reais)
    // ========================================================================
    async getDashboardStats() {
      // Executa consultas paralelas aos metadados paginados de cada coleção real
      const [prodRes, clientRes, salesRes] = await Promise.all([
        request('/api/v1/products?limit=1'),
        request('/api/v1/clients?limit=1'),
        request('/api/v1/sales?limit=1')
      ]);

      const booksCount = (prodRes.ok && prodRes.data && prodRes.data.meta) ? prodRes.data.meta.totalItems : 0;
      const clientsCount = (clientRes.ok && clientRes.data && clientRes.data.meta) ? clientRes.data.meta.totalItems : 0;
      const salesCount = (salesRes.ok && salesRes.data && salesRes.data.meta) ? salesRes.data.meta.totalItems : 0;

      const telemetry = lastTelemetry;
      const rlLimit = telemetry.rateLimitLimit || "100";
      const rlRem = telemetry.rateLimitRemaining || "100";
      const rlReset = telemetry.rateLimitReset ? `${telemetry.rateLimitReset}s` : "60s";

      return {
        booksCount,
        clientsCount,
        salesCount,
        rateLimitRemaining: `${rlRem}/${rlLimit}`,
        rateLimitReset: rlReset,
        productsEtag: prodRes.etag || null
      };
    },

    // ========================================================================
    // PRODUTOS & CATÁLOGO (/api/v1/products)
    // ========================================================================
    async getProducts({ page = 1, limit = 10, search = '', inStock = null, sort = null, ifNoneMatch = null } = {}) {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('limit', limit);
      if (search) params.append('search', search);
      if (inStock !== null && inStock !== undefined && inStock !== '') {
        params.append('inStock', inStock);
      }
      if (sort) params.append('sort', sort);

      const headers = {};
      if (ifNoneMatch) headers['If-None-Match'] = ifNoneMatch;

      return request(`/api/v1/products?${params.toString()}`, { headers });
    },

    async getProductById(id, ifNoneMatch = null) {
      const headers = {};
      if (ifNoneMatch) headers['If-None-Match'] = ifNoneMatch;
      return request(`/api/v1/products/${encodeURIComponent(id)}`, { headers });
    },

    async updateProduct(id, payload, ifMatch = null) {
      const headers = { 'Content-Type': 'application/json' };
      if (ifMatch) headers['If-Match'] = ifMatch;

      return request(`/api/v1/products/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(payload)
      });
    },

    async deleteProduct(id, ifMatch = null) {
      const headers = {};
      if (ifMatch) headers['If-Match'] = ifMatch;
      return request(`/api/v1/products/${encodeURIComponent(id)}`, {
        method: 'DELETE',
        headers
      });
    },

    // ========================================================================
    // CLIENTES & FIDELIDADE (/api/v1/clients)
    // ========================================================================
    async getClients({ page = 1, limit = 10, search = '', ifNoneMatch = null } = {}) {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('limit', limit);
      if (search) params.append('search', search);

      const headers = {};
      if (ifNoneMatch) headers['If-None-Match'] = ifNoneMatch;

      return request(`/api/v1/clients?${params.toString()}`, { headers });
    },

    async getClientById(id, ifNoneMatch = null) {
      const headers = {};
      if (ifNoneMatch) headers['If-None-Match'] = ifNoneMatch;
      return request(`/api/v1/clients/${encodeURIComponent(id)}`, { headers });
    },

    async createClient(payload) {
      return request('/api/v1/clients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    },

    async updateClient(id, payload, ifMatch = null) {
      const headers = { 'Content-Type': 'application/json' };
      if (ifMatch) headers['If-Match'] = ifMatch;

      return request(`/api/v1/clients/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(payload)
      });
    },

    async deleteClient(id, ifMatch = null) {
      const headers = {};
      if (ifMatch) headers['If-Match'] = ifMatch;
      return request(`/api/v1/clients/${encodeURIComponent(id)}`, {
        method: 'DELETE',
        headers
      });
    },

    async deleteUser(id, ifMatch = null) {
      const headers = {};
      if (ifMatch) headers['If-Match'] = ifMatch;
      return request(`/api/v1/users/${encodeURIComponent(id)}`, {
        method: 'DELETE',
        headers
      });
    },

    // ========================================================================
    // VENDAS (PDV & CHECKOUT) (/api/v1/sales)
    // ========================================================================
    async createSale(payload, idempotencyKey = null) {
      const headers = { 'Content-Type': 'application/json' };
      if (idempotencyKey) {
        headers['Idempotency-Key'] = idempotencyKey;
      }

      return request('/api/v1/sales', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });
    },

    // ========================================================================
    // HISTÓRICO DE COMPRAS (/api/v1/clients/{clientId}/sales)
    // ========================================================================
    async getClientSales(clientId, { page = 1, limit = 10, sort = null, ifNoneMatch = null } = {}) {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('limit', limit);
      if (sort) params.append('sort', sort);

      const headers = {};
      if (ifNoneMatch) headers['If-None-Match'] = ifNoneMatch;

      return request(`/api/v1/clients/${encodeURIComponent(clientId)}/sales?${params.toString()}`, { headers });
    }
  };
})();
