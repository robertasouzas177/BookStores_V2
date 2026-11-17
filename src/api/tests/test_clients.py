"""test_clients.py — Testes do CRUD de clientes e programa de fidelidade.

Casos de teste:
- CLIENT-001: POST /clients → 201 com Location header.
- CLIENT-002: GET /clients/{id} → 200.
- CLIENT-003: PATCH /clients/{id} → 200 com dado atualizado.
- CLIENT-004: DELETE /clients/{id} sem vendas → 204.
- CLIENT-005: POST /clients sem CPF → 422.
- CLIENT-006: POST /clients sem birthDate → 422.
- CLIENT-007: GET /clients/{clientId}/sales → 200 paginado.
- CLIENT-008: Listar clientes paginado → 200 com meta.
- CLIENT-009: SELLER pode criar clientes → 201.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


CLIENTS_URL = "/api/v1/clients"

_VALID_CLIENT = {
    "name": "Maria Oliveira",
    "email": "maria.oliveira@example.com",
    "phone": "11988765432",
    "cpf": "71428793860",
    "birthDate": "15/06/1990",
    "active": True,
}


# ---------------------------------------------------------------------------
# CLIENT-001 — Criar cliente
# ---------------------------------------------------------------------------


def test_client001_criar_cliente(client: TestClient, admin_headers: dict) -> None:
    """CLIENT-001: POST /clients → 201 com Location e pontuação inicial 0."""
    response = client.post(CLIENTS_URL, json=_VALID_CLIENT, headers=admin_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert "id" in body
    assert body["email"] == _VALID_CLIENT["email"]
    assert body["cpf"] == _VALID_CLIENT["cpf"]
    assert body["loyaltyPoints"] == 0
    assert "location" in response.headers
    assert "/api/v1/clients/" in response.headers["location"]


# ---------------------------------------------------------------------------
# CLIENT-002 — Obter cliente por ID
# ---------------------------------------------------------------------------


def test_client002_obter_cliente_por_id(client: TestClient, admin_headers: dict) -> None:
    """CLIENT-002: GET /clients/{id} → 200 com campos corretos."""
    create_resp = client.post(CLIENTS_URL, json=_VALID_CLIENT, headers=admin_headers)
    assert create_resp.status_code == 201
    client_id = create_resp.json()["id"]

    response = client.get(f"{CLIENTS_URL}/{client_id}", headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == client_id
    assert body["email"] == _VALID_CLIENT["email"]
    assert body["cpf"] == _VALID_CLIENT["cpf"]
    assert "loyaltyPoints" in body
    assert "active" in body


# ---------------------------------------------------------------------------
# CLIENT-003 — Atualizar cliente
# ---------------------------------------------------------------------------


def test_client003_atualizar_cliente(client: TestClient, admin_headers: dict) -> None:
    """CLIENT-003: PATCH /clients/{id} → 200 com nome atualizado."""
    create_resp = client.post(CLIENTS_URL, json=_VALID_CLIENT, headers=admin_headers)
    assert create_resp.status_code == 201
    client_id = create_resp.json()["id"]

    get_resp = client.get(f"{CLIENTS_URL}/{client_id}", headers=admin_headers)
    etag = get_resp.headers.get("etag", "")

    patch_headers = {**admin_headers, "If-Match": etag}
    response = client.patch(
        f"{CLIENTS_URL}/{client_id}",
        json={"name": "Maria Silva Atualizada"},
        headers=patch_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Maria Silva Atualizada"
    assert body["id"] == client_id


# ---------------------------------------------------------------------------
# CLIENT-004 — Deletar cliente sem vendas
# ---------------------------------------------------------------------------


def test_client004_deletar_cliente_sem_vendas(client: TestClient, admin_headers: dict) -> None:
    """CLIENT-004: DELETE /clients/{id} sem vendas → 204."""
    create_resp = client.post(CLIENTS_URL, json=_VALID_CLIENT, headers=admin_headers)
    assert create_resp.status_code == 201
    client_id = create_resp.json()["id"]

    response = client.delete(f"{CLIENTS_URL}/{client_id}", headers=admin_headers)

    assert response.status_code == 204
    assert response.content == b""

    # Confirma remoção
    get_resp = client.get(f"{CLIENTS_URL}/{client_id}", headers=admin_headers)
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# CLIENT-005 — Sem CPF → 422
# ---------------------------------------------------------------------------


def test_client005_sem_cpf(client: TestClient, admin_headers: dict) -> None:
    """CLIENT-005: POST /clients sem campo cpf → 422."""
    payload_sem_cpf = {
        "name": "Teste",
        "email": "semcpf@example.com",
        "phone": "11000000000",
        "birthDate": "01/01/1980",
        "active": True,
    }
    response = client.post(CLIENTS_URL, json=payload_sem_cpf, headers=admin_headers)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422
    assert response.headers.get("content-type", "").startswith("application/problem+json")


# ---------------------------------------------------------------------------
# CLIENT-006 — Sem birthDate → 422
# ---------------------------------------------------------------------------


def test_client006_sem_birth_date(client: TestClient, admin_headers: dict) -> None:
    """CLIENT-006: POST /clients sem campo birthDate → 422."""
    payload_sem_birth = {
        "name": "Teste",
        "email": "semnascimento@example.com",
        "phone": "11000000001",
        "cpf": "12345678901",
        "active": True,
    }
    response = client.post(CLIENTS_URL, json=payload_sem_birth, headers=admin_headers)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422


# ---------------------------------------------------------------------------
# CLIENT-007 — Histórico de vendas do cliente
# ---------------------------------------------------------------------------


def test_client007_historico_vendas_cliente(
    client: TestClient,
    admin_headers: dict,
    db: Session,
) -> None:
    """CLIENT-007: GET /clients/{clientId}/sales → 200 paginado."""
    # Usa o cliente seed
    seed_client_id = "8NV1c7Q4TCYGcsuPch8I"

    response = client.get(f"{CLIENTS_URL}/{seed_client_id}/sales", headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert "data" in body
    assert "meta" in body
    meta = body["meta"]
    assert "totalItems" in meta
    assert "page" in meta
    assert "hasNext" in meta


# ---------------------------------------------------------------------------
# CLIENT-008 — Lista paginada de clientes
# ---------------------------------------------------------------------------


def test_client008_listar_clientes_paginado(client: TestClient, admin_headers: dict) -> None:
    """CLIENT-008: GET /clients → 200 com estrutura de paginação."""
    response = client.get(CLIENTS_URL, headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert "data" in body
    assert "meta" in body
    meta = body["meta"]
    assert "totalItems" in meta
    # Seeds garantem pelo menos 1 cliente
    assert meta["totalItems"] >= 1


# ---------------------------------------------------------------------------
# CLIENT-009 — SELLER pode criar clientes
# ---------------------------------------------------------------------------


def test_client009_seller_pode_criar_cliente(client: TestClient, seller_headers: dict) -> None:
    """CLIENT-009: SELLER tem permissão para POST /clients → 201."""
    payload = {**_VALID_CLIENT, "email": "seller.client@example.com", "cpf": "52998224726"}
    response = client.post(CLIENTS_URL, json=payload, headers=seller_headers)

    assert response.status_code == 201, response.text
