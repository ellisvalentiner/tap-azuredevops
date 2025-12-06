"""Releases stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.projects import ProjectsStream


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
