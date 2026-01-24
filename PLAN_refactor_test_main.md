# PLAN: Refactor `tests/test_main.py`

## Before you start
- Review `jira_stories_export_script/AGENTS.md` for repo-specific coding and testing preferences (Python version, `uv` usage, unittest conventions, style rules).

## Context
`tests/test_main.py` originated when most logic lived in `main.py`. The production code is now split across `lib/` modules, but the tests still live in a single file named as if it targets `main`.

Notes that may be useful in a new work-session:
- This project targets Python 3.12 and uses `uv`.
- Run tests via: `uv run ./run_tests.py` (from the project root).
- Test framework is the standard library `unittest` (not pytest).
- Test discovery expects filenames starting with `test_` under `jira_stories_export_script/tests/`.

Current `lib/` layout:
- `lib/config.py`
- `lib/jira_client.py`
- `lib/export_csv.py`

Current `tests/test_main.py` coverage:
- `load_config()` / `JiraConfig` (from `lib.config`)
- `get_active_sprint_id()` (from `lib.jira_client`)
- `fetch_sprint_issues()` paging behavior (from `lib.jira_client`)
- `write_csv()` output columns / safe extraction (from `lib.export_csv`)

## Recommendation
Splitting tests by module is a good idea here.

Reasons:
- The current filename (`test_main.py`) no longer matches what’s being tested.
- The file already contains logically separate test groups by module.
- Future additions (e.g., more Jira endpoints, config validation, CSV variations) will be easier to locate and maintain when tests are grouped by production module.

This is a small repo, so the gain is mostly clarity/maintenance (not performance). Still, this is a “low-risk, high-readability” refactor.

## Proposed test layout
Replace the single file with module-aligned files:
- `tests/test_config.py`
- `tests/test_jira_client.py`
- `tests/test_export_csv.py`

Optional (only if helpers start to repeat):
- `tests/helpers.py` (shared test utilities only)

## Proposed contents mapping
Move/rename existing tests as follows:

### `tests/test_config.py`
- Move `test_load_config_reads_and_normalizes_env` here.
- Keep using `patch.dict(os.environ, ..., clear=True)`.

Potential small refactor when you do the move:
- Consider adding a module-level helper like `make_env(tmp_csv_path: Path) -> dict[str, str]` to reduce duplication if more config tests are added.

### `tests/test_jira_client.py`
- Move `test_get_active_sprint_id_requires_exactly_one_active_sprint` here.
- Move `test_fetch_sprint_issues_pages_until_complete` here.

Potential small refactor when you do the move:
- Avoid defining `fake_jira_get` inside the test method (currently a nested function). Instead, define it as a module-level function or use a small callable class/closure at module scope.
  - This aligns better with the project’s general preference to avoid nested function definitions.
- Consider using a shared `make_cfg()` helper for `JiraConfig` creation, since the same config literal appears in multiple tests.

Optional coverage improvement (separate commit / optional step):
- Add a focused unit test for `build_auth_header()`.
- Add a focused unit test for `jira_get()` that confirms it calls `raise_for_status()` and returns `response.json()` (can be mocked).

### `tests/test_export_csv.py`
- Move `test_write_csv_emits_expected_columns` here.

Optional coverage improvement (separate commit / optional step):
- Add direct unit tests for `safe_field()` (happy path, missing keys, `None` values).

## Naming conventions
- Keep `unittest.TestCase` style classes.
- Rename `class TestMain` into module-specific class names, e.g.:
  - `class TestConfig(unittest.TestCase)`
  - `class TestJiraClient(unittest.TestCase)`
  - `class TestExportCsv(unittest.TestCase)`

## Execution and safety checks
After splitting:
- Run the full suite: `uv run ./run_tests.py`
- Ensure test discovery still finds all tests (filenames start with `test_` and are under `tests/`).

## Suggested implementation order (when you decide to do it)
1. Create the three new test files and move the relevant tests.
2. Run tests.
3. Delete `tests/test_main.py` (only after confirming all tests are present and passing).
4. (Optional) Add shared helpers only if duplication appears after the split.

## Success criteria
- Tests remain functionally identical (same assertions, same mocking strategy).
- No behavior changes in `lib/`.
- New test filenames clearly indicate what module they target.
