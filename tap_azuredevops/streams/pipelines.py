"""Pipelines stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.projects import ProjectsStream


class PipelinesStream(AzureDevOpsStream):
    """Pipelines stream."""

    name = "pipelines"
    path = "/{project_name}/_apis/pipelines/pipelines"
    primary_keys = ["id"]
    replication_key = None
    records_jsonpath = "$.value[*]"
    parent_stream_type = ProjectsStream

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType, description="Pipeline ID"),
        th.Property("name", th.StringType, description="Pipeline name"),
        th.Property("folder", th.StringType, description="Pipeline folder"),
        th.Property("revision", th.IntegerType, description="Pipeline revision"),
        th.Property("url", th.StringType, description="Pipeline URL"),
        th.Property(
            "_links",
            th.ObjectType(
                th.Property(
                    "self",
                    th.ObjectType(
                        th.Property("href", th.StringType),
                    ),
                ),
                th.Property(
                    "web",
                    th.ObjectType(
                        th.Property("href", th.StringType),
                    ),
                ),
            ),
            description="Pipeline links",
        ),
        th.Property(
            "configuration",
            th.ObjectType(
                th.Property("type", th.StringType),
                th.Property("path", th.StringType),
                th.Property(
                    "repository",
                    th.ObjectType(
                        th.Property("id", th.StringType),
                        th.Property("type", th.StringType),
                        th.Property("name", th.StringType),
                    ),
                ),
            ),
            description="Pipeline configuration",
        ),
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
            msg = "Context is required for pipelines stream"
            raise ValueError(msg)

        project_name = context["name"]
        return f"{self.get_base_url()}/{project_name}/_apis/pipelines/pipelines"
