# STYLEGUIDE.md — Constituição Técnica (Bookstore API)

## 1. Objetivo

Este documento define as regras técnicas obrigatórias da Bookstore API.

Todos os artefatos produzidos pelos agentes de IA devem respeitar integralmente este documento, o contrato OpenAPI da API e os requisitos descritos em SPEC.md.

---

# 2. Stack Tecnológica

## Aplicação Original

A aplicação Bookstore foi originalmente desenvolvida utilizando:

- Firebase Firestore
- Firebase Authentication
- Firebase Hosting

Esta implementação publicada é a principal referência funcional do sistema.

---

## Arquitetura de Referência Acadêmica

Para fins de modelagem, documentação e geração de código orientada por SDD:

### Linguagem

```text
Python 3.12+
```

### Framework

```text
FastAPI
```

### Validação

```text
Pydantic v2
```

### Persistência

```text
SQLAlchemy 2.0
```

### Banco

```text
SQLite
```

### Segurança

```text
JWT
PyJWT
```

### Testes

```text
pytest
httpx
fastapi.testclient
```

---

# 3. Organização do Projeto

```text
README.md

docs/
├── AGENTS.md
├── STYLEGUIDE.md
├── SPEC.md
├── PLAN.md
├── TESTS.md
├── AI_WORKFLOW.md
└── ai-evidence/

apidog/
└── Bookstore API.openapi.yaml

src/api/
├── schemas.py
├── models.py
├── database.py
├── security.py
├── exceptions.py
├── routers/
└── tests/

demo/
├── app.py
├── README.md
├── index.html
├── assets/
├── components/
└── pages/
    ├── 01_login.html
    ├── 02_produtos.html
    ├── 03_clientes.html
    ├── 04_vendas.html
    ├── 05_historico.html
    └── 06_painel_tecnico.html
```

---

# 4. Contrato Oficial

A fonte oficial de verdade do projeto é:

```text
apidog/Bookstore API.openapi.yaml
```

Todos os agentes devem respeitar:

- Endpoints
- Schemas
- Status Codes
- Headers
- Exemplos
- Regras de autenticação
- Regras de negócio

Nenhuma rota pode ser criada fora do contrato.

---

# 5. Entidades Oficiais

As entidades do sistema são:

```text
Users
Products
Clients
Sales
SaleItems
```

---

# 6. Relacionamentos

```text
User 1:N Sales

Client 1:N Sales

Sale 1:N SaleItems

Product 1:N SaleItems
```

Observação:

```text
SaleItems existe como entidade ORM.

Na API pública os itens permanecem embutidos
no recurso Sale conforme o contrato OpenAPI.
```

---

# 7. Convenções de Nomenclatura

## JSON

Todos os payloads devem utilizar:

```text
camelCase
```

Exemplos:

```json
createdAt
updatedAt
clientId
sellerId
grossTotal
finalTotal
loyaltyPoints
```

---

## Python

Todo código Python deve utilizar:

```text
snake_case
```

Exemplos:

```python
created_at
updated_at
client_id
seller_id
gross_total
final_total
```

---

# 8. Identificadores

## Identificadores de Negócio

A API utiliza IDs originados do Firestore.

Exemplos:

```text
8NV1c7Q4TCYGcsuPch8I

KIYBXACS6uVj5DbKEsPQ

SDMXDsjJtqcqK1nWnrk0YjQDqPY2
```

Portanto:

```text
NÃO utilizar UUID como identificador principal
das entidades de negócio.
```

Os IDs devem ser modelados como:

```text
String
```

---

## UUID

UUIDs devem ser utilizados apenas para:

```text
X-Request-Id

Idempotency-Key
```

---

# 9. Versionamento

Todos os endpoints seguem o padrão:

```text
/api/v1
```

Exemplos:

```text
/api/v1/auth/login

/api/v1/users

/api/v1/products

/api/v1/clients

/api/v1/sales
```

---

# 10. Paginação

Coleções retornam:

```json
{
  "data": [],
  "meta": {}
}
```

Meta deve conter:

```json
{
  "page": 1,
  "limit": 10,
  "totalItems": 42,
  "totalPages": 5,
  "hasNext": true
}
```

---

# 11. Programa de Fidelidade

Regras obrigatórias:

- Todo cliente cadastrado participa do programa.
- Os pontos acumulados são armazenados em:

```text
loyaltyPoints
```

- Cada venda gera créditos de fidelidade.
- Ao atingir 100 pontos o cliente recebe desconto de 10%.
- O desconto utilizado é registrado em:

```text
discount
```

na venda.

---

# 12. Controle de Estoque

Regras obrigatórias:

- Não permitir estoque negativo.
- Toda venda reduz estoque.
- Produtos sem estoque não podem ser vendidos.
- Produtos vinculados a vendas históricas não podem ser removidos.

Quando não houver estoque:

```http
409 Conflict
```

Código:

```text
INSUFFICIENT_STOCK
```

---

# 13. Autenticação

A autenticação utiliza:

```text
JWT Bearer Token
```

Endpoints:

```text
POST /api/v1/auth/login

POST /api/v1/auth/refresh

POST /api/v1/auth/logout

GET /api/v1/auth/me
```

---

# 14. Controle de Acesso (RBAC)

Perfis válidos:

```text
ADMIN

SELLER
```

---

## ADMIN

Pode:

- Gerenciar usuários
- Gerenciar produtos
- Gerenciar clientes
- Consultar vendas
- Configurar o sistema

---

## SELLER

Pode:

- Consultar produtos
- Consultar clientes
- Registrar vendas
- Consultar vendas

---

# 15. RFC 9457

Todos os erros devem utilizar:

```http
application/problem+json
```

Estrutura:

```json
{
  "type": "",
  "title": "",
  "status": 0,
  "detail": "",
  "instance": "",
  "code": "",
  "invalidParams": []
}
```

---

# 16. Headers Avançados

## Cache

```http
ETag

If-None-Match
```

Suporte a:

```http
304 Not Modified
```

---

## Concorrência Otimista

```http
If-Match
```

Suporte a:

```http
412 Precondition Failed
```

---

## Idempotência

```http
Idempotency-Key
```

Utilizada no registro de vendas.

---

## Rastreabilidade

```http
X-Request-Id

traceparent
```

---

# 17. Rate Limiting

Modelo:

```text
Token Bucket
```

Capacidade:

```text
100 requisições
```

Janela:

```text
100 tokens por minuto
```

Retornos:

```http
429 Too Many Requests
```

Headers:

```http
RateLimit-Limit
RateLimit-Remaining
RateLimit-Reset
```

---

# 18. Health Checks

Endpoints obrigatórios:

```http
GET /health/live

GET /health/ready
```

---

# 19. Regras para Agentes

Todos os agentes devem seguir:

```text
AGENTS.md
STYLEGUIDE.md
SPEC.md
PLAN.md
apidog/Bookstore API.openapi.yaml
```

Fluxo obrigatório:

```text
Constitution
↓
Specify
↓
Plan
↓
Implement
↓
Validate
```

É proibido:

- Inventar entidades.
- Inventar rotas.
- Inventar campos.
- Ignorar o OpenAPI.
- Implementar funcionalidades não previstas na especificação.
