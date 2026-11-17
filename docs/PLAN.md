# PLAN.md — Roteiro Técnico de Implementação (Bookstore API)

**Gerado por:** Roberta Souza 
**Fontes de Governança:** AGENTS.md, STYLEGUIDE.md, SPEC.md e Bookstore API.openapi.yaml

**Objetivo:** Evoluir a especificação da Bookstore API para uma arquitetura backend documentada, testável e compatível com os conceitos estudados de ORM, autenticação JWT, RBAC e Spec-Driven Development.

---

# Fase 1 — Fundação e Estrutura Arquitetural

- [ ] Passo 1.1: Criar a estrutura de diretórios do projeto:

```text
src/api/
├── __init__.py
├── main.py
├── schemas.py
├── models.py
├── database.py
├── security.py
├── exceptions.py
├── routers/
│   ├── auth.py
│   ├── users.py
│   ├── products.py
│   ├── clients.py
│   └── sales.py
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_products.py
    ├── test_clients.py
    └── test_sales.py
```

- [ ] Passo 1.2: Criar o arquivo `requirements.txt`.
- [ ] Passo 1.3: Configurar dependências FastAPI, Pydantic v2, SQLAlchemy 2.0, PyJWT, pytest e httpx.
- [ ] Passo 1.4: Validar conformidade da estrutura com STYLEGUIDE.md.

---

# Fase 2 — Extração de Schemas e Contratos OpenAPI

- [ ] Passo 2.1: Extrair do contrato OpenAPI os schemas da entidade Users.
- [ ] Passo 2.2: Extrair do contrato OpenAPI os schemas da entidade Products.
- [ ] Passo 2.3: Extrair do contrato OpenAPI os schemas da entidade Clients.
- [ ] Passo 2.4: Extrair do contrato OpenAPI os schemas da entidade Sales.
- [ ] Passo 2.5: Criar schema SaleItems para representar itens de venda.

### Schemas de autenticação

- [ ] Passo 2.6: Criar LoginRequestDTO.
- [ ] Passo 2.7: Criar TokenResponseDTO.
- [ ] Passo 2.8: Criar UserResponseDTO.
- [ ] Passo 2.9: Criar RefreshTokenDTO.

### Schemas de erro

- [ ] Passo 2.10: Criar InvalidParam.
- [ ] Passo 2.11: Criar ApiError seguindo RFC 9457.

### Regras de negócio

- [ ] Passo 2.12: Implementar validações de estoque.
- [ ] Passo 2.13: Implementar validações de ISBN.
- [ ] Passo 2.14: Implementar validações de programa de fidelidade.
- [ ] Passo 2.15: Implementar validações de venda e itens da venda.

---

# Fase 3 — Modelagem ORM e Persistência

## Users

- [ ] Passo 3.1: Criar UserModel.
- [ ] Passo 3.2: Definir role ADMIN e EMPLOYEE.
- [ ] Passo 3.3: Configurar relacionamento User → Sales.

## Products

- [ ] Passo 3.4: Criar ProductModel.
- [ ] Passo 3.5: Configurar controle de estoque.

## Clients

- [ ] Passo 3.6: Criar ClientModel.
- [ ] Passo 3.7: Configurar loyaltyPoints.
- [ ] Passo 3.8: Configurar loyaltyProgramActive.
- [ ] Passo 3.9: Configurar relacionamento Client → Sales.

## Sales

- [ ] Passo 3.10: Criar SaleModel.
- [ ] Passo 3.11: Configurar relacionamento User → Sales.
- [ ] Passo 3.12: Configurar relacionamento Client → Sales.
- [ ] Passo 3.13: Configurar relacionamento Sale → SaleItems.

## SaleItems

- [ ] Passo 3.14: Criar SaleItemModel.
- [ ] Passo 3.15: Configurar relacionamento Product → SaleItems.
- [ ] Passo 3.16: Configurar relacionamento Sale → SaleItems.

## Banco de Dados

- [ ] Passo 3.17: Implementar database.py.
- [ ] Passo 3.18: Configurar SQLite para ambiente de desenvolvimento.
- [ ] Passo 3.19: Criar SessionLocal.
- [ ] Passo 3.20: Implementar get_db().
- [ ] Passo 3.21: Criar seed inicial de usuários.
- [ ] Passo 3.22: Criar seed inicial de produtos.
- [ ] Passo 3.23: Criar seed inicial de clientes.
- [ ] Passo 3.24: Criar seed inicial de vendas.

---

# Fase 4 — Segurança, JWT e Controle de Acesso

## Autenticação

