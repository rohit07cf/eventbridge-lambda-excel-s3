"""
tests/test_excel_generator.py
------------------------------
Unit tests for excel_generator.generate_excel().

These tests verify the structure, content, and formatting of the generated
workbook.  No AWS services, boto3 imports, or network calls are used.

Test IDs match the spec (requirements.md REQ-10.2 / tasks.md Phase 4):
    T-01  Workbook can be generated and loaded without exception
    T-02  Worksheet is named "Cost Report"
    T-03  All 11 required column headers are present in row 1
    T-04  Exactly 6 data rows exist (ws.max_row == 7)
    T-05  All 6 expected item names appear in column A (rows 2-7)
    T-06  Jan 2026 through Sep 2026 headers are present
    T-07  All monthly cost values in every data row are numeric (int or float)
    T-08  The BytesIO output can be reloaded by openpyxl.load_workbook
"""

import sys
import os
from io import BytesIO

import pytest
import openpyxl

# Allow imports from src/ without installing the package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_provider import get_report_data
from excel_generator import generate_excel, COLUMN_HEADERS

# ---------------------------------------------------------------------------
# Shared fixture — build the workbook once for the entire test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def workbook() -> openpyxl.Workbook:
    """Generate the Excel workbook from dummy data and return the loaded wb."""
    buf: BytesIO = generate_excel(get_report_data())
    return openpyxl.load_workbook(buf)


@pytest.fixture(scope="module")
def worksheet(workbook: openpyxl.Workbook):
    """Return the active (Cost Report) worksheet."""
    return workbook["Cost Report"]


# ---------------------------------------------------------------------------
# T-01 — Workbook can be generated and loaded without exception
# ---------------------------------------------------------------------------

def test_t01_workbook_generates_without_exception() -> None:
    """Calling generate_excel(get_report_data()) must not raise any exception."""
    buf = generate_excel(get_report_data())
    assert isinstance(buf, BytesIO)
    assert len(buf.getvalue()) > 0


# ---------------------------------------------------------------------------
# T-02 — Worksheet is named "Cost Report"
# ---------------------------------------------------------------------------

def test_t02_worksheet_name(workbook: openpyxl.Workbook) -> None:
    """The workbook must contain exactly one sheet named 'Cost Report'."""
    assert workbook.sheetnames == ["Cost Report"]


# ---------------------------------------------------------------------------
# T-03 — All 11 required column headers are present in row 1
# ---------------------------------------------------------------------------

def test_t03_all_column_headers_present(worksheet) -> None:
    """Row 1 must contain all 11 expected column headers in order."""
    actual_headers = [
        worksheet.cell(row=1, column=col).value
        for col in range(1, len(COLUMN_HEADERS) + 1)
    ]
    assert actual_headers == COLUMN_HEADERS, (
        f"Header mismatch.\nExpected: {COLUMN_HEADERS}\nActual  : {actual_headers}"
    )


# ---------------------------------------------------------------------------
# T-04 — Exactly 6 data rows exist (max_row == 7: header + 6 data)
# ---------------------------------------------------------------------------

def test_t04_exactly_six_data_rows(worksheet) -> None:
    """ws.max_row must equal 7 (1 header row + 6 data rows)."""
    assert worksheet.max_row == 7, (
        f"Expected 7 rows (1 header + 6 data), got {worksheet.max_row}"
    )


# ---------------------------------------------------------------------------
# T-05 — All 6 expected item names appear in column A (rows 2-7)
# ---------------------------------------------------------------------------

EXPECTED_ITEMS = [
    "SQL LTC",
    "AWS ARR",
    "AWS FIRE",
    "SQL Health Supp/Retire",
    "Azure Filer (All)",
    "Filer (All)",
]


def test_t05_expected_item_names_present(worksheet) -> None:
    """Column A rows 2-7 must contain the six required item names."""
    actual_items = [worksheet.cell(row=r, column=1).value for r in range(2, 8)]
    assert actual_items == EXPECTED_ITEMS, (
        f"Item mismatch.\nExpected: {EXPECTED_ITEMS}\nActual  : {actual_items}"
    )


# ---------------------------------------------------------------------------
# T-06 — Jan 2026 through Sep 2026 headers are present
# ---------------------------------------------------------------------------

EXPECTED_MONTH_HEADERS = [
    "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026", "May 2026",
    "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026",
]


def test_t06_month_headers_present(worksheet) -> None:
    """Header row must contain all nine month column headers (Jan–Sep 2026)."""
    header_row = [
        worksheet.cell(row=1, column=col).value
        for col in range(1, worksheet.max_column + 1)
    ]
    for month in EXPECTED_MONTH_HEADERS:
        assert month in header_row, f"Month header '{month}' not found in row 1"


# ---------------------------------------------------------------------------
# T-07 — All monthly cost values in every data row are numeric
# ---------------------------------------------------------------------------

def test_t07_monthly_values_are_numeric(worksheet) -> None:
    """Columns 3-11 (Jan-Sep 2026) in every data row must be int or float."""
    errors: list[str] = []
    for row_idx in range(2, worksheet.max_row + 1):
        for col_idx in range(3, worksheet.max_column + 1):
            value = worksheet.cell(row=row_idx, column=col_idx).value
            if not isinstance(value, (int, float)):
                col_letter = openpyxl.utils.get_column_letter(col_idx)
                errors.append(
                    f"Cell {col_letter}{row_idx}: expected numeric, "
                    f"got {type(value).__name__!r} ({value!r})"
                )
    assert not errors, "Non-numeric cost values found:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# T-08 — BytesIO output can be reloaded by openpyxl.load_workbook
# ---------------------------------------------------------------------------

def test_t08_bytesio_is_valid_xlsx() -> None:
    """The buffer returned by generate_excel must be a loadable .xlsx file."""
    buf = generate_excel(get_report_data())
    # load_workbook raises if the buffer is not a valid OOXML package.
    wb = openpyxl.load_workbook(buf)
    assert wb is not None
    assert "Cost Report" in wb.sheetnames
