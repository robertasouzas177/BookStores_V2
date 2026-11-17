"""schemas.py — Schemas Pydantic v2 da Bookstore API.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """Schema base configurado para Pydantic v2 com suporte a camelCase e ORM."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# ============================================================================
# RFC 9457 — Problem Details
# ============================================================================


class InvalidParam(BaseSchema):
    """Extensão da RFC 9457 para detalhar campos inválidos em erros 422."""

    name: str = Field(..., description="Nome do campo que originou o erro de validação.")
    reason: str = Field(..., description="Motivo pelo qual o campo foi considerado inválido.")


class ApiError(BaseSchema):
    """Problem Details para APIs HTTP (RFC 9457). Content-Type: application/problem+json."""

    type: str = Field(
        default="about:blank",
        description="URI que identifica o tipo do problema.",
        examples=["https://api.bookstore.dev/errors/validation-failed"],
    )
    title: str = Field(
        ...,
        description="Resumo curto e legível do problema.",
        examples=["Erro de Validação de Dados"],
    )
    status: int = Field(
        ...,
        description="Código de status HTTP associado.",
        examples=[422],
    )
    detail: Optional[str] = Field(
        default=None,
        description="Explicação específica e detalhada desta ocorrência.",
        examples=["O campo 'title' é obrigatório."],
    )
    instance: Optional[str] = Field(
        default=None,
        description="URI da requisição que originou o erro.",
        examples=["/api/v1/products"],
    )
    code: Optional[str] = Field(
        default=None,
        description="Código de erro estável e legível por máquina para tomada de decisão programática.",
        examples=["VALIDATION_FAILED"],
    )
    invalid_params: Optional[List[InvalidParam]] = Field(
        default=None,
        description="Extensão RFC 9457: lista de campos inválidos, presente em erros 422.",
    )


# ============================================================================
# Paginação
# ============================================================================


class PaginationMeta(BaseSchema):
    """Metadados de paginação padronizados."""

    page: int = Field(..., ge=1, description="Página atual (1-based).", examples=[1])
    limit: int = Field(..., ge=1, le=100, description="Quantidade de itens por página.", examples=[10])
    total_items: int = Field(..., ge=0, description="Total geral de registros encontrados.", examples=[42])
    total_pages: int = Field(..., ge=0, description="Total de páginas calculadas.", examples=[5])
    has_next: bool = Field(..., description="Indica se existe página seguinte.", examples=[True])


# ============================================================================
# Autenticação e Perfis (RBAC)
# ============================================================================


class UserRole(str, Enum):
    """Perfis de acesso oficiais da Bookstore API."""

    ADMIN = "ADMIN"
    SELLER = "SELLER"


class LoginRequest(BaseSchema):
    """Dados de entrada para autenticação de usuário."""

    email: EmailStr = Field(..., description="E-mail de acesso do usuário.", examples=["admin@api.com"])
    password: str = Field(..., min_length=1, description="Senha do usuário.", examples=["Sup3rS3cr3t!"])


class TokenResponse(BaseSchema):
    """Resposta emitida após autenticação ou rotação de token bem-sucedida."""

    access_token: str = Field(..., description="JWT de acesso com tempo de vida de 15 minutos.")
    refresh_token: str = Field(..., description="Token opaco de uso único para renovação de sessão.")
    token_type: Literal["Bearer"] = Field(default="Bearer", description="Tipo de autenticação Bearer.")
    expires_in: int = Field(default=900, description="Validade do access token em segundos (900 = 15 min).")
    refresh_expires_in: int = Field(
        default=1209600,
        description="Validade do refresh token em segundos (1209600 = 14 dias).",
    )


class RefreshRequest(BaseSchema):
    """Dados de entrada para renovação (rotação) ou revogação de tokens."""

    refresh_token: str = Field(
        ...,
        min_length=20,
        max_length=512,
        description="Token de renovação recebido no login ou na renovação anterior.",
        examples=["rt_9f82a1c0d4e5b6a7c8d9e0f1a2b3c4d5"],
    )


