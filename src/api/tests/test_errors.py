"""test_errors.py — Testes de conformidade RFC 9457 (Problem Details).

Casos de teste:
- ERROR-001: 400 Bad Request → application/problem+json com campos obrigatórios.
- ERROR-002: 401 Unauthorized → formato RFC 9457.
- ERROR-003: 403 Forbidden → INSUFFICIENT_PERMISSIONS.
- ERROR-004: 404 Not Found → NOT_FOUND.
- ERROR-005: 409 Conflict → INSUFFICIENT_STOCK ou DUPLICATE_RESOURCE.
- ERROR-006: 412 Precondition Failed → If-Match inválido.
- ERROR-007: 422 Unprocessable Entity → invalidParams array.
- ERROR-008: 429 Too Many Requests → TooManyRequestsException diretamente.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.exceptions import TooManyRequestsException


# Constantes de URLs
USERS_URL = "/api/v1/users"
PRODUCTS_URL = "/api/v1/products"
CLIENTS_URL = "/api/v1/clients"
SALES_URL = "/api/v1/sales"
LOGIN_URL = "/api/v1/auth/login"

SEED_PRODUCT_ID = "KIYBXACS6uVj5DbKEsPQ"
SEED_CLIENT_ID = "8NV1c7Q4TCYGcsuPch8I"


def _assert_problem_json(response, expected_status: int) -> dict:
    """Helper que verifica o Content-Type RFC 9457 e status code."""
    assert response.status_code == expected_status, response.text
    ct = response.headers.get("content-type", "")
    assert "application/problem+json" in ct, f"Content-Type esperado application/problem+json, obtido: {ct}"
    body = response.json()
    assert "type" in body, "Campo 'type' ausente no RFC 9457"
    assert "title" in body, "Campo 'title' ausente no RFC 9457"
    assert "status" in body, "Campo 'status' ausente no RFC 9457"
    assert body["status"] == expected_status
    return body


# ---------------------------------------------------------------------------
# ERROR-001 — 400 Bad Request
# ---------------------------------------------------------------------------


def test_error001_400_bad_request(client: TestClient, admin_headers: dict) -> None:
    """ERROR-001: Payload de login malformado → 422 (FastAPI recusa antes de 400)."""
    # Envia body inválido (campo obrigatório ausente)
    response = client.post(LOGIN_URL, json={"email": "admin@api.com"})  # sem password

    # FastAPI/Pydantic retorna 422 para campos obrigatórios ausentes
    assert response.status_code == 422
    body = _assert_problem_json(response, 422)
    assert body.get("code") == "VALIDATION_FAILED"


# ---------------------------------------------------------------------------
# ERROR-002 — 401 Unauthorized
# ---------------------------------------------------------------------------


def test_error002_401_unauthorized_estrutura(client: TestClient) -> None:
    """ERROR-002: 401 Unauthorized → corpo RFC 9457 com todos os campos obrigatórios."""
    response = client.get("/api/v1/auth/me")  # sem token

    body = _assert_problem_json(response, 401)
    assert "code" in body
    assert body["code"] == "AUTH_TOKEN_MISSING"
    assert "detail" in body


# ---------------------------------------------------------------------------
# ERROR-003 — 403 Forbidden
# ---------------------------------------------------------------------------


def test_error003_403_forbidden(client: TestClient, seller_headers: dict) -> None:
    """ERROR-003: SELLER tentando rota ADMIN-only → 403 INSUFFICIENT_PERMISSIONS."""
    response = client.get(USERS_URL, headers=seller_headers)

    body = _assert_problem_json(response, 403)
    assert body["code"] == "INSUFFICIENT_PERMISSIONS"
    assert "detail" in body


# ---------------------------------------------------------------------------
# ERROR-004 — 404 Not Found
# ---------------------------------------------------------------------------


def test_error004_404_not_found(client: TestClient, admin_headers: dict) -> None:
    """ERROR-004: Recurso inexistente → 404 NOT_FOUND RFC 9457."""
    response = client.get(f"{USERS_URL}/IDQUENAOEXISTE9999", headers=admin_headers)

    body = _assert_problem_json(response, 404)
    assert body["code"] == "NOT_FOUND"
    assert "instance" in body
    assert "detail" in body


# ---------------------------------------------------------------------------
# ERROR-005 — 409 Conflict (INSUFFICIENT_STOCK)
# ---------------------------------------------------------------------------


def test_error005_409_insufficient_stock(client: TestClient, admin_headers: dict) -> None:
    """ERROR-005: Venda com estoque insuficiente → 409 INSUFFICIENT_STOCK RFC 9457."""
    payload = {
        "clientId": SEED_CLIENT_ID,
        "paymentMethod": "CREDIT_CARD",
        "items": [{"productId": SEED_PRODUCT_ID, "quantity": 9999}],
    }
    response = client.post(SALES_URL, json=payload, headers=admin_headers)

    body = _assert_problem_json(response, 409)
    assert body["code"] == "INSUFFICIENT_STOCK"
    assert "detail" in body


# ---------------------------------------------------------------------------
# ERROR-005b — 409 Conflict (DUPLICATE_RESOURCE)
# ---------------------------------------------------------------------------


def test_error005b_409_duplicate_resource(client: TestClient, admin_headers: dict) -> None:
    """ERROR-005b: E-mail de usuário duplicado → 409 DUPLICATE_RESOURCE."""
    payload = {
        "name": "Usuário Duplicado",
        "email": "admin@api.com",  # já existe no seed
        "password": "Senha123!",
        "phone": "11999999999",
        "active": True,
    }
    response = client.post(USERS_URL, json=payload, headers=admin_headers)

    body = _assert_problem_json(response, 409)
    assert body["code"] == "DUPLICATE_RESOURCE"


# ---------------------------------------------------------------------------
# ERROR-006 — 412 Precondition Failed (If-Match inválido)
# ---------------------------------------------------------------------------


def test_error006_412_precondition_failed(client: TestClient, admin_headers: dict) -> None:
    """ERROR-006: PATCH com If-Match desatualizado → 412 PRECONDITION_FAILED."""
    # Busca um usuário existente do seed
    list_resp = client.get(USERS_URL, headers=admin_headers)
    assert list_resp.status_code == 200
    users = list_resp.json()["data"]
    assert len(users) > 0
    user_id = users[0]["id"]

    # PATCH com ETag intencionalmente errado
    headers_with_bad_etag = {**admin_headers, "If-Match": 'W/"etag-completamente-errado"'}
    response = client.patch(
        f"{USERS_URL}/{user_id}",
        json={"name": "Novo Nome"},
        headers=headers_with_bad_etag,
    )

    body = _assert_problem_json(response, 412)
    assert body["code"] == "PRECONDITION_FAILED"


# ---------------------------------------------------------------------------
# ERROR-007 — 422 Unprocessable Entity com invalidParams
# ---------------------------------------------------------------------------


def test_error007_422_invalid_params(client: TestClient, admin_headers: dict) -> None:
    """ERROR-007: Payload inválido → 422 com invalidParams array."""
    # Envia produto sem campo obrigatório 'code'
    payload_invalido = {
        "title": "Sem Código",
        "author": "Autor",
        "isbn": "9788533613379",
        "price": 50,
        "stock": 1,
        # 'code' ausente
    }
    response = client.post(PRODUCTS_URL, json=payload_invalido, headers=admin_headers)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422
    assert "invalidParams" in body
    assert isinstance(body["invalidParams"], list)
    assert len(body["invalidParams"]) > 0
    # Cada item deve ter 'name' e 'reason'
    for param in body["invalidParams"]:
        assert "name" in param
        assert "reason" in param


# ---------------------------------------------------------------------------
# ERROR-008 — 429 Too Many Requests
# ---------------------------------------------------------------------------


def test_error008_429_too_many_requests(client: TestClient) -> None:
    """ERROR-008: TooManyRequestsException → verifica estrutura RFC 9457 da exceção."""
    exc = TooManyRequestsException(
        detail="Limite de requisições excedido.",
        retry_after=60,
    )
    assert exc.status_code == 429
    assert exc.code == "TOO_MANY_REQUESTS"
    assert exc.headers.get("Retry-After") == "60"
    assert exc.title == "Muitas Requisições"
