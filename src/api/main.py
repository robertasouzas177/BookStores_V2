"""main.py — Ponto de entrada ASGI da Bookstore API.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
"""

from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.database import init_db
from src.api.exceptions import (
    ApiErrorException,
    api_error_exception_handler,
    http_exception_handler,
    integrity_exception_handler,
    validation_exception_handler,
)
from src.api.routers.auth import health_router, router as auth_router
from src.api.routers.clients import router as clients_router
from src.api.routers.products import router as products_router
from src.api.routers.sales import router as sales_router
from src.api.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (startup e shutdown)."""
    # 1. Startup: inicialização de tabelas e carregamento dos seeds oficiais no SQLite
    init_db()
    yield
    # 2. Shutdown: liberação de recursos quando necessário


# 1. Instância central da aplicação FastAPI com metadados do contrato OpenAPI
app = FastAPI(
    title="Bookstore API",
    version="1.0.0",
    description=(
        "API REST corporativa para gerenciamento de livrarias, controle de catálogo de livros, "
        "clientes, autenticação JWT, programa de fidelidade e checkout transacional com idempotência, "
        "concorrência otimista (ETags) e observabilidade padronizada sob RFC 9457."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 2. Configuração de Middleware CORS para comunicação com a aplicação web da demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "ETag",
        "X-Request-Id",
        "RateLimit-Limit",
        "RateLimit-Remaining",
        "RateLimit-Reset",
        "Idempotency-Replayed",
        "Location",
    ],
)

# 3. Registro dos handlers de exceção canônicos padronizados sob a RFC 9457
app.add_exception_handler(ApiErrorException, api_error_exception_handler)
app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# 4. Registro de todos os routers oficiais da Bookstore API
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(clients_router)
app.include_router(sales_router)


# 5. Bloco de execução direta para compatibilidade com execução via script
if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
