"""Azure DevOps tap class."""

from __future__ import annotations

import os

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_azuredevops.streams import (
    BranchesStream,
    BuildsStream,
    CommitsStream,
    PipelinesStream,
    ProjectsStream,
    PullRequestsStream,
    ReleasesStream,
    RepositoriesStream,
    TagsStream,
    WorkItemsStream,
)


class TapAzureDevOps(Tap):
    """Azure DevOps tap class."""

    name = "tap-azuredevops"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "organization",
            th.StringType,
            required=True,
            description="Azure DevOps organization name",
        ),
        th.Property(
            "personal_access_token",
            th.StringType,
            required=True,
            secret=True,
            description="Personal Access Token for authentication",
        ),
        th.Property(
            "projects",
            th.ArrayType(th.StringType),
            description="Optional list of project names to filter. If not provided, all projects will be synced.",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="Start date for incremental replication (ISO 8601 format)",
        ),
    ).to_dict()

    def __init__(self, *args, config: dict | None = None, **kwargs) -> None:
        """Initialize tap with support for environment variables.

        Environment variables take precedence over config file values:
        - AZURE_DEVOPS_ORGANIZATION: Azure DevOps organization name
        - AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN: Personal Access Token

        Args:
            *args: Positional arguments passed to parent class.
            config: Configuration dictionary.
            **kwargs: Keyword arguments passed to parent class.
        """
        # Merge environment variables into config if provided
        if config is None:
            config = {}

        # Environment variables take precedence over config file values
        env_org = os.getenv("AZURE_DEVOPS_ORGANIZATION")
        env_token = os.getenv("AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN")

        if env_org:
            config["organization"] = env_org
        if env_token:
            config["personal_access_token"] = env_token

        super().__init__(*args, config=config, **kwargs)

    def discover_streams(self) -> list:
        """Return a list of discovered streams."""
        return [
            ProjectsStream(self),
            RepositoriesStream(self),
            PullRequestsStream(self),
            CommitsStream(self),
            BranchesStream(self),
            TagsStream(self),
            WorkItemsStream(self),
            BuildsStream(self),
            PipelinesStream(self),
            ReleasesStream(self),
        ]


if __name__ == "__main__":
    TapAzureDevOps.cli()
