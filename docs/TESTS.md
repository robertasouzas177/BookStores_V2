# TESTS.md — Plano de Testes da Bookstore API

## 1. Objetivo

Este documento define os cenários de teste da Bookstore API e serve como referência para validação funcional, testes automatizados e garantia de conformidade com:

- OpenAPI Specification
- SPEC.md
- STYLEGUIDE.md
- Regras de negócio da livraria
- Programa de fidelidade
- Controle de estoque
- JWT
- RBAC
- RFC 9457

---

# 2. Escopo de Testes

Os testes abrangem:

- Autenticação JWT
- Controle de acesso RBAC
- Usuários
- Produtos
- Clientes
- Programa de Fidelidade
- Vendas
- Itens de Venda (SaleItems)
- Controle de Estoque
- Tratamento de Erros RFC 9457
- Relacionamentos ORM
- Regras de negócio

---

# 3. Testes de Autenticação

## AUTH-001 — Login com credenciais válidas

### Objetivo

Validar a autenticação do usuário.

### Resultado Esperado

```http
200 OK
```

Retornando token JWT válido.

---

## AUTH-002 — Login com senha inválida

### Resultado Esperado

```http
401 Unauthorized
```

---

## AUTH-003 — Login com usuário inexistente

### Resultado Esperado

```http
401 Unauthorized
```

---

## AUTH-004 — Acesso sem token

### Resultado Esperado

```http
401 Unauthorized
```

---

## AUTH-005 — Token expirado

### Resultado Esperado

```http
401 Unauthorized
```

---

## AUTH-006 — Refresh Token válido

### Resultado Esperado

```http
200 OK
```

Novo token gerado.

---

## AUTH-007 — Refresh Token inválido

### Resultado Esperado

```http
401 Unauthorized
```

---

## AUTH-008 — Logout

### Resultado Esperado

```http
200 OK
```

ou

```http
204 No Content
```

conforme contrato OpenAPI.

---

## AUTH-009 — Endpoint /auth/me autenticado

### Resultado Esperado

```http
200 OK
```

Retornando informações do usuário.

---

# 4. Testes de Controle de Acesso (RBAC)

## RBAC-001 — ADMIN acessando recurso administrativo

### Resultado Esperado

```http
200 OK
```

---

## RBAC-002 — EMPLOYEE acessando recurso administrativo

### Resultado Esperado

```http
403 Forbidden
```

---

## RBAC-003 — Usuário sem autenticação

### Resultado Esperado

```http
401 Unauthorized
```

---

## RBAC-004 — ADMIN gerenciando usuários

### Resultado Esperado

Acesso permitido.

---

## RBAC-005 — EMPLOYEE gerenciando usuários

### Resultado Esperado

```http
403 Forbidden
```

---

# 5. Testes de Usuários

## USER-001 — Criar usuário

### Resultado Esperado

```http
201 Created
```

---

## USER-002 — Consultar usuário

### Resultado Esperado

```http
200 OK
```

---

## USER-003 — Atualizar usuário

### Resultado Esperado

```http
200 OK
```

---

## USER-004 — Excluir usuário

### Resultado Esperado

```http
204 No Content
```

---

## USER-005 — Consultar usuário inexistente

### Resultado Esperado

```http
404 Not Found
```

---

# 6. Testes de Produtos

## PROD-001 — Criar produto válido

### Resultado Esperado

```http
201 Created
```

---

## PROD-002 — Consultar produto por ID

### Resultado Esperado

```http
200 OK
```

---

## PROD-003 — Atualizar produto

### Resultado Esperado

```http
200 OK
```

---

## PROD-004 — Excluir produto

### Resultado Esperado

```http
204 No Content
```

---

## PROD-005 — Produto inexistente

### Resultado Esperado

```http
404 Not Found
```

---

## PROD-006 — ISBN válido

### Resultado Esperado

Produto criado com sucesso.

---

## PROD-007 — ISBN inválido

### Resultado Esperado

```http
422 Validation Error
```

---

## PROD-008 — Estoque inicial válido

### Resultado Esperado

Estoque maior ou igual a zero.

---

## PROD-009 — Estoque negativo

### Resultado Esperado

```http
422 Validation Error
```

---

## PROD-010 — Consulta por ISBN

### Resultado Esperado

```http
200 OK
```

---

# 7. Testes de Clientes

## CLIENT-001 — Criar cliente

### Resultado Esperado

```http
201 Created
```

---

## CLIENT-002 — Atualizar cliente

### Resultado Esperado

```http
200 OK
```

---

## CLIENT-003 — Excluir cliente

### Resultado Esperado

```http
204 No Content
```

---

## CLIENT-004 — Consultar cliente inexistente

### Resultado Esperado

```http
404 Not Found
```

---

## CLIENT-005 — Habilitar programa de fidelidade

### Resultado Esperado

```json
{
  "loyaltyProgramActive": true
}
```

---

## CLIENT-006 — Cliente fora do programa

