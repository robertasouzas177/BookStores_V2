"""sales.py — Router de registro e consulta de vendas da Bookstore API.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
"""

from datetime import datetime
import math
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.exceptions import BadRequestException, ConflictException, NotFoundException
from src.api.models import ClientModel, ProductModel, SaleItemModel, SaleModel, UserModel
from src.api.schemas import (
    CreateSaleDTO,
    PaginatedSalesResponse,
    PaginationMeta,
    Sale,
    SaleItem,
)
from src.api.security import (
    check_if_none_match,
    extract_request_id,
    generate_etag,
    get_idempotent_response,
    require_roles,
    save_idempotent_response,
)

router = APIRouter(prefix="/api/v1/sales", tags=["Sales"])


def _apply_common_headers(request: Request, response: Response) -> None:
    """Propaga cabeçalhos de correlação e rate limit padronizados."""
    req_id = extract_request_id(request)
    response.headers["X-Request-Id"] = req_id
    if traceparent := request.headers.get("traceparent"):
        response.headers["traceparent"] = traceparent
    response.headers["RateLimit-Limit"] = "100"
    response.headers["RateLimit-Remaining"] = "95"
    response.headers["RateLimit-Reset"] = "60"


def _serialize_sale(sale: SaleModel) -> Sale:
    """Converte a entidade SaleModel em schema Sale contratual."""
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


def _compute_sale_etag(sale: SaleModel) -> str:
    """Gera o ETag estável de representação de uma venda imutável."""
    raw = f"{sale.id}:{sale.client_id}:{sale.seller_id}:{sale.gross_total}:{sale.discount}:{sale.final_total}:{sale.created_at}"
    return generate_etag(raw)


# ============================================================================
# Endpoints de Vendas (/api/v1/sales)
# ============================================================================


