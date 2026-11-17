# 04-security-review.md

## Fase

Fase 4 — Segurança, JWT, RBAC e RFC 9457

## Persona

```text
[Backend Coder]
```

Implementação:

```text
src/api/security.py
src/api/exceptions.py
```

---

## Ferramenta Utilizada

```text
Google Antigravity Agentic Desktop Application
```

---

# Prompt de Implementação Utilizado

```text
Atuando como [Backend Coder], execute a Fase 4 do docs/PLAN.md.

Utilize obrigatoriamente:

- src/api/schemas.py
- src/api/models.py
- src/api/database.py
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
- docs/AGENTS.md

Crie os arquivos:

- src/api/security.py
- src/api/exceptions.py

Objetivo:

Implementar autenticação JWT, controle de acesso RBAC e tratamento padronizado de erros conforme RFC 9457.
```

---

# Objetivo da Fase

Implementar a camada completa de segurança da Bookstore API, incluindo:

- JWT
- Refresh Token Rotation
- RBAC
- RFC 9457
- Idempotência
- ETag
- If-Match
- If-None-Match
- X-Request-Id

---

# Arquivos Gerados

```text
src/api/security.py

src/api/exceptions.py
```

---

# Funcionalidades Implementadas

## JWT

Implementado:

- create_access_token()
- decode_access_token()

Algoritmo:

```text
HS256
```

Payload:

```json
{
  "sub": "<user_id>",
  "email": "<user_email>",
  "role": "ADMIN|SELLER",
  "iat": 1234567890,
  "exp": 1234567890
}
```

---

## Expiração

### Access Token

```text
900 segundos
(15 minutos)
```

---

### Refresh Token

```text
1.209.600 segundos
(14 dias)
```

---

# Refresh Token Rotation

Implementado:

```text
family_id
token_hash
expires_at
revoked
user_id
```

Funcionalidades:

- geração de refresh token opaco
- armazenamento apenas do hash SHA-256
- revogação de sessão
- rotação obrigatória
- detecção de reutilização

---

## Proteção Contra Replay

Foi implementado:

```text
REFRESH_TOKEN_REUSED
```

Fluxo:

1. Refresh Token utilizado
2. Refresh Token marcado como revogado
3. Novo Refresh Token emitido
4. Mesmo token reutilizado
5. Toda a família é invalidada
6. Retorno HTTP 401

---

# RBAC

Perfis suportados:

```text
ADMIN

SELLER
```

---

## Dependências FastAPI

Implementadas:

```python
get_current_user()

require_roles()
```

---

## Comportamentos

### 401 Unauthorized

Casos:

- token ausente
- token inválido
- token expirado
- usuário inativo

---

### 403 Forbidden

Casos:

- falta de permissão
- perfil insuficiente

Código:

```text
INSUFFICIENT_PERMISSIONS
```

---

# Segurança de Credenciais

Implementado:

```text
PBKDF2-HMAC-SHA256
```

Configuração:

```text
100.000 iterações
```

Proteções:

- salt aleatório
- hash seguro
- comparação via:

hmac.compare_digest()

---

# RFC 9457

Implementado:

```text
application/problem+json
```

---

## Estrutura ApiError

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

## Exception Hierarchy

Implementadas:

```text
BadRequestException

UnauthorizedException

ForbiddenException

NotFoundException

ConflictException

PreconditionFailedException

UnprocessableEntityException

TooManyRequestsException
```

---

## Status HTTP Cobertos

```text
400

401

403

404

409

412

422

429
```

---

# Códigos Contratuais

Implementados:

```text
INVALID_CREDENTIALS

AUTH_TOKEN_EXPIRED

AUTH_TOKEN_INVALID

AUTH_TOKEN_MISSING

USER_INACTIVE

REFRESH_TOKEN_REUSED

INSUFFICIENT_STOCK

RESOURCE_IN_USE

DUPLICATE_RESOURCE

IDEMPOTENCY_IN_PROGRESS

VALIDATION_FAILED
```

---

# Headers Avançados

## Cache

Implementado:

```text
ETag

If-None-Match
```

Suporte para:

```http
304 Not Modified
```

---

## Concorrência Otimista

Implementado:

```text
If-Match
```

Suporte para:

```http
412 Precondition Failed
```

---

## Idempotência

Implementado:

```text
Idempotency-Key
```

Funções:

```text
get_idempotent_response()

save_idempotent_response()
```

Preparado para:

```text
POST /api/v1/sales
```

---

## Rastreabilidade

Implementado:

```text
X-Request-Id

traceparent
```

Função:

```text
extract_request_id()
```

---

# Integração com a Persistência

Integração validada com:

```text
UserModel

RefreshTokenModel

SessionLocal

get_db()
```

---

# Revisão do Tech Lead

## Prompt Utilizado

```text
Atuando como [Tech Lead], execute uma revisão arquitetural completa dos arquivos:

- src/api/security.py
- src/api/exceptions.py

Utilize como fontes obrigatórias:

- OpenAPI
- SPEC
- STYLEGUIDE
- PLAN
- TESTS
- AGENTS
- schemas.py
- models.py
- database.py
```

---

# Resultado da Revisão

## Status

```text
✅ APROVADO
```

---

# Principais Verificações

### JWT

✅ geração

✅ validação

✅ expiração

✅ payload correto

---

### Refresh Tokens

✅ family_id

✅ token_hash

✅ revogação

✅ rotação

✅ reutilização

---

### RBAC

✅ ADMIN

✅ SELLER

✅ require_roles

✅ get_current_user

---

### RFC 9457

✅ application/problem+json

✅ code

✅ invalidParams

✅ handlers globais

---

### Segurança

✅ hashing seguro

✅ replay protection

✅ comparação resistente a timing attack

---

### Integração ORM

✅ UserModel

✅ RefreshTokenModel

✅ SessionLocal

✅ get_db

---

### Headers Avançados

✅ ETag

✅ If-Match

✅ If-None-Match

✅ Idempotency-Key

✅ X-Request-Id

---

# Parecer do Tech Lead

```text
APROVADO
```

A camada de segurança, autenticação JWT, refresh token rotation, RBAC e tratamento de erros RFC 9457 atende integralmente às exigências da OpenAPI Bookstore, do SPEC.md e da metodologia Spec-Driven Development.

---

# Decisão

```text
AUTORIZADO O AVANÇO PARA A FASE 5
```

Próxima etapa:

```text
src/api/routers/auth.py

src/api/routers/users.py

src/api/routers/products.py

src/api/routers/clients.py

src/api/routers/sales.py
```

---

# Status da Fase

```text
✅ HOMOLOGADO

✅ FASE 4 CONCLUÍDA
```