### Resultado Esperado

```json
{
  "loyaltyProgramActive": false
}
```

---

# 8. Testes de Programa de Fidelidade

## LOYALTY-001 — Cliente participante realiza venda

### Resultado Esperado

```text
+10 pontos
```

---

## LOYALTY-002 — Cliente não participante realiza venda

### Resultado Esperado

```text
0 pontos
```

---

## LOYALTY-003 — Venda sem cliente vinculado

### Resultado Esperado

```text
0 pontos
```

---

## LOYALTY-004 — Cliente atinge 100 pontos

### Resultado Esperado

```text
Desconto de 10% disponível
```

---

## LOYALTY-005 — Aplicação do desconto

### Resultado Esperado

```text
Desconto aplicado
```

---

## LOYALTY-006 — Reinicialização dos pontos

### Resultado Esperado

```text
loyaltyPoints = 0
```

---

# 9. Testes de Vendas

## SALE-001 — Registrar venda sem cliente

### Resultado Esperado

```http
201 Created
```

---

## SALE-002 — Registrar venda com cliente

### Resultado Esperado

```http
201 Created
```

---

## SALE-003 — Registrar venda utilizando desconto

### Resultado Esperado

```http
201 Created
```

e

```text
loyaltyDiscountApplied = true
```

---

## SALE-004 — Venda sem itens

### Resultado Esperado

```http
422 Validation Error
```

---

## SALE-005 — Consulta de venda

### Resultado Esperado

```http
200 OK
```

---

## SALE-006 — Atualização de venda

### Resultado Esperado

```http
200 OK
```

---

## SALE-007 — Exclusão de venda

### Resultado Esperado

```http
204 No Content
```

---

## SALE-008 — Cálculo automático do total

### Resultado Esperado

```text
totalAmount = soma dos subtotais
```

---

# 10. Testes de SaleItems

## ITEM-001 — Adicionar item à venda

### Resultado Esperado

```http
201 Created
```

---

## ITEM-002 — Quantidade inválida

### Resultado Esperado

```http
422 Validation Error
```

---

## ITEM-003 — Produto inexistente

### Resultado Esperado

```http
404 Not Found
```

---

## ITEM-004 — Calcular subtotal

### Fórmula

```text
subtotal = quantity × unitPrice
```

### Resultado Esperado

Valor calculado corretamente.

---

# 11. Testes de Estoque

## STOCK-001 — Reduzir estoque após venda

### Resultado Esperado

Estoque atualizado automaticamente.

---

## STOCK-002 — Estoque insuficiente

### Resultado Esperado

```http
409 Conflict
```

---

## STOCK-003 — Bloqueio de estoque negativo

### Resultado Esperado

Operação rejeitada.

---

## STOCK-004 — Produto sem estoque

### Resultado Esperado

Não permitir venda.

---

# 12. Testes ORM

## ORM-001 — User → Sales

Validar relacionamento:

```text
User 1:N Sales
```

---

## ORM-002 — Client → Sales

Validar relacionamento:

```text
Client 0..1 : N Sales
```

---

## ORM-003 — Sale → SaleItems

Validar relacionamento:

```text
Sale 1:N SaleItems
```

---

## ORM-004 — Product → SaleItems

Validar relacionamento:

```text
Product 1:N SaleItems
```

---

## ORM-005 — Persistência dos relacionamentos

### Resultado Esperado

Integridade referencial preservada.

---

# 13. Testes RFC 9457

Todos os cenários abaixo devem validar a presença dos campos:

```json
{
  "type": "",
  "title": "",
  "status": 0,
  "detail": ""
}
```

---

## ERROR-001 — 400 Bad Request

### Resultado Esperado

```http
400 Bad Request
```

---

## ERROR-002 — 401 Unauthorized

### Resultado Esperado

```http
401 Unauthorized
```

---

## ERROR-003 — 403 Forbidden

### Resultado Esperado

```http
403 Forbidden
```

---

## ERROR-004 — 404 Not Found

### Resultado Esperado

```http
404 Not Found
```

---

## ERROR-005 — 409 Conflict

### Resultado Esperado

```http
409 Conflict
```

---

## ERROR-006 — 422 Validation Error

### Resultado Esperado

```http
422 Validation Error
```

Com lista `invalidParams`.

---

# 14. Critérios de Aceite

A Bookstore API será considerada validada quando:

- Todos os testes planejados forem implementados.
- Todos os testes executarem com sucesso.
- O contrato OpenAPI for respeitado.
- As regras do SPEC.md forem respeitadas.
- Os relacionamentos ORM funcionarem corretamente.
- O programa de fidelidade funcionar corretamente.
- O controle de estoque funcionar corretamente.
- Os erros seguirem RFC 9457.

---

# 15. Resultado Esperado da Fase QA

```text
100% dos testes executando com sucesso.

100% de conformidade com OpenAPI.

100% de conformidade com RFC 9457.

100% de conformidade com as regras de negócio da Bookstore API.
```
