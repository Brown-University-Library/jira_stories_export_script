import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.config import load_jira_config


class TestConfig(unittest.TestCase):
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
                cfg = load_jira_config()

        self.assertEqual(cfg.base_url, 'https://example.atlassian.net')
        self.assertEqual(cfg.email, 'user@example.com')
        self.assertEqual(cfg.api_token, 'token123')
        self.assertEqual(cfg.board_id, 42)
        self.assertEqual(cfg.out_csv_path, csv_path.expanduser().resolve())
