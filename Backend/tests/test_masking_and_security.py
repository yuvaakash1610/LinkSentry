from app.core.security import sanitize_input_string
from app.utils.masking import (
    mask_card_number,
    mask_sensitive_text,
    mask_sensitive_url_params,
)


def test_mask_card_number():
    raw = "My card number is 4532-1234-5678-9012 for billing."
    masked = mask_card_number(raw)
    assert "4532" not in masked
    assert "9012" in masked
    assert "***-***-***-9012" in masked


def test_mask_sensitive_text():
    raw = "Your secret OTP is: 849201. Do not share password: MySecretPass123 or CVV: 492. UPI: test@okhdfcbank"
    masked = mask_sensitive_text(raw)
    assert "849201" not in masked
    assert "[REDACTED_OTP]" in masked
    assert "MySecretPass123" not in masked
    assert "[REDACTED_PWD]" in masked
    assert "492" not in masked
    assert "[REDACTED_CVV]" in masked
    assert "test@okhdfcbank" not in masked
    assert "[REDACTED_UPI]" in masked


def test_mask_sensitive_url_params():
    url = "https://example.com/auth?token=secret12345&user=john&apiKey=xyz987"
    masked = mask_sensitive_url_params(url)
    assert "secret12345" not in masked
    assert "xyz987" not in masked
    assert "token=%5BREDACTED%5D" in masked or "token=[REDACTED]" in masked
    assert "john" in masked


def test_sanitize_input_string():
    dirty = "Hello \x00World\t\n!"
    clean = sanitize_input_string(dirty, max_length=50)
    assert "\x00" not in clean
    assert "Hello World" in clean
