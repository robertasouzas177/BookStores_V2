"""test_auth.py — Testes de autenticação e gestão de sessão.

Casos de teste:
- AUTH-001: Login válido retorna par de tokens.
- AUTH-002: Login com senha errada → 401 INVALID_CREDENTIALS.
- AUTH-003: Login com e-mail inexistente → 401 INVALID_CREDENTIALS.
- AUTH-004: GET /me sem token → 401 AUTH_TOKEN_MISSING.
- AUTH-005: GET /me com token expirado → 401 AUTH_TOKEN_EXPIRED.
- AUTH-006: POST /refresh com token válido → novo par de tokens.
- AUTH-007: POST /refresh com token inválido → 401.
- AUTH-008: POST /logout com token válido → 204.
- AUTH-009: GET /me com token válido → dados do usuário.
- AUTH-010: Reutilização de refresh token → 401 REFRESH_TOKEN_REUSED.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.security import JWT_ALGORITHM, JWT_SECRET_KEY, create_refresh_token

# ---------------------------------------------------------------------------
# Constantes reutilizáveis
# ---------------------------------------------------------------------------

LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"

ADMIN_EMAIL = "admin@api.com"
ADMIN_PASSWORD = "Sup3rS3cr3t!"

SELLER_EMAIL = "vendedor@example.com"
SELLER_PASSWORD = "Sup3rS3cr3t!"


# ---------------------------------------------------------------------------
# AUTH-001 — Login válido
# ---------------------------------------------------------------------------


def test_auth001_login_valido_retorna_tokens(client: TestClient) -> None:
    """AUTH-001: POST /login com credenciais corretas → 200 com par de tokens."""
    response = client.post(LOGIN_URL, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    assert response.status_code == 200, response.text

    body = response.json()
    assert "accessToken" in body
    assert "refreshToken" in body
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 900
    assert body["refreshExpiresIn"] == 1209600
    assert isinstance(body["accessToken"], str)
    assert len(body["accessToken"]) > 10


# ---------------------------------------------------------------------------
# AUTH-002 — Login com senha errada
# ---------------------------------------------------------------------------


def test_auth002_login_senha_errada(client: TestClient) -> None:
    """AUTH-002: POST /login com senha incorreta → 401 INVALID_CREDENTIALS."""
    response = client.post(LOGIN_URL, json={"email": ADMIN_EMAIL, "password": "SenhaErrada!"})

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "INVALID_CREDENTIALS"
    assert body["status"] == 401
    assert response.headers.get("content-type", "").startswith("application/problem+json")


# ---------------------------------------------------------------------------
# AUTH-003 — Login com e-mail inexistente
# ---------------------------------------------------------------------------


def test_auth003_login_email_inexistente(client: TestClient) -> None:
    """AUTH-003: POST /login com e-mail não cadastrado → 401 INVALID_CREDENTIALS."""
    response = client.post(LOGIN_URL, json={"email": "naoexiste@example.com", "password": "Qualquer1!"})

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "INVALID_CREDENTIALS"
    assert body["status"] == 401


# ---------------------------------------------------------------------------
# AUTH-004 — GET /me sem token
# ---------------------------------------------------------------------------


def test_auth004_me_sem_token(client: TestClient) -> None:
    """AUTH-004: GET /me sem cabeçalho Authorization → 401 AUTH_TOKEN_MISSING."""
    response = client.get(ME_URL)

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "AUTH_TOKEN_MISSING"


# ---------------------------------------------------------------------------
# AUTH-005 — GET /me com token expirado
# ---------------------------------------------------------------------------


def test_auth005_me_token_expirado(client: TestClient) -> None:
    """AUTH-005: GET /me com token expirado → 401 AUTH_TOKEN_EXPIRED."""
    # Forja token expirado há 1 segundo
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    expired_payload = {
        "sub": "SDMXDsjJtqcqK1nWnrk0YjQDqPY2",
        "email": ADMIN_EMAIL,
        "role": "ADMIN",
        "iat": int((past - timedelta(seconds=900)).timestamp()),
        "exp": int(past.timestamp()),
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "AUTH_TOKEN_EXPIRED"


# ---------------------------------------------------------------------------
# AUTH-006 — POST /refresh com token válido
# ---------------------------------------------------------------------------


def test_auth006_refresh_valido_retorna_novo_par(client: TestClient, db: Session) -> None:
    """AUTH-006: POST /refresh com refresh token válido → novo par de tokens."""
    # Faz login para obter refresh token real
    login_resp = client.post(LOGIN_URL, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refreshToken"]

    response = client.post(REFRESH_URL, json={"refreshToken": refresh_token})

    assert response.status_code == 200, response.text
    body = response.json()
    assert "accessToken" in body
    assert "refreshToken" in body
    # Novo refresh token deve ser diferente do anterior (rotação)
    assert body["refreshToken"] != refresh_token


# ---------------------------------------------------------------------------
# AUTH-007 — POST /refresh com token inválido
# ---------------------------------------------------------------------------


def test_auth007_refresh_token_invalido(client: TestClient) -> None:
    """AUTH-007: POST /refresh com token inválido → 401."""
    response = client.post(REFRESH_URL, json={"refreshToken": "token-completamente-invalido"})

    assert response.status_code == 401
    body = response.json()
    assert body["status"] == 401


# ---------------------------------------------------------------------------
# AUTH-008 — POST /logout
# ---------------------------------------------------------------------------


def test_auth008_logout_valido(client: TestClient) -> None:
    """AUTH-008: POST /logout com refresh token válido → 204 No Content."""
    login_resp = client.post(LOGIN_URL, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refreshToken"]

    response = client.post(LOGOUT_URL, json={"refreshToken": refresh_token})

    assert response.status_code == 204
    assert response.content == b""


# ---------------------------------------------------------------------------
# AUTH-009 — GET /me com token válido
# ---------------------------------------------------------------------------


def test_auth009_me_com_token_valido(client: TestClient, admin_headers: dict) -> None:
    """AUTH-009: GET /me com token válido → 200 com dados do usuário autenticado."""
    response = client.get(ME_URL, headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email"] == ADMIN_EMAIL
    assert body["role"] == "ADMIN"
    assert "id" in body
    assert "name" in body
    assert "active" in body


# ---------------------------------------------------------------------------
# AUTH-010 — Reutilização de refresh token (token rotation reuse detection)
# ---------------------------------------------------------------------------


def test_auth010_refresh_token_reuse_detectado(client: TestClient) -> None:
    """AUTH-010: Reuso de refresh token já rotacionado → 401 REFRESH_TOKEN_REUSED."""
    # 1. Login → obter refresh token original
    login_resp = client.post(LOGIN_URL, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert login_resp.status_code == 200
    original_refresh = login_resp.json()["refreshToken"]

    # 2. Primeira rotação — válida
    first_refresh_resp = client.post(REFRESH_URL, json={"refreshToken": original_refresh})
    assert first_refresh_resp.status_code == 200

    # 3. Segunda rotação com o token ORIGINAL (já usado) → deve ser bloqueada
    reuse_resp = client.post(REFRESH_URL, json={"refreshToken": original_refresh})

    assert reuse_resp.status_code == 401
    body = reuse_resp.json()
    assert body["code"] == "REFRESH_TOKEN_REUSED"
