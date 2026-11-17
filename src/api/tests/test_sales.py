"""test_sales.py — Testes de registro e consulta de vendas.

Casos de teste:
- SALE-001: POST /sales válida → 201 com totais corretos.
- SALE-002: POST /sales sem clientId → 422.
- SALE-003: seller_id vem do JWT, não do corpo.
- SALE-004: POST /sales com items vazio → 422.
- SALE-005: Verificar cálculo de grossTotal.
- SALE-006: Verificar aplicação de discount.
- SALE-007: Verificar finalTotal = grossTotal - discount.
- SALE-008: Idempotência → segundo request com mesma chave retorna Idempotency-Replayed: true.
- SALE-009: Estoque insuficiente → 409 INSUFFICIENT_STOCK.
- SALE-010: GET /sales/{id} → 200 com dados corretos.
- SALE-011: GET /sales → 200 paginado.
"""

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

import uuid


SALES_URL = "/api/v1/sales"

# IDs do banco de seed (database.py)
SEED_CLIENT_ID = "8NV1c7Q4TCYGcsuPch8I"       # Ana Souza
SEED_PRODUCT_ID = "KIYBXACS6uVj5DbKEsPQ"       # Duna, price=80, stock=10
SEED_PRODUCT2_ID = "PRD2c7Q4TCYGcsuPch88"      # O Príncipe Cruel, price=60, stock=15


def _make_sale_payload(
    client_id: str = SEED_CLIENT_ID,
    product_id: str = SEED_PRODUCT_ID,
    quantity: int = 1,
    discount: float = 0,
    payment_method: str = "CREDIT_CARD",
) -> dict:
    payload: dict = {
        "clientId": client_id,
        "paymentMethod": payment_method,
        "items": [{"productId": product_id, "quantity": quantity}],
    }
    if discount:
        payload["discount"] = discount
    return payload


# ---------------------------------------------------------------------------
# SALE-001 — Venda válida com cálculo de totais
# ---------------------------------------------------------------------------


