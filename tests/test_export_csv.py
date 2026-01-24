import csv
import tempfile
import unittest
from pathlib import Path

from lib.export_csv import write_csv


class TestExportCsv(unittest.TestCase):
    def test_write_csv_emits_expected_columns(self) -> None:
        """
        Checks that CSV export writes headers and issue rows with safe field extraction.
        """
        issues: list[dict] = [
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
            out_path: Path = Path(tmpdir) / 'export.csv'
            write_csv(out_path, issues)

            with out_path.open('r', newline='', encoding='utf-8') as f:
                rows: list[dict[str, str]] = list(csv.DictReader(f))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['key'], 'ABC-123')
        self.assertEqual(rows[0]['assignee'], 'A. User')
        self.assertEqual(rows[0]['story_points'], '5')
        self.assertEqual(rows[1]['key'], 'ABC-124')
        self.assertEqual(rows[1]['assignee'], '')
