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
    """Popula o banco com seeds iniciais conforme os passos 3.28 a 3.31 do PLAN.md."""
    from src.api.models import ClientModel, ProductModel, UserModel

    # 1. Usuários iniciais (ADMIN e SELLER)
    admin_exists = db.query(UserModel).filter(UserModel.email == "admin@api.com").first()
    if not admin_exists:
        admin_user = UserModel(
            id="SDMXDsjJtqcqK1nWnrk0YjQDqPY2",
            name="Administrador do Sistema",
            email="admin@api.com",
            # Hash reservado para 'Sup3rS3cr3t!' (compatível com a fase 4 de segurança)
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
            loyalty_points=40,
            active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(sample_client)

    db.commit()


def init_db() -> None:
    """Cria todas as tabelas e insere dados iniciais caso ainda não existam."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_initial_data(db)
