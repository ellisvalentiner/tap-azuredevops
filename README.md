# tap-azuredevops

A [Singer](https://www.singer.io/) tap for extracting data from Azure DevOps.

## Overview

This tap extracts data from Azure DevOps, including:

- **Projects**: Organization projects
- **Repositories**: Git repositories within projects
- **Pull Requests**: Pull requests for each repository
- **Commits**: Commits for each repository
- **Branches**: Branches for each repository
- **Tags**: Git tags for each repository
- **Work Items**: Work items (issues, tasks, bugs, etc.) for each project
- **Builds**: CI/CD build history for each project
- **Pipelines**: Pipeline definitions for each project
- **Releases**: Release and deployment history for each project

## Installation

**Note:** This tap is distributed via GitHub only and is not published to PyPI.

### For Local Development

Install using `uv`:

```bash
uv sync
```

### For Meltano

When using with Meltano, install directly from GitHub. See the [With Meltano](#with-meltano) section below for configuration examples.

## Configuration

Configuration can be provided via a JSON config file or environment variables (or a combination of both). Environment variables take precedence over config file values.

### Using a Config File

Copy the sample configuration file and update it with your credentials:

```bash
cp config-sample.json config.json
```

Then edit `config.json` with your Azure DevOps credentials:

```json
{
  "organization": "your-org-name",
  "personal_access_token": "your-pat-token"
}
```

### Configuration Options

**Required:**
- `organization`: Azure DevOps organization name
- `personal_access_token`: Personal Access Token for authentication

**Optional:**
- `projects`: Array of project names to filter (defaults to all projects)
- `start_date`: Start date for incremental replication (ISO 8601 format)

Example with all options:

```json
{
  "organization": "your-org-name",
  "personal_access_token": "your-pat-token",
  "projects": ["project1", "project2"],
  "start_date": "2024-01-01T00:00:00Z"
}
```

### Environment Variables

As an alternative to storing credentials in the JSON config file, you can use environment variables. This is especially useful for CI/CD pipelines and production deployments. Environment variables take precedence over config file values.

**Supported environment variables:**
- `AZURE_DEVOPS_ORGANIZATION`: Azure DevOps organization name
- `AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN`: Personal Access Token for authentication

**Example using environment variables:**

```bash
export AZURE_DEVOPS_ORGANIZATION="your-org-name"
export AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN="your-pat-token"

# Run tap with minimal config (or empty config)
uv run tap-azuredevops --config config.json --discover
```

You can also mix environment variables with config file values. For example, you might store the organization in the config file but use an environment variable for the token:

```bash
export AZURE_DEVOPS_PERSONAL_ACCESS_TOKEN="your-pat-token"
```

```json
{
  "organization": "your-org-name"
}
```

### Personal Access Token

To create a Personal Access Token:

1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Create a new token with appropriate scopes:
   - **Code (read)**: Required for repositories, commits, branches, tags
   - **Pull Requests (read)**: Required for pull requests
   - **Release (Read & Execute)**: Required for releases (optional - tap will skip releases if not available)
   - **Build (read)**: Required for builds
   - **Work Items (read)**: Required for work items

## Usage

### Discovery

Discover available streams and their schemas:

```bash
uv run tap-azuredevops --config config.json --discover
```

Or if installed globally:

```bash
tap-azuredevops --config config.json --discover
```

### Sync

Sync all streams:

```bash
uv run tap-azuredevops --config config.json
```

Sync specific streams:

```bash
uv run tap-azuredevops --config config.json --catalog catalog.json
```

### With Meltano

Add to your `meltano.yml`:

```yaml
plugins:
  extractors:
    - name: tap-azuredevops
      namespace: tap_azuredevops
      pip_url: git+https://github.com/ellisvalentiner/tap-azuredevops.git
      config:
        organization: ${AZURE_DEVOPS_ORGANIZATION}
        personal_access_token: ${AZURE_DEVOPS_PAT}
```

To install a specific version, use:

```yaml
pip_url: git+https://github.com/ellisvalentiner/tap-azuredevops.git@v0.1.1
```

To install from a specific branch:

```yaml
pip_url: git+https://github.com/ellisvalentiner/tap-azuredevops.git@main
```

Alternatively, you can install from a pre-built wheel (faster, no build step):

```yaml
pip_url: https://github.com/ellisvalentiner/tap-azuredevops/releases/download/v0.1.1/tap_azuredevops-0.1.1-py3-none-any.whl
```

**Note:** Pre-built wheels are available as artifacts on each [GitHub release](https://github.com/ellisvalentiner/tap-azuredevops/releases).

## Streams

### Projects

Extracts all projects in the organization.

- **Primary Key**: `id`
- **Endpoint**: `GET /_apis/projects`

### Repositories

Extracts all Git repositories for each project.

- **Primary Key**: `id`
- **Parent Stream**: `projects`
- **Endpoint**: `GET /{project}/_apis/git/repositories`

### Pull Requests

Extracts all pull requests for each repository.

- **Primary Key**: `pullRequestId`
- **Replication Key**: `creationDate` (supports incremental sync)
- **Parent Stream**: `repositories`
- **Endpoint**: `GET /{project}/_apis/git/repositories/{repoId}/pullrequests`

### Commits

Extracts all commits for each repository.

- **Primary Key**: `commitId`
- **Replication Key**: `author.date` (supports incremental sync)
- **Parent Stream**: `repositories`
- **Endpoint**: `GET /{project}/_apis/git/repositories/{repoId}/commits`

### Branches

Extracts all branches for each repository.

- **Primary Key**: `name`
- **Parent Stream**: `repositories`
- **Endpoint**: `GET /{project}/_apis/git/repositories/{repoId}/refs?filter=heads/`

### Tags

Extracts all Git tags for each repository.

- **Primary Key**: `name`
- **Parent Stream**: `repositories`
- **Endpoint**: `GET /{project}/_apis/git/repositories/{repoId}/refs?filter=tags/`

### Work Items

Extracts all work items (issues, tasks, bugs, user stories, etc.) for each project.

- **Primary Key**: `id`
- **Replication Key**: `fields/System.ChangedDate` (supports incremental sync)
- **Parent Stream**: `projects`
- **Endpoint**: `GET /{project}/_apis/wit/workitems`
- **Note**: Uses WIQL (Work Item Query Language) to query work items efficiently

### Builds

Extracts all CI/CD builds for each project.

- **Primary Key**: `id`
- **Replication Key**: `finishTime` (supports incremental sync)
- **Parent Stream**: `projects`
- **Endpoint**: `GET /{project}/_apis/build/builds`

### Pipelines

Extracts all pipeline definitions for each project.

- **Primary Key**: `id`
- **Parent Stream**: `projects`
- **Endpoint**: `GET /{project}/_apis/pipelines/pipelines`

### Releases

Extracts all releases and deployments for each project.

- **Primary Key**: `id`
- **Replication Key**: `createdOn` (supports incremental sync)
- **Parent Stream**: `projects`
- **Endpoint**: `GET /{project}/_apis/release/releases`
- **Note**: If your Personal Access Token doesn't have "Release (Read & Execute)" permissions, the tap will log a warning and skip releases for that project, but continue processing other streams. To enable releases, add the "Release (Read & Execute)" scope to your PAT.

## Development

### Setup

```bash
# Install dependencies
uv sync

# Install development dependencies
uv sync --extra dev
```

### Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=tap_azuredevops
```

### Formatting and Linting

```bash
# Format code
ruff format .

# Fix linting issues
ruff check --fix .

# Check linting
ruff check .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/tap-azuredevops.git`
3. Install dependencies: `uv sync --extra dev`
4. Create a branch for your changes: `git checkout -b feature/your-feature`
5. Make your changes and test them
6. Run linting: `ruff check . && ruff format .`
7. Run tests: `uv run pytest`
8. Submit a pull request

### Code Style

This project uses `ruff` for formatting and linting. Please ensure your code passes:

```bash
ruff format .
ruff check .
```

### Testing

Add tests for new features in the `tests/` directory. Run tests with:

```bash
uv run pytest
```

## Troubleshooting

### Authentication Errors

If you encounter authentication errors:
- Verify your Personal Access Token is valid and not expired
- Ensure the token has the required scopes (Code read, Pull Requests read)
- Check that your organization name is correct

### Rate Limiting

Azure DevOps has rate limits (typically 200 requests per minute). The tap includes automatic retry logic with exponential backoff. If you encounter rate limit errors:
- Reduce the number of projects being synced
- Use the `projects` config option to filter to specific projects
- Consider using incremental sync to reduce full table scans

### 404 Errors

If you see 404 errors:
- Verify the organization name is correct
- Ensure the projects exist in your organization
- Check that your PAT has access to the projects

## License

MIT License - see [LICENSE](LICENSE) file for details.

