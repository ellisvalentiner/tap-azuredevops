"""Azure DevOps REST API client."""

from __future__ import annotations

from singer_sdk.authenticators import BasicAuthenticator
from singer_sdk.streams import RESTStream


class AzureDevOpsAuthenticator(BasicAuthenticator):
    """Azure DevOps Basic Auth authenticator using PAT."""

    def __init__(self, personal_access_token: str) -> None:
        """Initialize authenticator.

        Args:
            personal_access_token: Personal Access Token for authentication.
        """
        super().__init__(
            username="",  # Azure DevOps uses empty username with PAT
            password=personal_access_token,
        )


class AzureDevOpsStream(RESTStream):
    """Base stream class for Azure DevOps REST API streams."""

    url_base = "https://dev.azure.com"
    api_version = "7.1"

    @property
    def authenticator(self) -> AzureDevOpsAuthenticator:
        """Return authenticator instance."""
        return AzureDevOpsAuthenticator(
            personal_access_token=self.config["personal_access_token"]
        )

    @property
    def organization(self) -> str:
        """Return organization name from config."""
        return self.config["organization"]

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
        params: dict = {
            "api-version": self.api_version,
        }

        # Handle pagination
        if next_page_token:
            params.update(next_page_token)

        return params

    def get_base_url(self) -> str:
        """Return base URL for the organization.

        Returns:
            Base URL string.
        """
        return f"{self.url_base}/{self.organization}"
