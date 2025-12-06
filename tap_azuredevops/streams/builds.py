"""Builds stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.projects import ProjectsStream


class BuildsStream(AzureDevOpsStream):
    """Builds stream."""

    name = "builds"
    path = "/{project_name}/_apis/build/builds"
    primary_keys = ["id"]
    replication_key = "finishTime"
    records_jsonpath = "$.value[*]"
    parent_stream_type = ProjectsStream

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType, description="Build ID"),
        th.Property("buildNumber", th.StringType, description="Build number"),
        th.Property("status", th.StringType, description="Build status"),
        th.Property("result", th.StringType, description="Build result"),
        th.Property("queueTime", th.DateTimeType, description="Queue time"),
        th.Property("startTime", th.DateTimeType, description="Start time"),
        th.Property("finishTime", th.DateTimeType, description="Finish time"),
        th.Property("url", th.StringType, description="Build URL"),
        th.Property(
            "definition",
            th.ObjectType(
                th.Property("id", th.IntegerType),
                th.Property("name", th.StringType),
                th.Property("url", th.StringType),
            ),
            description="Build definition",
        ),
        th.Property(
            "project",
            th.ObjectType(
                th.Property("id", th.StringType),
                th.Property("name", th.StringType),
            ),
            description="Project information",
        ),
        th.Property("sourceBranch", th.StringType, description="Source branch"),
        th.Property("sourceVersion", th.StringType, description="Source version"),
        th.Property("reason", th.StringType, description="Build reason"),
        th.Property(
            "requestedBy",
            th.ObjectType(
                th.Property("displayName", th.StringType),
                th.Property("uniqueName", th.StringType),
                th.Property("id", th.StringType),
            ),
            description="Requested by",
        ),
        th.Property(
            "requestedFor",
            th.ObjectType(
                th.Property("displayName", th.StringType),
                th.Property("uniqueName", th.StringType),
                th.Property("id", th.StringType),
            ),
            description="Requested for",
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

        # Add date filter for incremental sync
        starting_timestamp = self.get_starting_timestamp(context)
        if starting_timestamp:
            params["minTime"] = starting_timestamp

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
            msg = "Context is required for builds stream"
            raise ValueError(msg)

        project_name = context["name"]
        return f"{self.get_base_url()}/{project_name}/_apis/build/builds"

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
