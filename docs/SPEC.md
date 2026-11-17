# SPEC.md — Especificação de Negócio (Bookstore API)

## 1. Visão Geral

A Bookstore API é uma API REST para gerenciamento de livrarias baseada em um sistema previamente desenvolvido utilizando Firebase Firestore.

O sistema centraliza operações relacionadas a produtos, clientes, usuários e vendas, permitindo controle de estoque, programa de fidelidade e registro de transações comerciais.

A especificação OpenAPI localizada em:

```text
apidog/Bookstore API.openapi.yaml
```

é a fonte oficial de contratos, endpoints, schemas, exemplos e regras da API.

O projeto utiliza a metodologia Spec-Driven Development (SDD).

---

## 2. Entidades do Domínio

### Users

Representam operadores e administradores do sistema.

Campos principais:

- id
- name
- email
- phone
- active
- createdAt
- role

Perfis previstos:

- ADMIN
- SELLER

---

### Products

Representam os livros comercializados pela livraria.

Campos principais:

- id
- code
- title
- author
- isbn
- price
- stock
- createdAt

---

### Clients

Representam clientes cadastrados na base da livraria.

Campos principais:

- id
- name
- email
- phone
- cpf
- birthDate
- loyaltyPoints
- active
- createdAt

---

### Sales

Representam vendas registradas na livraria.

Campos principais:

- id
- clientId
- sellerId
- createdAt
- paymentMethod
- grossTotal
- discount
- finalTotal
- items

---

### SaleItems

Representam os itens que compõem uma venda.

No modelo OpenAPI e Firebase os itens são armazenados internamente dentro da venda.

Para fins de modelagem ORM relacional, os itens podem ser representados pela entidade lógica SaleItems.

Campos principais:

- productId
- title
- quantity
- unitPrice

---

## 3. Relacionamentos

### Users → Sales

```text
User 1:N Sales
```

Um vendedor pode registrar diversas vendas.

---

### Clients → Sales

```text
Client 1:N Sales
```

Toda venda deve possuir um cliente associado.

O campo clientId é obrigatório conforme definido no contrato OpenAPI.

---

### Sales → Products

Do ponto de vista do domínio:

```text
Sale N:N Products
```

Para modelagem ORM:

```text
Sale 1:N SaleItems

Product 1:N SaleItems
```

---

## 4. Programa de Fidelidade

Todos os clientes cadastrados participam do programa de fidelidade.

### Regras

- Cada venda registrada credita pontos automaticamente ao cliente.
- O saldo de pontos é armazenado no campo loyaltyPoints.
- Ao atingir 100 pontos, o cliente pode utilizar um desconto de 10%.
- O desconto aplicado é registrado no campo discount da venda.
- Após utilização do benefício, a pontuação do cliente deve ser atualizada conforme as regras do sistema.
- O controle de pontos deve ocorrer automaticamente durante o processamento das vendas.

---

## 5. Controle de Estoque

Todos os produtos possuem estoque controlado.

### Regras

- Toda venda reduz automaticamente o estoque dos produtos vendidos.
- Não é permitido estoque negativo.
- Produtos sem estoque disponível não podem ser vendidos.
- Tentativas de venda sem estoque devem retornar:

```http
409 Conflict
```

com código:

```text
INSUFFICIENT_STOCK
```

- Produtos vinculados a vendas históricas não podem ser excluídos.

---

## 6. Regras de Negócio

### Produtos

- Devem possuir código interno obrigatório (code).
- Devem possuir ISBN válido.
- Devem possuir preço maior que zero.
- Devem possuir estoque maior ou igual a zero.

### Clientes

- Devem possuir CPF válido.
- Devem possuir data de nascimento informada.
- Participam do programa de fidelidade.
- Acumulam pontos automaticamente conforme as vendas.

### Vendas

- Devem possuir cliente obrigatório.
- Devem possuir vendedor obrigatório.
- Devem possuir ao menos um item.
- Devem registrar forma de pagamento.
- Devem calcular grossTotal, discount e finalTotal.
- Devem atualizar o estoque dos produtos envolvidos.

### Imutabilidade das Vendas

Após registradas:

- não podem ser alteradas;
- não podem ser excluídas.

A venda representa um registro histórico permanente.

## Histórico de Compras por Cliente

A API disponibiliza o endpoint:

GET /api/v1/clients/{clientId}/sales

que permite consultar o histórico de vendas associado a um cliente específico.

O recurso suporta paginação e segue os mesmos padrões definidos para os demais endpoints da API.
---

## 7. Autenticação e Autorização

A API utiliza autenticação JWT.

Endpoints:

- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me

### Perfis

#### ADMIN

Permissões administrativas completas.

#### SELLER

Permissões de operação e registro de vendas.

---

## 8. Persistência

O sistema original utiliza Firebase Firestore.

Para fins de modelagem arquitetural e aplicação dos conceitos de ORM estudados na disciplina, os relacionamentos também são representados através de uma modelagem relacional compatível com SQLAlchemy 2.0.

---

## 9. Health Checks

A API disponibiliza:

```http
GET /health/live
```

Validação de disponibilidade da aplicação.

```http
GET /health/ready
```

Validação de prontidão e acesso às dependências.

---

## 10. Fonte da Verdade

Os seguintes artefatos compõem a documentação oficial do projeto:

```text
AGENTS.md
STYLEGUIDE.md
SPEC.md
PLAN.md
apidog/Bookstore API.openapi.yaml
```

Qualquer alteração de regra de negócio deve ser refletida primeiramente no OpenAPI e na documentação antes da implementação.