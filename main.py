from __future__ import annotations

import base64
import csv
import os
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    email: str
    api_token: str
    board_id: int
    out_csv_path: Path


def _get_env(name: str) -> str:
    """Returns an environment variable value, raising a helpful error when missing."""
    value: str | None = os.getenv(name)
    if value is None or value.strip() == '':
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value.strip()


def load_config() -> JiraConfig:
    """Loads Jira configuration from environment variables."""
    os_base_url: str = _get_env('JIRA_BASE_URL').rstrip('/')
    os_email: str = _get_env('JIRA_EMAIL')
    os_api_token: str = _get_env('JIRA_API_TOKEN')
    os_board_id: int = int(_get_env('JIRA_BOARD_ID'))
    os_out_csv_path: Path = Path(_get_env('JIRA_OUT_CSV_PATH')).expanduser().resolve()  # expanduser() resolves `~` paths

    return JiraConfig(
        base_url=os_base_url,
        email=os_email,
        api_token=os_api_token,
        board_id=os_board_id,
        out_csv_path=os_out_csv_path,
    )


def build_auth_header(email: str, api_token: str) -> str:
    """Builds a Basic auth header value from email and API token."""
    raw: str = f'{email}:{api_token}'
    encoded: str = base64.b64encode(raw.encode('utf-8')).decode('ascii')
    return f'Basic {encoded}'


def jira_get(client: httpx.Client, url: str, params: dict[str, str | int] | None) -> dict:
    """Performs a GET request to Jira and returns parsed JSON."""
    response: httpx.Response = client.get(url, params=params)
    response.raise_for_status()
    data: dict = response.json()
    return data


def get_active_sprint_id(client: httpx.Client, cfg: JiraConfig) -> int:
    """Finds the active sprint id for the configured board."""
    url: str = f'{cfg.base_url}/rest/agile/1.0/board/{cfg.board_id}/sprint'
    data: dict = jira_get(client, url, params={'state': 'active'})

    values: list[dict] = data.get('values', [])
    if len(values) != 1:
        names: list[str] = [v.get('name', '<unnamed>') for v in values]
        raise RuntimeError(f'Expected exactly one active sprint for board {cfg.board_id}, got {len(values)}: {names}')

    sprint_id: int = int(values[0]['id'])
    return sprint_id


def fetch_sprint_issues(client: httpx.Client, cfg: JiraConfig, sprint_id: int) -> list[dict]:
    """Fetches all issues in a sprint, paging until complete."""
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


def safe_field(fields: dict, path: list[str]) -> str:
    """Safely extracts a nested field and returns a string."""
    value: object = fields
    for key in path:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            value = ''
            break
    if value is None:
        return ''
    return str(value)


def write_csv(out_path: Path, issues: list[dict]) -> None:
    """Writes issues to a CSV file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str] = [
        'key',
        'summary',
        'status',
        'assignee',
        'reporter',
        'issuetype',
        'priority',
        'story_points',
    ]

    with out_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for issue in issues:
            fields: dict = issue.get('fields', {})
            row: dict[str, str] = {
                'key': str(issue.get('key', '')),
                'summary': safe_field(fields, ['summary']),
                'status': safe_field(fields, ['status', 'name']),
                'assignee': safe_field(fields, ['assignee', 'displayName']),
                'reporter': safe_field(fields, ['reporter', 'displayName']),
                'issuetype': safe_field(fields, ['issuetype', 'name']),
                'priority': safe_field(fields, ['priority', 'name']),
                # Note: story points is instance-specific; set this to your field id if you want it.
                # Commonly it's "customfield_10016", but do not assume—inspect your instance.
                'story_points': safe_field(fields, ['customfield_10016']),
            }
            writer.writerow(row)


def main() -> None:
    load_dotenv()
    cfg: JiraConfig = load_config()
    headers: dict[str, str] = {
        'Authorization': build_auth_header(cfg.email, cfg.api_token),
        'Accept': 'application/json',
    }

    with httpx.Client(headers=headers, timeout=30.0) as client:
        sprint_id: int = get_active_sprint_id(client, cfg)
        issues: list[dict] = fetch_sprint_issues(client, cfg, sprint_id)
        write_csv(cfg.out_csv_path, issues)

    print(f'Wrote {len(issues)} issues to {cfg.out_csv_path}')


if __name__ == '__main__':
    main()
