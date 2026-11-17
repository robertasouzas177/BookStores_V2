"""test_users.py — Testes do CRUD de usuários.

Casos de teste:
- USER-001: POST /users como ADMIN → 201 com Location header.
- USER-002: GET /users/{id} → 200 com dados corretos.
- USER-003: PATCH /users/{id} → 200 com nome atualizado.
- USER-004: PATCH /users/{id} com active=false → 200, usuário inativado.
- USER-005: GET /users/{id} ID inexistente → 404 NOT_FOUND.
- USER-006: GET /users (lista paginada) → 200 com meta.
- USER-007: SELLER não pode acessar /users → 403 INSUFFICIENT_PERMISSIONS.
- USER-008: POST /users com e-mail duplicado → 409 DUPLICATE_RESOURCE.
"""

from fastapi.testclient import TestClient


USERS_URL = "/api/v1/users"

# Payload válido para criação de usuário
_NEW_USER_PAYLOAD = {
    "name": "Novo Vendedor",
    "email": "novo.vendedor@example.com",
    "password": "SenhaTemporaria123!",
    "phone": "11999887766",
    "active": True,
}


# ---------------------------------------------------------------------------
# USER-001 — Criar usuário como ADMIN
# ---------------------------------------------------------------------------


def test_user001_criar_usuario_admin(client: TestClient, admin_headers: dict) -> None:
    """USER-001: POST /users como ADMIN → 201 com cabeçalho Location."""
    response = client.post(USERS_URL, json=_NEW_USER_PAYLOAD, headers=admin_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert "id" in body
    assert body["email"] == _NEW_USER_PAYLOAD["email"]
    assert body["name"] == _NEW_USER_PAYLOAD["name"]
    assert "location" in response.headers
    assert "/api/v1/users/" in response.headers["location"]


# ---------------------------------------------------------------------------
# USER-002 — Obter usuário por ID
# ---------------------------------------------------------------------------


def test_user002_obter_usuario_por_id(client: TestClient, admin_headers: dict) -> None:
    """USER-002: GET /users/{id} → 200 com campos corretos."""
    # Cria usuário primeiro
    create_resp = client.post(USERS_URL, json=_NEW_USER_PAYLOAD, headers=admin_headers)
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    response = client.get(f"{USERS_URL}/{user_id}", headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == user_id
    assert body["email"] == _NEW_USER_PAYLOAD["email"]
    assert body["name"] == _NEW_USER_PAYLOAD["name"]
    assert "active" in body
    assert "role" in body


# ---------------------------------------------------------------------------
# USER-003 — Atualizar nome do usuário
# ---------------------------------------------------------------------------


def test_user003_atualizar_nome(client: TestClient, admin_headers: dict) -> None:
    """USER-003: PATCH /users/{id} → 200 com nome atualizado."""
    create_resp = client.post(USERS_URL, json=_NEW_USER_PAYLOAD, headers=admin_headers)
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    # Obtém ETag atual
    get_resp = client.get(f"{USERS_URL}/{user_id}", headers=admin_headers)
    etag = get_resp.headers.get("etag", "")

    patch_headers = {**admin_headers, "If-Match": etag}
    response = client.patch(
        f"{USERS_URL}/{user_id}",
        json={"name": "Nome Atualizado"},
        headers=patch_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Nome Atualizado"
    assert body["id"] == user_id


# ---------------------------------------------------------------------------
# USER-004 — Inativar usuário
# ---------------------------------------------------------------------------


def test_user004_inativar_usuario(client: TestClient, admin_headers: dict) -> None:
    """USER-004: PATCH /users/{id} com active=false → 200, usuário inativado."""
    create_resp = client.post(USERS_URL, json=_NEW_USER_PAYLOAD, headers=admin_headers)
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    get_resp = client.get(f"{USERS_URL}/{user_id}", headers=admin_headers)
    etag = get_resp.headers.get("etag", "")

    patch_headers = {**admin_headers, "If-Match": etag}
    response = client.patch(
        f"{USERS_URL}/{user_id}",
        json={"active": False},
        headers=patch_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["active"] is False


# ---------------------------------------------------------------------------
# USER-005 — ID inexistente → 404
# ---------------------------------------------------------------------------


def test_user005_id_inexistente(client: TestClient, admin_headers: dict) -> None:
    """USER-005: GET /users/{id} com ID inexistente → 404 NOT_FOUND."""
    response = client.get(f"{USERS_URL}/IDQUENAOEXISTE", headers=admin_headers)

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "NOT_FOUND"
    assert body["status"] == 404
    assert response.headers.get("content-type", "").startswith("application/problem+json")


# ---------------------------------------------------------------------------
# USER-006 — Lista paginada de usuários
# ---------------------------------------------------------------------------


def test_user006_listar_usuarios_paginado(client: TestClient, admin_headers: dict) -> None:
    """USER-006: GET /users → 200 com estrutura de paginação."""
    response = client.get(USERS_URL, headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert "data" in body
    assert "meta" in body
    meta = body["meta"]
    assert "page" in meta
    assert "limit" in meta
    assert "totalItems" in meta
    assert "totalPages" in meta
    assert "hasNext" in meta
    # Seeds garantem pelo menos 2 usuários (ADMIN + SELLER)
    assert meta["totalItems"] >= 2


# ---------------------------------------------------------------------------
# USER-007 — SELLER não pode acessar /users
# ---------------------------------------------------------------------------


def test_user007_seller_nao_acessa_users(client: TestClient, seller_headers: dict) -> None:
    """USER-007: SELLER tentando GET /users → 403 INSUFFICIENT_PERMISSIONS."""
    response = client.get(USERS_URL, headers=seller_headers)

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "INSUFFICIENT_PERMISSIONS"
    assert body["status"] == 403


# ---------------------------------------------------------------------------
# USER-008 — E-mail duplicado → 409
# ---------------------------------------------------------------------------


def test_user008_email_duplicado(client: TestClient, admin_headers: dict) -> None:
    """USER-008: POST /users com e-mail já cadastrado → 409 DUPLICATE_RESOURCE."""
    # Cria usuário pela primeira vez
    client.post(USERS_URL, json=_NEW_USER_PAYLOAD, headers=admin_headers)

    # Tenta criar com o mesmo e-mail novamente
    response = client.post(USERS_URL, json=_NEW_USER_PAYLOAD, headers=admin_headers)

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "DUPLICATE_RESOURCE"
    assert body["status"] == 409
