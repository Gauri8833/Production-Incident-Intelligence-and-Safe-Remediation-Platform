import pytest
from src.ingestion.validators import (
    validate_log_dict,
    validate_metric_dict,
    mask_pii,
)


def test_valid_log():
    record = {
        "timestamp": "2026-10-01T10:20:00Z",
        "service_name": "payment_service",
        "level": "ERROR",
        "message": "database connection timeout",
    }
    result = validate_log_dict(record)
    assert result.is_valid
    assert len(result.errors) == 0


def test_missing_timestamp_log():
    record = {
        "service_name": "payment_service",
        "level": "ERROR",
        "message": "database connection timeout",
    }
    result = validate_log_dict(record)
    assert not result.is_valid
    assert any("timestamp" in err for err in result.errors)


def test_missing_service_name_log():
    record = {
        "timestamp": "2026-10-01T10:20:00Z",
        "level": "ERROR",
        "message": "database connection timeout",
    }
    result = validate_log_dict(record)
    assert not result.is_valid
    assert any("service_name" in err for err in result.errors)


def test_unknown_log_level():
    record = {
        "timestamp": "2026-10-01T10:20:00Z",
        "service_name": "payment_service",
        "level": "SUPER_ERROR",
        "message": "database connection timeout",
    }
    result = validate_log_dict(record)
    assert not result.is_valid
    assert any("level" in err for err in result.errors)


def test_valid_metric():
    record = {
        "timestamp": "2026-10-01T10:20:00Z",
        "service_name": "database",
        "metric_name": "database_connections_percent",
        "metric_value": 98.5,
    }
    result = validate_metric_dict(record)
    assert result.is_valid
    assert len(result.errors) == 0


def test_invalid_metric_value():
    record = {
        "timestamp": "2026-10-01T10:20:00Z",
        "service_name": "database",
        "metric_name": "database_connections_percent",
        "metric_value": 150.0,  # > 100%
    }
    result = validate_metric_dict(record)
    assert not result.is_valid
    assert any("cannot exceed 100%" in err for err in result.errors)


def test_negative_metric_value():
    record = {
        "timestamp": "2026-10-01T10:20:00Z",
        "service_name": "database",
        "metric_name": "request_count",
        "metric_value": -5.0,
    }
    result = validate_metric_dict(record)
    assert not result.is_valid
    assert any("negative" in err for err in result.errors)


def test_pii_masking():
    raw_message = "User user@example.com charged card 4111-2222-3333-4444 with Bearer eyJhbGciOiJIUzI1NiJ9"
    masked = mask_pii(raw_message)
    assert "user@example.com" not in masked
    assert "[EMAIL_MASKED]" in masked
    assert "4111-2222-3333-4444" not in masked
    assert "[CARD_MASKED]" in masked
    assert "[TOKEN_MASKED]" in masked
