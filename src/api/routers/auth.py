"""auth.py — Router de autenticação e gestão de sessões da Bookstore API.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
"""

from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import UnauthorizedException
from src.api.models import UserModel
from src.api.schemas import (
    HealthCheck,
    HealthResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    User,
)
from src.api.security import (
    create_access_token,
    create_refresh_token,
    extract_request_id,
    get_current_user,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
health_router = APIRouter(tags=["Health"])


def _apply_common_headers(request: Request, response: Response) -> None:
    """Propaga cabeçalhos de correlação e rate limit padronizados."""
    req_id = extract_request_id(request)
    response.headers["X-Request-Id"] = req_id
    if traceparent := request.headers.get("traceparent"):
        response.headers["traceparent"] = traceparent
    # Cabeçalhos padrão de rate limit
    response.headers["RateLimit-Limit"] = "100"
    response.headers["RateLimit-Remaining"] = "95"
    response.headers["RateLimit-Reset"] = "60"


# ============================================================================
# Endpoints de Autenticação (/api/v1/auth)
# ============================================================================


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Autenticar usuário",
    description="Autentica com e-mail e senha e retorna um access token e um refresh token com rotação.",
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Autentica usuário e retorna tokens de acesso e renovação."""
    _apply_common_headers(request, response)

    user = db.query(UserModel).filter(UserModel.email == payload.email).first()

    # Mensagem de erro genérica para não revelar existência prévia de e-mail
    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedException(
            title="Credenciais Inválidas",
            detail="E-mail ou senha incorretos.",
            code="INVALID_CREDENTIALS",
            type_uri="https://api.bookstore.dev/errors/invalid-credentials",
        )

    if not user.active:
        raise UnauthorizedException(
            title="Não Autenticado",
            detail="A conta de usuário está inativa.",
            code="USER_INACTIVE",
        )

    access_token, access_exp = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )
    refresh_token, refresh_exp = create_refresh_token(
        user_id=user.id,
        db=db,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=access_exp,
        refresh_expires_in=refresh_exp,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Renovar tokens (rotação)",
    description="Troca um refresh token válido por um novo par de tokens com rotação e detecção de reuso.",
)
async def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Executa a rotação de refresh token."""
    _apply_common_headers(request, response)

    new_access, new_refresh, access_exp, refresh_exp = rotate_refresh_token(
        raw_refresh_token=payload.refresh_token,
        db=db,
    )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="Bearer",
        expires_in=access_exp,
        refresh_expires_in=refresh_exp,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerrar sessão",
    description="Revoga o refresh token informado e toda a sua família de sessões.",
)
async def logout(
    payload: RefreshRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Response:
    """Invalida a família do refresh token informado."""
    _apply_common_headers(request, response)
    revoke_refresh_token(payload.refresh_token, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=dict(response.headers))


@router.get(
    "/me",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Obter usuário autenticado",
    description="Retorna os dados cadastrais e o perfil de permissão do usuário dono do token.",
)
async def get_me(
    request: Request,
    response: Response,
    current_user: UserModel = Depends(get_current_user),
) -> User:
    """Retorna o perfil do usuário logado."""
    _apply_common_headers(request, response)
    response.headers["Cache-Control"] = "no-store"
    return User.model_validate(current_user)


# ============================================================================
# Sondas de Saúde (/health/live e /health/ready)
# ============================================================================


@health_router.get(
    "/health/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Indica se o processo da aplicação está vivo.",
)
async def health_live(request: Request, response: Response) -> HealthResponse:
    """Sonda de liveness."""
    req_id = extract_request_id(request)
    response.headers["X-Request-Id"] = req_id
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse(status="UP")


@health_router.get(
    "/health/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Indica se a instância está pronta para receber tráfego com banco conectado.",
)
async def health_ready(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Response:
    """Sonda de readiness validando conectividade com o banco de dados."""
    req_id = extract_request_id(request)
    headers = {
        "X-Request-Id": req_id,
        "Cache-Control": "no-store",
    }
    checks = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = HealthCheck(status="UP", latency_ms=1)
        resp_obj = HealthResponse(status="UP", checks=checks)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=resp_obj.model_dump(by_alias=True, mode="json"),
            headers=headers,
        )
    except Exception:
        checks["database"] = HealthCheck(status="DOWN")
        resp_obj = HealthResponse(status="DOWN", checks=checks)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=resp_obj.model_dump(by_alias=True, mode="json"),
            headers=headers,
        )
