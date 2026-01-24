# Critique: PLAN_update_spreadsheet.md

## Overall assessment

The plan is a solid, implementable outline that correctly:

- Keeps the `gsheet_experimentation_script/` code as a *reference only*.
- Targets a true “replace sheet contents” workflow (`clear()` + one bulk `update()`), which is the right basic batching strategy.
- Identifies the right integration seam (`main.py` after `write_csv()`), while keeping most logic in `lib/`.

That said, there are a few oversights that will likely cause friction during implementation (worksheet selection, large-sheet limits, error handling, and config boundaries), plus a couple improvements that will make the feature safer and more maintainable.

---

## Strengths

- **Good contextualization for future sessions**
  - Calling out the env vars, the temp nature of the experimentation directory, and the service account email is exactly the kind of context that’s easy to lose.

- **Good separation-of-concerns direction**
  - Proposing `lib/gsheet_client.py` is aligned with the repo’s existing “thin `main()` / logic in `lib/`” approach.

- **Correct high-level API choice**
  - Using `worksheet.clear()` followed by a single `worksheet.update(...)` is the simplest batch-style write that still dramatically reduces request count.

- **Testing is included**
  - The plan explicitly calls out tests and mocking, which is often forgotten for integrations.

---

## Oversights / risks

### 1) “Fully replace data” needs a more precise definition

`worksheet.clear()` clears cell values, but does not necessarily reset formatting, filters, protected ranges, frozen rows, etc.

- If “fully replace all existing spreadsheet data” means **values only**, current approach is fine.
- If it means **values + formatting/layout**, the plan should call that out explicitly and likely avoid trying to wipe formatting unless required (it’s more invasive and harder to test).

**Suggestion:** Add a short statement clarifying “replace” = values only (recommended), and confirm whether preserving formatting/frozen header/etc. is desired.

### 2) Worksheet selection is underspecified

The experiment uses `worksheets()[0]`. That’s fine for a demo, but brittle for a production-ish script.

**Missing decisions:**

- Should the script always write to the first worksheet?
- Should it target a worksheet by name (e.g. `GSHEET_WORKSHEET_NAME`)?
- Should it create the worksheet if it doesn’t exist?

**Suggestion:** Add `GSHEET_WORKSHEET_NAME` (optional; default to first worksheet) so the update target is explicit.

### 3) Large update limits and chunking aren’t addressed

Google Sheets API has payload / cell update limits. A single `worksheet.update(rows, 'A1')` can fail if the dataset is large.

**Suggestion:** Plan for chunked writes if the cell count is beyond a threshold.

- Example approach:
  - `worksheet.clear()` once
  - then write in chunks of N rows via successive `update()` calls
  - (still “batchy” compared to per-cell writes, but avoids request-size failures)

Even if you *don’t implement chunking initially*, at least record this as a known risk.

### 4) Config layering in `lib/config.py` is likely to get awkward

Right now `lib/config.py` is Jira-only and is small/clean. Adding `GSheetConfig` and `load_gsheet_config()` there is workable, but it mixes two distinct concerns.

**Suggestion:** Consider either:

- keep `lib/config.py` as-is and add `lib/gsheet_config.py`, or
- keep a unified config module but make it explicit (e.g., `load_jira_config()` + `load_gsheet_config()`), so it’s not “JiraConfig + extra unrelated config”.

### 5) Credentials env var format is tricky

`GSHEET_CREDENTIALS_JSON` is a JSON blob stored inside an env var. This is common, but brittle:

- quoting/newlines in `private_key` can break parsing
- shell escaping varies

The experimentation sample shows multi-line JSON inside single quotes. That works in some contexts but can still be error-prone.

**Suggestion:** Expand the plan to support one additional option:

- `GSHEET_CREDENTIALS_FILE` pointing to a service-account JSON file path

This avoids env escaping problems and is easier to rotate.

### 6) Error handling and operator feedback

The plan says “Add print statement confirming update”, but doesn’t address failures:

- missing sheet permissions
- invalid spreadsheet id
- invalid creds
- API rate/quota errors

**Suggestion:** Add explicit error-handling expectations:

- raise a clear `RuntimeError` with context (spreadsheet id, worksheet name)
- keep `main()` simple; handle and re-raise in `lib/gsheet_client.py`

### 7) Tests: what exactly is tested needs tightening

Mocking gspread is doable but can become “test the mocks”. The most valuable unit tests here are:

- config parsing tests
- data-shaping tests (`issues` -> 2D rows)
- *minimal* client interaction tests (verify correct method calls, correct arguments)

**Suggestion:** In the plan, specify tests more concretely:

- `Checks load_gsheet_config reads and validates env vars`
- `Checks issues_to_rows includes header and stringifies fields`
- `Checks update_spreadsheet clears then updates from A1`

(And ensure unittest docstrings start with “Checks...”, per `AGENTS.md`.)

---

## Additional suggestions (nice-to-have but high leverage)

### A) Add a “disable spreadsheet write” toggle

Because writing to Sheets is a side effect, it’s helpful to have a quick way to disable it.

Options:

- env var: `GSHEET_ENABLED=0/1`
- or CLI flag: `--skip-gsheet`

This makes local testing easier and reduces risk.

### B) Define `issues_to_rows()` output precisely

The plan says “including header row”, which is good. Also clarify:

- all values should be `str`
- preserve the same field ordering as CSV
- avoid `None` values

Since `write_csv()` already contains a clear field mapping, `issues_to_rows()` should likely share that mapping to avoid divergence.

### C) Consider writing directly from `out_csv_path`

An alternative to re-deriving rows from Jira `issues` is:

- write CSV
- then read CSV and push the same tabular data to Sheets

That guarantees the Sheet matches the CSV output exactly (including any future changes). It also keeps the “single source of truth” for column definitions in one place.

If you prefer not to do that, the plan should at least note the “dual mapping” risk (CSV mapping and Sheet mapping drifting).

### D) Dependency versions and groups

The plan’s dependency additions are reasonable, but you may want to align with the repo’s existing version style (`~=...` with a pinned minor).

Also consider whether these should be in main dependencies vs a dependency group:

- If spreadsheet update is a core feature, main deps are fine.
- If it’s optional, it could go in a `local`/`prod` group.

---

## Concrete edits to improve the plan (recommended)

If you want to upgrade the plan without making it longer, I’d add these bullets:

- Define whether “replace” means values only (recommended) vs values + formatting.
- Add `GSHEET_WORKSHEET_NAME` (optional, default first worksheet).
- Add note about large-sheet chunking limits.
- Decide whether to support `GSHEET_CREDENTIALS_FILE` in addition to `GSHEET_CREDENTIALS_JSON`.
- Prefer either:
  - `lib/gsheet_config.py` + `lib/gsheet_client.py`, or
  - rename `load_config()` to `load_jira_config()` if `lib/config.py` becomes multi-config.

---

## Status

Critique written and saved to `jira_stories_export_script/PLAN-CRITIQUE_update_spreadsheet.md`.
