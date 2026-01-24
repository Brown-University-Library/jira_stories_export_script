from __future__ import annotations

import base64

import httpx

from lib.config import JiraConfig


def build_auth_header(email: str, api_token: str) -> str:
    """
    Builds a Basic auth header value from email and API token.
    """
    raw: str = f'{email}:{api_token}'
    encoded: str = base64.b64encode(raw.encode('utf-8')).decode('ascii')
    return f'Basic {encoded}'


def jira_get(client: httpx.Client, url: str, params: dict[str, str | int] | None) -> dict:
    """
    Performs a GET request to Jira and returns parsed JSON.
    """
    response: httpx.Response = client.get(url, params=params)
    response.raise_for_status()
    data: dict = response.json()
    return data


def get_active_sprint_id(client: httpx.Client, cfg: JiraConfig) -> int:
    """
    Finds the active sprint id for the configured board.
    """
    url: str = f'{cfg.base_url}/rest/agile/1.0/board/{cfg.board_id}/sprint'
    data: dict = jira_get(client, url, params={'state': 'active'})

    values: list[dict] = data.get('values', [])
    if len(values) != 1:
        names: list[str] = [v.get('name', '<unnamed>') for v in values]
        raise RuntimeError(f'Expected exactly one active sprint for board {cfg.board_id}, got {len(values)}: {names}')

    sprint_id: int = int(values[0]['id'])
    return sprint_id


def fetch_sprint_issues(client: httpx.Client, cfg: JiraConfig, sprint_id: int) -> list[dict]:
    """
    Fetches all issues in a sprint, paging until complete.
    """
    url: str = f'{cfg.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue'

    start_at: int = 0
    max_results: int = 100
    issues: list[dict] = []

    while True:
        data: dict = jira_get(
            client,
            url,
            params={'startAt': start_at, 'maxResults': max_results},
        )
        page_issues: list[dict] = data.get('issues', [])
        issues.extend(page_issues)

        total: int = int(data.get('total', len(issues)))
        start_at = start_at + len(page_issues)

        if start_at >= total or len(page_issues) == 0:
            break

    return issues