@router.get(
    "",
    response_model=PaginatedSalesResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar vendas",
    description="Retorna as vendas registradas com paginação e filtros opcionais por cliente, vendedor e período.",
)
async def list_sales(
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1, description="Página atual."),
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página."),
    client_id: Optional[str] = Query(default=None, alias="clientId", description="Filtra por cliente."),
    seller_id: Optional[str] = Query(default=None, alias="sellerId", description="Filtra por vendedor."),
    payment_method: Optional[str] = Query(default=None, alias="paymentMethod", description="Filtra por forma de pagamento."),
    date_from: Optional[datetime] = Query(default=None, alias="dateFrom", description="Início do período (inclusive)."),
    date_to: Optional[datetime] = Query(default=None, alias="dateTo", description="Fim do período (inclusive)."),
    sort: Optional[str] = Query(default=None, description="Ordenação (ex: -createdAt,finalTotal)."),
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Lista vendas com paginação, filtros e ordenação."""
    _apply_common_headers(request, response)

    query = db.query(SaleModel)

    if client_id:
        query = query.filter(SaleModel.client_id == client_id)
    if seller_id:
        query = query.filter(SaleModel.seller_id == seller_id)
    if payment_method:
        query = query.filter(SaleModel.payment_method == payment_method)
    if date_from:
        query = query.filter(SaleModel.created_at >= date_from)
    if date_to:
        query = query.filter(SaleModel.created_at <= date_to)

    sort_mapping = {
        "createdAt": SaleModel.created_at,
        "created_at": SaleModel.created_at,
        "finalTotal": SaleModel.final_total,
        "final_total": SaleModel.final_total,
    }

    order_clauses = []
    if sort:
        for term in sort.split(","):
            term = term.strip()
            descending = term.startswith("-")
            field_name = term[1:] if descending else term
            col = sort_mapping.get(field_name)
            if col is not None:
                order_clauses.append(col.desc() if descending else col.asc())

    if not order_clauses:
        order_clauses.append(SaleModel.created_at.desc())

    query = query.order_by(*order_clauses)

    total_items = query.count()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0
    has_next = page < total_pages

    sales = query.offset((page - 1) * limit).limit(limit).all()

    etag_content = f"sales:{total_items}:{page}:{limit}:{[s.id for s in sales]}"
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


@router.post(
    "",
    response_model=Sale,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar venda",
    description="Registra uma transação de venda imutável, decrementa estoque e credita fidelidade.",
)
async def create_sale(
    payload: CreateSaleDTO,
    request: Request,
    response: Response,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    current_seller: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Registra venda comercial com suporte a idempotência e regras de negócio de estoque e fidelidade."""
    _apply_common_headers(request, response)

    # 1. Controle de Idempotência
    if idempotency_key:
        cached_record = get_idempotent_response(idempotency_key)
        if cached_record:
            cached_data = cached_record["data"]
            headers = dict(response.headers)
            headers["Idempotency-Replayed"] = "true"
            headers["Location"] = f"/api/v1/sales/{cached_data.get('id', '')}"
            return JSONResponse(
                status_code=cached_record["status_code"],
                content=cached_data,
                headers=headers,
            )

    # 2. Validação obrigatória do cliente
    client = db.query(ClientModel).filter(ClientModel.id == payload.client_id).first()
    if not client:
        raise NotFoundException(
            title="Recurso Inexistente",
            detail="O cliente informado não foi localizado.",
            code="NOT_FOUND",
        )
    if not client.active:
        raise BadRequestException(
            title="Cliente Inativo",
            detail="O cliente informado está inativo no sistema.",
            code="CLIENT_INACTIVE",
        )

    # 3. Validação dos produtos e estoque
    products_to_update = []
    item_calculations = []
    gross_total = 0.0

    for item_dto in payload.items:
        product = db.query(ProductModel).filter(ProductModel.id == item_dto.product_id).first()
        if not product:
            raise NotFoundException(
                title="Recurso Inexistente",
                detail=f"O livro com identificador '{item_dto.product_id}' não foi localizado no catálogo.",
                code="NOT_FOUND",
            )

        # Regra de Estoque: impede estoque negativo e venda sem estoque suficiente
        if product.stock < item_dto.quantity:
            raise ConflictException(
                title="Estoque Insuficiente",
                detail=f"O produto '{product.title}' possui {product.stock} unidade(s) em estoque; solicitadas: {item_dto.quantity}.",
                code="INSUFFICIENT_STOCK",
                type_uri="https://api.bookstore.dev/errors/insufficient-stock",
            )

        unit_price = float(product.price)
        subtotal = unit_price * item_dto.quantity
        gross_total += subtotal

        products_to_update.append((product, item_dto.quantity))
        item_calculations.append({
            "product": product,
            "quantity": item_dto.quantity,
            "unit_price": unit_price,
        })

    # 4. Cálculo financeiro da venda
    discount = payload.discount or 0
    final_total = max(0.0, float(gross_total - discount))

    # 5. Atualização de Estoque
    for product, qty in products_to_update:
        product.stock -= qty

    # 6. Atualização do Programa de Fidelidade
    # Se desconto utilizado e possuía benefício, consome pontuação (100 pontos)
    if discount > 0 and client.loyalty_points >= 100:
        client.loyalty_points -= 100

    # Cada venda acumula pontos de fidelidade baseados no valor pago
    points_earned = int(final_total)
    client.loyalty_points = max(0, client.loyalty_points + points_earned)

    # 7. Criação da Venda e dos Itens
    sale_id = secrets.token_urlsafe(16)
    new_sale = SaleModel(
        id=sale_id,
        client_id=client.id,
        seller_id=current_seller.id,
        gross_total=gross_total,
        discount=discount,
        final_total=final_total,
        payment_method=payload.payment_method,
    )
    db.add(new_sale)

    for it in item_calculations:
        new_item = SaleItemModel(
            sale_id=sale_id,
            product_id=it["product"].id,
            title=it["product"].title,
            quantity=it["quantity"],
            unit_price=it["unit_price"],
        )
        db.add(new_item)

    db.commit()
    db.refresh(new_sale)

    # 8. Serialização e Cache de Idempotência
    sale_dto = _serialize_sale(new_sale)
    sale_content = sale_dto.model_dump(by_alias=True, mode="json")

    if idempotency_key:
        save_idempotent_response(idempotency_key, sale_content, status_code=201)

    response.headers["Location"] = f"/api/v1/sales/{new_sale.id}"
    new_etag = _compute_sale_etag(new_sale)
    response.headers["ETag"] = new_etag

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=sale_content,
        headers=dict(response.headers),
    )


@router.get(
    "/{id}",
    response_model=Sale,
    status_code=status.HTTP_200_OK,
    summary="Obter venda por ID",
    description="Busca uma venda específica. Vendas são imutáveis após registradas.",
)
async def get_sale_by_id(
    id: str,
    request: Request,
    response: Response,
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Busca venda por identificador."""
    _apply_common_headers(request, response)

    sale = db.query(SaleModel).filter(SaleModel.id == id).first()
    if not sale:
        raise NotFoundException(
            title="Recurso Inexistente",
            detail="A venda com o identificador informado não foi localizada.",
            code="NOT_FOUND",
        )

    etag = _compute_sale_etag(sale)
    if check_if_none_match(if_none_match, etag):
        res = Response(status_code=status.HTTP_304_NOT_MODIFIED)
        res.headers["ETag"] = etag
        res.headers["X-Request-Id"] = response.headers["X-Request-Id"]
        return res

    response.headers["ETag"] = etag
    sale_dto = _serialize_sale(sale)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=sale_dto.model_dump(by_alias=True, mode="json"),
        headers=dict(response.headers),
    )
