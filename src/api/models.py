"""models.py — Modelos ORM da Bookstore API utilizando SQLAlchemy 2.0.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.api.database import Base


class UserModel(Base):
    """Modelo ORM representando operadores e administradores (coleção UsuarioAPI)."""

    __tablename__ = "users"

    # ID gerado pelo Firestore mantido como String(128)
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="SELLER", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relacionamento: User 1:N Sales
    sales: Mapped[List["SaleModel"]] = relationship(
        "SaleModel",
        back_populates="seller",
    )

    # Relacionamento: User 1:N RefreshTokens
    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class ProductModel(Base):
    """Modelo ORM representando os livros do catálogo (coleção Produtos)."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(String(17), nullable=False, index=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # Preço inteiro do Firestore
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relacionamento: Product 1:N SaleItems (com proteção de integridade referencial)
    sale_items: Mapped[List["SaleItemModel"]] = relationship(
        "SaleItemModel",
        back_populates="product",
    )


class ClientModel(Base):
    """Modelo ORM representando clientes do programa de fidelidade (coleção Clientes)."""

    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True, nullable=False)
    birth_date: Mapped[str] = mapped_column(String(10), nullable=False)  # Formato DD/MM/AAAA
    loyalty_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relacionamento: Client 1:N Sales
    sales: Mapped[List["SaleModel"]] = relationship(
        "SaleModel",
        back_populates="client",
    )


class SaleModel(Base):
    """Modelo ORM representando a venda imutável (coleção Vendas)."""

    __tablename__ = "sales"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    client_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    client_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    seller_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seller_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    gross_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relacionamento: Client 1:N Sales
    client: Mapped["ClientModel"] = relationship(
        "ClientModel",
        back_populates="sales",
    )

    # Relacionamento: User 1:N Sales
    seller: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="sales",
    )

    # Relacionamento: Sale 1:N SaleItems
    items: Mapped[List["SaleItemModel"]] = relationship(
        "SaleItemModel",
        back_populates="sale",
        cascade="all, delete-orphan",
    )


class SaleItemModel(Base):
    """Modelo ORM representando a entidade associativa de itens da venda."""

    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Restrição mandatória: impede exclusão de produto com histórico de vendas
    product_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Relacionamento: Sale 1:N SaleItems
    sale: Mapped["SaleModel"] = relationship(
        "SaleModel",
        back_populates="items",
    )

    # Relacionamento: Product 1:N SaleItems
    product: Mapped["ProductModel"] = relationship(
        "ProductModel",
        back_populates="sale_items",
    )


class RefreshTokenModel(Base):
    """Modelo ORM para persistência, rotação e controle de revogação de refresh tokens."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    family_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relacionamento: User 1:N RefreshTokens
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="refresh_tokens",
    )
