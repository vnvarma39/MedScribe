"""
MedScribe — Application Settings Unit Tests
"""
from app.core.config import Settings

def test_settings_cors_parsing():
    settings = Settings(CORS_ORIGINS="http://localhost:8501,http://localhost:3000")
    assert isinstance(settings.CORS_ORIGINS, list)
    assert "http://localhost:8501" in settings.CORS_ORIGINS
    assert "http://localhost:3000" in settings.CORS_ORIGINS

def test_settings_pagination_bounds():
    settings = Settings()
    assert settings.DEFAULT_PAGE_SIZE > 0
    assert settings.MAX_PAGE_SIZE >= 100
