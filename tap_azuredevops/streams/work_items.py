"""Work items stream."""

from __future__ import annotations

import singer_sdk.typing as th
from singer_sdk.pagination import JSONPathPaginator

from tap_azuredevops.client import AzureDevOpsStream
from tap_azuredevops.streams.projects import ProjectsStream


class WorkItemsStream(AzureDevOpsStream):
    """Work items stream."""

    name = "work_items"
    path = "/{project_name}/_apis/wit/wiql"
    primary_keys = ["id"]
    replication_key = "fields/System.ChangedDate"
    records_jsonpath = "$.workItems[*]"
    parent_stream_type = ProjectsStream

    schema = th.PropertiesList(
        th.Property("id", th.IntegerType, description="Work item ID"),
        th.Property("url", th.StringType, description="Work item URL"),
        th.Property(
            "fields",
            th.ObjectType(
                th.Property("System.Id", th.IntegerType),
                th.Property("System.WorkItemType", th.StringType),
                th.Property("System.Title", th.StringType),
                th.Property("System.State", th.StringType),
                th.Property(
                    "System.AssignedTo",
                    th.ObjectType(
                        th.Property("displayName", th.StringType),
                        th.Property("uniqueName", th.StringType),
                        th.Property("id", th.StringType),
                    ),
                ),
                th.Property("System.CreatedDate", th.DateTimeType),
                th.Property("System.ChangedDate", th.DateTimeType),
                th.Property("System.Description", th.StringType),
                th.Property("System.AreaPath", th.StringType),
                th.Property("System.IterationPath", th.StringType),
                th.Property("System.TeamProject", th.StringType),
            ),
            description="Work item fields",
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
            msg = "Context is required for work items stream"
            raise ValueError(msg)

        project_name = context["name"]
        return f"{self.get_base_url()}/{project_name}/_apis/wit/workitems"

    def prepare_request_payload(
        self,
        context: dict | None,
        next_page_token: dict | None,
    ) -> dict | None:
        """Prepare request payload for WIQL query.

        Args:
            context: Stream context.
            next_page_token: Token for next page of results.

        Returns:
            Request payload dictionary.
        """
        # Build WIQL query for incremental sync
        starting_timestamp = self.get_starting_timestamp(context)

        if starting_timestamp:
            # Format timestamp for WIQL (ISO 8601)
            wiql_query = (
                f"SELECT [System.Id] FROM WorkItems "
                f"WHERE [System.ChangedDate] >= '{starting_timestamp}' "
                f"ORDER BY [System.ChangedDate]"
            )
        else:
            wiql_query = "SELECT [System.Id] FROM WorkItems ORDER BY [System.ChangedDate]"

        return {
            "query": wiql_query,
        }

    def request_records(self, context: dict | None) -> None:
        """Request work items using WIQL query then fetch details.

        Args:
            context: Stream context.
        """
        project_name = context["name"] if context else None
        if not project_name:
            msg = "Context is required for work items stream"
            raise ValueError(msg)

        # Step 1: Execute WIQL query to get work item IDs
        wiql_url = f"{self.get_base_url()}/{project_name}/_apis/wit/wiql"
        params = self.get_url_params(context, None)

        # Get WIQL query payload
        payload = self.prepare_request_payload(context, None)

        # Execute WIQL query
        response = self._request(
            method="POST",
            url=wiql_url,
            params=params,
            json=payload,
        )

        work_items_response = response.json()
        work_item_refs = work_items_response.get("workItems", [])

        if not work_item_refs:
            return

        # Step 2: Fetch work item details in batches
        work_item_ids = [str(wi["id"]) for wi in work_item_refs]

        # Azure DevOps allows up to 200 work items per batch
        batch_size = 200
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i : i + batch_size]
            ids_param = ",".join(batch_ids)

            # Fetch work item details
            work_items_url = f"{self.get_base_url()}/{project_name}/_apis/wit/workitems"
            params = {
                **self.get_url_params(context, None),
                "ids": ids_param,
                "$expand": "all",
            }

            response = self._request(
                method="GET",
                url=work_items_url,
                params=params,
            )

            work_items_data = response.json()
            work_items = work_items_data.get("value", [])

            for work_item in work_items:
                # Flatten fields for replication key
                if "fields" in work_item and "System.ChangedDate" in work_item["fields"]:
                    work_item["fields/System.ChangedDate"] = work_item["fields"][
                        "System.ChangedDate"
                    ]

                yield work_item

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
