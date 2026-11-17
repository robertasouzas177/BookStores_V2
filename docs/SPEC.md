# SPEC.md — Especificação de Negócio (Bookstore API)

## 1. Visão Geral

A Bookstore API é uma API REST para gerenciamento de livrarias, baseada em um sistema previamente desenvolvido utilizando Firebase Firestore.

O sistema permite o gerenciamento de produtos, clientes, usuários e vendas, centralizando as operações de estoque, fidelização de clientes e registro de transações comerciais.

A especificação OpenAPI da solução encontra-se no arquivo `Bookstore API.openapi.yaml`, que representa a principal fonte de verdade para contratos, endpoints, schemas, validações e exemplos de uso da API.

O projeto segue a abordagem **Spec-Driven Development (SDD)**, utilizando especificação formal antes da implementação para garantir consistência entre documentação, regras de negócio e código.

---

## 2. Entidades do Domínio

### Users

Representam operadores e administradores responsáveis pela utilização do sistema.

**Campos principais:**

- id
- name
- email
- role

### Products

Representam os livros comercializados pela livraria.

**Campos principais:**

- id
- title
- author
- isbn
- price
- stock

### Clients

Representam clientes cadastrados na base da livraria.

**Campos principais:**

- id
- name
- email
- phone
- loyaltyPoints
- loyaltyProgramActive

### Sales

Representam as vendas realizadas na livraria.

**Campos principais:**

- id
- userId
- clientId
- saleDate
- totalAmount
- paymentMethod
- loyaltyDiscountApplied

### SaleItems

Representam os itens que compõem uma venda.

**Campos principais:**

- id
- saleId
- productId
- quantity
- unitPrice
- subtotal

---

## 3. Relacionamentos

### Client → Sales

Uma venda pode ou não estar associada a um cliente cadastrado.

Quando associada:

```text
Client 1:N Sales
```

O campo `clientId` é opcional, permitindo vendas para clientes ocasionais não cadastrados.

### User → Sales

Cada venda deve possuir um usuário responsável pelo registro da operação.

```text
User 1:N Sales
```

### Sales → SaleItems

Uma venda pode possuir um ou mais itens.

```text
Sale 1:N SaleItems
```

### Products → SaleItems

Um produto pode participar de diversas vendas ao longo do tempo.

```text
Product 1:N SaleItems
```

### Relacionamento Conceitual

Do ponto de vista do negócio:

```text
Sale N:N Products
```

Para fins de modelagem relacional e ORM, essa relação deve ser implementada através da entidade intermediária **SaleItems**.

---

## 4. Programa de Fidelidade

A participação no programa de fidelidade é opcional.

### Campo de Controle

```text
loyaltyProgramActive (boolean)
```

### Regras

- Apenas clientes cadastrados podem participar do programa.
- O cliente deve possuir `loyaltyProgramActive = true`.
- Clientes que não participam do programa mantêm `loyaltyPoints = 0`.
- Cada venda válida gera 10 pontos para o cliente participante.
- Ao atingir 100 pontos acumulados, o cliente recebe um desconto de 10%.
- Após a utilização do benefício, a pontuação acumulada é reiniciada para 0.
- Apenas vendas vinculadas a um cliente cadastrado geram pontuação.
- Vendas sem cliente associado não geram pontuação.
- O campo `loyaltyDiscountApplied` registra se o desconto foi utilizado naquela venda.

---

## 5. Controle de Estoque

Os produtos possuem controle individual de estoque.

### Regras

- Toda venda reduz automaticamente o estoque dos produtos vendidos.
- O sistema não deve permitir estoque negativo.
- Produtos sem estoque não podem ser adicionados a novas vendas.
- A exclusão de um produto não deve ser permitida caso existam vendas vinculadas ao produto.
- O estoque deve refletir a quantidade física disponível para venda.
- O histórico de vendas deve permanecer preservado mesmo após alterações cadastrais do produto.

---

## 6. Regras de Negócio

### Produtos

- Devem possuir ISBN válido.
- Devem possuir preço maior que zero.
- Devem possuir estoque maior ou igual a zero.
- Devem possuir título e autor informados.

### Clientes

- Podem participar ou não do programa de fidelidade.
- Acumulam pontos apenas quando participam do programa.
- Podem existir vendas sem cliente vinculado.

### Vendas

- Devem possuir pelo menos um item.
- Devem possuir um usuário responsável pela operação.
- Podem ou não possuir cliente associado.
- Devem registrar a forma de pagamento utilizada.
- Devem calcular automaticamente o valor total da venda.
- Devem atualizar o estoque dos produtos envolvidos.
- Devem registrar a data e hora da transação.

### Itens da Venda

- Devem possuir produto válido.
- Devem possuir quantidade maior que zero.
- Devem registrar o preço unitário praticado no momento da venda.
- Devem registrar o subtotal do item para preservação histórica.

### Usuários

- São responsáveis pelo registro das vendas.
- Possuem perfis de acesso definidos pelo sistema.
- Devem utilizar autenticação para acessar funcionalidades protegidas.

---

## 7. Autenticação e Autorização

A API utiliza autenticação baseada em JWT (JSON Web Token).

### Endpoints de Autenticação

- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
- GET /auth/me

### Cabeçalho de Autorização

```http
Authorization: Bearer <token>
```

### Perfis de Acesso

#### ADMIN

Permissões:

- Gerenciar usuários
- Gerenciar produtos
- Gerenciar clientes
- Gerenciar vendas
- Executar operações administrativas
- Consultar relatórios
- Alterar permissões de acesso

#### EMPLOYEE

Permissões:

- Consultar produtos
- Consultar clientes
- Registrar vendas
- Consultar vendas
- Atualizar informações operacionais permitidas

---

## 8. Persistência de Dados

A aplicação original utiliza Firebase Firestore como mecanismo principal de persistência.

Para fins de modelagem arquitetural, geração automatizada de código e aplicação dos conceitos de ORM estudados na disciplina, os relacionamentos do domínio também são descritos em formato compatível com modelagem relacional.

Essa abordagem permite utilizar o mesmo domínio de negócio em diferentes estratégias de persistência sem alterar as regras funcionais da aplicação.

---

## 9. Testes Funcionais Esperados

### Autenticação

- Login válido
- Login inválido
- Token expirado
- Token ausente
- Refresh token
- Logout

### Produtos

- Cadastro de produto
- Atualização de produto
- Exclusão de produto
- Consulta por ISBN
- Controle de estoque
- Bloqueio de estoque negativo

### Clientes

- Cadastro de cliente
- Atualização de cliente
- Participação no programa de fidelidade
- Acúmulo de pontos
- Aplicação de desconto

### Vendas

- Registro de venda
- Associação de produtos
- Associação opcional de cliente
- Aplicação de desconto por fidelidade
- Atualização automática de estoque
- Cálculo de valor total

### Itens da Venda

- Inclusão de itens
- Cálculo de subtotal
- Validação de quantidade
- Validação de estoque disponível

### Erros da API

- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 409 Conflict
- 422 Validation Error

---

## 10. Fonte da Verdade

A evolução da Bookstore API deve seguir a metodologia SDD:

```text
Constitution
├── STYLEGUIDE.md
└── AGENTS.md

Specify
├── Bookstore API.openapi.yaml
└── SPEC.md

Plan
└── PLAN.md

Implement
├── Models
├── Schemas
├── Routers
├── Security
└── Tests
```

Qualquer alteração de regra de negócio deve ser refletida primeiro na especificação e somente depois na implementação.
