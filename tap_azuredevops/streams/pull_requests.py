"""Pull requests stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.repositories import RepositoriesStream


class PullRequestsStream(AzureDevOpsStream):
    """Pull requests stream."""

    name = "pull_requests"
    path = "/{project}/_apis/git/repositories/{repositoryId}/pullrequests"
    primary_keys = ["pullRequestId"]
    replication_key = "creationDate"
    records_jsonpath = "$.value[*]"
    parent_stream_type = RepositoriesStream

    schema = th.PropertiesList(
        th.Property("pullRequestId", th.IntegerType, description="Pull request ID"),
        th.Property("status", th.StringType, description="Pull request status"),
        th.Property("creationDate", th.DateTimeType, description="Creation date"),
        th.Property("title", th.StringType, description="Pull request title"),
        th.Property("description", th.StringType, description="Pull request description"),
        th.Property("sourceRefName", th.StringType, description="Source branch"),
        th.Property("targetRefName", th.StringType, description="Target branch"),
        th.Property("mergeStatus", th.StringType, description="Merge status"),
        th.Property("mergeId", th.StringType, description="Merge ID"),
        th.Property(
            "lastMergeSourceCommit",
            th.ObjectType(
                th.Property("commitId", th.StringType),
                th.Property("url", th.StringType),
            ),
            description="Last merge source commit",
        ),
        th.Property(
            "lastMergeTargetCommit",
            th.ObjectType(
                th.Property("commitId", th.StringType),
                th.Property("url", th.StringType),
            ),
            description="Last merge target commit",
        ),
        th.Property(
            "lastMergeCommit",
            th.ObjectType(
                th.Property("commitId", th.StringType),
                th.Property("url", th.StringType),
            ),
            description="Last merge commit",
        ),
        th.Property(
            "reviewers",
            th.ArrayType(
                th.ObjectType(
                    th.Property("reviewerUrl", th.StringType),
                    th.Property("vote", th.IntegerType),
                    th.Property("id", th.StringType),
                    th.Property("displayName", th.StringType),
                    th.Property("uniqueName", th.StringType),
                    th.Property("url", th.StringType),
                    th.Property("imageUrl", th.StringType),
                    th.Property("isContainer", th.BooleanType),
                )
            ),
            description="Reviewers",
        ),
        th.Property("url", th.StringType, description="Pull request URL"),
        th.Property("supportsIterations", th.BooleanType, description="Supports iterations"),
        th.Property(
            "repository",
            th.ObjectType(
                th.Property("id", th.StringType),
                th.Property("name", th.StringType),
                th.Property("url", th.StringType),
                th.Property(
                    "project",
                    th.ObjectType(
                        th.Property("id", th.StringType),
                        th.Property("name", th.StringType),
                    ),
                ),
            ),
            description="Repository information",
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

        # Add status filter to get all PRs (active, completed, abandoned)
        params["searchCriteria.status"] = "all"

        # Add date filter for incremental sync
        starting_timestamp = self.get_starting_timestamp(context)
        if starting_timestamp:
            params["searchCriteria.fromDate"] = starting_timestamp

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
            msg = "Context is required for pull requests stream"
            raise ValueError(msg)

        project_name = context["project"]["name"]
        repository_id = context["id"]
        return (
            f"{self.get_base_url()}/{project_name}/_apis/git/repositories/"
            f"{repository_id}/pullrequests"
        )

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
