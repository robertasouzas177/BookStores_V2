"""products.py — Router de catálogo de produtos (livros) da Bookstore API.

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
from src.api.models import ProductModel, SaleItemModel, UserModel
from src.api.schemas import (
    CreateProductDTO,
    PaginatedProductsResponse,
    PaginationMeta,
    Product,
    UpdateProductDTO,
)
from src.api.security import (
    check_if_none_match,
    extract_request_id,
    generate_etag,
    require_roles,
    verify_if_match,
)

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


def _apply_common_headers(request: Request, response: Response) -> None:
    """Propaga cabeçalhos de correlação e rate limit padronizados."""
    req_id = extract_request_id(request)
    response.headers["X-Request-Id"] = req_id
    if traceparent := request.headers.get("traceparent"):
        response.headers["traceparent"] = traceparent
    response.headers["RateLimit-Limit"] = "100"
    response.headers["RateLimit-Remaining"] = "97"
    response.headers["RateLimit-Reset"] = "60"


def _compute_product_etag(product: ProductModel) -> str:
    """Gera o ETag estável de representação de um livro."""
    raw = f"{product.id}:{product.title}:{product.author}:{product.isbn}:{product.code}:{product.price}:{product.stock}"
    return generate_etag(raw)


# ============================================================================
# Endpoints de Produtos (/api/v1/products)
# ============================================================================


@router.get(
    "",
    response_model=PaginatedProductsResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar produtos (livros)",
    description="Retorna a lista paginada de livros cadastrados com filtros e validação condicional via ETag.",
)
async def list_products(
    request: Request,
    response: Response,
    page: int = Query(default=1, ge=1, description="Página atual."),
    limit: int = Query(default=10, ge=1, le=100, description="Itens por página."),
    search: Optional[str] = Query(default=None, description="Busca textual por título ou autor."),
    in_stock: Optional[bool] = Query(default=None, alias="inStock", description="Filtra apenas livros com estoque > 0."),
    sort: Optional[str] = Query(default=None, description="Ordenação (ex: -createdAt,price)."),
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Lista catálogo de livros."""
    _apply_common_headers(request, response)

    query = db.query(ProductModel)

    # Filtro de busca textual em título ou autor
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ProductModel.title.ilike(search_pattern),
                ProductModel.author.ilike(search_pattern),
            )
        )

    # Filtro de estoque disponível
    if in_stock is True:
        query = query.filter(ProductModel.stock > 0)
    elif in_stock is False:
        query = query.filter(ProductModel.stock == 0)

    # Ordenação configurável
    sort_mapping = {
        "title": ProductModel.title,
        "price": ProductModel.price,
        "stock": ProductModel.stock,
        "createdAt": ProductModel.created_at,
        "created_at": ProductModel.created_at,
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
        order_clauses.append(ProductModel.created_at.desc())

    query = query.order_by(*order_clauses)

    total_items = query.count()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0
    has_next = page < total_pages

    products = query.offset((page - 1) * limit).limit(limit).all()

    etag_content = f"{total_items}:{page}:{limit}:{[p.id for p in products]}:{[p.stock for p in products]}"
    etag = generate_etag(etag_content)

    if check_if_none_match(if_none_match, etag):
        res = Response(status_code=status.HTTP_304_NOT_MODIFIED)
        res.headers["ETag"] = etag
        res.headers["X-Request-Id"] = response.headers["X-Request-Id"]
        return res

    response.headers["ETag"] = etag

    paginated_response = PaginatedProductsResponse(
        data=[Product.model_validate(p) for p in products],
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
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    summary="Criar produto (livro)",
    description="Cadastra um novo livro no catálogo (acesso restrito ao perfil ADMIN).",
)
async def create_product(
    payload: CreateProductDTO,
    request: Request,
    response: Response,
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> Product:
    """Cadastra um novo livro no estoque."""
    _apply_common_headers(request, response)

    # Identificador compatível com Firestore
    product_id = secrets.token_urlsafe(16)

    new_product = ProductModel(
        id=product_id,
        code=payload.code,
        title=payload.title,
        author=payload.author,
        isbn=payload.isbn,
        price=payload.price,
        stock=payload.stock,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    response.headers["Location"] = f"/api/v1/products/{new_product.id}"
    return Product.model_validate(new_product)


@router.get(
    "/{id}",
    response_model=Product,
    status_code=status.HTTP_200_OK,
    summary="Obter produto por ID",
    description="Busca um livro específico pelo identificador do Firestore.",
)
async def get_product_by_id(
    id: str,
    request: Request,
    response: Response,
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match"),
    current_user: UserModel = Depends(require_roles("ADMIN", "SELLER")),
    db: Session = Depends(get_db),
) -> Response:
    """Busca produto por identificador."""
    _apply_common_headers(request, response)

    product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if not product:
        raise NotFoundException(
            detail="O recurso com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    etag = _compute_product_etag(product)
    if check_if_none_match(if_none_match, etag):
        res = Response(status_code=status.HTTP_304_NOT_MODIFIED)
        res.headers["ETag"] = etag
        res.headers["X-Request-Id"] = response.headers["X-Request-Id"]
        return res

    response.headers["ETag"] = etag
    product_dto = Product.model_validate(product)
    return Response(
        content=product_dto.model_dump_json(by_alias=True),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
        headers=dict(response.headers),
    )


@router.patch(
    "/{id}",
    response_model=Product,
    status_code=status.HTTP_200_OK,
    summary="Atualizar produto (parcial)",
    description="Atualiza parcialmente dados do livro (suporta controle de concorrência If-Match).",
)
async def update_product(
    id: str,
    payload: UpdateProductDTO,
    request: Request,
    response: Response,
    if_match: Optional[str] = Header(default=None, alias="If-Match"),
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> Response:
    """Atualiza dados do livro parcialmente."""
    _apply_common_headers(request, response)

    product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if not product:
        raise NotFoundException(
            detail="O recurso com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    # Concorrência otimista
    current_etag = _compute_product_etag(product)
    verify_if_match(if_match, current_etag)

    if payload.title is not None:
        product.title = payload.title
    if payload.author is not None:
        product.author = payload.author
    if payload.code is not None:
        product.code = payload.code
    if payload.isbn is not None:
        product.isbn = payload.isbn
    if payload.price is not None:
        product.price = payload.price
    if payload.stock is not None:
        product.stock = payload.stock

    db.commit()
    db.refresh(product)

    new_etag = _compute_product_etag(product)
    response.headers["ETag"] = new_etag

    product_dto = Product.model_validate(product)
    return Response(
        content=product_dto.model_dump_json(by_alias=True),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
        headers=dict(response.headers),
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover produto",
    description="Exclui o livro do catálogo. Retorna 409 se houver histórico de vendas vinculado.",
)
async def delete_product(
    id: str,
    request: Request,
    response: Response,
    current_admin: UserModel = Depends(require_roles("ADMIN")),
    db: Session = Depends(get_db),
) -> Response:
    """Exclui produto com validação de integridade referencial."""
    _apply_common_headers(request, response)

    product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if not product:
        raise NotFoundException(
            detail="O recurso com o identificador informado não foi localizado.",
            code="NOT_FOUND",
        )

    # Regra de Integridade: impede exclusão de produto com histórico de vendas
    sales_count = db.query(SaleItemModel).filter(SaleItemModel.product_id == id).count()
    if sales_count > 0:
        raise ConflictException(
            title="Recurso em Uso",
            detail="O produto possui vendas associadas e não pode ser removido.",
            code="RESOURCE_IN_USE",
            type_uri="https://api.bookstore.dev/errors/resource-in-use",
        )

    db.delete(product)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=dict(response.headers))
