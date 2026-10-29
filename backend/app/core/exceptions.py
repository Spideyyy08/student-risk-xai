"""
Custom Exceptions and Exception Handlers.
Enforces strict contract: every error response is JSON {"detail": "<string>", "errors": [...]}.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST, errors: list = None):
        self.detail = detail
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(detail)


class ThrottledException(AppException):
    def __init__(self, detail: str = "Too many failed attempts. Please try again later."):
        super().__init__(detail=detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found."):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Permission denied."):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    content = {"detail": str(exc.detail)}
    if exc.errors:
        content["errors"] = exc.errors
    return JSONResponse(status_code=exc.status_code, content=content)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail_str = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail_str},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Format FastAPI validation errors into a human-readable single detail string
    to satisfy frontend new Error(errData.detail).
    """
    raw_errors = exc.errors()
    first_msg = "Validation error."
    if raw_errors:
        first = raw_errors[0]
        field = ".".join(str(loc) for loc in first.get("loc", []) if loc != "body")
        msg = first.get("msg", "invalid value")
        if field:
            first_msg = f"{field}: {msg}"
        else:
            first_msg = msg

    formatted_errors = []
    for err in raw_errors:
        loc = ".".join(str(x) for x in err.get("loc", []))
        formatted_errors.append({"location": loc, "message": err.get("msg", "")})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": first_msg,
            "errors": formatted_errors,
        },
    )
