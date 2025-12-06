"""Azure DevOps streams."""

from tap_azuredevops.streams.branches import BranchesStream
from tap_azuredevops.streams.builds import BuildsStream
from tap_azuredevops.streams.commits import CommitsStream
from tap_azuredevops.streams.pipelines import PipelinesStream
from tap_azuredevops.streams.projects import ProjectsStream
from tap_azuredevops.streams.pull_requests import PullRequestsStream
from tap_azuredevops.streams.releases import ReleasesStream
from tap_azuredevops.streams.repositories import RepositoriesStream
from tap_azuredevops.streams.tags import TagsStream
from tap_azuredevops.streams.work_items import WorkItemsStream

__all__ = [
    "ProjectsStream",
    "RepositoriesStream",
    "PullRequestsStream",
    "CommitsStream",
    "BranchesStream",
    "TagsStream",
    "WorkItemsStream",
    "BuildsStream",
    "PipelinesStream",
    "ReleasesStream",
]
