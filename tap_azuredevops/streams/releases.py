"""Releases stream."""

from __future__ import annotations

import logging

import requests
import singer_sdk.typing as th
from singer_sdk.exceptions import FatalAPIError
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.projects import ProjectsStream

logger = logging.getLogger(__name__)


class ReleasesStream(AzureDevOpsStream):
    """Releases stream."""

    name = "releases"
    path = "/{project_name}/_apis/release/releases"
    primary_keys = ["id"]
    replication_key = "createdOn"
    records_jsonpath = "$.value[*]"
    parent_stream_type = ProjectsStream

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType, description="Release ID"),
        th.Property("name", th.StringType, description="Release name"),
        th.Property("status", th.StringType, description="Release status"),
        th.Property("createdOn", th.DateTimeType, description="Created date"),
        th.Property("modifiedOn", th.DateTimeType, description="Modified date"),
        th.Property(
            "createdBy",
            th.ObjectType(
                th.Property("displayName", th.StringType),
                th.Property("uniqueName", th.StringType),
                th.Property("id", th.StringType),
            ),
            description="Created by",
        ),
        th.Property(
            "modifiedBy",
            th.ObjectType(
                th.Property("displayName", th.StringType),
                th.Property("uniqueName", th.StringType),
                th.Property("id", th.StringType),
            ),
            description="Modified by",
        ),
        th.Property(
            "releaseDefinition",
            th.ObjectType(
                th.Property("id", th.IntegerType),
                th.Property("name", th.StringType),
                th.Property("url", th.StringType),
            ),
            description="Release definition",
        ),
        th.Property(
            "environments",
            th.ArrayType(
                th.ObjectType(
                    th.Property("id", th.IntegerType),
                    th.Property("name", th.StringType),
                    th.Property("status", th.StringType),
                    th.Property(
                        "deploySteps",
                        th.ArrayType(
                            th.ObjectType(
                                th.Property("id", th.IntegerType),
                                th.Property("deploymentId", th.IntegerType),
                                th.Property("attempt", th.IntegerType),
                                th.Property("status", th.StringType),
                                th.Property("startedOn", th.DateTimeType),
                                th.Property("completedOn", th.DateTimeType),
                            )
                        ),
                    ),
                )
            ),
            description="Environments",
        ),
        th.Property(
            "artifacts",
            th.ArrayType(
                th.ObjectType(
                    th.Property("alias", th.StringType),
                    th.Property("type", th.StringType),
                    th.Property("definitionReference", th.ObjectType()),
                )
            ),
            description="Artifacts",
        ),
        th.Property("url", th.StringType, description="Release URL"),
    ).to_dict()

    def get_new_paginator(self) -> JSONPathPaginator:
        """Return paginator instance.

        Returns:
            JSONPathPaginator instance.
        """
        return JSONPathPaginator(jsonpath="$.continuationToken")

    def get_url_params(
        self,
        context: dict | None,
        next_page_token: dict | None,
    ) -> dict:
        """Return URL parameters for API requests.

        Args:
            context: Stream context.
            next_page_token: Token for next page of results.

        Returns:
            Dictionary of URL parameters.
        """
        params = super().get_url_params(context, next_page_token)

        # Add date filter for incremental sync
        starting_timestamp = self.get_starting_timestamp(context)
        if starting_timestamp:
            params["minCreatedTime"] = starting_timestamp

        # Handle pagination
        if next_page_token and "continuationToken" in next_page_token:
            params["continuationToken"] = next_page_token["continuationToken"]

        return params

    def get_url(self, context: dict | None) -> str:
        """Return URL for the stream.

        Args:
            context: Stream context containing parent record.

        Returns:
            URL string.
        """
        if context is None:
            msg = "Context is required for releases stream"
            raise ValueError(msg)

        project_name = context["name"]
        return f"{self.get_base_url()}/{project_name}/_apis/release/releases"

    def get_starting_timestamp(self, context: dict | None) -> str | None:
        """Return starting timestamp for incremental sync.

        Args:
            context: Stream context.

        Returns:
            Starting timestamp string or None.
        """
        if "start_date" in self.config:
            return self.config["start_date"]

        return self.get_starting_replication_key_value(context)

    def _request(
        self,
        *args,
        **kwargs,
    ) -> requests.Response:
        """Make API request with 401 error handling.

        Override to handle 401 errors gracefully for releases endpoint.
        This can occur if the PAT doesn't have Release permissions.

        Args:
            *args: Positional arguments passed to parent _request.
            **kwargs: Keyword arguments passed to parent _request.

        Returns:
            Response object. For 401 errors, returns a mock empty response.
        """
        try:
            return super()._request(*args, **kwargs)
        except FatalAPIError as e:
            # Check if it's a 401 error
            if "401" in str(e) or "Unauthorized" in str(e):
                project_name = "unknown"
                if hasattr(self, "_context") and self._context:
                    project_name = self._context.get("name", "unknown")
                logger.warning(
                    f"401 Unauthorized when accessing releases for project '{project_name}'. "
                    "This usually means the Personal Access Token doesn't have 'Release (Read)' "
                    "permissions. Skipping releases for this project. "
                    "To fix this, add 'Release (Read & Execute)' scope to your PAT."
                )
                # Return a mock response with empty data to continue processing
                mock_response = requests.Response()
                mock_response.status_code = 200
                mock_response._content = b'{"value": []}'
                mock_response.headers["Content-Type"] = "application/json"
                # Set encoding to avoid issues
                mock_response.encoding = "utf-8"
                # Set url if available from kwargs
                if "url" in kwargs:
                    mock_response.url = kwargs["url"]
                return mock_response
            # Re-raise other FatalAPIErrors
            raise

    def request_records(self, context: dict | None) -> None:
        """Request records from the API.

        Override to store context for error messages.

        Args:
            context: Stream context.
        """
        # Store context for error messages
        self._context = context
        # Call parent implementation
        super().request_records(context)
