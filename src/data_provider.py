"""
data_provider.py
----------------
Supplies the cost-report data consumed by the Excel generator.

Stable return schema
~~~~~~~~~~~~~~~~~~~~
``get_report_data()`` returns a ``list[dict]`` where every dict conforms to:

    {
        "item":     str,    # Display name of the cost item
        "location": str,    # Deployment location
        "jan_2026": float,  # Cost for January 2026
        "feb_2026": float,
        "mar_2026": float,
        "apr_2026": float,
        "may_2026": float,
        "jun_2026": float,
        "jul_2026": float,
        "aug_2026": float,
        "sep_2026": float,
    }

This schema is a **stable interface contract**.  To integrate a real data source
(Flexera, Apptio, AXIS, S3 input, etc.) replace the body of ``get_report_data()``
so it returns rows in this same format.  ``excel_generator.py`` and
``lambda_function.py`` require zero changes for that swap — see design.md §14.1.
"""

# Type alias for a single report row (documentation aid; not enforced at runtime).
ReportRow = dict  # keys: item, location, jan_2026 … sep_2026


def get_report_data() -> list[ReportRow]:
    """Return the cost-report dataset as a list of row dicts.

    Current implementation: six hard-coded dummy rows.
    Dummy values are realistic cloud/IT cost figures with plausible
    month-on-month variation across Jan–Sep 2026.

    Returns
    -------
    list[ReportRow]
        Exactly six dicts, each conforming to the stable schema defined in
        the module docstring and in design.md §4.1.
    """
    return [
        {
            "item": "SQL LTC",
            "location": "US-East",
            "jan_2026": 12000,
            "feb_2026": 12450,
            "mar_2026": 12600,
            "apr_2026": 12750,
            "may_2026": 12900,
            "jun_2026": 13050,
            "jul_2026": 13200,
            "aug_2026": 13550,
            "sep_2026": 13900,
        },
        {
            "item": "AWS ARR",
            "location": "US-East",
            "jan_2026": 8500,
            "feb_2026": 8700,
            "mar_2026": 8750,
            "apr_2026": 8800,
            "may_2026": 8900,
            "jun_2026": 9000,
            "jul_2026": 9100,
            "aug_2026": 9200,
            "sep_2026": 9300,
        },
        {
            "item": "AWS FIRE",
            "location": "US-West",
            "jan_2026": 7200,
            "feb_2026": 7400,
            "mar_2026": 7450,
            "apr_2026": 7500,
            "may_2026": 7600,
            "jun_2026": 7700,
            "jul_2026": 7800,
            "aug_2026": 7950,
            "sep_2026": 8100,
        },
        {
            "item": "SQL Health Supp/Retire",
            "location": "On-Prem",
            "jan_2026": 15500,
            "feb_2026": 15100,
            "mar_2026": 14800,
            "apr_2026": 14500,
            "may_2026": 14200,
            "jun_2026": 13900,
            "jul_2026": 13600,
            "aug_2026": 13400,
            "sep_2026": 13200,
        },
        {
            "item": "Azure Filer (All)",
            "location": "Azure-East",
            "jan_2026": 9800,
            "feb_2026": 10000,
            "mar_2026": 10100,
            "apr_2026": 10200,
            "may_2026": 10350,
            "jun_2026": 10500,
            "jul_2026": 10600,
            "aug_2026": 10700,
            "sep_2026": 10800,
        },
        {
            "item": "Filer (All)",
            "location": "Global",
            "jan_2026": 11000,
            "feb_2026": 11200,
            "mar_2026": 11350,
            "apr_2026": 11450,
            "may_2026": 11550,
            "jun_2026": 11650,
            "jul_2026": 11700,
            "aug_2026": 11800,
            "sep_2026": 11900,
        },
    ]
