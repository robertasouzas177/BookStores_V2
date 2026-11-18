"""exceptions.py — Tratamento padronizado de erros da Bookstore API conforme RFC 9457.

Fonte oficial de verdade:
- apidog/Bookstore API.openapi.yaml
- docs/SPEC.md
- docs/STYLEGUIDE.md
- docs/PLAN.md
"""

from typing import Any, Dict, List, Optional
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiErrorException(Exception):
    """Exceção base da Bookstore API conforme a especificação RFC 9457 (Problem Details)."""

    def __init__(
        self,
        status_code: int,
        title: str,
        detail: Optional[str] = None,
        type_uri: str = "about:blank",
        instance: Optional[str] = None,
        code: Optional[str] = None,
        invalid_params: Optional[List[Dict[str, str]]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type_uri = type_uri
        self.instance = instance
        self.code = code
        self.invalid_params = invalid_params or []
        self.headers = headers or {}
        super().__init__(detail or title)


# ============================================================================
# Exceções Semânticas por Status HTTP
# ============================================================================


class BadRequestException(ApiErrorException):
    """400 Bad Request — Requisição malformada (JSON inválido, parâmetro ausente)."""

    def __init__(
        self,
        detail: str = "O corpo da requisição não é um JSON válido.",
        instance: Optional[str] = None,
        code: str = "BAD_REQUEST",
    ):
        super().__init__(
            status_code=400,
            title="Requisição Inválida",
            detail=detail,
            type_uri="https://api.bookstore.dev/errors/bad-request",
            instance=instance,
            code=code,
        )


class UnauthorizedException(ApiErrorException):
    """401 Unauthorized — Token ausente, inválido, expirado ou credenciais incorretas."""

    def __init__(
        self,
        detail: str = "Credenciais inválidas.",
        code: str = "INVALID_CREDENTIALS",
        title: str = "Não Autenticado",
        type_uri: str = "https://api.bookstore.dev/errors/unauthorized",
        instance: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        default_headers = {"WWW-Authenticate": "Bearer"}
        if headers:
            default_headers.update(headers)
        super().__init__(
            status_code=401,
            title=title,
            detail=detail,
            type_uri=type_uri,
            instance=instance,
            code=code,
            headers=default_headers,
        )


class ForbiddenException(ApiErrorException):
    """403 Forbidden — Autenticado, porém sem a permissão (role/escopo) exigida."""

    def __init__(
        self,
        detail: str = "Sua conta não possui permissão suficiente para esta operação.",
        instance: Optional[str] = None,
        code: str = "INSUFFICIENT_PERMISSIONS",
    ):
        super().__init__(
            status_code=403,
            title="Acesso Negado",
            detail=detail,
            type_uri="https://api.bookstore.dev/errors/forbidden",
            instance=instance,
            code=code,
        )


class NotFoundException(ApiErrorException):
    """404 Not Found — Recurso não localizado."""

    def __init__(
        self,
        detail: str = "O recurso com o identificador informado não foi localizado.",
        instance: Optional[str] = None,
        code: str = "NOT_FOUND",
        title: str = "Recurso Inexistente",
    ):
        super().__init__(
            status_code=404,
            title=title,
            detail=detail,
            type_uri="https://api.bookstore.dev/errors/not-found",
            instance=instance,
            code=code,
        )


class ConflictException(ApiErrorException):
    """409 Conflict — Conflito de estado (estoque insuficiente, duplicidade, recurso em uso)."""

    def __init__(
        self,
        detail: str,
        code: str = "CONFLICT",
        title: str = "Conflito de Estado",
        type_uri: str = "https://api.bookstore.dev/errors/conflict",
        instance: Optional[str] = None,
    ):
        if code == "INSUFFICIENT_STOCK":
            title = "Estoque Insuficiente"
            type_uri = "https://api.bookstore.dev/errors/insufficient-stock"
        elif code == "RESOURCE_IN_USE":
            title = "Recurso em Uso"
            type_uri = "https://api.bookstore.dev/errors/resource-in-use"
        elif code == "DUPLICATE_RESOURCE":
            title = "Recurso Duplicado"
            type_uri = "https://api.bookstore.dev/errors/duplicate-resource"
        elif code == "IDEMPOTENCY_IN_PROGRESS":
            title = "Requisição em Andamento"
            type_uri = "https://api.bookstore.dev/errors/idempotency-in-progress"

        super().__init__(
            status_code=409,
            title=title,
            detail=detail,
            type_uri=type_uri,
            instance=instance,
            code=code,
        )


class PreconditionFailedException(ApiErrorException):
    """412 Precondition Failed — Versão do recurso diverge (If-Match não confere)."""

    def __init__(
        self,
        detail: str = "O recurso foi modificado por outro usuário. Releia (GET) e tente novamente.",
        instance: Optional[str] = None,
        code: str = "PRECONDITION_FAILED",
    ):
        super().__init__(
            status_code=412,
            title="Pré-condição Falhou",
            detail=detail,
            type_uri="https://api.bookstore.dev/errors/precondition-failed",
            instance=instance,
            code=code,
        )


class UnprocessableEntityException(ApiErrorException):
    """422 Unprocessable Entity — Violação de regras de validação ou payload semântico."""

    def __init__(
        self,
        detail: str = "Erro de validação nos dados enviados.",
        invalid_params: Optional[List[Dict[str, str]]] = None,
        instance: Optional[str] = None,
        code: str = "VALIDATION_FAILED",
    ):
        super().__init__(
            status_code=422,
            title="Erro de Validação de Dados",
            detail=detail,
            type_uri="https://api.bookstore.dev/errors/validation-failed",
            instance=instance,
            code=code,
            invalid_params=invalid_params,
        )


class TooManyRequestsException(ApiErrorException):
    """429 Too Many Requests — Limite de requisições excedido (Rate Limiting)."""

    def __init__(
        self,
        detail: str = "Limite de requisições excedido. Tente novamente em instantes.",
        retry_after: Optional[int] = 60,
        instance: Optional[str] = None,
        code: str = "TOO_MANY_REQUESTS",
    ):
        headers = {"Retry-After": str(retry_after)} if retry_after else {}
        super().__init__(
            status_code=429,
            title="Muitas Requisições",
            detail=detail,
            type_uri="https://api.bookstore.dev/errors/too-many-requests",
            instance=instance,
            code=code,
            headers=headers,
        )


# ============================================================================
# Fábrica de Respostas RFC 9457 e Handlers FastAPI
# ============================================================================


def create_problem_details(
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    type_uri: str = "about:blank",
    instance: Optional[str] = None,
    code: Optional[str] = None,
    invalid_params: Optional[List[Dict[str, str]]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """Gera uma resposta JSONResponse formatada estritamente como application/problem+json."""
    content: Dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
    }
    if detail is not None:
        content["detail"] = detail
    if instance is not None:
        content["instance"] = instance
    if code is not None:
        content["code"] = code
    if invalid_params:
        content["invalidParams"] = invalid_params

    resp_headers = {"Content-Type": "application/problem+json"}
    if headers:
        resp_headers.update(headers)

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=resp_headers,
    )


async def api_error_exception_handler(request: Request, exc: ApiErrorException) -> JSONResponse:
    """Handler global para exceções do tipo ApiErrorException."""
    instance = exc.instance or request.url.path
    return create_problem_details(
        status_code=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        type_uri=exc.type_uri,
        instance=instance,
        code=exc.code,
        invalid_params=exc.invalid_params,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler para erros de validação nativos do Pydantic no FastAPI, convertendo para RFC 9457."""
    invalid_params: List[Dict[str, str]] = []
    for error in exc.errors():
        # Extrai o nome do campo (geralmente último item de loc)
        loc = error.get("loc", [])
        field_name = str(loc[-1]) if loc else "body"
        reason = error.get("msg", "Campo inválido")
        invalid_params.append({"name": field_name, "reason": reason})

    first_error_msg = invalid_params[0]["reason"] if invalid_params else "Erro de validação"
    first_field = invalid_params[0]["name"] if invalid_params else "campo"
    detail = f"O campo '{first_field}' apresentou erro: {first_error_msg}."

    return create_problem_details(
        status_code=422,
        title="Erro de Validação de Dados",
        detail=detail,
        type_uri="https://api.bookstore.dev/errors/validation-failed",
        instance=request.url.path,
        code="VALIDATION_FAILED",
        invalid_params=invalid_params,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Converte exceções HTTP padrão do Starlette/FastAPI no formato RFC 9457."""
    titles = {
        400: "Requisição Inválida",
        401: "Não Autenticado",
        403: "Acesso Negado",
        404: "Recurso Inexistente",
        405: "Método Não Permitido",
        409: "Conflito de Estado",
        412: "Pré-condição Falhou",
        415: "Tipo de Mídia Não Suportado",
        422: "Erro de Validação de Dados",
        429: "Muitas Requisições",
        500: "Erro Interno do Servidor",
        503: "Serviço Indisponível",
    }
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        412: "PRECONDITION_FAILED",
        415: "UNSUPPORTED_MEDIA_TYPE",
        422: "VALIDATION_FAILED",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    title = titles.get(exc.status_code, "Erro na Requisição")
    code = codes.get(exc.status_code, "HTTP_ERROR")
    type_uri = f"https://api.bookstore.dev/errors/{code.lower().replace('_', '-')}"

    return create_problem_details(
        status_code=exc.status_code,
        title=title,
        detail=str(exc.detail) if exc.detail else title,
        type_uri=type_uri,
        instance=request.url.path,
        code=code,
        headers=exc.headers,
    )


async def integrity_exception_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Trata violações de chave estrangeira RESTRICT e integridade relacional, convertendo para 409 Conflict RFC 9457."""
    return create_problem_details(
        status_code=409,
        title="Recurso em Uso",
        detail="A operação não pode ser concluída porque o registro possui vendas ou vínculos dependentes no histórico.",
        type_uri="https://api.bookstore.dev/errors/resource-in-use",
        instance=request.url.path,
        code="RESOURCE_IN_USE",
    )
