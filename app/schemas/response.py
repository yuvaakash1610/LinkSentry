from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Normalized error payload details."""
    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable explanation of the error")
    request_id: Optional[str] = Field(None, description="Unique correlation identifier for the request")


class ErrorResponse(BaseModel):
    """Standardized error envelope across all API endpoints."""
    error: ErrorDetail


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field("ok", description="Service health state")
    service: str = Field("linksentry-backend", description="Service identifier")
    version: str = Field(..., description="Current semantic version")
