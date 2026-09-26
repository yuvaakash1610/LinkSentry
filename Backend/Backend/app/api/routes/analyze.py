from fastapi import APIRouter, Depends, Request
from app.core.config import get_settings
from app.core.limiter import limiter
from app.schemas.analyze import (
    CombinedAnalysisRequest,
    CombinedAnalysisResponse,
    QrAnalysisRequest,
    TextAnalysisRequest,
    TextAnalysisResponse,
    UrlAnalysisRequest,
    UrlAnalysisResponse,
)
from app.services.model_service import ModelService, get_model_service

router = APIRouter(prefix="/analyze", tags=["Analyze"])


@router.post(
    "/text",
    response_model=TextAnalysisResponse,
    summary="Analyze Message Text",
    description="Analyze message text for scam patterns, urgency triggers, and security indicators.",
)
@limiter.limit(lambda: get_settings().RATE_LIMIT_ANALYZE)
def analyze_text(
    payload: TextAnalysisRequest,
    request: Request,
    service: ModelService = Depends(get_model_service),
) -> TextAnalysisResponse:
    request_id = getattr(request.state, "request_id", None)
    return service.analyze_text_content(payload.text, request_id=request_id)


@router.post(
    "/url",
    response_model=UrlAnalysisResponse,
    summary="Analyze Suspicious URL",
    description="Analyze a URL string using lexical and structural heuristics without remote fetching.",
)
@limiter.limit(lambda: get_settings().RATE_LIMIT_ANALYZE)
def analyze_url(
    payload: UrlAnalysisRequest,
    request: Request,
    service: ModelService = Depends(get_model_service),
) -> UrlAnalysisResponse:
    request_id = getattr(request.state, "request_id", None)
    return service.analyze_url_content(payload.url, request_id=request_id)


@router.post(
    "/combined",
    response_model=CombinedAnalysisResponse,
    summary="Analyze Combined Message and URLs",
    description="Jointly evaluate message context and associated URLs for correlated threats.",
)
@limiter.limit(lambda: get_settings().RATE_LIMIT_ANALYZE)
def analyze_combined(
    payload: CombinedAnalysisRequest,
    request: Request,
    service: ModelService = Depends(get_model_service),
) -> CombinedAnalysisResponse:
    request_id = getattr(request.state, "request_id", None)
    return service.analyze_combined_content(
        text=payload.text, urls=payload.urls, request_id=request_id
    )


@router.post(
    "/qr",
    response_model=CombinedAnalysisResponse,
    summary="Analyze QR Code Content",
    description="Evaluate raw decoded string payload from an Android QR code scan.",
)
@limiter.limit(lambda: get_settings().RATE_LIMIT_ANALYZE)
def analyze_qr(
    payload: QrAnalysisRequest,
    request: Request,
    service: ModelService = Depends(get_model_service),
) -> CombinedAnalysisResponse:
    request_id = getattr(request.state, "request_id", None)
    return service.analyze_qr_content(payload.content, request_id=request_id)

