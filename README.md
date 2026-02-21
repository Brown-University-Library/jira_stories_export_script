# Jira Stories Export Script

## Overview

This code pulls the current sprint's issues from Jira and populates a Google Sheet. Purpose: It's useful for reporting or sharing sprint information with stakeholders who don't have Jira access.


## Assumes

- Jira is configured with a board containing sprint-stories, and a Jira API token has been created.
- A Google Sheets Service Account has been set up, and JSON credentials have been created.
- A Google Sheet has been created, and the service account has been granted access to it.
- `uv` (https://docs.astral.sh/uv/) is installed.

See `sample_dotenv.txt` for the required environment variables.


## Usage

```bash
uv run ./main.py
```

(First time: copy `./sample_dotenv.txt` to `../.env` and fill in the necessary values.)


## How It Works

### Main Flow

The `./main.py` script manages the export. The `main()` function: 
- loads configuration from environment variables
- connects to Jira to fetch the active sprint's issues
- converts the jira issue data into data for spreadsheet rows
- pushes the results to Google Sheets

### Jira Integration

The script connects to Jira's Agile REST API using Basic authentication. It locates the single active sprint for a configured board, then paginates through all issues in that sprint. Expects exactly one active sprint — if zero or multiple are found, the script exits with an error.

### Google Sheets Integration

The script authenticates as a service account and updates the first worksheet of a target spreadsheet. It clears existing content before writing fresh data, so the sheet always reflects the current sprint state.

### Data Transformation

The script flattens Jira's nested issue structure into a simple row format. It extracts common fields (key, summary, status, assignee, reporter, issue type, priority, story points) and handles missing or null values gracefully.


## Architecture

Configuration uses immutable dataclasses and is loaded from environment variables. Missing or invalid values raise clear error messages at startup.

The `lib/` package separates concerns into focused modules: Jira API calls, Google Sheets operations, data transformation, and configuration handling. Each module exposes functions that are easy to test in isolation.


## License

MIT License

Copyright (c) 2026 Brown University Library

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---
