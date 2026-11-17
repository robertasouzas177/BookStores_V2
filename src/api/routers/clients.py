"""clients.py — Router de gerenciamento de clientes e programa de fidelidade.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
"""

import math
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import ConflictException, NotFoundException
from src.api.models import ClientModel, SaleModel, UserModel
from src.api.schemas import (
    Client,
    CreateClientDTO,
    PaginatedClientsResponse,
    PaginatedSalesResponse,
    PaginationMeta,
    Sale,
    SaleItem,
    UpdateClientDTO,
)
from src.api.security import (
    check_if_none_match,
    extract_request_id,
    generate_etag,
    require_roles,
    verify_if_match,
)

router = APIRouter(prefix="/api/v1/clients", tags=["Clients"])


def _apply_common_headers(request: Request, response: Response) -> None:
    """Propaga cabeçalhos de correlação e rate limit padronizados."""
    req_id = extract_request_id(request)
    response.headers["X-Request-Id"] = req_id
    if traceparent := request.headers.get("traceparent"):
        response.headers["traceparent"] = traceparent
    response.headers["RateLimit-Limit"] = "100"
    response.headers["RateLimit-Remaining"] = "98"
    response.headers["RateLimit-Reset"] = "60"


def _compute_client_etag(client: ClientModel) -> str:
    """Gera o ETag estável de representação de um cliente."""
    raw = f"{client.id}:{client.name}:{client.email}:{client.cpf}:{client.loyalty_points}:{client.active}"
    return generate_etag(raw)


