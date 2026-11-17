# AI_WORKFLOW.md — Evidências do Desenvolvimento com IA utilizando SDD

## 1. Objetivo

Este documento registra o processo de desenvolvimento da Bookstore API utilizando Inteligência Artificial e a metodologia **Spec-Driven Development (SDD)** ensinada nas aulas 10 e 11 da disciplina de Programação Web.

O objetivo é demonstrar a utilização prática de agentes de IA durante todas as etapas do ciclo de desenvolvimento, desde a análise da especificação até a validação final da solução.

---

# 2. Ferramentas Utilizadas

## Google Antigravity Agentic Desktop Application

Ferramenta principal utilizada para execução do workflow SDD.

Responsável por:

- Auditoria da especificação OpenAPI;
- Planejamento arquitetural;
- Geração de código;
- Revisões técnicas;
- Validação dos artefatos;
- Execução de testes.

---

## Microsoft Copilot

Utilizado como apoio durante o projeto para:

- Interpretação dos requisitos da disciplina;
- Revisão dos documentos SDD;
- Refinamento dos artefatos de especificação;
- Construção dos prompts utilizados no Antigravity;
- Análise crítica dos relatórios emitidos pelos agentes;
- Apoio na preparação da apresentação final.

O Copilot foi utilizado como ferramenta complementar ao Antigravity, auxiliando na elaboração e refinamento do fluxo de trabalho baseado em SDD.

---

# 3. Metodologia Utilizada

O projeto seguiu integralmente a metodologia:

```text
Spec-Driven Development (SDD)
```

Fluxo aplicado:

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

---

# 4. Etapa Constitution

## Objetivo

Definir as regras imutáveis do projeto.

## Artefatos Produzidos

- AGENTS.md
- STYLEGUIDE.md

## Resultado

Foram estabelecidas:

- Regras de governança;
- Perfis de agentes;
- Convenções técnicas;
- Padrões de autenticação;
- Convenções de persistência;
- Regras de modelagem ORM;
- Padrões RFC 9457;
- Regras de teste.

Status:

```text
✅ Homologado pelo Tech Lead
```

---

# 5. Etapa Specify

## Objetivo

Definir formalmente o domínio e os contratos da aplicação.

## Artefatos Utilizados

- apidog/Bookstore API.openapi.yaml
- SPEC.md

## Origem dos Dados

A especificação foi construída a partir da aplicação real desenvolvida anteriormente utilizando:

- Firebase Firestore
- Firebase Authentication
- Firebase Hosting

Aplicação publicada:

```text
bookstore_vendas
```

## Resultado

Foram documentados:

- Usuários
- Produtos
- Clientes
- Vendas
- Programa de Fidelidade
- Controle de Estoque
- Autenticação JWT
- Controle de Acesso (RBAC)
- RFC 9457
- Rate Limiting
- ETag
- Idempotency-Key

Status:

```text
✅ Homologado pelo Tech Lead
```

---

# 6. Etapa Plan

## Objetivo

Transformar a especificação em um roteiro de implementação.

## Artefato Produzido

- PLAN.md

## Persona Utilizada

```text
[Tech Lead]
```

## Resultado

O projeto foi dividido em:

```text
Fase 1 — Fundação

Fase 2 — Schemas

Fase 3 — ORM e Persistência

Fase 4 — Segurança

Fase 5 — Routers

Fase 6 — Testes
```

Status:

```text
✅ Homologado pelo Tech Lead
```

---

# 7. Etapa Implement

## Persona Utilizada

```text
[Backend Coder]
```

---

## Fase 2 — Schemas

Arquivo produzido:

```text
src/api/schemas.py
```

Conteúdo:

- Schemas Pydantic v2
- DTOs
- Paginação
- Health Checks
- RFC 9457

Revisão:

```text
✅ Homologado pelo Tech Lead
```

---

## Fase 3 — ORM

Arquivos produzidos:

```text
src/api/models.py

src/api/database.py
```

Conteúdo:

- SQLAlchemy 2.0
- Relacionamentos ORM
- RefreshTokenModel
- Integração com SQLite
- SessionLocal
- get_db()

Revisão:

```text
✅ Homologado pelo Tech Lead
```

---

## Fase 4 — Segurança

Arquivos produzidos:

```text
src/api/security.py

src/api/exceptions.py
```

Conteúdo:

- JWT
- Refresh Token Rotation
- RBAC
- RFC 9457

Revisão:

```text
✅ Homologado pelo Tech Lead
```

---

## Fase 5 — Routers

Arquivos produzidos:

```text
src/api/routers/auth.py

src/api/routers/users.py

src/api/routers/products.py

src/api/routers/clients.py

src/api/routers/sales.py
```

Conteúdo:

- Endpoints REST
- Idempotency-Key
- ETag
- If-Match
- If-None-Match
- Regras de negócio

Revisão:

```text
✅ Homologado pelo Tech Lead
```

---

# 8. Etapa Validate

## Persona Utilizada

```text
[QA Engineer]
```

Arquivos produzidos:

```text
src/api/tests/conftest.py

src/api/tests/test_auth.py

src/api/tests/test_users.py

src/api/tests/test_products.py

src/api/tests/test_clients.py

src/api/tests/test_sales.py

src/api/tests/test_errors.py

src/api/tests/test_health.py
```

---

## Resultado da Suíte de Testes

```text
66 testes executados

66 testes aprovados

100% de sucesso
```

Principais validações:

- JWT
- RBAC
- Refresh Token Rotation
- RFC 9457
- Programa de Fidelidade
- Controle de Estoque
- ORM
- ETag
- Health Checks
- Idempotência

Status:

```text
✅ Homologado pelo Tech Lead
```

---

# 9. Homologações Registradas

Durante o desenvolvimento foram realizadas revisões formais conduzidas pela persona:

```text
[Tech Lead]
```

Documentos auditados:

- Homologação Documental
- Homologação dos Schemas
- Homologação dos Models
- Homologação da Segurança
- Homologação dos Routers
- Homologação Final

Todas as fases receberam aprovação formal antes do avanço para a fase seguinte.

---

# 10. Evidência de Uso de IA

O desenvolvimento utilizou agentes especializados durante todo o ciclo SDD:

## Spec Auditor

Responsável pela auditoria da especificação OpenAPI.

---

## Tech Lead

Responsável por:

- Planejamento;
- Revisões arquiteturais;
- Homologações;
- Controle de qualidade.

---

## Backend Coder

Responsável por:

- Schemas;
- ORM;
- Segurança;
- Routers.

---

## QA Engineer

Responsável por:

- Testes automatizados;
- Validação funcional;
- Homologação técnica.

---

# 11. Resultado Final

```text
Constitution
✅ Concluído

Specify
✅ Concluído

Plan
✅ Concluído

Implement
✅ Concluído

Validate
✅ Concluído
```

O projeto Bookstore API foi desenvolvido seguindo integralmente os princípios de Spec-Driven Development (SDD), utilizando agentes de IA para planejamento, implementação e validação da solução, mantendo alinhamento total com a especificação OpenAPI derivada da aplicação real baseada em Firebase Firestore.

Status Final:

✅ PROJETO HOMOLOGADO E APROVADO PARA APRESENTAÇÃO