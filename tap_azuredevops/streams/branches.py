"""Branches stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.repositories import RepositoriesStream


class BranchesStream(AzureDevOpsStream):
    """Branches stream."""

    name = "branches"
    path = "/{project}/_apis/git/repositories/{repositoryId}/refs"
    primary_keys = ["name"]
    replication_key = None
    records_jsonpath = "$.value[*]"
    parent_stream_type = RepositoriesStream

    schema = th.PropertiesList(
        th.Property("name", th.StringType, description="Branch name"),
        th.Property("objectId", th.StringType, description="Object ID"),
        th.Property(
            "creator",
            th.ObjectType(
                th.Property("displayName", th.StringType),
                th.Property("url", th.StringType),
                th.Property("id", th.StringType),
                th.Property("uniqueName", th.StringType),
                th.Property("imageUrl", th.StringType),
                th.Property("descriptor", th.StringType),
            ),
            description="Branch creator",
        ),
        th.Property("url", th.StringType, description="Branch URL"),
        th.Property("peeledObjectId", th.StringType, description="Peeled object ID"),
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

        # Filter to only heads (branches, not tags)
        params["filter"] = "heads/"

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
            msg = "Context is required for branches stream"
            raise ValueError(msg)

        project_name = context["project"]["name"]
        repository_id = context["id"]
        return f"{self.get_base_url()}/{project_name}/_apis/git/repositories/{repository_id}/refs"
