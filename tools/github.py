import os
import requests
from typing import Dict, Any,List
from dotenv import load_dotenv
from tools.base import BaseTool
from engine.types import ExecutionRequest

load_dotenv()

class GitHubTool(BaseTool):
    """Fetches repository stats from GitHub API."""

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com/repos"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    @property
    def name(self) -> str:
        return "github"

    @property
    def description(self) -> str:
        return "Fetches GitHub repo stats: stars, language, license, forks, open issues"

    @property
    def capabilities(self) -> List[str]:
        """Currently supports repository metadata lookup."""
        return ["repository_metadata"]

    @property
    def required_args(self)-> List[str]:
        return ["repo"]

    def _fetch_from_api(self, repo: str) -> Dict[str, Any]:
        """
        Fetch repository data from GitHub API.

        Args:
            repo: Repository in format "owner/repo" (e.g., "karpathy/nanoGPT")

        Returns:
            Raw JSON from GitHub API

        Raises:
            ValueError: Repo not found
            ConnectionError: Rate limited or API down
        """
        #send as a string
        url = f"{self.base_url}/{repo}"

        response = requests.get(url, headers=self.headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError(f"Repository '{repo}' not found")
        elif response.status_code == 403:
            # Check if rate limited
            if "rate limit" in response.text.lower():
                raise ConnectionError(
                    "GitHub API rate limit exceeded. "
                    "Add GITHUB_TOKEN to .env for 5,000 requests/hour "
                    "or wait for reset."
                )
            else:
                raise ValueError(f"Access forbidden for '{repo}'")
        elif response.status_code == 503:
            raise ConnectionError("GitHub service unavailable. Try again later.")
        else:
            raise ConnectionError(
                f"GitHub API returned status {response.status_code}: {response.text}"
            )

    def _normalize_response(self, raw_data: Dict[str, Any], repo: str) -> Dict[str, Any]:
        """
        Transform GitHub's verbose response into clean format.

        Args:
            raw_data: Raw JSON from GitHub
            repo: Original repo string

        Returns:
            Normalized dict with key repo stats
        """
        return {
            "name": raw_data.get("name"),
            "full_name": raw_data.get("full_name"),
            "description": raw_data.get("description"),
            "stars": raw_data.get("stargazers_count"),
            "forks": raw_data.get("forks_count"),
            "language": raw_data.get("language"),
            "license": raw_data.get("license", {}).get("spdx_id") if raw_data.get("license") else "No license",
            "open_issues": raw_data.get("open_issues_count"),
            "topics": raw_data.get("topics", []),
            "created_at": raw_data.get("created_at"),
            "updated_at": raw_data.get("updated_at"),
            "url": raw_data.get("html_url")
        }

    def execute(self, request: ExecutionRequest, trace: list) -> Dict[str, Any]:
        """
        Execute GitHub repo lookup through Aegis.

        Args:
            request: ExecutionRequest with repo in arguments
            trace: Trace list for observability

        Returns:
            Normalized repo data dict
        """
        repo = request.arguments.get("repo")
        if not repo:
            raise ValueError("'repo' argument is required (format: 'owner/repo')")

        # Validate format
        if "/" not in repo or len(repo.split("/")) != 2:
            raise ValueError(
                f"Invalid repo format: '{repo}'. Expected 'owner/repo' (e.g., 'karpathy/nanoGPT')"
            )

        # Trace: Starting API call
        trace.append({
            "component": "github_tool",
            "event": "api_call_started",
            "repo": repo
        })

        try:
            # Fetch from GitHub API
            raw_data = self._fetch_from_api(repo)

            # Trace: API responded
            trace.append({
                "component": "github_tool",
                "event": "api_response_received",
                "repo": repo,
                "status_code": 200
            })

            # Normalize
            normalized = self._normalize_response(raw_data, repo)

            # Trace: Normalization done
            trace.append({
                "component": "github_tool",
                "event": "response_normalized",
                "repo": repo,
                "stars": normalized["stars"],
                "language": normalized["language"]
            })

            return normalized

        except ValueError as e:
            # Repo not found or bad request — fatal
            trace.append({
                "component": "github_tool",
                "event": "api_error_fatal",
                "repo": repo,
                "error": str(e)
            })
            raise

        except Exception as e:
            # Rate limits, network errors — retryable
            trace.append({
                "component": "github_tool",
                "event": "api_error_operational",
                "repo": repo,
                "error": str(e)
            })
            raise

"""Not for now, but worth keeping on your roadmap:

Handle GitHub rate limits (403 with rate-limit headers).
Cache repeated repository lookups to reduce API calls.
Support authenticated requests via personal access tokens.
Expose additional metadata like last updated time or default branch if needed.
Save raw API responses optionally for debugging while still returning normalized results."""