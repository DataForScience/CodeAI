from typing import Any, Dict, List
import requests

class GitHubAPIClient:
    """Small wrapper around GitHub's REST API.

    The client authenticates using a personal access token (PAT) passed in via
    the `Authorization: token ...` header.
    """

    def __init__(self, token: str) -> None:
        """Create a new GitHub API client.

        Args:
            token: GitHub personal access token.
        """
        self.token = token

    def get_user(self) -> Dict[str, Any]:
        """Fetch the authenticated user's profile.

        Returns:
            JSON-decoded user object as returned by `GET /user`.
        """
        response = requests.get("https://api.github.com/user", headers={"Authorization": f"token {self.token}"})
        return response.json()

    def get_repositories(self) -> List[Dict[str, Any]]:
        """Fetch repositories visible to the authenticated GitHub user.

        This calls the GitHub REST API endpoint `GET /user/repos` using the
        instance token.

        Returns:
            A JSON-decoded list where each element is a repository object as
            defined by the GitHub API.

        Raises:
            TimeoutError: If the request exceeds the configured timeout.
            RuntimeError: If the request fails for network/HTTP reasons.
            ValueError: If the response body is not valid JSON or is not a
                list.
        """
        try:
            response = requests.get(
                "https://api.github.com/user/repos",
                headers={"Authorization": f"token {self.token}"},
                timeout=10,
            )
            response.raise_for_status()

            try:
                data = response.json()
            except ValueError as e:
                raise ValueError("GitHub API returned invalid JSON for repositories") from e

            if not isinstance(data, list):
                raise ValueError(f"Expected a list of repositories, got {type(data).__name__}")

            return data
        except requests.Timeout as e:
            raise TimeoutError("Timed out while fetching repositories from GitHub") from e
        except requests.RequestException as e:
            raise RuntimeError("Failed to fetch repositories from GitHub") from e

    def get_repository(self, repo_name: str) -> Dict[str, Any]:
        """Fetch a single repository by its full name.

        Args:
            repo_name: Repository full name in the form `owner/repo`.

        Returns:
            JSON-decoded repository object as returned by `GET /repos/{repo}`.
        """
        response = requests.get(f"https://api.github.com/repos/{repo_name}", headers={"Authorization": f"token {self.token}"})
        return response.json()

    def get_commits(self, repo_name: str) -> List[Dict[str, Any]]:
        """List commits for a repository.

        Args:
            repo_name: Repository full name in the form `owner/repo`.

        Returns:
            JSON-decoded list of commit objects as returned by
            `GET /repos/{repo}/commits`.
        """
        response = requests.get(f"https://api.github.com/repos/{repo_name}/commits", headers={"Authorization": f"token {self.token}"})
        return response.json()
    
    def get_commit(self, repo_name: str, commit_sha: str) -> Dict[str, Any]:
        """Fetch a single commit.

        Args:
            repo_name: Repository full name in the form `owner/repo`.
            commit_sha: Commit SHA.

        Returns:
            JSON-decoded commit object as returned by
            `GET /repos/{repo}/commits/{sha}`.
        """
        response = requests.get(f"https://api.github.com/repos/{repo_name}/commits/{commit_sha}", headers={"Authorization": f"token {self.token}"})
        return response.json()