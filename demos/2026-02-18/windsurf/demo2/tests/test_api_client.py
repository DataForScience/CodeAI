"""Unit tests for `demo2.api_client`.

All tests mock `requests.get` to avoid real HTTP requests.
"""

import pytest
import requests

from demo2.api_client import GitHubAPIClient


class DummyResponse:
    """Minimal stand-in for `requests.Response` used by tests."""

    def __init__(self, json_data=None, *, status_code=200, json_raises=None, raise_for_status_raises=None):
        self._json_data = json_data
        self.status_code = status_code
        self._json_raises = json_raises
        self._raise_for_status_raises = raise_for_status_raises

    def raise_for_status(self):
        if self._raise_for_status_raises is not None:
            raise self._raise_for_status_raises

    def json(self):
        if self._json_raises is not None:
            raise self._json_raises
        return self._json_data


@pytest.fixture
def client():
    """Return a `GitHubAPIClient` configured with a deterministic test token."""
    return GitHubAPIClient(token="test-token")


def test_get_user_calls_correct_endpoint_and_header(monkeypatch, client):
    """`get_user` should call the expected endpoint and include auth header."""
    captured = {}

    def fake_get(url, headers=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        return DummyResponse({"login": "octocat"})

    monkeypatch.setattr(requests, "get", fake_get)

    data = client.get_user()
    assert data == {"login": "octocat"}
    assert captured["url"] == "https://api.github.com/user"
    assert captured["headers"]["Authorization"] == "token test-token"


def test_get_repository_calls_correct_endpoint(monkeypatch, client):
    """`get_repository` should call the expected endpoint and include auth header."""
    captured = {}

    def fake_get(url, headers=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        return DummyResponse({"full_name": "owner/repo"})

    monkeypatch.setattr(requests, "get", fake_get)

    data = client.get_repository("owner/repo")
    assert data["full_name"] == "owner/repo"
    assert captured["url"] == "https://api.github.com/repos/owner/repo"
    assert captured["headers"]["Authorization"] == "token test-token"


def test_get_commits_calls_correct_endpoint(monkeypatch, client):
    """`get_commits` should call the expected endpoint and include auth header."""
    captured = {}

    def fake_get(url, headers=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        return DummyResponse([{"sha": "abc"}])

    monkeypatch.setattr(requests, "get", fake_get)

    data = client.get_commits("owner/repo")
    assert data == [{"sha": "abc"}]
    assert captured["url"] == "https://api.github.com/repos/owner/repo/commits"
    assert captured["headers"]["Authorization"] == "token test-token"


def test_get_commit_calls_correct_endpoint(monkeypatch, client):
    """`get_commit` should call the expected endpoint and include auth header."""
    captured = {}

    def fake_get(url, headers=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        return DummyResponse({"sha": "deadbeef"})

    monkeypatch.setattr(requests, "get", fake_get)

    data = client.get_commit("owner/repo", "deadbeef")
    assert data["sha"] == "deadbeef"
    assert captured["url"] == "https://api.github.com/repos/owner/repo/commits/deadbeef"
    assert captured["headers"]["Authorization"] == "token test-token"


def test_get_repositories_success_returns_list(monkeypatch, client):
    """`get_repositories` should return list data and set a timeout."""
    captured = {}

    def fake_get(url, headers=None, timeout=None, **kwargs):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return DummyResponse(
            [
                {"id": 1, "full_name": "owner/repo1"},
                {"id": 2, "full_name": "owner/repo2"},
            ]
        )

    monkeypatch.setattr(requests, "get", fake_get)

    data = client.get_repositories()
    assert isinstance(data, list)
    assert data[0]["full_name"] == "owner/repo1"
    assert captured["url"] == "https://api.github.com/user/repos"
    assert captured["headers"]["Authorization"] == "token test-token"
    assert captured["timeout"] == 10


def test_get_repositories_timeout_raises_timeout_error(monkeypatch, client):
    """`get_repositories` should translate request timeouts into `TimeoutError`."""

    def fake_get(*args, **kwargs):
        raise requests.Timeout("boom")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(TimeoutError):
        client.get_repositories()


def test_get_repositories_http_error_raises_runtime_error(monkeypatch, client):
    """`get_repositories` should translate HTTP errors into `RuntimeError`."""
    http_error = requests.HTTPError("bad")

    def fake_get(*args, **kwargs):
        return DummyResponse([], raise_for_status_raises=http_error)

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(RuntimeError):
        client.get_repositories()


def test_get_repositories_invalid_json_raises_value_error(monkeypatch, client):
    """`get_repositories` should raise `ValueError` when JSON decoding fails."""

    def fake_get(*args, **kwargs):
        return DummyResponse(None, json_raises=ValueError("nope"))

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(ValueError):
        client.get_repositories()


def test_get_repositories_non_list_json_raises_value_error(monkeypatch, client):
    """`get_repositories` should raise `ValueError` when response isn't a list."""

    def fake_get(*args, **kwargs):
        return DummyResponse({"message": "not a list"})

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(ValueError):
        client.get_repositories()
