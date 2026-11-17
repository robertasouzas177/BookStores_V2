"""conftest.py — Configuração de fixtures e banco isolado para a suíte de testes.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
- docs/TESTS.md
"""

from typing import Generator
import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.database import Base, get_db, seed_initial_data
from src.api.exceptions import (
    ApiErrorException,
    api_error_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.api.models import UserModel
from src.api.routers.auth import health_router, router as auth_router
from src.api.routers.clients import router as clients_router
from src.api.routers.products import router as products_router
from src.api.routers.sales import router as sales_router
from src.api.routers.users import router as users_router
from src.api.security import create_access_token

# ============================================================================
# Banco de Dados em Memória SQLite Isolado
# ============================================================================

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Garante integridade referencial mandatória no SQLite durante os testes."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


# ============================================================================
# Instância de Aplicação FastAPI para Testes
# ============================================================================


def create_test_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI com todos os routers e handlers RFC 9457."""
    test_app = FastAPI(title="Bookstore API - Test Suite")

    # Registro oficial dos exception handlers RFC 9457
    test_app.add_exception_handler(ApiErrorException, api_error_exception_handler)
    test_app.add_exception_handler(RequestValidationError, validation_exception_handler)
    test_app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Registro de todos os routers da Bookstore API
    test_app.include_router(auth_router)
    test_app.include_router(health_router)
    test_app.include_router(users_router)
    test_app.include_router(products_router)
    test_app.include_router(clients_router)
    test_app.include_router(sales_router)

    return test_app


app = create_test_app()


# ============================================================================
# Fixtures Reutilizáveis do Pytest
# ============================================================================


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Cria tabelas, popula dados iniciais de seed e limpa após cada teste."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_initial_data(session)

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Cliente HTTP com override de get_db apontando para o banco isolado."""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_token(db: Session) -> str:
    """Gera token de autenticação JWT para o perfil ADMIN."""
    admin_user = db.query(UserModel).filter(UserModel.email == "admin@api.com").first()
    token, _ = create_access_token(
        user_id=admin_user.id,
        email=admin_user.email,
        role="ADMIN",
    )
    return token


@pytest.fixture(scope="function")
def seller_token(db: Session) -> str:
    """Gera token de autenticação JWT para o perfil SELLER."""
    seller_user = db.query(UserModel).filter(UserModel.email == "vendedor@example.com").first()
    token, _ = create_access_token(
        user_id=seller_user.id,
        email=seller_user.email,
        role="SELLER",
    )
    return token


@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict:
    """Cabeçalhos contendo Bearer token do perfil ADMIN."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def seller_headers(seller_token: str) -> dict:
    """Cabeçalhos contendo Bearer token do perfil SELLER."""
    return {"Authorization": f"Bearer {seller_token}"}
