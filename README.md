# API de Gestão de Livraria

## Propósito

Esta API foi desenvolvida para atender uma aplicação de gestão de livraria, permitindo o controle de produtos, clientes, usuários do sistema e vendas realizadas. O objetivo é centralizar os dados de negócio e disponibilizar operações de consulta, cadastro, atualização e exclusão de registros através de uma API REST padronizada

## Problema Resolvido


Muitas pequenas livrarias realizam o controle de estoque e vendas de forma manual ou em sistemas pouco integrados. A API permite organizar e automatizar processos relacionados a:

- Cadastro e gerenciamento de livros.
- Controle de estoque.
- Cadastro de clientes.
- Controle de usuários do sistema.
- Registro e consulta de vendas.
- Histórico de compras realizadas pelos clientes.


## Público-Alvo

- Livrarias de pequeno e médio porte.
- Funcionários responsáveis por vendas e estoque.
- Administradores do sistema.
- Clientes cadastrados para programas de fidelidade.


## Principais Funcionalidades
Produtos
- Cadastro de livros.
- Controle de estoque.
- Consulta por ISBN.
- Consulta por autor e título.

Clientes
- Cadastro de clientes.
- Consulta de histórico de compras.
- Controle de pontos de fidelidade.

Usuários
- Gerenciamento de usuários do sistema.
- Controle de acesso administrativo.

Vendas
- Registro de vendas.
- Associação entre cliente, vendedor e produtos vendidos.
- Cálculo de descontos.
- Controle de formas de pagamento.

## Arquitetura dos Recursos
## Clientes
Representam os consumidores cadastrados na livraria.
## Produtos
Representam os livros disponibilizados para venda.
## Usuários
Representam os operadores e administradores do sistema.
## Vendas
Representam transações realizadas na livraria.
Relacionamentos:

- Um Cliente pode possuir várias Vendas.
- Uma Venda possui um ou mais Produtos.
- Um Usuário registra várias Vendas.
- Cada Produto pode participar de várias Vendas.
## Tecnologias Utilizadas

- Firebase Firestore
- API REST
- Apidog
- OpenAPI
- 
## Equipe
Roberta Cristina Rodrigues de Souza – RA 28404813009
