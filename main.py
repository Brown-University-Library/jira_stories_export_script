from __future__ import annotations

import httpx
from dotenv import load_dotenv

from lib.config import JiraConfig, load_config
from lib.export_csv import write_csv
from lib.jira_client import build_auth_header, fetch_sprint_issues, get_active_sprint_id


def main() -> None:
    ## config -------------------------------------------------------
    load_dotenv()
    cfg: JiraConfig = load_config()

    ## export jira data ---------------------------------------------
    headers: dict[str, str] = {
        'Authorization': build_auth_header(cfg.email, cfg.api_token),
        'Accept': 'application/json',
    }

    with httpx.Client(headers=headers, timeout=30.0) as client:
        sprint_id: int = get_active_sprint_id(client, cfg)
        issues: list[dict] = fetch_sprint_issues(client, cfg, sprint_id)
        write_csv(cfg.out_csv_path, issues)

    print(f'Wrote {len(issues)} issues to {cfg.out_csv_path}')

    ## update google sheet ------------------------------------------
    ## TODO


if __name__ == '__main__':
    main()
