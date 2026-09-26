from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class FeedbackRating(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNCERTAIN = "uncertain"


class FeedbackCategory(str, Enum):
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    USER_CORRECTION = "USER_CORRECTION"
    GENERAL = "GENERAL"


class FeedbackRequest(BaseModel):
    """Payload for submitting user or app feedback on analysis results."""
    feedback: Optional[FeedbackRating] = Field(
        None,
        description="User verdict on model accuracy: correct, incorrect, uncertain",
        examples=["correct", "incorrect", "uncertain"],
    )
    category: Optional[FeedbackCategory] = Field(
        None,
        description="Optional category classification",
    )
    request_id: Optional[str] = Field(
        None,
        description="Original analysis request ID being reviewed",
    )
    reported_risk_tier: Optional[str] = Field(
        None,
        description="Risk tier assigned by LinkSentry",
    )
    input_text: Optional[str] = Field(
        None,
        max_length=10000,
        description="Optional submitted text",
    )
    input_url: Optional[str] = Field(
        None,
        max_length=4096,
        description="Optional submitted URL",
    )
    user_notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="User notes or context",
    )

    @model_validator(mode="after")
    def validate_feedback_rating_or_category(self) -> "FeedbackRequest":
        if self.feedback is None and self.category is None:
            raise ValueError("Either 'feedback' (correct, incorrect, uncertain) or 'category' must be provided.")
        return self


class FeedbackResponse(BaseModel):
    """Acknowledgement of feedback submission."""
    status: str = Field("success", description="Status of the feedback reception")
    feedback_id: str = Field(..., description="Generated feedback ticket identifier")
    message: str = Field(
        "Thank you for helping keep LinkSentry accurate and secure.",
        description="User message",
    )
