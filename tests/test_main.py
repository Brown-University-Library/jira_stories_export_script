import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import main


class TestMain(unittest.TestCase):
    def test_load_config_reads_and_normalizes_env(self) -> None:
        """
        Checks that config loads from environment and normalizes values.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'out.csv'
            with patch.dict(
                os.environ,
                {
                    'JIRA_BASE_URL': 'https://example.atlassian.net/',
                    'JIRA_EMAIL': 'user@example.com',
                    'JIRA_API_TOKEN': 'token123',
                    'JIRA_BOARD_ID': '42',
                    'JIRA_OUT_CSV_PATH': str(csv_path),
                },
                clear=True,
            ):
                cfg = main.load_config()

        self.assertEqual(cfg.base_url, 'https://example.atlassian.net')
        self.assertEqual(cfg.email, 'user@example.com')
        self.assertEqual(cfg.api_token, 'token123')
        self.assertEqual(cfg.board_id, 42)
        self.assertEqual(cfg.out_csv_path, csv_path.expanduser().resolve())

    def test_get_active_sprint_id_requires_exactly_one_active_sprint(self) -> None:
        """
        Checks that active sprint lookup errors when Jira returns zero or many active sprints.
        """
        cfg = main.JiraConfig(
            base_url='https://example.atlassian.net',
            email='user@example.com',
            api_token='token123',
            board_id=123,
            out_csv_path=Path('out.csv'),
        )

        client: Mock = Mock()
        with patch.object(main, 'jira_get', return_value={'values': []}):
            with self.assertRaises(RuntimeError) as ctx:
                main.get_active_sprint_id(client, cfg)

        self.assertIn('Expected exactly one active sprint', str(ctx.exception))

    def test_fetch_sprint_issues_pages_until_complete(self) -> None:
        """
        Checks that sprint issue fetching continues paging until all issues are collected.
        """
        cfg = main.JiraConfig(
            base_url='https://example.atlassian.net',
            email='user@example.com',
            api_token='token123',
            board_id=123,
            out_csv_path=Path('out.csv'),
        )

        client: Mock = Mock()

        responses = [
            {'issues': [{'id': 1}, {'id': 2}], 'total': 3},
            {'issues': [{'id': 3}], 'total': 3},
        ]

        def fake_jira_get(_client: Mock, _url: str, params: dict[str, str | int] | None) -> dict:
            start_at = int((params or {}).get('startAt', 0))
            if start_at == 0:
                return responses[0]
            return responses[1]

        with patch.object(main, 'jira_get', side_effect=fake_jira_get):
            issues = main.fetch_sprint_issues(client, cfg, sprint_id=999)

        self.assertEqual([i['id'] for i in issues], [1, 2, 3])

    def test_write_csv_emits_expected_columns(self) -> None:
        """
        Checks that CSV export writes headers and issue rows with safe field extraction.
        """
        issues = [
            {
                'key': 'ABC-123',
                'fields': {
                    'summary': 'Fix thing',
                    'status': {'name': 'In Progress'},
                    'assignee': {'displayName': 'A. User'},
                    'reporter': {'displayName': 'R. User'},
                    'issuetype': {'name': 'Story'},
                    'priority': {'name': 'Medium'},
                    'customfield_10016': 5,
                },
            },
            {
                'key': 'ABC-124',
                'fields': {
                    'summary': 'No assignee yet',
                    'status': {'name': 'To Do'},
                    'assignee': None,
                },
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / 'export.csv'
            main.write_csv(out_path, issues)

            with out_path.open('r', newline='', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['key'], 'ABC-123')
        self.assertEqual(rows[0]['assignee'], 'A. User')
        self.assertEqual(rows[0]['story_points'], '5')
        self.assertEqual(rows[1]['key'], 'ABC-124')
        self.assertEqual(rows[1]['assignee'], '')
