"""Projects stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream


class ProjectsStream(AzureDevOpsStream):
    """Projects stream."""

    name = "projects"
    path = "/_apis/projects"
    primary_keys = ["id"]
    replication_key = None
    records_jsonpath = "$.value[*]"

    schema = th.PropertiesList(
        th.Property("id", th.StringType, description="Project ID"),
        th.Property("name", th.StringType, description="Project name"),
        th.Property("description", th.StringType, description="Project description"),
        th.Property("url", th.StringType, description="Project URL"),
        th.Property("state", th.StringType, description="Project state"),
        th.Property("revision", th.IntegerType, description="Project revision"),
        th.Property("visibility", th.StringType, description="Project visibility"),
        th.Property("lastUpdateTime", th.DateTimeType, description="Last update time"),
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

        # Azure DevOps uses continuationToken for pagination
        if next_page_token and "continuationToken" in next_page_token:
            params["continuationToken"] = next_page_token["continuationToken"]

        return params

    def get_url(self, context: dict | None) -> str:
        """Return URL for the stream.

        Args:
            context: Stream context.

        Returns:
            URL string.
        """
        return f"{self.get_base_url()}/_apis/projects"

    def get_child_context(self, record: dict, context: dict | None) -> dict:
        """Return context for child streams.

        Args:
            record: Parent record.
            context: Parent stream context.

        Returns:
            Child stream context.
        """
        return {
            "name": record["name"],
            "id": record["id"],
        }

    def post_process(self, row: dict, context: dict | None = None) -> dict | None:
        """Post-process record.

        Args:
            row: Record dictionary.
            context: Stream context.

        Returns:
            Processed record dictionary or None to skip.
        """
        # Filter projects if specified in config
        if "projects" in self.config and self.config["projects"]:
            if row.get("name") not in self.config["projects"]:
                return None

        return row