# ============================================================================
# Users — Coleção UsuarioAPI
# ============================================================================


class User(BaseSchema):
    """Representação de um usuário da plataforma (coleção UsuarioAPI)."""

    id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="ID do documento da coleção UsuarioAPI no Firestore.",
        examples=["SDMXDsjJtqcqK1nWnrk0YjQDqPY2"],
    )
    name: str = Field(..., min_length=1, max_length=150, description="Nome completo do usuário.")
    email: EmailStr = Field(..., max_length=254, description="Endereço de e-mail do usuário.")
    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        description="Telefone de contato do usuário.",
        examples=["16999999999"],
    )
    active: bool = Field(default=True, description="Indica se o usuário está ativo.")
    created_at: datetime = Field(..., description="Data e hora de criação do registro (ISO 8601).")
    role: Optional[UserRole] = Field(
        default=None,
        description="Perfil de acesso associado ao usuário (ADMIN ou SELLER).",
    )


class CreateUserDTO(BaseSchema):
    """Dados de entrada para criação de usuário."""

    name: str = Field(..., min_length=1, max_length=150, description="Nome do usuário.")
    email: EmailStr = Field(..., max_length=254, description="E-mail único do usuário.")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Senha de acesso em texto puro; nunca retornada.",
    )
    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        pattern=r"^[0-9]{10,11}$",
        description="Telefone contendo DDD e número (apenas dígitos).",
        examples=["16999999999"],
    )
    active: bool = Field(default=True, description="Status inicial de ativação do usuário.")


class UpdateUserDTO(BaseSchema):
    """Dados permitidos para atualização parcial de usuário."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        pattern=r"^[0-9]{10,11}$",
    )
    active: Optional[bool] = Field(default=None, description="Permite inativar o usuário enviando false.")


class PaginatedUsersResponse(BaseSchema):
    """Envelope de resposta paginada de usuários."""

    data: List[User] = Field(..., description="Lista de usuários da página atual.")
    meta: PaginationMeta = Field(..., description="Metadados da paginação.")


# ============================================================================
# Products — Coleção Produtos
# ============================================================================


class Product(BaseSchema):
    """Representação de um livro no catálogo (coleção Produtos)."""

    id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="ID do documento no Cloud Firestore.",
        examples=["KIYBXACS6uVj5DbKEsPQ"],
    )
    title: str = Field(..., min_length=1, max_length=200, description="Título do livro.")
    author: str = Field(..., min_length=1, max_length=120, description="Nome do autor ou autora.")
    code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Código textual próprio do produto no Firestore (campo codigo).",
        examples=["0t1E9I47QBhiNZJdnqaf"],
    )
    isbn: str = Field(
        ...,
        min_length=10,
        max_length=17,
        pattern=r"^[0-9]{10}([0-9]{3})?$",
        description="ISBN com 10 ou 13 dígitos numéricos.",
        examples=["9788501101958"],
    )
    price: int = Field(
        ...,
        ge=0,
        description="Preço armazenado como inteiro no Firestore (unidade monetária inteira).",
        examples=[80],
    )
    stock: int = Field(..., ge=0, description="Quantidade disponível em estoque.", examples=[10])
    created_at: datetime = Field(..., description="Data de criação em ISO 8601.")


class CreateProductDTO(BaseSchema):
    """Dados de entrada para cadastro de livro."""

    title: str = Field(..., min_length=1, max_length=200, description="Título do livro.")
    author: str = Field(..., min_length=1, max_length=120, description="Nome do autor ou autora.")
    code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Código textual identificador do livro.",
        examples=["0t1E9I47QBhiNZJdnqaf"],
    )
    isbn: str = Field(
        ...,
        min_length=10,
        max_length=17,
        pattern=r"^[0-9]{10}([0-9]{3})?$",
        description="ISBN do livro (10 ou 13 dígitos numéricos).",
        examples=["9788501101958"],
    )
    price: int = Field(..., ge=0, description="Preço em unidades monetárias inteiras.", examples=[80])
    stock: int = Field(default=0, ge=0, description="Quantidade inicial em estoque.", examples=[10])


class UpdateProductDTO(BaseSchema):
    """Dados para atualização parcial de um livro."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    author: Optional[str] = Field(default=None, min_length=1, max_length=120)
    code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    isbn: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=17,
        pattern=r"^[0-9]{10}([0-9]{3})?$",
    )
    price: Optional[int] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)


