"""users.py — Router de gerenciamento de usuários da Bookstore API.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
"""

import math
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import ConflictException, NotFoundException
from src.api.models import SaleModel, UserModel
from src.api.schemas import (
    CreateUserDTO,
    PaginatedUsersResponse,
    PaginationMeta,
    UpdateUserDTO,
    User,
)
from src.api.security import (
    check_if_none_match,
    extract_request_id,
    generate_etag,
    get_password_hash,
    require_roles,
    verify_if_match,
)

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


def _apply_common_headers(request: Request, response: Response) -> None:
    """Propaga cabeçalhos de correlação e rate limit padronizados."""
    req_id = extract_request_id(request)
    response.headers["X-Request-Id"] = req_id
    if traceparent := request.headers.get("traceparent"):
        response.headers["traceparent"] = traceparent
    response.headers["RateLimit-Limit"] = "100"
    response.headers["RateLimit-Remaining"] = "98"
    response.headers["RateLimit-Reset"] = "60"


def _compute_user_etag(user: UserModel) -> str:
    """Gera o ETag estável de representação de um usuário."""
    raw = f"{user.id}:{user.name}:{user.email}:{user.phone}:{user.active}:{user.role}"
    return generate_etag(raw)


# ============================================================================
# Endpoints de Usuários (/api/v1/users)
# ============================================================================


