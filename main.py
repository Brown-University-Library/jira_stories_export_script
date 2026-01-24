import httpx
from dotenv import load_dotenv

from lib.config import GSheetConfig, JiraConfig, load_gsheet_config, load_jira_config
from lib.export_csv import issues_to_rows, write_csv
from lib.gsheet_client import get_gspread_client, update_spreadsheet
from lib.jira_client import build_auth_header, fetch_sprint_issues, get_active_sprint_id


def main() -> None:
    ## config -------------------------------------------------------
    load_dotenv()
    cfg: JiraConfig = load_jira_config()

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
    gsheet_cfg: GSheetConfig = load_gsheet_config()
    rows: list[list[str]] = issues_to_rows(issues)
    client = get_gspread_client(gsheet_cfg)
    update_spreadsheet(client, gsheet_cfg.spreadsheet_id, rows)

    print(f'Updated Google Spreadsheet with {len(issues)} issues')


if __name__ == '__main__':
    main()
