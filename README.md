Possible future improvements. We're NOT addressing these now.

### Worksheet selection is underspecified

The experiment uses `worksheets()[0]`. That’s fine for a demo, but brittle for a production-ish script.

**Missing decisions:**

- Should the script always write to the first worksheet?
- Should it target a worksheet by name (e.g. `GSHEET_WORKSHEET_NAME`)?
- Should it create the worksheet if it doesn’t exist?

**Suggestion:** Add `GSHEET_WORKSHEET_NAME` (optional; default to first worksheet) so the update target is explicit.

### Large update limits and chunking aren’t addressed

Google Sheets API has payload / cell update limits. A single `worksheet.update(rows, 'A1')` can fail if the dataset is large.

**Suggestion:** Plan for chunked writes if the cell count is beyond a threshold.

- Example approach:
  - `worksheet.clear()` once
  - then write in chunks of N rows via successive `update()` calls
  - (still “batchy” compared to per-cell writes, but avoids request-size failures)

Even if you *don’t implement chunking initially*, at least record this as a known risk.
