# Jira Stories Export Script

## Overview
Brief description of what the script does: fetches issues from the active Jira sprint and exports them to a Google Spreadsheet.


## Assumes
- Jira is configured with a board containing sprint-stories, and a Jira API token has been created.
- A Google Sheets Service Account has been set up, and JSON credentials have been created.


## Usage
Command to run the export script: `uv run ./main.py`.


## How It Works

### Main Flow
Explanation of the orchestration in `main.py`: loading config, fetching Jira data, transforming to rows, updating Google Sheet.

### Jira Integration
Details about `lib/jira_client.py`: Basic auth header construction, active sprint discovery, paginated issue fetching via Jira Agile API.

### Google Sheets Integration
Details about `lib/gsheet_client.py`: Service account authentication, spreadsheet clearing and batch updating.

### Data Transformation
Details about `lib/export_csv.py`: Safe nested field extraction from Jira issue fields, conversion to 2D row format (key, summary, status, assignee, reporter, issuetype, priority, story_points).

### Configuration Management
Details about `lib/config.py`: Frozen dataclasses for type-safe config, environment variable loading with validation.


## Architecture
Brief note on the modular structure with `lib/` package containing separate concerns (config, Jira client, Google Sheets client, data transformation).


## License
MIT License
