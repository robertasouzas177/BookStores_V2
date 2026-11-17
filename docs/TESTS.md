# TESTS.md — Plano de Testes da Bookstore API

## 1. Objetivo

Este documento define os cenários de teste da Bookstore API e estabelece os critérios de validação para:

- Contrato OpenAPI
- Regras de negócio
- Autenticação JWT
- Controle de acesso RBAC
- Programa de fidelidade
- Controle de estoque
- Persistência ORM
- RFC 9457
- Idempotência
- Cache e concorrência otimista

---

# 2. Escopo

Cobertura obrigatória:

- Auth
- Users
- Products
- Clients
- Sales
- Fidelidade
- Estoque
- ORM
- RFC 9457
- ETag
- Rate Limiting
- Health Checks
- Refresh Token Rotation

---

# 3. Testes de Autenticação

## AUTH-001 — Login válido

### Endpoint

```http
POST /api/v1/auth/login
```

### Resultado esperado

```http
200 OK
```

Retorna:

- accessToken
- refreshToken
- expiresIn
- refreshExpiresIn

---

## AUTH-002 — Senha inválida

### Resultado esperado

```http
401 Unauthorized
```

Código:

```text
INVALID_CREDENTIALS
```

---

## AUTH-003 — Usuário inexistente

### Resultado esperado

```http
401 Unauthorized
```

---

## AUTH-004 — Token ausente

### Endpoint

```http
GET /api/v1/auth/me
```

### Resultado esperado

```http
401 Unauthorized
```

---

## AUTH-005 — Token expirado

### Resultado esperado

```http
401 Unauthorized
```

Código:

```text
AUTH_TOKEN_EXPIRED
```

---

## AUTH-006 — Refresh Token válido

### Endpoint

```http
POST /api/v1/auth/refresh
```

### Resultado esperado

```http
200 OK
```

Novo access token emitido.

---

## AUTH-007 — Refresh Token inválido

### Resultado esperado

```http
401 Unauthorized
```

---

## AUTH-008 — Logout

### Endpoint

```http
POST /api/v1/auth/logout
```

### Resultado esperado

```http
204 No Content
```

---

## AUTH-009 — Perfil autenticado

### Endpoint

```http
GET /api/v1/auth/me
```

### Resultado esperado

```http
200 OK
```

---

## AUTH-010 — Reutilização de Refresh Token

### Objetivo

Validar rotação obrigatória de refresh tokens.

### Resultado esperado

```http
401 Unauthorized
```

Código:

```text
REFRESH_TOKEN_REUSED
```

---

# 4. Testes RBAC

## RBAC-001 — ADMIN acessando recurso administrativo

### Resultado esperado

```http
200 OK
```

---

## RBAC-002 — SELLER acessando recurso administrativo

### Resultado esperado

```http
403 Forbidden
```

---

## RBAC-003 — Usuário não autenticado

### Resultado esperado

```http
401 Unauthorized
```

---

# 5. Testes de Usuários

## USER-001 — Criar usuário

```http
POST /api/v1/users
```

Resultado:

```http
201 Created
```

---

## USER-002 — Consultar usuário

```http
GET /api/v1/users/{id}
```

Resultado:

```http
200 OK
```

---

## USER-003 — Atualizar usuário

```http
PATCH /api/v1/users/{id}
```

Resultado:

```http
200 OK
```

---

## USER-004 — Inativar usuário

### Cenário

Atualizar:

```json
{
  "active": false
}
```

Resultado:

```http
200 OK
```

---

## USER-005 — Usuário inexistente

Resultado:

```http
404 Not Found
```

---

# 6. Testes de Produtos

## PROD-001 — Criar produto

Resultado:

```http
201 Created
```

---

## PROD-002 — Consultar produto

Resultado:

```http
200 OK
```

---

## PROD-003 — Atualizar produto

Resultado:

```http
200 OK
```

---

## PROD-004 — Excluir produto

Resultado:

```http
204 No Content
```

---

## PROD-005 — Produto inexistente

Resultado:

```http
404 Not Found
```

---

## PROD-006 — Código obrigatório

### Validar campo

```text
code
```

Resultado:

```http
422 Validation Error
```

quando ausente.

---

## PROD-007 — ISBN inválido

Resultado:

```http
422 Validation Error
```

---

## PROD-008 — Estoque negativo

Resultado:

```http
422 Validation Error
```

---

## PROD-009 — Produto vinculado a vendas

Resultado:

```http
409 Conflict
```

Código:

```text
RESOURCE_IN_USE
```

---

# 7. Testes de Clientes

## CLIENT-001 — Criar cliente

Resultado:

```http
201 Created
```

---

## CLIENT-002 — Atualizar cliente

Resultado:

```http
200 OK
```

---

## CLIENT-003 — Excluir cliente

Resultado:

```http
204 No Content
```

---

## CLIENT-004 — Cliente inexistente

Resultado:

```http
404 Not Found
```

---

## CLIENT-005 — CPF obrigatório

Resultado:

```http
422 Validation Error
```

---

