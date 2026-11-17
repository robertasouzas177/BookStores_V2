# PLAN.md — Roteiro Técnico de Implementação (Bookstore API)

**Gerado por:** [Tech Lead]

**Fontes de Governança:**

- docs/AGENTS.md
- docs/STYLEGUIDE.md
- docs/SPEC.md
- apidog/Bookstore API.openapi.yaml

Objetivo:

Implementar uma arquitetura de referência para a Bookstore API utilizando os princípios de Spec-Driven Development (SDD), respeitando integralmente o contrato OpenAPI derivado da aplicação real construída sobre Firebase Firestore.

---

# Fase 1 — Fundação e Estrutura Arquitetural

- [ ] Passo 1.1 Criar estrutura base do projeto.
- [ ] Passo 1.2 Configurar ambiente Python 3.12.
- [ ] Passo 1.3 Configurar dependências FastAPI.
- [ ] Passo 1.4 Configurar dependências SQLAlchemy 2.0.
- [ ] Passo 1.5 Configurar PyJWT.
- [ ] Passo 1.6 Configurar pytest, httpx e TestClient.
- [ ] Passo 1.7 Validar aderência ao STYLEGUIDE.md.

---

# Fase 2 — Extração de Schemas OpenAPI

## Users

- [x] Passo 2.1 Criar schema User.
- [x] Passo 2.2 Criar CreateUserDTO.
- [x] Passo 2.3 Criar UpdateUserDTO.

## Products

- [x] Passo 2.4 Criar schema Product.
- [x] Passo 2.5 Criar CreateProductDTO.
- [x] Passo 2.6 Criar UpdateProductDTO.

## Clients

- [x] Passo 2.7 Criar schema Client.
- [x] Passo 2.8 Criar CreateClientDTO.
- [x] Passo 2.9 Criar UpdateClientDTO.

## Sales

- [x] Passo 2.10 Criar schema Sale.
- [x] Passo 2.11 Criar CreateSaleDTO.
- [x] Passo 2.12 Criar SaleItem.
- [x] Passo 2.13 Criar PaginatedSalesResponse.

## Auth

- [x] Passo 2.14 Criar LoginRequest.
- [x] Passo 2.15 Criar TokenResponse.
- [x] Passo 2.16 Criar RefreshRequest.
- [x] Passo 2.17 Reutilizar o schema User na resposta de GET /api/v1/auth/me.

## Paginação

- [x] Passo 2.18 Criar PaginationMeta.
- [x] Passo 2.19 Criar PaginatedUsersResponse.
- [x] Passo 2.20 Criar PaginatedProductsResponse.
- [x] Passo 2.21 Criar PaginatedClientsResponse.

## RFC9457

- [x] Passo 2.22 Criar InvalidParam.
- [x] Passo 2.23 Criar ApiError.
- [x] Passo 2.24 Adicionar campo code.
- [x] Passo 2.25 Implementar application/problem+json.

---

# Fase 3 — Persistência e ORM

## Usuários

- [x] Passo 3.1 Criar UserModel.
- [x] Passo 3.2 Implementar ADMIN.
- [x] Passo 3.3 Implementar SELLER.

## Produtos

- [x] Passo 3.4 Criar ProductModel.
- [x] Passo 3.5 Implementar campo code.
- [x] Passo 3.6 Implementar ISBN.
- [x] Passo 3.7 Implementar estoque.

## Clientes

- [x] Passo 3.8 Criar ClientModel.
- [x] Passo 3.9 Implementar CPF.
- [x] Passo 3.10 Implementar birthDate.
- [x] Passo 3.11 Implementar loyaltyPoints.

## Vendas

- [x] Passo 3.12 Criar SaleModel.
- [x] Passo 3.13 Implementar clientId obrigatório.
- [x] Passo 3.14 Implementar sellerId.
- [x] Passo 3.15 Implementar grossTotal.
- [x] Passo 3.16 Implementar discount.
- [x] Passo 3.17 Implementar finalTotal.

## Itens

- [x] Passo 3.18 Criar SaleItemModel.
- [x] Passo 3.19 Implementar relacionamento Sale → SaleItems.
- [x] Passo 3.20 Implementar relacionamento Product → SaleItems.

## Sessão e Tokens

- [x] Passo 3.21 Criar RefreshTokenModel.
- [x] Passo 3.22 Implementar familyId.
- [x] Passo 3.23 Implementar token hash.
- [x] Passo 3.24 Implementar revogação.
- [x] Passo 3.25 Implementar expiração.

## Database

- [x] Passo 3.26 Criar SessionLocal.
- [x] Passo 3.27 Implementar get_db().
- [x] Passo 3.28 Criar seed inicial.
- [x] Passo 3.29 Criar usuários ADMIN e SELLER.
- [x] Passo 3.30 Criar produtos de exemplo.
- [x] Passo 3.31 Criar clientes de exemplo.

---

# Fase 4 — Segurança e RFC 9457

