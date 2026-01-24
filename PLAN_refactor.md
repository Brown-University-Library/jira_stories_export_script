# PLAN: Refactor `main.py` into thin orchestrator + `lib/` modules

## Goal

Refactor `jira_stories_export_script/main.py` so it contains only:

- `main()`
- Any other functions *directly called by `main()`* (thin orchestration wrappers only)

All other reusable logic should move into one or more modules under:

- `jira_stories_export_script/lib/`

This plan is **plan-only** (no code changes yet).

## Current state (as of Jan 24, 2026)

### Entry point

- `main()` currently:
  - loads `.env` via `dotenv.load_dotenv()`
  - loads config via `load_config()`
  - builds Basic auth header via `build_auth_header()`
  - creates an `httpx.Client`
  - calls `get_active_sprint_id()`
  - calls `fetch_sprint_issues()`
  - calls `write_csv()`
  - prints summary
  - has a `## update google sheet` TODO

### Public functions currently imported/used by tests

`tests/test_main.py` imports `main` and calls:

- `main.load_config()`
- `main.get_active_sprint_id(...)` (with `main.jira_get` patched)
- `main.fetch_sprint_issues(...)` (with `main.jira_get` patched)
- `main.write_csv(...)`

It also references:

- `main.JiraConfig`

Implication: moving symbols out of `main.py` will require updating tests and/or providing compatibility wrappers.

### Functions/classes currently in `main.py`

- `JiraConfig` (dataclass)
- `_get_env()`
- `load_config()`
- `build_auth_header()`
- `jira_get()`
- `get_active_sprint_id()`
- `fetch_sprint_issues()`
- `safe_field()`
- `write_csv()`
- `main()`

## Target structure (proposed)

Create a `lib/` package and split responsibilities:

- `jira_stories_export_script/lib/config.py`
  - `JiraConfig`
  - `_get_env()` (or rename to `get_required_env()`; optional)
  - `load_config()`

- `jira_stories_export_script/lib/jira_client.py`
  - `build_auth_header()`
  - `jira_get()`
  - `get_active_sprint_id()`
  - `fetch_sprint_issues()`

- `jira_stories_export_script/lib/export_csv.py`
  - `safe_field()`
  - `write_csv()`

- (Optional, for readability) `jira_stories_export_script/lib/workflow.py`
  - Higher-level orchestration function(s), e.g. `export_active_sprint_to_csv(...)`
  - This is only worth it if it meaningfully simplifies `main.py`.

Keep `jira_stories_export_script/main.py` as a thin orchestrator.

## How `main.py` should look after refactor

### Allowed contents

- `def main() -> None:`
  - parse/configure
  - call a small number of “workflow” helpers

- Thin wrapper functions directly called by `main()`
  - Example: `def export_active_sprint(cfg: JiraConfig) -> int:` (returns count) that delegates to `lib/`.

### Not allowed in `main.py`

- “Library” functions that are not directly called by `main()`
  - e.g. `safe_field()`, `jira_get()` should not remain in `main.py`.

## Compatibility/testing strategy

Because tests currently import and call multiple helper functions from `main.py`, choose **one** of these approaches during implementation:

### Option A (preferred): Update tests to import from `lib/`

- Update `tests/test_main.py` to import the new modules, e.g.:
  - `from lib.config import load_config, JiraConfig`
  - `from lib.jira_client import get_active_sprint_id, fetch_sprint_issues, jira_get`
  - `from lib.export_csv import write_csv`
- Keep tests behavior the same; update patch targets accordingly (patch `lib.jira_client.jira_get`, etc.).

Pros:
- Clean separation; aligns with goal that helpers live under `lib/`.

Cons:
- Requires changing test imports/patch paths.

### Option B: Keep backwards-compatibility re-exports in `main.py`

- `main.py` imports helper symbols from `lib.*` and re-exports them so existing tests keep working.

Pros:
- Smaller test churn.

Cons:
- Conflicts with the goal “`main.py` only contains `main()` and directly-called-by-`main()` functions”.
  - Re-exporting many helpers is effectively keeping helpers in `main.py`’s public surface.

Recommendation: **Option A**.

## Implementation plan (future work)

1. Create `jira_stories_export_script/lib/` directory
   - Add `__init__.py` so it’s a package.
   - Ensure imports work when running `uv run ./run_tests.py` from the script directory.

2. Move config-related code
   - Move `JiraConfig`, `_get_env`, `load_config` into `lib/config.py`.
   - Update `main.py` to import `load_config`/`JiraConfig` from `lib.config`.

3. Move Jira HTTP logic
   - Move `build_auth_header`, `jira_get`, `get_active_sprint_id`, `fetch_sprint_issues` into `lib/jira_client.py`.
   - Ensure `httpx` types/imports remain consistent.

4. Move CSV export logic
   - Move `safe_field`, `write_csv` into `lib/export_csv.py`.

5. Slim `main.py`
   - Keep `main()`.
   - Add at most 1-2 thin orchestration helpers directly called by `main()` if it improves readability.
   - Otherwise, `main()` can call into `lib.*` directly.

6. Update tests (if following Option A)
   - Update imports to reference `lib.*` modules.
   - Update patch targets:
     - `patch.object(main, 'jira_get', ...)` becomes patching `lib.jira_client.jira_get`.
   - Keep assertions the same.

7. Run formatting/lint/tests
   - `uv run ./run_tests.py`
   - (Optional) run ruff if used by repo workflow.

## Risks / gotchas

- Import paths: tests currently do `import main` from within `jira_stories_export_script/tests/`.
  - Adding `lib/` requires ensuring it is importable in the same execution context.
  - Likely solution: treat `jira_stories_export_script/` as the working directory / module root when running tests (current behavior), and make `lib` a package via `lib/__init__.py`.

- Patching in unit tests: patch paths must be updated carefully when functions move modules.

- Future “Google Sheet update” TODO: keep it out of `main.py` logic-heavy code; implement under `lib/` as a separate module (e.g., `lib/google_sheets.py`) when ready.

## “New session” quick-start checklist

If picking this up in a fresh session:

1. Read:
   - `jira_stories_export_script/main.py`
   - `jira_stories_export_script/tests/test_main.py`
   - `jira_stories_export_script/ruff.toml` (style constraints)

2. Confirm current test runner:
   - `uv run ./run_tests.py`

3. Decide compatibility strategy:
   - Prefer updating tests to import from `lib/` (Option A).

4. Execute the implementation plan steps 1–7.