## CLIENT-006 — Data de nascimento obrigatória

Resultado:

```http
422 Validation Error
```

---

## CLIENT-007 — Histórico de vendas do cliente

### Endpoint

```http
GET /api/v1/clients/{clientId}/sales
```

Resultado:

```http
200 OK
```

---

# 8. Testes de Fidelidade

## LOYALTY-001 — Acúmulo de pontos

### Cenário

Registrar venda válida.

### Resultado esperado

```text
+10 pontos
```

---

## LOYALTY-002 — Cliente atinge 100 pontos

### Resultado esperado

```text
Elegível para desconto de 10%
```

---

## LOYALTY-003 — Aplicar desconto

### Resultado esperado

Campo:

```text
discount
```

maior que zero.

---

## LOYALTY-004 — Atualização da pontuação

### Resultado esperado

Pontuação persistida corretamente.

---

# 9. Testes de Vendas

## SALE-001 — Registrar venda válida

### Endpoint

```http
POST /api/v1/sales
```

Resultado:

```http
201 Created
```

---

## SALE-002 — Cliente obrigatório

### Cenário

Criar venda sem clientId.

Resultado:

```http
422 Validation Error
```

---

## SALE-003 — Vendedor obrigatório

### Resultado esperado

Venda associada ao seller autenticado.

---

## SALE-004 — Venda sem itens

Resultado:

```http
422 Validation Error
```

---

## SALE-005 — Consultar venda

Resultado:

```http
200 OK
```

---

## SALE-006 — PATCH em vendas

### Endpoint inexistente

Resultado:

```http
405 Method Not Allowed
```

---

## SALE-007 — DELETE em vendas

### Endpoint inexistente

Resultado:

```http
405 Method Not Allowed
```

---

## SALE-008 — Cálculo financeiro

Validar:

```text
grossTotal

discount

finalTotal
```

---

## SALE-009 — Idempotência

### Reutilizar mesmo

```http
Idempotency-Key
```

### Resultado esperado

Venda não duplicada.

Header:

```http
Idempotency-Replayed
```

---

# 10. Testes de Itens da Venda

## ITEM-001 — Item embutido na venda

Validar estrutura:

```json
{
  "items": []
}
```

---

## ITEM-002 — Quantidade inválida

Resultado:

```http
422 Validation Error
```

---

## ITEM-003 — Produto inexistente

Resultado:

```http
404 Not Found
```

---

## ITEM-004 — Snapshot do preço

Validar:

```text
unitPrice
```

registrado no momento da venda.

---

# 11. Testes de Estoque

## STOCK-001 — Reduzir estoque após venda

Resultado:

Estoque atualizado.

---

## STOCK-002 — Estoque insuficiente

Resultado:

```http
409 Conflict
```

Código:

```text
INSUFFICIENT_STOCK
```

---

## STOCK-003 — Impedir estoque negativo

Resultado:

Operação bloqueada.

---

## STOCK-004 — Concorrência

Validar atualização simultânea de estoque.

---

# 12. Testes ORM

## ORM-001

```text
User 1:N Sales
```

---

## ORM-002

```text
Client 1:N Sales
```

---

## ORM-003

```text
Sale 1:N SaleItems
```

---

## ORM-004

```text
Product 1:N SaleItems
```

---

## ORM-005

Integridade referencial preservada.

---

# 13. Testes RFC 9457

Todos os erros devem validar:

```json
{
  "type": "",
  "title": "",
  "status": 0,
  "detail": "",
  "instance": "",
  "code": ""
}
```

---

## ERROR-001

```http
400 Bad Request
```

---

## ERROR-002

```http
401 Unauthorized
```

---

## ERROR-003

```http
403 Forbidden
```

---

## ERROR-004

```http
404 Not Found
```

---

## ERROR-005

```http
409 Conflict
```

---

## ERROR-006

```http
412 Precondition Failed
```

---

## ERROR-007

```http
422 Validation Error
```

Validar:

```json
invalidParams
```

---

## ERROR-008

```http
429 Too Many Requests
```

---

# 14. Testes de Cache e Concorrência

## CONC-001 — ETag

### Resultado esperado

```http
304 Not Modified
```

---

## CONC-002 — If-Match

### Resultado esperado

```http
412 Precondition Failed
```

---

# 15. Testes de Health Check

## HEALTH-001

```http
GET /health/live
```

Resultado:

```http
200 OK
```

---

## HEALTH-002

```http
GET /health/ready
```

Resultado:

```http
200 OK
```

ou

```http
503 Service Unavailable
```

quando dependências estiverem indisponíveis.

---

# 16. Critérios de Aceite

A Bookstore API somente será considerada validada quando:

- Todos os testes executarem com sucesso.
- A implementação respeitar o OpenAPI.
- A implementação respeitar o SPEC.md.
- A implementação respeitar o STYLEGUIDE.md.
- Todos os erros seguirem RFC 9457.
- JWT, RBAC, Fidelidade, Estoque, ETag, Idempotency-Key e Rate Limiting estiverem funcionando conforme especificado.