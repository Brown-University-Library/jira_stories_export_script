import json
import os
import unittest
from unittest.mock import MagicMock, patch

from lib.config import load_gsheet_config
from lib.export_csv import issues_to_rows
from lib.gsheet_client import get_gspread_client, update_spreadsheet


class TestGSheetConfig(unittest.TestCase):
    def test_load_gsheet_config_reads_and_validates_env_vars(self) -> None:
        """
        Checks load_gsheet_config reads and validates env vars.
        """
        creds: dict = {
            'type': 'service_account',
            'project_id': 'test-project',
            'private_key_id': 'key123',
            'private_key': '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n',
            'client_email': 'test@test-project.iam.gserviceaccount.com',
            'client_id': '123456789',
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
        with patch.dict(
            os.environ,
            {
                'GSHEET_CREDENTIALS_JSON': json.dumps(creds),
                'GSHEET_SPREADSHEET_ID': 'test-spreadsheet-id-abc123',
            },
            clear=True,
        ):
            cfg = load_gsheet_config()

        self.assertEqual(cfg.credentials, creds)
        self.assertEqual(cfg.spreadsheet_id, 'test-spreadsheet-id-abc123')

    def test_load_gsheet_config_raises_on_invalid_json(self) -> None:
        """
        Checks load_gsheet_config raises error on invalid JSON.
        """
        with patch.dict(
            os.environ,
            {
                'GSHEET_CREDENTIALS_JSON': 'not valid json',
                'GSHEET_SPREADSHEET_ID': 'test-spreadsheet-id-xyz789',
            },
            clear=True,
        ):
            with self.assertRaises(RuntimeError) as ctx:
                load_gsheet_config()

        self.assertIn('Invalid JSON', str(ctx.exception))


class TestIssuesToRows(unittest.TestCase):
    def test_issues_to_rows_includes_header_and_stringifies_fields(self) -> None:
        """
        Checks issues_to_rows includes header and stringifies fields.
        """
        issues: list[dict] = [
            {
                'key': 'PROJ-123',
                'fields': {
                    'summary': 'Test issue',
                    'status': {'name': 'In Progress'},
                    'assignee': {'displayName': 'Alice'},
                    'reporter': {'displayName': 'Bob'},
                    'issuetype': {'name': 'Story'},
                    'priority': {'name': 'High'},
                    'customfield_10016': 5,
                },
            },
            {
                'key': 'PROJ-124',
                'fields': {
                    'summary': 'Another issue',
                    'status': {'name': 'Done'},
                    'assignee': None,
                    'reporter': {'displayName': 'Charlie'},
                    'issuetype': {'name': 'Bug'},
                    'priority': {'name': 'Low'},
                    'customfield_10016': None,
                },
            },
        ]

        rows: list[list[str]] = issues_to_rows(issues)

        self.assertEqual(len(rows), 3)
        self.assertEqual(
            rows[0],
            ['key', 'summary', 'status', 'assignee', 'reporter', 'issuetype', 'priority', 'story_points'],
        )
        self.assertEqual(rows[1], ['PROJ-123', 'Test issue', 'In Progress', 'Alice', 'Bob', 'Story', 'High', '5'])
        self.assertEqual(rows[2], ['PROJ-124', 'Another issue', 'Done', '', 'Charlie', 'Bug', 'Low', ''])

    def test_issues_to_rows_handles_empty_list(self) -> None:
        """
        Checks issues_to_rows handles empty issue list.
        """
        rows: list[list[str]] = issues_to_rows([])

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0],
            ['key', 'summary', 'status', 'assignee', 'reporter', 'issuetype', 'priority', 'story_points'],
        )


class TestGSpreadClient(unittest.TestCase):
    @patch('lib.gsheet_client.gspread.authorize')
    @patch('lib.gsheet_client.Credentials.from_service_account_info')
    def test_get_gspread_client_creates_authenticated_client(
        self, mock_creds_from_info: MagicMock, mock_authorize: MagicMock
    ) -> None:
        """
        Checks get_gspread_client creates authenticated client with correct scope.
        """
        from lib.config import GSheetConfig

        mock_credentials = MagicMock()
        mock_creds_from_info.return_value = mock_credentials
        mock_client = MagicMock()
        mock_authorize.return_value = mock_client

        cfg = GSheetConfig(credentials={'test': 'creds'}, spreadsheet_id='test-id')
        client = get_gspread_client(cfg)

        mock_creds_from_info.assert_called_once_with(
            {'test': 'creds'}, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        mock_authorize.assert_called_once_with(mock_credentials)
        self.assertEqual(client, mock_client)

    @patch('lib.gsheet_client.gspread.Client')
    def test_update_spreadsheet_clears_then_updates_from_a1(self, mock_client_class: MagicMock) -> None:
        """
        Checks update_spreadsheet clears then updates from A1.
        """
        mock_client = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_worksheet = MagicMock()

        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheets.return_value = [mock_worksheet]

        rows: list[list[str]] = [['header1', 'header2'], ['val1', 'val2']]

        update_spreadsheet(mock_client, 'test-spreadsheet-id', rows)

        mock_client.open_by_key.assert_called_once_with('test-spreadsheet-id')
        mock_spreadsheet.worksheets.assert_called_once()
        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once_with(rows, 'A1')
