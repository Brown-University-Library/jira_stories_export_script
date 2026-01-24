import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lib.config import JiraConfig
from lib.jira_client import fetch_sprint_issues, get_active_sprint_id


def make_test_config() -> JiraConfig:
    """
    Creates a test JiraConfig instance.
    """
    return JiraConfig(
        base_url='https://example.atlassian.net',
        email='user@example.com',
        api_token='token123',
        board_id=123,
        out_csv_path=Path('out.csv'),
    )


def fake_jira_get_for_paging(_client: Mock, _url: str, params: dict[str, str | int] | None) -> dict:
    """
    Simulates paginated Jira responses for testing fetch_sprint_issues.
    """
    responses: list[dict] = [
        {'issues': [{'id': 1}, {'id': 2}], 'total': 3},
        {'issues': [{'id': 3}], 'total': 3},
    ]
    start_at: int = int((params or {}).get('startAt', 0))
    if start_at == 0:
        return responses[0]
    return responses[1]


class TestJiraClient(unittest.TestCase):
    def test_get_active_sprint_id_requires_exactly_one_active_sprint(self) -> None:
        """
        Checks that active sprint lookup errors when Jira returns zero active sprints.
        """
        cfg: JiraConfig = make_test_config()
        client: Mock = Mock()

        with patch('lib.jira_client.jira_get', return_value={'values': []}):
            with self.assertRaises(RuntimeError) as ctx:
                get_active_sprint_id(client, cfg)

        self.assertIn('Expected exactly one active sprint', str(ctx.exception))

    def test_get_active_sprint_id_errors_on_multiple_active_sprints(self) -> None:
        """
        Checks that active sprint lookup errors when Jira returns multiple active sprints.
        """
        cfg: JiraConfig = make_test_config()
        client: Mock = Mock()
        multiple_sprints: dict = {
            'values': [
                {'id': 1, 'state': 'active'},
                {'id': 2, 'state': 'active'},
            ]
        }

        with patch('lib.jira_client.jira_get', return_value=multiple_sprints):
            with self.assertRaises(RuntimeError) as ctx:
                get_active_sprint_id(client, cfg)

        self.assertIn('Expected exactly one active sprint', str(ctx.exception))

    def test_fetch_sprint_issues_pages_until_complete(self) -> None:
        """
        Checks that sprint issue fetching continues paging until all issues are collected.
        """
        cfg: JiraConfig = make_test_config()
        client: Mock = Mock()

        with patch('lib.jira_client.jira_get', side_effect=fake_jira_get_for_paging):
            issues: list[dict] = fetch_sprint_issues(client, cfg, sprint_id=999)

        self.assertEqual([i['id'] for i in issues], [1, 2, 3])