- [ ] Passo 4.1: Configurar geração de JWT.
- [ ] Passo 4.2: Configurar validação de JWT.
- [ ] Passo 4.3: Implementar login.
- [ ] Passo 4.4: Implementar refresh token.
- [ ] Passo 4.5: Implementar logout.
- [ ] Passo 4.6: Implementar endpoint /auth/me.

## RBAC

- [ ] Passo 4.7: Criar enum de perfis.
- [ ] Passo 4.8: Implementar perfil ADMIN.
- [ ] Passo 4.9: Implementar perfil EMPLOYEE.
- [ ] Passo 4.10: Criar dependência require_roles().

## Tratamento de Erros

- [ ] Passo 4.11: Criar ApiErrorException.
- [ ] Passo 4.12: Implementar erro 400.
- [ ] Passo 4.13: Implementar erro 401.
- [ ] Passo 4.14: Implementar erro 403.
- [ ] Passo 4.15: Implementar erro 404.
- [ ] Passo 4.16: Implementar erro 409.
- [ ] Passo 4.17: Implementar erro 422.

---

# Fase 5 — Implementação dos Routers

## Auth

- [ ] Passo 5.1: Implementar POST /auth/login.
- [ ] Passo 5.2: Implementar POST /auth/refresh.
- [ ] Passo 5.3: Implementar POST /auth/logout.
- [ ] Passo 5.4: Implementar GET /auth/me.

## Users

- [ ] Passo 5.5: Implementar GET /users.
- [ ] Passo 5.6: Implementar POST /users.
- [ ] Passo 5.7: Implementar GET /users/{id}.
- [ ] Passo 5.8: Implementar PATCH /users/{id}.
- [ ] Passo 5.9: Implementar DELETE /users/{id}.

## Products

- [ ] Passo 5.10: Implementar GET /products.
- [ ] Passo 5.11: Implementar POST /products.
- [ ] Passo 5.12: Implementar GET /products/{id}.
- [ ] Passo 5.13: Implementar PATCH /products/{id}.
- [ ] Passo 5.14: Implementar DELETE /products/{id}.

## Clients

- [ ] Passo 5.15: Implementar GET /clients.
- [ ] Passo 5.16: Implementar POST /clients.
- [ ] Passo 5.17: Implementar GET /clients/{id}.
- [ ] Passo 5.18: Implementar PATCH /clients/{id}.
- [ ] Passo 5.19: Implementar DELETE /clients/{id}.

## Sales

- [ ] Passo 5.20: Implementar GET /sales.
- [ ] Passo 5.21: Implementar POST /sales.
- [ ] Passo 5.22: Implementar GET /sales/{id}.
- [ ] Passo 5.23: Implementar PATCH /sales/{id}.
- [ ] Passo 5.24: Implementar DELETE /sales/{id}.

## Regras de Negócio

- [ ] Passo 5.25: Atualizar estoque após venda.
- [ ] Passo 5.26: Validar estoque disponível.
- [ ] Passo 5.27: Atualizar pontos de fidelidade.
- [ ] Passo 5.28: Aplicar desconto por fidelidade.
- [ ] Passo 5.29: Registrar itens da venda.

---

# Fase 6 — Testes Automatizados

## Autenticação

- [ ] Passo 6.1: Testar login válido.
- [ ] Passo 6.2: Testar login inválido.
- [ ] Passo 6.3: Testar token expirado.
- [ ] Passo 6.4: Testar acesso sem token.

## Produtos

- [ ] Passo 6.5: Testar cadastro.
- [ ] Passo 6.6: Testar atualização.
- [ ] Passo 6.7: Testar exclusão.
- [ ] Passo 6.8: Testar controle de estoque.

## Clientes

- [ ] Passo 6.9: Testar cadastro.
- [ ] Passo 6.10: Testar pontos de fidelidade.
- [ ] Passo 6.11: Testar aplicação de desconto.

## Vendas

- [ ] Passo 6.12: Testar registro de venda.
- [ ] Passo 6.13: Testar venda sem cliente.
- [ ] Passo 6.14: Testar venda com cliente fidelidade.
- [ ] Passo 6.15: Testar cálculo do total.

## Erros

- [ ] Passo 6.16: Testar erro 400.
- [ ] Passo 6.17: Testar erro 401.
- [ ] Passo 6.18: Testar erro 403.
- [ ] Passo 6.19: Testar erro 404.
- [ ] Passo 6.20: Testar erro 409.
- [ ] Passo 6.21: Testar erro 422.

## Validação Final

- [ ] Passo 6.22: Executar suíte completa de testes.
- [ ] Passo 6.23: Validar conformidade OpenAPI.
- [ ] Passo 6.24: Validar conformidade RFC 9457.
- [ ] Passo 6.25: Marcar projeto como concluído.
