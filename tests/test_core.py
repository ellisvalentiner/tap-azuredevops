"""Core tests for tap-azuredevops."""

from __future__ import annotations

import pytest

from tap_azuredevops.tap import TapAzureDevOps


def test_tap_initialization():
    """Test tap initialization with valid config."""
    config = {
        "organization": "test-org",
        "personal_access_token": "test-token",
    }

    tap = TapAzureDevOps(config=config)
    assert tap.name == "tap-azuredevops"
    assert tap.config["organization"] == "test-org"
    assert tap.config["personal_access_token"] == "test-token"


def test_tap_config_validation():
    """Test tap config validation."""
    from singer_sdk.exceptions import ConfigValidationError

    # Missing required fields should raise error
    with pytest.raises(ConfigValidationError):
        TapAzureDevOps(config={})

    # Missing organization should raise error
    with pytest.raises(ConfigValidationError):
        TapAzureDevOps(config={"personal_access_token": "test-token"})

    # Missing token should raise error
    with pytest.raises(ConfigValidationError):
        TapAzureDevOps(config={"organization": "test-org"})


def test_tap_discover_streams():
    """Test stream discovery."""
    config = {
        "organization": "test-org",
        "personal_access_token": "test-token",
    }

    tap = TapAzureDevOps(config=config)
    streams = tap.discover_streams()

    assert len(streams) == 10
    stream_names = [stream.name for stream in streams]
    assert "projects" in stream_names
    assert "repositories" in stream_names
    assert "pull_requests" in stream_names
    assert "commits" in stream_names
    assert "branches" in stream_names
    assert "tags" in stream_names
    assert "work_items" in stream_names
    assert "builds" in stream_names
    assert "pipelines" in stream_names
    assert "releases" in stream_names


def test_tap_with_optional_config():
    """Test tap with optional configuration."""
    config = {
        "organization": "test-org",
        "personal_access_token": "test-token",
        "projects": ["project1", "project2"],
        "start_date": "2024-01-01T00:00:00Z",
    }

    tap = TapAzureDevOps(config=config)
    assert tap.config["projects"] == ["project1", "project2"]
    assert tap.config["start_date"] == "2024-01-01T00:00:00Z"
