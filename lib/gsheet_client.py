from __future__ import annotations

import gspread
from google.oauth2.service_account import Credentials

from lib.config import GSheetConfig


def get_gspread_client(config: GSheetConfig) -> gspread.Client:
    """
    Returns an authenticated gspread client with write scope.
    """
    scopes: list[str] = ['https://www.googleapis.com/auth/spreadsheets']
    credentials: Credentials = Credentials.from_service_account_info(config.credentials, scopes=scopes)
    client: gspread.Client = gspread.authorize(credentials)
    return client


def update_spreadsheet(client: gspread.Client, spreadsheet_id: str, rows: list[list[str]]) -> None:
    """
    Clears and batch-updates a spreadsheet with new data.
    """
    ## open spreadsheet and get first worksheet
    spreadsheet: gspread.Spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet: gspread.Worksheet = spreadsheet.worksheets()[0]

    ## clear existing data
    worksheet.clear()

    ## batch update with new data starting at A1
    worksheet.update(rows, 'A1')
