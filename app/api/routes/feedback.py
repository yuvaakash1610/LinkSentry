import uuid
from fastapi import APIRouter
from app.core.logging import get_logger
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.utils.masking import mask_sensitive_text, mask_sensitive_url_params

router = APIRouter(prefix="/feedback", tags=["Feedback"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=FeedbackResponse,
    summary="Submit Detection Feedback",
    description="Submit user or app feedback (correct, incorrect, uncertain) to improve security intelligence.",
)
def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    feedback_id = str(uuid.uuid4())

    rating_str = payload.feedback.value if payload.feedback else None
    category_str = payload.category.value if payload.category else None

    # Scrub sensitive credentials, OTPs, PINs, or raw PII
    safe_text_preview = (
        mask_sensitive_text(payload.input_text[:100])
        if payload.input_text
        else None
    )
    safe_url_preview = (
        mask_sensitive_url_params(payload.input_url)
        if payload.input_url
        else None
    )

    logger.info(
        "Feedback registered: id=%s feedback=%s category=%s tier=%s text_preview=%s url_preview=%s",
        feedback_id,
        rating_str,
        category_str,
        payload.reported_risk_tier,
        safe_text_preview,
        safe_url_preview,
        extra={
            "feedback_id": feedback_id,
            "feedback_rating": rating_str,
            "category": category_str,
        },
    )

    return FeedbackResponse(
        status="success",
        feedback_id=feedback_id,
        message="Thank you for helping keep LinkSentry accurate and secure.",
    )