def test_sale001_venda_valida(client: TestClient, admin_headers: dict) -> None:
    """SALE-001: POST /sales válida → 201 com grossTotal, discount e finalTotal corretos."""
    payload = _make_sale_payload(quantity=2)  # Duna: 2 * 80 = 160

    response = client.post(SALES_URL, json=payload, headers=admin_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert "id" in body
    assert body["grossTotal"] == 160.0
    assert body["discount"] == 0.0
    assert body["finalTotal"] == 160.0
    assert body["clientId"] == SEED_CLIENT_ID
    assert len(body["items"]) == 1
    assert "location" in response.headers


# ---------------------------------------------------------------------------
# SALE-002 — Sem clientId → 422
# ---------------------------------------------------------------------------


def test_sale002_sem_client_id(client: TestClient, admin_headers: dict) -> None:
    """SALE-002: POST /sales sem clientId → 422 VALIDATION_FAILED."""
    payload = {
        "paymentMethod": "CREDIT_CARD",
        "items": [{"productId": SEED_PRODUCT_ID, "quantity": 1}],
    }
    response = client.post(SALES_URL, json=payload, headers=admin_headers)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422
    assert response.headers.get("content-type", "").startswith("application/problem+json")


# ---------------------------------------------------------------------------
# SALE-003 — sellerId vem do JWT, não do corpo
# ---------------------------------------------------------------------------


def test_sale003_seller_id_do_jwt(client: TestClient, seller_headers: dict) -> None:
    """SALE-003: sellerId na resposta corresponde ao usuário autenticado pelo JWT."""
    payload = _make_sale_payload()

    response = client.post(SALES_URL, json=payload, headers=seller_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    # sellerId deve ser o ID do SELLER autenticado
    assert body["sellerId"] == "VND1c7Q4TCYGcsuPch99"


# ---------------------------------------------------------------------------
# SALE-004 — Items vazio → 422
# ---------------------------------------------------------------------------


def test_sale004_items_vazio(client: TestClient, admin_headers: dict) -> None:
    """SALE-004: POST /sales com items=[] → 422."""
    payload = {
        "clientId": SEED_CLIENT_ID,
        "paymentMethod": "CREDIT_CARD",
        "items": [],
    }
    response = client.post(SALES_URL, json=payload, headers=admin_headers)

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == 422


# ---------------------------------------------------------------------------
# SALE-005 — Cálculo de grossTotal
# ---------------------------------------------------------------------------


def test_sale005_calculo_gross_total(client: TestClient, admin_headers: dict) -> None:
    """SALE-005: grossTotal = soma de (unitPrice * quantity) de todos os itens."""
    # Duna (80) x 1 + O Príncipe Cruel (60) x 2 = 80 + 120 = 200
    payload = {
        "clientId": SEED_CLIENT_ID,
        "paymentMethod": "PIX",
        "items": [
            {"productId": SEED_PRODUCT_ID, "quantity": 1},
            {"productId": SEED_PRODUCT2_ID, "quantity": 2},
        ],
    }
    response = client.post(SALES_URL, json=payload, headers=admin_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["grossTotal"] == 200.0
    assert len(body["items"]) == 2


# ---------------------------------------------------------------------------
# SALE-006 — Aplicação de desconto
# ---------------------------------------------------------------------------


def test_sale006_discount_aplicado(client: TestClient, admin_headers: dict, db: Session) -> None:
    """SALE-006: discount é subtraído do grossTotal corretamente."""
    # Adiciona pontos ao cliente seed para poder usar desconto
    from src.api.models import ClientModel
    seed_client = db.query(ClientModel).filter(ClientModel.id == SEED_CLIENT_ID).first()
    seed_client.loyalty_points = 200
    db.commit()

    payload = _make_sale_payload(quantity=1, discount=10.0)  # grossTotal=80, discount=10

    response = client.post(SALES_URL, json=payload, headers=admin_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["discount"] == 10.0
    assert body["finalTotal"] == 70.0


# ---------------------------------------------------------------------------
# SALE-007 — finalTotal = grossTotal - discount
# ---------------------------------------------------------------------------


def test_sale007_final_total_formula(client: TestClient, admin_headers: dict, db: Session) -> None:
    """SALE-007: finalTotal = max(0, grossTotal - discount)."""
    from src.api.models import ClientModel
    seed_client = db.query(ClientModel).filter(ClientModel.id == SEED_CLIENT_ID).first()
    seed_client.loyalty_points = 500
    db.commit()

    payload = _make_sale_payload(quantity=1, discount=5.0)

    response = client.post(SALES_URL, json=payload, headers=admin_headers)

    assert response.status_code == 201, response.text
    body = response.json()
    expected_final = max(0.0, body["grossTotal"] - body["discount"])
    assert body["finalTotal"] == expected_final


# ---------------------------------------------------------------------------
# SALE-008 — Idempotência com Idempotency-Key
# ---------------------------------------------------------------------------


def test_sale008_idempotency_key(client: TestClient, admin_headers: dict) -> None:
    """SALE-008: Segundo request com mesma Idempotency-Key retorna Idempotency-Replayed: true."""
    idem_key = f"idem-test-{uuid.uuid4().hex}"
    headers_with_key = {**admin_headers, "Idempotency-Key": idem_key}
    payload = _make_sale_payload(quantity=1)

    # Primeiro request
    first_resp = client.post(SALES_URL, json=payload, headers=headers_with_key)
    assert first_resp.status_code == 201, first_resp.text
    first_body = first_resp.json()

    # Segundo request com a mesma chave
    second_resp = client.post(SALES_URL, json=payload, headers=headers_with_key)
    assert second_resp.status_code == 201
    second_body = second_resp.json()

    # Deve retornar o mesmo ID e ter cabeçalho de replay
    assert second_body["id"] == first_body["id"]
    assert second_resp.headers.get("Idempotency-Replayed") == "true"


# ---------------------------------------------------------------------------
# SALE-009 — Estoque insuficiente → 409
# ---------------------------------------------------------------------------


def test_sale009_estoque_insuficiente(client: TestClient, admin_headers: dict) -> None:
    """SALE-009: POST /sales com quantity > stock → 409 INSUFFICIENT_STOCK."""
    # Duna tem stock=10, pedir 999
    payload = _make_sale_payload(quantity=999)

    response = client.post(SALES_URL, json=payload, headers=admin_headers)

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "INSUFFICIENT_STOCK"
    assert body["status"] == 409
    assert response.headers.get("content-type", "").startswith("application/problem+json")


# ---------------------------------------------------------------------------
# SALE-010 — Obter venda por ID
# ---------------------------------------------------------------------------


def test_sale010_obter_venda_por_id(client: TestClient, admin_headers: dict) -> None:
    """SALE-010: GET /sales/{id} → 200 com dados completos da venda."""
    # Cria uma venda
    create_resp = client.post(SALES_URL, json=_make_sale_payload(), headers=admin_headers)
    assert create_resp.status_code == 201
    sale_id = create_resp.json()["id"]

    response = client.get(f"{SALES_URL}/{sale_id}", headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == sale_id
    assert "grossTotal" in body
    assert "finalTotal" in body
    assert "items" in body
    assert "etag" in response.headers


# ---------------------------------------------------------------------------
# SALE-011 — Listar vendas paginado
# ---------------------------------------------------------------------------


def test_sale011_listar_vendas_paginado(client: TestClient, admin_headers: dict) -> None:
    """SALE-011: GET /sales → 200 com estrutura de paginação."""
    # Cria uma venda para garantir conteúdo
    client.post(SALES_URL, json=_make_sale_payload(), headers=admin_headers)

    response = client.get(SALES_URL, headers=admin_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert "data" in body
    assert "meta" in body
    meta = body["meta"]
    assert "totalItems" in meta
    assert "hasNext" in meta
    assert meta["totalItems"] >= 1


# ---------------------------------------------------------------------------
# SALE-012 — Atualização de Estoque e Acúmulo de Pontos (Passos 6.16 e 6.17)
# ---------------------------------------------------------------------------


def test_sale012_decremento_estoque_e_acumulo_pontos(
    client: TestClient,
    admin_headers: dict,
    db: Session,
) -> None:
    """Passo 6.16 & 6.17: Venda decrementa estoque e credita pontos ao cliente."""
    from src.api.models import ClientModel, ProductModel

    prod_before = db.query(ProductModel).filter(ProductModel.id == SEED_PRODUCT_ID).first()
    stock_before = prod_before.stock

    cli_before = db.query(ClientModel).filter(ClientModel.id == SEED_CLIENT_ID).first()
    points_before = cli_before.loyalty_points

    payload = _make_sale_payload(quantity=2)  # finalTotal = 160.0
    resp = client.post(SALES_URL, json=payload, headers=admin_headers)
    assert resp.status_code == 201

    db.expire_all()
    prod_after = db.query(ProductModel).filter(ProductModel.id == SEED_PRODUCT_ID).first()
    cli_after = db.query(ClientModel).filter(ClientModel.id == SEED_CLIENT_ID).first()

    assert prod_after.stock == stock_before - 2
    assert cli_after.loyalty_points == points_before + 160


# ---------------------------------------------------------------------------
# Infraestrutura — ETag e Rate Limiting (Passos 6.19 e 6.22)
# ---------------------------------------------------------------------------


def test_sales_etag_304_not_modified(client: TestClient, admin_headers: dict) -> None:
    """Passo 6.19: If-None-Match com ETag atual retorna HTTP 304 Not Modified."""
    list_resp = client.get(SALES_URL, headers=admin_headers)
    assert list_resp.status_code == 200
    etag = list_resp.headers.get("etag")
    assert etag is not None

    cached_resp = client.get(SALES_URL, headers={**admin_headers, "If-None-Match": etag})
    assert cached_resp.status_code == 304


def test_sales_rate_limiting_headers(client: TestClient, admin_headers: dict) -> None:
    """Passo 6.22: Respostas HTTP incluem cabeçalhos de rate limiting padronizados."""
    resp = client.get(SALES_URL, headers=admin_headers)
    assert "RateLimit-Limit" in resp.headers
    assert "RateLimit-Remaining" in resp.headers
    assert "RateLimit-Reset" in resp.headers


# ---------------------------------------------------------------------------
# ORM — ORM-001 a ORM-005
# ---------------------------------------------------------------------------


def test_orm001_user_sales_relationship(db: Session) -> None:
    """ORM-001: User 1:N Sales."""
    from src.api.models import SaleModel, UserModel

    user = db.query(UserModel).filter(UserModel.email == "vendedor@example.com").first()
    assert user is not None
    assert hasattr(user, "sales")

    sale = SaleModel(
        id=f"sale_orm_{uuid.uuid4().hex[:8]}",
        client_id=SEED_CLIENT_ID,
        seller_id=user.id,
        gross_total=100.0,
        discount=0,
        final_total=100.0,
        payment_method="CASH",
    )
    db.add(sale)
    db.commit()

    db.refresh(user)
    assert any(s.id == sale.id for s in user.sales)
    assert sale.seller.id == user.id


def test_orm002_client_sales_relationship(db: Session) -> None:
    """ORM-002: Client 1:N Sales."""
    from src.api.models import ClientModel, SaleModel

    client = db.query(ClientModel).filter(ClientModel.id == SEED_CLIENT_ID).first()
    assert client is not None
    assert hasattr(client, "sales")

    sale = SaleModel(
        id=f"sale_cli_{uuid.uuid4().hex[:8]}",
        client_id=client.id,
        seller_id="SDMXDsjJtqcqK1nWnrk0YjQDqPY2",
        gross_total=50.0,
        discount=0,
        final_total=50.0,
        payment_method="PIX",
    )
    db.add(sale)
    db.commit()

    db.refresh(client)
    assert any(s.id == sale.id for s in client.sales)
    assert sale.client.id == client.id


def test_orm003_sale_items_relationship(db: Session) -> None:
    """ORM-003: Sale 1:N SaleItems."""
    from src.api.models import SaleItemModel, SaleModel

    sale = SaleModel(
        id=f"sale_item_{uuid.uuid4().hex[:8]}",
        client_id=SEED_CLIENT_ID,
        seller_id="SDMXDsjJtqcqK1nWnrk0YjQDqPY2",
        gross_total=80.0,
        discount=0,
        final_total=80.0,
        payment_method="CREDIT_CARD",
    )
    item = SaleItemModel(
        sale_id=sale.id,
        product_id=SEED_PRODUCT_ID,
        title="Duna",
        quantity=1,
        unit_price=80.0,
    )
    sale.items.append(item)
    db.add(sale)
    db.commit()

    db.refresh(sale)
    assert len(sale.items) >= 1
    assert sale.items[0].sale_id == sale.id
    assert sale.items[0].sale.id == sale.id


def test_orm004_product_sale_items_relationship(db: Session) -> None:
    """ORM-004: Product 1:N SaleItems."""
    from src.api.models import ProductModel, SaleItemModel, SaleModel

    product = db.query(ProductModel).filter(ProductModel.id == SEED_PRODUCT_ID).first()
    assert product is not None
    assert hasattr(product, "sale_items")

    sale = SaleModel(
        id=f"sale_prod_{uuid.uuid4().hex[:8]}",
        client_id=SEED_CLIENT_ID,
        seller_id="SDMXDsjJtqcqK1nWnrk0YjQDqPY2",
        gross_total=80.0,
        discount=0,
        final_total=80.0,
        payment_method="CREDIT_CARD",
    )
    item = SaleItemModel(
        sale_id=sale.id,
        product_id=product.id,
        title=product.title,
        quantity=1,
        unit_price=float(product.price),
    )
    db.add(sale)
    db.add(item)
    db.commit()

    db.refresh(product)
    assert any(si.id == item.id for si in product.sale_items)
    assert item.product.id == product.id


def test_orm005_referential_integrity_restrict(db: Session) -> None:
    """ORM-005: Integridade referencial com ondelete=RESTRICT impede exclusão de produto com venda."""
    from sqlalchemy.exc import IntegrityError
    from src.api.models import ProductModel, SaleItemModel, SaleModel

    # Cria produto, venda e item associado
    prod = ProductModel(
        id=f"prod_restr_{uuid.uuid4().hex[:8]}",
        code=f"CODE_{uuid.uuid4().hex[:6]}",
        title="Livro Restrito",
        author="Autor Restrito",
        isbn="9788501109999",
        price=50,
        stock=5,
    )
    db.add(prod)
    db.flush()

    sale = SaleModel(
        id=f"sale_restr_{uuid.uuid4().hex[:8]}",
        client_id=SEED_CLIENT_ID,
        seller_id="SDMXDsjJtqcqK1nWnrk0YjQDqPY2",
        gross_total=50.0,
        discount=0,
        final_total=50.0,
        payment_method="CASH",
    )
    item = SaleItemModel(
        sale_id=sale.id,
        product_id=prod.id,
        title=prod.title,
        quantity=1,
        unit_price=50.0,
    )
    db.add(sale)
    db.add(item)
    db.commit()

    # Tentativa de deletar o produto diretamente no ORM deve falhar pela restrição de chave estrangeira
    with pytest.raises(IntegrityError):
        db.delete(prod)
        db.commit()
    db.rollback()

