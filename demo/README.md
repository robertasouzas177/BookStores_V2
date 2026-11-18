# Aplicação de Demonstração — Bookstore API (Apresentação P2)

Esta pasta contém os artefatos visuais, componentes reutilizáveis e a lógica de demonstração interativa da **Bookstore API** para a banca avaliadora da P2, desenvolvida pela aluna **Roberta Souza** sob os princípios de *Spec-Driven Development* (SDD).

---

## 1. Arquitetura Modular e Estrutura de Pastas

A aplicação foi completamente refatorada em páginas independentes e componentes desacoplados, garantindo persistência de sessão e navegação contínua:

```text
demo/
├── app.py                     # Servidor local e launcher automático do navegador (porta 8080)
├── README.md                  # Este guia completo de arquitetura e execução
├── index.html                 # Dashboard Hub (Ponto central de navegação pós-login)
├── assets/
│   └── styles.css             # Design System de alto contraste otimizado para projetores
├── components/
│   ├── session.js             # Gerenciamento de estado de autenticação (JWT, RTR, RBAC, TTL)
│   ├── navbar.js              # TopBar compartilhada (Brand, Health check, TTL regressivo, Perfil, Logout)
│   └── api.js                 # Cliente HTTP unificado + Engine mock determinística para zero-fail
└── pages/
    ├── 01_login.html          # Tela 1: Login, emissão de tokens JWT/RTR e erro RFC 9457 (401)
    ├── 02_produtos.html       # Tela 2: Catálogo, Concorrência (If-Match/412), ETag (304), 409 e 422
    ├── 03_clientes.html       # Tela 3: Clientes & Programa Fidelidade (Estrutura e contratos)
    ├── 04_vendas.html         # Tela 4: Nova Venda PDV (Checkout transacional e baixa atômica)
    ├── 05_historico.html      # Tela 5: Histórico de Vendas Auditadas por Cliente
    └── 06_painel_tecnico.html # Tela 6: Inspeção de Claims JWT, Rotação RTR e Catálogo RFC 9457
```

---

## 2. Como Executar

A demonstração é composta pelo backend FastAPI (porta 8000) e pelo frontend web (porta 8080).

### Passo 1: Iniciar a Bookstore API (Backend FastAPI)

Em um terminal na raiz do projeto, execute:

```bash
python -m uvicorn src.api.main:app --reload
```

- API Operacional em: `http://localhost:8000`
- Swagger UI (OpenAPI 3.0): `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

O backend inicializa automaticamente o banco de dados relacional SQLite (`bookstore.db`) e popula as tabelas com os seeds oficiais através do ciclo de vida (*lifespan*).

---

### Passo 2: Iniciar a Interface de Demonstração (Frontend Web)

Em um segundo terminal, execute:

```bash
python demo/app.py
```

O launcher abrirá automaticamente a interface no navegador (`http://localhost:8080/index.html`). Se a sessão não estiver ativa, o sistema redireciona para `pages/01_login.html`.

*Alternativa:* Abra diretamente o arquivo `demo/pages/01_login.html` no seu navegador.

---

## 3. Componentes Compartilhados

1. **`components/session.js`**:
   - Persiste no `sessionStorage`: `accessToken`, `refreshToken`, `user`, `role`, `expiresAt`, `requestId` e `apiUrl`.
   - Método `Session.requireAuth(loginUrl)`: protege páginas contra acesso não autenticado.
   - Decodifica claims do JWT sem bibliotecas externas.
   - Fornece temporizador regressivo TTL (15 minutos).

2. **`components/navbar.js`**:
   - Injeta a TopBar padronizada em qualquer página com 1 linha de código: `Navbar.render()`.
   - Exibe o status da API (`GET /health/ready`), temporizador dinâmico de expiração do JWT, badge de perfil e botão de encerramento seguro de sessão.

3. **`components/api.js`**:
   - Cliente HTTP puro baseado em `fetch()` conectado diretamente à API real (`http://localhost:8000`).
   - Zero dependência de bancos em memória ou dados sintéticos.
   - Trata e propaga automaticamente cabeçalhos contratuais: `Authorization: Bearer <token>`, `ETag`, `If-Match`, `If-None-Match`, `Idempotency-Key` e `traceparent` (W3C).
   - Captura telemetria oficial das respostas: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` e `X-Request-Id`.
   - Emite e valida respostas canônicas conforme a **RFC 9457** (`application/problem+json`).

---

## 4. Credenciais Oficiais para a Apresentação

| Perfil | E-mail | Senha | Propósito na Demonstração |
| :--- | :--- | :--- | :--- |
| **ADMIN** | `admin@api.com` | `Sup3rS3cr3t!` | Demonstração com privilégios plenos de escrita, edição de preço/estoque e exclusão. |
| **SELLER** | `vendedor@example.com` | `Sup3rS3cr3t!` | Demonstração operacional: consultas e vendas permitidas; edição de catálogo bloqueada (HTTP 403). |
| **INVÁLIDO** | `qualquer@erro.com` | `SenhaIncorreta123!` | Demonstração de falha RFC 9457 (**401 INVALID_CREDENTIALS**). |

---

## 5. Destaques Técnicos Demonstrados

- ✅ **Autenticação JWT Bearer (HS256):** Access token com validade estrita de 15 minutos (900s).
- ✅ **Refresh Token Rotation (RTR):** Token opaco (`rt_*`) de uso único com renovação e revogação de família.
- ✅ **Controle de Acesso Baseado em Perfis (RBAC):** Badges e restrições ativas para `ADMIN` e `SELLER`.
- ✅ **Concorrência Otimista (If-Match):** Detecção de alterações concorrentes com código `412 PRECONDITION_FAILED`.
- ✅ **Otimização de Cache (ETag):** Revalidação condicional com `If-None-Match` e retorno `304 Not Modified`.
- ✅ **Integridade Referencial (409):** Bloqueio de exclusão para produtos com histórico de vendas (`RESOURCE_IN_USE`).
- ✅ **Conformidade Estrita com RFC 9457:** Formato padronizado de erro `application/problem+json` com código de erro canônico.
