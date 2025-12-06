"""Repositories stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.projects import ProjectsStream


class RepositoriesStream(AzureDevOpsStream):
    """Repositories stream."""

    name = "repositories"
    path = "/{project}/_apis/git/repositories"
    primary_keys = ["id"]
    replication_key = None
    records_jsonpath = "$.value[*]"
    parent_stream_type = ProjectsStream

    schema = th.PropertiesList(
        th.Property("id", th.StringType, description="Repository ID"),
        th.Property("name", th.StringType, description="Repository name"),
        th.Property("url", th.StringType, description="Repository URL"),
        th.Property(
            "project",
            th.ObjectType(
                th.Property("id", th.StringType),
                th.Property("name", th.StringType),
                th.Property("state", th.StringType),
                th.Property("visibility", th.StringType),
            ),
            description="Project information",
        ),
        th.Property("defaultBranch", th.StringType, description="Default branch"),
        th.Property("size", th.IntegerType, description="Repository size in bytes"),
        th.Property("remoteUrl", th.StringType, description="Remote URL"),
        th.Property("sshUrl", th.StringType, description="SSH URL"),
        th.Property("webUrl", th.StringType, description="Web URL"),
        th.Property("isDisabled", th.BooleanType, description="Is repository disabled"),
        th.Property("isInMainBranch", th.BooleanType, description="Is in main branch"),
        th.Property("isFork", th.BooleanType, description="Is fork"),
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
            msg = "Context is required for repositories stream"
            raise ValueError(msg)

        project_name = context["name"]
        return f"{self.get_base_url()}/{project_name}/_apis/git/repositories"

    def get_child_context(self, record: dict, context: dict | None) -> dict:
        """Return context for child streams.

        Args:
            record: Parent record.
            context: Parent stream context.

        Returns:
            Child stream context.
        """
        return {
            "id": record["id"],
            "name": record["name"],
            "project": {
                "id": context["id"] if context else None,
                "name": context["name"] if context else None,
            },
        }
