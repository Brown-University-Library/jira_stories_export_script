from __future__ import annotations

import csv
from pathlib import Path


def safe_field(fields: dict, path: list[str]) -> str:
    """
    Safely extracts a nested field and returns a string.
    """
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


def issues_to_rows(issues: list[dict]) -> list[list[str]]:
    """
    Converts Jira issues to a 2D list of strings for spreadsheet update.
    """
    ## header row
    header: list[str] = [
        'key',
        'summary',
        'status',
        'assignee',
        'reporter',
        'issuetype',
        'priority',
        'story_points',
    ]
    rows: list[list[str]] = [header]

    ## data rows
    for issue in issues:
        fields: dict = issue.get('fields', {})
        row: list[str] = [
            str(issue.get('key', '')),
            safe_field(fields, ['summary']),
            safe_field(fields, ['status', 'name']),
            safe_field(fields, ['assignee', 'displayName']),
            safe_field(fields, ['reporter', 'displayName']),
            safe_field(fields, ['issuetype', 'name']),
            safe_field(fields, ['priority', 'name']),
            safe_field(fields, ['customfield_10016']),
        ]
        rows.append(row)

    return rows


def write_csv(out_path: Path, issues: list[dict]) -> None:
    """
    Writes issues to a CSV file.
    """
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
                'story_points': safe_field(fields, ['customfield_10016']),
            }
            writer.writerow(row)
