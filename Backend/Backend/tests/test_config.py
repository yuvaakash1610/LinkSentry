import pytest
from app.core.config import Settings, get_settings


def test_default_configuration():
    settings = get_settings()
    assert settings.APP_NAME == "LinkSentry Backend"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.API_PREFIX == "/api"
    assert settings.MAX_TEXT_LENGTH == 10000
    assert settings.MAX_URL_LENGTH == 4096
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert len(settings.ALLOWED_ORIGINS) >= 1


def test_cors_origins_parsing():
    # Comma-separated string parsing
    s = Settings(ALLOWED_ORIGINS="http://localhost:3000, https://linksentry.app")
    assert s.ALLOWED_ORIGINS == ["http://localhost:3000", "https://linksentry.app"]


def test_weight_configuration():
    settings = get_settings()
    total_weights = settings.TEXT_WEIGHT + settings.URL_WEIGHT + settings.RULE_WEIGHT
    assert abs(total_weights - 1.0) < 0.01