@router.get(
    "",
    response_model=PaginatedUsersResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar usuários",
    description="Retorna a lista paginada de usuários com filtros e validação condicional via ETag.",
)
async def list_users(
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1, description="Página atual."),
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página."),
    role: Optional[str] = Query(default=None, description="Filtra por perfil (ADMIN ou SELLER)."),
    active: Optional[bool] = Query(default=None, description="Filtra por usuários ativos/inativos."),
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> Response:
    """Lista usuários paginados (acesso restrito ao perfil ADMIN)."""
    _apply_common_headers(request, response)

    query = db.query(UserModel)
    if role:
        query = query.filter(UserModel.role == role)
    if active is not None:
        query = query.filter(UserModel.active == active)

    total_items = query.count()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0
    has_next = page < total_pages

    users = (
        query.order_by(UserModel.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    etag_content = f"{total_items}:{page}:{limit}:{[u.id for u in users]}:{[u.active for u in users]}"
    etag = generate_etag(etag_content)

    if check_if_none_match(if_none_match, etag):
        res = Response(status_code=status.HTTP_304_NOT_MODIFIED)
        res.headers["ETag"] = etag
        res.headers["X-Request-Id"] = response.headers["X-Request-Id"]
        return res

    response.headers["ETag"] = etag

    paginated_response = PaginatedUsersResponse(
        data=[User.model_validate(u) for u in users],
        meta=PaginationMeta(
            page=page,
            limit=limit,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
        ),
    )
    return Response(
        content=paginated_response.model_dump_json(by_alias=True),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
        headers=dict(response.headers),
    )


@router.post(
    "",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário",
    description="Cadastra um novo usuário da API com senha criptografada.",
)
async def create_user(
    payload: CreateUserDTO,
    request: Request,
    response: Response,
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> User:
    """Cria um novo usuário na base de dados."""
    _apply_common_headers(request, response)

    existing_user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if existing_user:
        raise ConflictException(
            title="Recurso Duplicado",
            detail="Já existe um usuário cadastrado com o e-mail informado.",
            code="DUPLICATE_RESOURCE",
            type_uri="https://api.bookstore.dev/errors/duplicate-resource",
        )

    # Identificador alfanumérico opaco compatível com o Firestore
    user_id = secrets.token_urlsafe(16)
    hashed_password = get_password_hash(payload.password)

    new_user = UserModel(
        id=user_id,
        name=payload.name,
        email=payload.email,
        password_hash=hashed_password,
        phone=payload.phone,
        active=payload.active,
        role="SELLER",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response.headers["Location"] = f"/api/v1/users/{new_user.id}"
    return User.model_validate(new_user)


@router.get(
    "/{id}",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Obter usuário",
    description="Retorna os dados cadastrais de um usuário pelo identificador.",
)
async def get_user_by_id(
    id: str,
    request: Request,
    response: Response,
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> Response:
    """Busca usuário por identificador."""
    _apply_common_headers(request, response)

    user = db.query(UserModel).filter(UserModel.id == id).first()
    if not user:
        raise NotFoundException(
            detail="O recurso com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    etag = _compute_user_etag(user)
    if check_if_none_match(if_none_match, etag):
        res = Response(status_code=status.HTTP_304_NOT_MODIFIED)
        res.headers["ETag"] = etag
        res.headers["X-Request-Id"] = response.headers["X-Request-Id"]
        return res

    response.headers["ETag"] = etag
    user_dto = User.model_validate(user)
    return Response(
        content=user_dto.model_dump_json(by_alias=True),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
        headers=dict(response.headers),
    )


@router.patch(
    "/{id}",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Atualizar usuário (parcial)",
    description="Atualiza parcialmente dados do usuário (ex.: inativação via active: false). Suporta concorrência via If-Match.",
)
async def update_user(
    id: str,
    payload: UpdateUserDTO,
    request: Request,
    response: Response,
    if_match: Optional[str] = Header(default=None, alias="If-Match"),
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> Response:
    """Atualiza dados do usuário parcialmente."""
    _apply_common_headers(request, response)

    user = db.query(UserModel).filter(UserModel.id == id).first()
    if not user:
        raise NotFoundException(
            detail="O recurso com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    # Concorrência otimista
    current_etag = _compute_user_etag(user)
    verify_if_match(if_match, current_etag)

    if payload.name is not None:
        user.name = payload.name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.active is not None:
        user.active = payload.active

    db.commit()
    db.refresh(user)

    new_etag = _compute_user_etag(user)
    response.headers["ETag"] = new_etag

    user_dto = User.model_validate(user)
    return Response(
        content=user_dto.model_dump_json(by_alias=True),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
        headers=dict(response.headers),
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover usuário / vendedor",
    description="Exclui o operador da API. Retorna 409 se houver vendas vinculadas ao vendedor ou precondição falhar.",
)
async def delete_user(
    id: str,
    request: Request,
    response: Response,
    if_match: Optional[str] = Header(default=None, alias="If-Match"),
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> Response:
    """Remove usuário com validação de integridade referencial e auditoria de vendas."""
    _apply_common_headers(request, response)

    user = db.query(UserModel).filter(UserModel.id == id).first()
    if not user:
        raise NotFoundException(
            title="Recurso Inexistente",
            detail="O usuário com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    # Impede autoexclusão da própria conta do administrador autenticado
    if user.id == current_admin.id:
        raise ConflictException(
            title="Operação Não Permitida",
            detail="O administrador não pode excluir a própria conta conectada na sessão.",
            code="SELF_DELETION_FORBIDDEN",
        )

    # Concorrência otimista: valida se os dados do usuário sofreram alterações concorrentes
    current_etag = _compute_user_etag(user)
    verify_if_match(if_match, current_etag)

    # Regra de Integridade: impede exclusão de vendedor/usuário com vendas vinculadas
    sales_count = db.query(SaleModel).filter(SaleModel.seller_id == id).count()
    if sales_count > 0:
        raise ConflictException(
            title="Recurso em Uso",
            detail=f"O vendedor '{user.name}' possui {sales_count} venda(s) registrada(s) e não pode ser excluído do sistema. Utilize a inativação cadastral (active: false).",
            code="RESOURCE_IN_USE",
            type_uri="https://api.bookstore.dev/errors/resource-in-use",
        )

    try:
        db.delete(user)
        db.commit()
    except Exception:
        db.rollback()
        raise ConflictException(
            title="Recurso em Uso",
            detail=f"Não é possível remover o vendedor '{user.name}' devido a vínculos no histórico de vendas.",
            code="RESOURCE_IN_USE",
            type_uri="https://api.bookstore.dev/errors/resource-in-use",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=dict(response.headers))
