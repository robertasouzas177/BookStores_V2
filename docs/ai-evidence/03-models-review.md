# 03-models-review.md

## Fase

Fase 3 — Modelagem ORM e Persistência

## Persona

```text
[Backend Coder]
```

Implementação:

```text
src/api/models.py
src/api/database.py
```

---

## Ferramenta Utilizada

```text
Google Antigravity Agentic Desktop Application
```

---

# Prompt Utilizado

```text
Atuando como [Backend Coder], execute a Fase 3 do docs/PLAN.md.

Utilize obrigatoriamente:

- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md

Crie:

- src/api/models.py
- src/api/database.py

(...)
```

---

# Objetivo

Implementar a camada de persistência da Bookstore API utilizando SQLAlchemy 2.0, compatível com:

- OpenAPI
- SPEC.md
- Firebase Firestore
- Refresh Token Rotation
- Programa de Fidelidade
- Controle de Estoque

---

# Arquivos Gerados

```text
src/api/models.py

src/api/database.py
```

---

# Entidades Implementadas

## UserModel

Representa os usuários da coleção:

```text
UsuarioAPI
```

Campos principais:

- id
- name
- email
- password_hash
- phone
- role
- active
- created_at

Relacionamentos:

```text
User 1:N Sales

User 1:N RefreshTokens
```

---

## ProductModel

Campos:

- id
- code
- title
- author
- isbn
- price
- stock
- created_at

Relacionamento:

```text
Product 1:N SaleItems
```

---

## ClientModel

Campos:

- id
- name
- email
- phone
- cpf
- birth_date
- loyalty_points
- active
- created_at

Relacionamento:

```text
Client 1:N Sales
```

---

## SaleModel

Campos:

- id
- client_id
- seller_id
- client_name
- seller_name
- payment_method
- gross_total
- discount
- final_total
- created_at

Relacionamentos:

```text
Sale 1:N SaleItems
```

---

## SaleItemModel

Campos:

- id
- sale_id
- product_id
- title
- quantity
- unit_price

Integridade:

```text
product_id → ondelete="RESTRICT"
```

---

## RefreshTokenModel

Campos:

- id
- user_id
- family_id
- token_hash
- revoked
- expires_at
- created_at

Objetivo:

- refresh token rotation
- revogação
- detecção de reuso

---

# Camada de Persistência

## database.py

Implementado:

- SQLite Engine
- SessionLocal
- Base
- get_db()
- init_db()
- seed_initial_data()

---

# Seed Inicial

Usuários:

```text
ADMIN
SELLER
```

Produtos:

```text
Duna

O Príncipe Cruel
```

Clientes:

```text
Cliente exemplo com fidelidade
```

---

# Revisão do Tech Lead

Prompt utilizado:

```text
Atuando como [Tech Lead], execute uma revisão arquitetural completa dos arquivos:

- src/api/models.py
- src/api/database.py

(...)
```

---

# Resultado da Revisão

## Status

```text
✅ APROVADO
```

---

# Principais Validações

### SQLAlchemy 2.0

✅ DeclarativeBase

✅ Mapped

✅ mapped_column

✅ relationship

---

### Compatibilidade Firestore

✅ IDs String(128)

✅ Sem UUID como chave de negócio

---

### Relacionamentos

✅ User 1:N Sales

✅ Client 1:N Sales

✅ Sale 1:N SaleItems

✅ Product 1:N SaleItems

---

### Integridade Referencial

✅ ondelete="RESTRICT"

✅ proteção de histórico

---

### Programa de Fidelidade

✅ loyalty_points

✅ discount

✅ gross_total

✅ final_total

---

### Refresh Tokens

✅ family_id

✅ token_hash

✅ revoked

✅ expires_at

---

### Banco de Dados

✅ SessionLocal

✅ get_db()

✅ seed inicial

---

# Parecer do Tech Lead

```text
APROVADO
```

A modelagem ORM e a camada de persistência atendem integralmente aos requisitos da Bookstore API e da metodologia SDD.

---

# Decisão

```text
AUTORIZADO O AVANÇO PARA A FASE 4
```

Próxima etapa:

```text
src/api/security.py

src/api/exceptions.py
```

Status:

```text
✅ HOMOLOGADO
✅ FASE 3 CONCLUÍDA
```