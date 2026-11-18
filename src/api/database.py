"""database.py — Configuração de banco de dados e sessão SQLAlchemy 2.0.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
"""

import os
from datetime import datetime, timezone
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Configuração de URL do banco (padrão SQLite local para ambiente de desenvolvimento)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookstore.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

# Habilitação obrigatória de chaves estrangeiras no driver SQLite
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Classe base declarativa do SQLAlchemy 2.0 para todos os modelos ORM."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI que fornece uma sessão de banco com fechamento automático."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_initial_data(db: Session) -> None:
    """Popula o banco com seeds iniciais conforme a especificação oficial e regras da P2."""
    from src.api.models import ClientModel, ProductModel, SaleItemModel, SaleModel, UserModel

    # 1. Usuários iniciais (ADMIN e SELLER)
    admin_exists = db.query(UserModel).filter(UserModel.email == "admin@api.com").first()
    if not admin_exists:
        admin_user = UserModel(
            id="SDMXDsjJtqcqK1nWnrk0YjQDqPY2",
            name="Administrador do Sistema",
            email="admin@api.com",
            password_hash="$2b$12$e8x8R7yMvLpKp0WvE7K8e.vQ5c6yW0QzH4qE9X8j5K2Z4W6v8b0mK",
            phone="16999999999",
            active=True,
            role="ADMIN",
            created_at=datetime.now(timezone.utc),
        )
        db.add(admin_user)

    seller_exists = db.query(UserModel).filter(UserModel.email == "vendedor@example.com").first()
    if not seller_exists:
        seller_user = UserModel(
            id="VND1c7Q4TCYGcsuPch99",
            name="Vendedor Operacional",
            email="vendedor@example.com",
            password_hash="$2b$12$e8x8R7yMvLpKp0WvE7K8e.vQ5c6yW0QzH4qE9X8j5K2Z4W6v8b0mK",
            phone="16988881111",
            active=True,
            role="SELLER",
            created_at=datetime.now(timezone.utc),
        )
        db.add(seller_user)

    # 2. Produtos iniciais
    product_exists = db.query(ProductModel).filter(ProductModel.id == "KIYBXACS6uVj5DbKEsPQ").first()
    if not product_exists:
        sample_product = ProductModel(
            id="KIYBXACS6uVj5DbKEsPQ",
            code="0t1E9I47QBhiNZJdnqaf",
            title="Duna",
            author="Frank Herbert",
            isbn="9788501101958",
            price=80,  # Unidade inteira Firestore
            stock=10,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sample_product)

    product_exists_2 = db.query(ProductModel).filter(ProductModel.id == "PRD2c7Q4TCYGcsuPch88").first()
    if not product_exists_2:
        sample_product_2 = ProductModel(
            id="PRD2c7Q4TCYGcsuPch88",
            code="1u2F0J58RCijOAKenrbg",
            title="O Príncipe Cruel",
            author="Holly Black",
            isbn="9788501101965",
            price=60,
            stock=15,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sample_product_2)

    product_exists_3 = db.query(ProductModel).filter(ProductModel.id == "PRD3c7Q4TCYGcsuPch90").first()
    if not product_exists_3:
        sample_product_3 = ProductModel(
            id="PRD3c7Q4TCYGcsuPch90",
            code="3w4H2L70TEklQCMgptdc",
            title="Fundação",
            author="Isaac Asimov",
            isbn="9788576574507",
            price=72,
            stock=0,  # Produto esgotado para teste de inStock=false e 409 INSUFFICIENT_STOCK
            created_at=datetime.now(timezone.utc),
        )
        db.add(sample_product_3)

    # 3. Clientes iniciais
    client_exists = db.query(ClientModel).filter(ClientModel.id == "8NV1c7Q4TCYGcsuPch8I").first()
    if not client_exists:
        sample_client = ClientModel(
            id="8NV1c7Q4TCYGcsuPch8I",
            name="Ana Souza",
            email="ana.souza@example.com",
            phone="16988887777",
            cpf="52998224725",
            birth_date="01/02/2000",
            loyalty_points=100,  # Cliente VIP (>=100 pts) elegível a 10% de desconto
            active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sample_client)
    else:
        # Garante que Ana Souza tenha 100 pontos para demonstrar benefício VIP
        if client_exists.loyalty_points < 100:
            client_exists.loyalty_points = 100

    client_exists_2 = db.query(ClientModel).filter(ClientModel.id == "CLI2c7Q4TCYGcsuPch02").first()
    if not client_exists_2:
        sample_client_2 = ClientModel(
            id="CLI2c7Q4TCYGcsuPch02",
            name="Carlos Eduardo Santos",
            email="carlos.santos@example.com",
            phone="16977776666",
            cpf="11144477735",
            birth_date="15/05/1995",
            loyalty_points=20,
            active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sample_client_2)

    db.commit()

    # 4. Venda inicial vinculada para demonstrar histórico imutável e bloqueio 409
    sale_exists = db.query(SaleModel).filter(SaleModel.id == "SAL1c7Q4TCYGcsuPch01").first()
    if not sale_exists:
        initial_sale = SaleModel(
            id="SAL1c7Q4TCYGcsuPch01",
            client_id="8NV1c7Q4TCYGcsuPch8I",
            client_name="Ana Souza",
            seller_id="SDMXDsjJtqcqK1nWnrk0YjQDqPY2",
            seller_name="Administrador do Sistema",
            payment_method="Dinheiro",
            gross_total=80.0,
            discount=0,
            final_total=80.0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(initial_sale)

        initial_item = SaleItemModel(
            sale_id="SAL1c7Q4TCYGcsuPch01",
            product_id="KIYBXACS6uVj5DbKEsPQ",
            title="Duna",
            quantity=1,
            unit_price=80.0,
        )
        db.add(initial_item)
        db.commit()


def init_db() -> None:
    """Cria todas as tabelas e insere dados iniciais caso ainda não existam."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_initial_data(db)
