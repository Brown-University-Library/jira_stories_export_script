from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    email: str
    api_token: str
    board_id: int
    out_csv_path: Path


def _get_env(name: str) -> str:
    """
    Returns an environment variable value, raising a helpful error when missing.
    """
    value: str | None = os.getenv(name)
    if value is None or value.strip() == '':
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value.strip()


def load_config() -> JiraConfig:
    """
    Loads Jira configuration from environment variables.
    """
    os_base_url: str = _get_env('JIRA_BASE_URL').rstrip('/')
    os_email: str = _get_env('JIRA_EMAIL')
    os_api_token: str = _get_env('JIRA_API_TOKEN')
    os_board_id: int = int(_get_env('JIRA_BOARD_ID'))
    os_out_csv_path: Path = Path(_get_env('JIRA_OUT_CSV_PATH')).expanduser().resolve()

    return JiraConfig(
        base_url=os_base_url,
        email=os_email,
        api_token=os_api_token,
        board_id=os_board_id,
        out_csv_path=os_out_csv_path,
    )