## JWT

- [x] Passo 4.1 Implementar Access Token.
- [x] Passo 4.2 Implementar Refresh Token.
- [x] Passo 4.3 Implementar rotação de token.
- [x] Passo 4.4 Implementar revogação.

## RBAC

- [x] Passo 4.5 Implementar ADMIN.
- [x] Passo 4.6 Implementar SELLER.
- [x] Passo 4.7 Implementar require_roles().

## RFC9457

- [x] Passo 4.8 Implementar 400.
- [x] Passo 4.9 Implementar 401.
- [x] Passo 4.10 Implementar 403.
- [x] Passo 4.11 Implementar 404.
- [x] Passo 4.12 Implementar 409.
- [x] Passo 4.13 Implementar 412.
- [x] Passo 4.14 Implementar 422.
- [x] Passo 4.15 Implementar 429.

## Headers Avançados

- [x] Passo 4.16 Implementar ETag.
- [x] Passo 4.17 Implementar If-None-Match.
- [x] Passo 4.18 Implementar If-Match.
- [x] Passo 4.19 Implementar Idempotency-Key.
- [x] Passo 4.20 Implementar X-Request-Id.

---

# Fase 5 — Implementação dos Routers

## Auth

- [x] Passo 5.1 POST /api/v1/auth/login
- [x] Passo 5.2 POST /api/v1/auth/refresh
- [x] Passo 5.3 POST /api/v1/auth/logout
- [x] Passo 5.4 GET /api/v1/auth/me

## Users

- [x] Passo 5.5 GET /api/v1/users
- [x] Passo 5.6 POST /api/v1/users
- [x] Passo 5.7 GET /api/v1/users/{id}
- [x] Passo 5.8 PATCH /api/v1/users/{id}

## Products

- [x] Passo 5.9 GET /api/v1/products
- [x] Passo 5.10 POST /api/v1/products
- [x] Passo 5.11 GET /api/v1/products/{id}
- [x] Passo 5.12 PATCH /api/v1/products/{id}
- [x] Passo 5.13 DELETE /api/v1/products/{id}

## Clients

- [x] Passo 5.14 GET /api/v1/clients
- [x] Passo 5.15 POST /api/v1/clients
- [x] Passo 5.16 GET /api/v1/clients/{id}
- [x] Passo 5.17 PATCH /api/v1/clients/{id}
- [x] Passo 5.18 DELETE /api/v1/clients/{id}
- [x] Passo 5.19 GET /api/v1/clients/{clientId}/sales

## Sales

- [x] Passo 5.20 GET /api/v1/sales
- [x] Passo 5.21 POST /api/v1/sales
- [x] Passo 5.22 GET /api/v1/sales/{id}

## Health

- [x] Passo 5.23 GET /health/live
- [x] Passo 5.24 GET /health/ready

---

# Fase 6 — Testes Automatizados

## Auth

- [x] Passo 6.1 Login válido.
- [x] Passo 6.2 Login inválido.
- [x] Passo 6.3 Rotação de refresh token.
- [x] Passo 6.4 Reutilização de refresh token.
- [x] Passo 6.5 Logout.

## Users

- [x] Passo 6.6 Criar usuário.
- [x] Passo 6.7 Atualizar usuário.
- [x] Passo 6.8 Inativar usuário.

## Products

- [x] Passo 6.9 CRUD de produtos.
- [x] Passo 6.10 Estoque.
- [x] Passo 6.11 Produto em uso.

## Clients

- [x] Passo 6.12 CRUD de clientes.
- [x] Passo 6.13 Fidelidade.
- [x] Passo 6.14 Histórico de vendas.

## Sales

- [x] Passo 6.15 Registro de venda.
- [x] Passo 6.16 Atualização de estoque.
- [x] Passo 6.17 Acúmulo de pontos.
- [x] Passo 6.18 Idempotência.

## Infraestrutura

- [x] Passo 6.19 ETag.
- [x] Passo 6.20 If-Match.
- [x] Passo 6.21 Health checks.
- [x] Passo 6.22 Rate limiting.

## RFC9457

- [x] Passo 6.23 Validar 400.
- [x] Passo 6.24 Validar 401.
- [x] Passo 6.25 Validar 403.
- [x] Passo 6.26 Validar 404.
- [x] Passo 6.27 Validar 409.
- [x] Passo 6.28 Validar 412.
- [x] Passo 6.29 Validar 422.
- [x] Passo 6.30 Validar 429.

---

# Critério de Conclusão

O projeto somente poderá ser considerado concluído quando:

- OpenAPI estiver 100% refletida na implementação.
- SPEC.md, STYLEGUIDE.md, PLAN.md e TESTS.md estiverem consistentes.
- Todos os testes planejados passarem.
- JWT, RBAC, RFC9457, ETag, Rate Limiting e Idempotency-Key estiverem implementados.
- Não houver divergências entre Firebase, OpenAPI e documentação SDD.