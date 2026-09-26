import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes.analyze import router as analyze_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.system import router as system_router
from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.logging import get_logger, setup_logging
from app.core.security import SecurityHeadersMiddleware
from app.schemas.response import ErrorDetail, ErrorResponse, HealthResponse


# Initialize structured logging
setup_logging()
logger = get_logger("linksentry.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and shutdown events."""
    settings = get_settings()
    logger.info(
        "Starting %s v%s in %s mode",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


def create_application() -> FastAPI:
    """Application factory for LinkSentry Backend."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Cybersecurity analysis backend for LinkSentry Android application. "
            "Analyzes scam messages, malicious URLs, QR payloads, and combined threat vectors. "
            "'Think before you tap.'"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.state.settings = settings

    # 1. CORS & Rate Limiter Configuration
    limiter.enabled = settings.RATE_LIMIT_ENABLED
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    allow_credentials = True
    origins = settings.ALLOWED_ORIGINS
    if isinstance(origins, list) and "*" in origins:
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # 2. Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)


    # 3. Request Correlation & Structured Logging Middleware
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        # Obtain or generate unique correlation request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        endpoint = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = request_id

            # Safe structured log record without raw body content
            logger.info(
                "%s %s -> status=%d duration=%.2fms",
                method,
                endpoint,
                response.status_code,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "Unhandled error during %s %s duration=%.2fms: %s",
                method,
                endpoint,
                duration_ms,
                exc,
                extra={
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "error_code": "INTERNAL_SERVER_ERROR",
                },
            )
            error_payload = ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="An unexpected server error occurred while processing your request.",
                    request_id=request_id,
                )
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_payload.model_dump(),
                headers={"X-Request-ID": request_id},
            )

    # 4. Centralized Exception Handlers

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(
        request: Request, exc: RateLimitExceeded
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "Rate limit exceeded on %s %s",
            request.method,
            request.url.path,
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": 429,
                "error_code": "TOO_MANY_REQUESTS",
            },
        )
        error_payload = ErrorResponse(
            error=ErrorDetail(
                code="TOO_MANY_REQUESTS",
                message="Rate limit exceeded. Please try again later.",
                request_id=request_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_payload.model_dump(),
            headers={"X-Request-ID": request_id} if request_id else {},
        )


    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        # Summarize validation issues safely without dumping sensitive inputs
        error_messages = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            error_messages.append(f"{loc}: {msg}")
        joined_message = "; ".join(error_messages) if error_messages else "The supplied input is invalid."

        logger.warning(
            "Validation failure on %s %s: %s",
            request.method,
            request.url.path,
            joined_message,
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": 422,
                "error_code": "INVALID_INPUT",
            },
        )

        error_payload = ErrorResponse(
            error=ErrorDetail(
                code="INVALID_INPUT",
                message=joined_message,
                request_id=request_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error_payload.model_dump(),
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    @app.exception_handler(HTTPException)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "TOO_MANY_REQUESTS",
        }
        error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

        error_payload = ErrorResponse(
            error=ErrorDetail(
                code=error_code,
                message=str(exc.detail),
                request_id=request_id,
            )
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload.model_dump(),
            headers={"X-Request-ID": request_id} if request_id else {},
        )

    # 5. Route Inclusions
    app.include_router(system_router, prefix=settings.API_PREFIX)
    app.include_router(analyze_router, prefix=settings.API_PREFIX)
    app.include_router(feedback_router, prefix=settings.API_PREFIX)

    # Top-level direct health check fallback
    @app.get(
        "/health",
        response_model=HealthResponse,
        include_in_schema=False,
    )
    def root_health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service="linksentry-backend",
            version=settings.APP_VERSION,
        )

    # Top-level direct model-info fallback
    @app.get(
        "/model-info",
        include_in_schema=False,
    )
    def root_model_info():
        from app.services.model_service import get_model_service
        return get_model_service().get_model_info()

    # Direct route alias for /api/openapi.json
    @app.get(
        f"{settings.API_PREFIX}/openapi.json",
        include_in_schema=False,
    )
    def api_openapi_json():
        return app.openapi()

    return app


app = create_application()
