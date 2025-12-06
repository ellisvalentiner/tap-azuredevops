"""Commits stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.repositories import RepositoriesStream


class CommitsStream(AzureDevOpsStream):
    """Commits stream."""

    name = "commits"
    path = "/{project}/_apis/git/repositories/{repositoryId}/commits"
    primary_keys = ["commitId"]
    replication_key = "authorDate"
    records_jsonpath = "$.value[*]"
    parent_stream_type = RepositoriesStream

    schema = th.PropertiesList(
        th.Property("commitId", th.StringType, description="Commit ID"),
        th.Property("authorDate", th.DateTimeType, description="Author date (from author.date)"),
        th.Property(
            "author",
            th.ObjectType(
                th.Property("name", th.StringType),
                th.Property("email", th.StringType),
                th.Property("date", th.DateTimeType),
            ),
            description="Author information",
        ),
        th.Property(
            "committer",
            th.ObjectType(
                th.Property("name", th.StringType),
                th.Property("email", th.StringType),
                th.Property("date", th.DateTimeType),
            ),
            description="Committer information",
        ),
        th.Property("comment", th.StringType, description="Commit message"),
        th.Property("url", th.StringType, description="Commit URL"),
        th.Property("remoteUrl", th.StringType, description="Remote URL"),
        th.Property(
            "changeCounts",
            th.ObjectType(
                th.Property("Add", th.IntegerType),
                th.Property("Edit", th.IntegerType),
                th.Property("Delete", th.IntegerType),
            ),
            description="Change counts",
        ),
        th.Property("parents", th.ArrayType(th.StringType), description="Parent commit IDs"),
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

        # Add date filter for incremental sync
        starting_timestamp = self.get_starting_timestamp(context)
        if starting_timestamp:
            params["fromDate"] = starting_timestamp

        return params

    def get_url(self, context: dict | None) -> str:
        """Return URL for the stream.

        Args:
            context: Stream context containing parent record.

        Returns:
            URL string.
        """
        if context is None:
            msg = "Context is required for commits stream"
            raise ValueError(msg)

        project_name = context["project"]["name"]
        repository_id = context["id"]
        return (
            f"{self.get_base_url()}/{project_name}/_apis/git/repositories/{repository_id}/commits"
        )

    def post_process(self, row: dict, context: dict | None = None) -> dict:
        """Post-process record to flatten author.date.

        Args:
            row: Record dictionary.
            context: Stream context.

        Returns:
            Processed record dictionary.
        """
        # Flatten author.date to authorDate for replication key
        if "author" in row and "date" in row.get("author", {}):
            row["authorDate"] = row["author"]["date"]

        return row

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
