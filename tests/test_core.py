"""Core tests for tap-azuredevops."""

from __future__ import annotations

import os
from unittest.mock import patch

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


def test_tap_with_environment_variables():
    """Test tap initialization with environment variables."""
    with patch.dict(
        os.environ,
        {
            "AZURE_DEVOPS_ORGANIZATION": "env-org",
            "AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN": "env-token",
        },
    ):
        tap = TapAzureDevOps(config={})
        assert tap.config["organization"] == "env-org"
        assert tap.config["personal_access_token"] == "env-token"


def test_tap_environment_variables_override_config():
    """Test that environment variables override config file values."""
    config = {
        "organization": "config-org",
        "personal_access_token": "config-token",
    }

    with patch.dict(
        os.environ,
        {
            "AZURE_DEVOPS_ORGANIZATION": "env-org",
            "AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN": "env-token",
        },
    ):
        tap = TapAzureDevOps(config=config)
        # Environment variables should take precedence
        assert tap.config["organization"] == "env-org"
        assert tap.config["personal_access_token"] == "env-token"


def test_tap_config_fallback_when_env_not_set():
    """Test that config file values work when environment variables are not set."""
    config = {
        "organization": "config-org",
        "personal_access_token": "config-token",
        "projects": ["project1"],
    }

    # Ensure environment variables are not set
    with patch.dict(os.environ, {}, clear=True):
        tap = TapAzureDevOps(config=config)
        # Config file values should be used
        assert tap.config["organization"] == "config-org"
        assert tap.config["personal_access_token"] == "config-token"
        assert tap.config["projects"] == ["project1"]


def test_tap_partial_environment_variables():
    """Test tap with only one environment variable set."""
    config = {
        "organization": "config-org",
        "personal_access_token": "config-token",
    }

    with patch.dict(os.environ, {"AZURE_DEVOPS_ORGANIZATION": "env-org"}):
        tap = TapAzureDevOps(config=config)
        # Organization should come from env, token from config
        assert tap.config["organization"] == "env-org"
        assert tap.config["personal_access_token"] == "config-token"