def _serialize_sale(sale: SaleModel) -> Sale:
    """Converte um SaleModel em DTO Sale com relacionamentos aninhados."""
    items_dto = [
        SaleItem(
            product_id=item.product_id,
            title=item.title,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        for item in sale.items
    ]
    client_name = sale.client.name if sale.client else None
    seller_name = sale.seller.name if sale.seller else (sale.seller.email if sale.seller else None)

    return Sale(
        id=sale.id,
        client_id=sale.client_id,
        client_name=client_name,
        seller_id=sale.seller_id,
        seller_name=seller_name,
        items=items_dto,
        gross_total=sale.gross_total,
        discount=sale.discount,
        final_total=sale.final_total,
        payment_method=sale.payment_method,
        created_at=sale.created_at,
    )


# ============================================================================
# Endpoints de Clientes (/api/v1/clients)
# ============================================================================


@router.get(
    "",
    response_model=PaginatedClientsResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar clientes",
    description="Retorna a lista paginada de clientes do programa de fidelidade.",
)
async def list_clients(
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1, description="Página atual."),
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página."),
    search: Optional[str] = Query(default=None, description="Busca textual por nome ou e-mail."),
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Lista clientes com paginação e busca textual."""
    _apply_common_headers(request, response)

    query = db.query(ClientModel)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ClientModel.name.ilike(search_pattern),
                ClientModel.email.ilike(search_pattern),
            )
        )

    total_items = query.count()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0
    has_next = page < total_pages

    clients = (
        query.order_by(ClientModel.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    etag_content = f"{total_items}:{page}:{limit}:{[c.id for c in clients]}:{[c.loyalty_points for c in clients]}"
    etag = generate_etag(etag_content)

    if check_if_none_match(if_none_match, etag):
        res = Response(status_code=status.HTTP_304_NOT_MODIFIED)
        res.headers["ETag"] = etag
        res.headers["X-Request-Id"] = response.headers["X-Request-Id"]
        return res

    response.headers["ETag"] = etag

    paginated_response = PaginatedClientsResponse(
        data=[Client.model_validate(c) for c in clients],
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
    response_model=Client,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar cliente",
    description="Cadastra um novo cliente no programa de fidelidade com pontuação inicial 0.",
)
async def create_client(
    payload: CreateClientDTO,
    request: Request,
    response: Response,
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Client:
    """Cadastra cliente no programa de fidelidade."""
    _apply_common_headers(request, response)

    if db.query(ClientModel).filter(ClientModel.cpf == payload.cpf).first():
        raise ConflictException(
            title="Recurso Duplicado",
            detail="Já existe um cliente cadastrado com o CPF informado.",
            code="DUPLICATE_RESOURCE",
            type_uri="https://api.bookstore.dev/errors/duplicate-resource",
        )

    if db.query(ClientModel).filter(ClientModel.email == payload.email).first():
        raise ConflictException(
            title="Recurso Duplicado",
            detail="Já existe um cliente cadastrado com o e-mail informado.",
            code="DUPLICATE_RESOURCE",
            type_uri="https://api.bookstore.dev/errors/duplicate-resource",
        )

    client_id = secrets.token_urlsafe(16)

    new_client = ClientModel(
        id=client_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        cpf=payload.cpf,
        birth_date=payload.birth_date,
        loyalty_points=0,
        active=payload.active,
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    response.headers["Location"] = f"/api/v1/clients/{new_client.id}"
    return Client.model_validate(new_client)


@router.get(
    "/{id}",
    response_model=Client,
    status_code=status.HTTP_200_OK,
    summary="Obter cliente por ID",
    description="Busca cliente pelo identificador.",
)
async def get_client_by_id(
    id: str,
    request: Request,
    response: Response,
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Busca dados de um cliente."""
    _apply_common_headers(request, response)

    client = db.query(ClientModel).filter(ClientModel.id == id).first()
    if not client:
        raise NotFoundException(
            title="Recurso Inexistente",
            detail="O recurso com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    etag = _compute_client_etag(client)
    if check_if_none_match(if_none_match, etag):
        res = Response(status_code=status.HTTP_304_NOT_MODIFIED)
        res.headers["ETag"] = etag
        res.headers["X-Request-Id"] = response.headers["X-Request-Id"]
        return res

    response.headers["ETag"] = etag
    client_dto = Client.model_validate(client)
    return Response(
        content=client_dto.model_dump_json(by_alias=True),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
        headers=dict(response.headers),
    )


@router.patch(
    "/{id}",
    response_model=Client,
    status_code=status.HTTP_200_OK,
    summary="Atualizar cliente (parcial)",
    description="Atualiza parcialmente dados do cliente com suporte a concorrência via If-Match.",
)
async def update_client(
    id: str,
    payload: UpdateClientDTO,
    request: Request,
    response: Response,
    if_match: Optional[str] = Header(default=None, alias="If-Match"),
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Atualiza dados do cliente parcialmente."""
    _apply_common_headers(request, response)

    client = db.query(ClientModel).filter(ClientModel.id == id).first()
    if not client:
        raise NotFoundException(
            title="Recurso Inexistente",
            detail="O recurso com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    current_etag = _compute_client_etag(client)
    verify_if_match(if_match, current_etag)

    if payload.email and payload.email != client.email:
        conflict = db.query(ClientModel).filter(ClientModel.email == payload.email).first()
        if conflict:
            raise ConflictException(
                title="Recurso Duplicado",
                detail="Já existe um registro com o e-mail informado.",
                code="DUPLICATE_RESOURCE",
            )
        client.email = payload.email

    if payload.cpf and payload.cpf != client.cpf:
        conflict_cpf = db.query(ClientModel).filter(ClientModel.cpf == payload.cpf).first()
        if conflict_cpf:
            raise ConflictException(
                title="Recurso Duplicado",
                detail="Já existe um registro com o CPF informado.",
                code="DUPLICATE_RESOURCE",
            )
        client.cpf = payload.cpf

    if payload.name is not None:
        client.name = payload.name
    if payload.phone is not None:
        client.phone = payload.phone
    if payload.birth_date is not None:
        client.birth_date = payload.birth_date
    if payload.active is not None:
        client.active = payload.active

    db.commit()
    db.refresh(client)

    new_etag = _compute_client_etag(client)
    response.headers["ETag"] = new_etag

    client_dto = Client.model_validate(client)
    return Response(
        content=client_dto.model_dump_json(by_alias=True),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
        headers=dict(response.headers),
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover cliente",
    description="Exclui o cliente. Retorna 409 se houver vendas vinculadas ao cliente.",
)
async def delete_client(
    id: str,
    request: Request,
    response: Response,
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> Response:
    """Remove cliente da base de dados."""
    _apply_common_headers(request, response)

    client = db.query(ClientModel).filter(ClientModel.id == id).first()
    if not client:
        raise NotFoundException(
            title="Recurso Inexistente",
            detail="O recurso com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    # Bloqueia exclusão de clientes com histórico de compras
    sales_count = db.query(SaleModel).filter(SaleModel.client_id == id).count()
    if sales_count > 0:
        raise ConflictException(
            title="Recurso em Uso",
            detail="O cliente possui vendas associadas e não pode ser removido.",
            code="RESOURCE_IN_USE",
            type_uri="https://api.bookstore.dev/errors/resource-in-use",
        )

    db.delete(client)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=dict(response.headers))


@router.get(
    "/{clientId}/sales",
    response_model=PaginatedSalesResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar vendas de um cliente",
    description="Sub-recurso: histórico de compras paginado de um cliente específico.",
)
async def list_sales_by_client(
    clientId: str,
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1, description="Página atual."),
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página."),
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Consulta o histórico de compras de um cliente específico."""
    _apply_common_headers(request, response)

    client = db.query(ClientModel).filter(ClientModel.id == clientId).first()
    if not client:
        raise NotFoundException(
            title="Recurso Inexistente",
            detail="O cliente com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    query = (
        db.query(SaleModel)
        .filter(SaleModel.client_id == clientId)
        .order_by(SaleModel.created_at.desc())
    )

    total_items = query.count()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0
    has_next = page < total_pages

    sales = query.offset((page - 1) * limit).limit(limit).all()

    etag_content = f"client-sales:{clientId}:{total_items}:{page}:{limit}:{[s.id for s in sales]}"
    etag = generate_etag(etag_content)

    if check_if_none_match(if_none_match, etag):
        res = Response(status_code=status.HTTP_304_NOT_MODIFIED)
        res.headers["ETag"] = etag
        res.headers["X-Request-Id"] = response.headers["X-Request-Id"]
        return res

    response.headers["ETag"] = etag

    sales_dto = [_serialize_sale(s) for s in sales]
    paginated_response = PaginatedSalesResponse(
        data=sales_dto,
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