class PaginatedProductsResponse(BaseSchema):
    """Envelope de resposta paginada de produtos."""

    data: List[Product] = Field(..., description="Lista de produtos da página.")
    meta: PaginationMeta = Field(..., description="Metadados da paginação.")


# ============================================================================
# Clients — Coleção Clientes
# ============================================================================


class Client(BaseSchema):
    """Representação de um cliente da livraria (coleção Clientes)."""

    id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="ID do documento do cliente no Firestore.",
        examples=["8NV1c7Q4TCYGcsuPch8I"],
    )
    name: str = Field(..., min_length=1, max_length=150, description="Nome completo do cliente.")
    email: EmailStr = Field(..., max_length=254, description="E-mail de contato do cliente.")
    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        description="Telefone de contato armazenado com DDD.",
        examples=["16988887777"],
    )
    cpf: str = Field(
        ...,
        min_length=11,
        max_length=11,
        pattern=r"^[0-9]{11}$",
        description="CPF do cliente contendo apenas os 11 dígitos numéricos.",
        examples=["52998224725"],
    )
    birth_date: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/([0-9]{4})$",
        description="Data de nascimento no formato DD/MM/AAAA conforme dado persistido.",
        examples=["01/02/2000"],
    )
    loyalty_points: int = Field(
        ...,
        ge=0,
        description="Pontos acumulados no programa de fidelidade.",
        examples=[40],
    )
    active: bool = Field(default=True, description="Indica se o cliente está ativo.")
    created_at: datetime = Field(..., description="Data e hora de cadastro em ISO 8601.")


class CreateClientDTO(BaseSchema):
    """Dados de entrada para cadastrar novo cliente."""

    name: str = Field(..., min_length=1, max_length=150, description="Nome completo do cliente.")
    email: EmailStr = Field(..., max_length=254, description="E-mail do cliente.")
    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        pattern=r"^[0-9]{10,11}$",
        description="Telefone com DDD.",
    )
    cpf: str = Field(
        ...,
        min_length=11,
        max_length=11,
        pattern=r"^[0-9]{11}$",
        description="CPF contendo exatamente 11 dígitos numéricos.",
        examples=["52998224725"],
    )
    birth_date: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/([0-9]{4})$",
        description="Data de nascimento no padrão DD/MM/AAAA.",
        examples=["01/02/2000"],
    )
    active: bool = Field(default=True, description="Status de ativação inicial.")


