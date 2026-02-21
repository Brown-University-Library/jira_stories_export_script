# Jira Stories Export Script

## Overview

A small utility that pulls the current sprint's issues from Jira and populates a Google Sheet. Useful for reporting or sharing sprint status with stakeholders who don't have Jira access.


## Assumes

- Jira is configured with a board containing sprint-stories, and a Jira API token has been created.
- A Google Sheets Service Account has been set up, and JSON credentials have been created.

See `sample_dotenv.txt` for the required environment variables.


## Usage

Copy `sample_dotenv.txt` to `../.env` and fill in your credentials. Then run:

```bash
uv run ./main.py
```


## How It Works

### Main Flow

The `./main.py` script manages the export. The `main()` function: 
- loads configuration from environment variables
- connects to Jira to fetch the active sprint's issues
- converts the issue data into spreadsheet rows
- pushes the results to Google Sheets

### Jira Integration

The script connects to Jira's Agile REST API using Basic authentication. It locates the single active sprint for a configured board, then paginates through all issues in that sprint. Expects exactly one active sprint — if zero or multiple are found, the script exits with an error.

### Google Sheets Integration

The script authenticates as a service account and updates the first worksheet of a target spreadsheet. It clears existing content before writing fresh data, so the sheet always reflects the current sprint state.

### Data Transformation

The script flattens Jira's nested issue structure into a simple row format. It extracts common fields (key, summary, status, assignee, reporter, issue type, priority, story points) and handles missing or null values gracefully.

### Configuration Management

Configuration uses immutable dataclasses and is loaded from environment variables. Missing or invalid values raise clear error messages at startup.


## Architecture

The `lib/` package separates concerns into focused modules: Jira API calls, Google Sheets operations, data transformation, and configuration handling. Each module exposes functions that are easy to test in isolation.


## License
MIT License
