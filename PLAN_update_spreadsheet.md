# Plan: Update Google Spreadsheet with Jira CSV Output

## Goal

Add functionality to `jira_stories_export_script` to update a Google Spreadsheet with the Jira CSV output data, fully replacing existing spreadsheet data (but not formatting, frozen rows, etc.). Use gspread batch techniques to minimize API requests.

---

## Pre-Implementation Requirement

**Review `AGENTS.md` for coding preferences before implementing any code.**

Key points from `AGENTS.md`:
- Python 3.12 type hints everywhere
- Use `uv` for running scripts and tests
- Single-return functions preferred
- Docstrings with triple-quotes on their own lines, present tense
- Header-comments start with `## `
- Use `unittest` framework (not pytest)
- Follow `ruff.toml`: single quotes, 125 char line-length

---

## Context for Future Sessions

### Environment Variables Required

The `.env` file (located at parent directory level) contains:
- `GSHEET_CREDENTIALS_JSON` — JSON string containing Google service account credentials
- `GSHEET_SPREADSHEET_ID` — Target spreadsheet ID (e.g., `some-id-here`)
- `LOG_LEVEL` — Logging level (optional, defaults to `INFO`)

### Existing Code Structure

- `main.py` — Entry point; orchestrates Jira fetch and CSV write, has `## TODO` placeholder for gsheet update
- `lib/config.py` — Contains `JiraConfig` dataclass and `load_config()` function
- `lib/export_csv.py` — Contains `write_csv()` and `safe_field()` functions
- `lib/jira_client.py` — Contains Jira API functions

### CSV Output Format

The CSV has these columns (defined in `lib/export_csv.py`):
```
key, summary, status, assignee, reporter, issuetype, priority, story_points
```

### Reference gspread Implementation

The temporary `gsheet_experimentation_script/` directory contains working examples:
- `helpers.py:get_gspread_client()` — Creates authenticated gspread client with write scope
- `main.py:run_simple_write()` — Demonstrates basic write operations

Key gspread patterns:
```python
import gspread
from google.oauth2.service_account import Credentials

# Authentication
scopes = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(credentials)

# Get spreadsheet and worksheet
spreadsheet = client.open_by_key(spreadsheet_id)
worksheet = spreadsheet.worksheets()[0]  # or spreadsheet.sheet1
```

### Batch Update Approach

To minimize API requests, use gspread's batch methods:
- `worksheet.clear()` — Clears all data in one request
- `worksheet.update(data, 'A1')` — Updates a range with 2D list in one request

---

## Implementation Steps

### Step 1: Add gspread dependencies

Edit `pyproject.toml` to add:
```toml
"gspread~=6.0",
"google-auth~=2.0",
```

Then run: `uv sync`

### Step 2: Extend configuration

Edit `lib/config.py`:
1. Create a new `GSheetConfig` dataclass:
   ```python
   @dataclass(frozen=True)
   class GSheetConfig:
       credentials: dict
       spreadsheet_id: str
   ```
2. Add `load_gsheet_config()` function to parse `GSHEET_CREDENTIALS_JSON` and `GSHEET_SPREADSHEET_ID`

### Step 3: Create gsheet client module

Create `lib/gsheet_client.py` with:
1. `get_gspread_client(config: GSheetConfig) -> gspread.Client` — Returns authenticated client
2. `update_spreadsheet(client: gspread.Client, spreadsheet_id: str, rows: list[list[str]]) -> None` — Clears and batch-updates spreadsheet

### Step 4: Create data conversion helper

Either in `lib/export_csv.py` or a new module:
- Add `issues_to_rows(issues: list[dict]) -> list[list[str]]` — Converts Jira issues to 2D list (including header row)
- Reuse existing `safe_field()` function

### Step 5: Update main.py

After `write_csv()` call:
1. Load gsheet config via `load_gsheet_config()`
2. Convert issues to rows via `issues_to_rows()`
3. Create gspread client via `get_gspread_client()`
4. Call `update_spreadsheet()` to push data
5. Add print statement confirming update

### Step 6: Add tests

Create `tests/test_gsheet_client.py`:
- First only use mocks when really needed. They're ok, but we don't want to test-the-mocks to an unreasonable degree.
- Test `issues_to_rows()` produces correct structure
- Add tests that perform these checks:
  - `Checks load_gsheet_config reads and validates env vars`
  - `Checks issues_to_rows includes header and stringifies fields`
  - `Checks update_spreadsheet clears then updates from A1`
- Test configuration loading 

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `pyproject.toml` | Add gspread, google-auth dependencies |
| `lib/config.py` | Add `GSheetConfig` dataclass and `load_gsheet_config()` |
| `lib/gsheet_client.py` | Create new module with gspread functions |
| `lib/export_csv.py` | Add `issues_to_rows()` (or create separate module) |
| `main.py` | Add gsheet update call after CSV write |
| `tests/test_gsheet_client.py` | Add unit tests |

---

## Verification Commands

```bash
# Run all tests
uv run ./run_tests.py

# Run main script (full flow)
uv run ./main.py

# Run specific test file
uv run ./run_tests.py test_gsheet_client
```

---

## Notes

- The `gsheet_experimentation_script/` directory is **temporary** and will be removed — do not depend on it for persistent code
- The spreadsheet should already be configured to accept programmatic requests (shared with service account email)