class UpdateClientDTO(BaseSchema):
    """Dados permitidos para atualização parcial de cliente."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    email: Optional[EmailStr] = Field(default=None, max_length=254)
    phone: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=15,
        pattern=r"^[0-9]{10,11}$",
    )
    cpf: Optional[str] = Field(
        default=None,
        min_length=11,
        max_length=11,
        pattern=r"^[0-9]{11}$",
    )
    birth_date: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=10,
        pattern=r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/([0-9]{4})$",
    )
    active: Optional[bool] = None


class PaginatedClientsResponse(BaseSchema):
    """Envelope de resposta paginada de clientes."""

    data: List[Client] = Field(..., description="Lista de clientes da página.")
    meta: PaginationMeta = Field(..., description="Metadados da paginação.")


# ============================================================================
# Sales & SaleItems — Coleção Vendas
# ============================================================================


class CreateSaleItemDTO(BaseSchema):
    """Dados de entrada de cada item que compõe a venda."""

    product_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID do documento do produto no Firestore.",
        examples=["KIYBXACS6uVj5DbKEsPQ"],
    )
    quantity: int = Field(..., ge=1, description="Quantidade de unidades a serem vendidas.", examples=[2])


class SaleItem(BaseSchema):
    """Item registrado como snapshot dentro da venda (campo itens do Firestore)."""

    product_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ID do documento do produto no Firestore.",
        examples=["KIYBXACS6uVj5DbKEsPQ"],
    )
    title: str = Field(..., description="Título do livro no momento da venda.", examples=["Duna"])
    quantity: int = Field(..., ge=1, description="Quantidade vendida.", examples=[2])
    unit_price: float = Field(
        ...,
        ge=0,
        description="Snapshot do preço unitário praticado na venda (double no Firestore).",
        examples=[23.9],
    )


class CreateSaleDTO(BaseSchema):
    """Dados de entrada para registro de venda. O vendedor é extraído do token JWT."""

    client_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="ID obrigatório do cliente cadastrado no Firestore.",
        examples=["8NV1c7Q4TCYGcsuPch8I"],
    )
    payment_method: str = Field(
        ...,
        description="Forma de pagamento utilizada (ex.: Dinheiro).",
        examples=["Dinheiro"],
    )
    discount: int = Field(
        default=0,
        ge=0,
        description="Valor inteiro de desconto concedido na venda.",
        examples=[0],
    )
    items: List[CreateSaleItemDTO] = Field(
        ...,
        min_length=1,
        description="Lista de itens da venda (ao menos 1 item obrigatório).",
    )


class Sale(BaseSchema):
    """Representação de uma venda imutável (coleção Vendas)."""

    id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="ID do documento da venda no Firestore.",
        examples=["ID_DOCUMENTO_FIRESTORE"],
    )
    client_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="ID do cliente cadastrado.",
        examples=["8NV1c7Q4TCYGcsuPch8I"],
    )
    client_name: Optional[str] = Field(
        default=None,
        description="Snapshot do nome do cliente no momento da venda.",
        examples=["Ana Souza"],
    )
    seller_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="ID do usuário vendedor responsável pela operação.",
        examples=["SDMXDsjJtqcqK1nWnrk0YjQDqPY2"],
    )
    seller_name: Optional[str] = Field(
        default=None,
        description="Snapshot do nome/e-mail do vendedor no momento da venda.",
        examples=["vendedor@example.com"],
    )
    items: List[SaleItem] = Field(
        ...,
        min_length=1,
        description="Itens integrantes da venda.",
    )
    gross_total: float = Field(
        ...,
        ge=0,
        description="Valor total bruto antes do desconto (totalBruto).",
        examples=[47.8],
    )
    discount: int = Field(
        ...,
        ge=0,
        description="Valor inteiro deduzido (desconto).",
        examples=[0],
    )
    final_total: float = Field(
        ...,
        ge=0,
        description="Valor líquido final da venda (totalFinal).",
        examples=[47.8],
    )
    payment_method: str = Field(
        ...,
        description="Forma de pagamento registrada.",
        examples=["Dinheiro"],
    )
    created_at: datetime = Field(..., description="Data e hora da transação em ISO 8601.")


class PaginatedSalesResponse(BaseSchema):
    """Envelope de resposta paginada de vendas."""

    data: List[Sale] = Field(..., description="Lista de vendas da página.")
    meta: PaginationMeta = Field(..., description="Metadados da paginação.")


# ============================================================================
# Health Checks
# ============================================================================


class HealthCheck(BaseSchema):
    """Estado de saúde de uma dependência individual."""

    status: Literal["UP", "DOWN"] = Field(..., description="Estado operacional da dependência.")
    latency_ms: Optional[int] = Field(default=None, description="Latência em milissegundos.")


class HealthResponse(BaseSchema):
    """Resposta das sondas de liveness (/health/live) e readiness (/health/ready)."""

    status: Literal["UP", "DOWN"] = Field(..., description="Estado geral do serviço.")
    checks: Optional[Dict[str, HealthCheck]] = Field(
        default=None,
        description="Detalhamento individual das dependências (presente em /health/ready).",
    )
