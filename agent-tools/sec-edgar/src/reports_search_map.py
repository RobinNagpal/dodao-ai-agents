from typing import Dict

# Define search keywords for different report types
search_map: Dict[str, list[str]] = {
    "balance_sheet": ["balance sheet"],
    "income_statement": [
        "statements of comprehensive income",
        "statements of operations and comprehensive income",
        "statement of operations and comprehensive income",
        "statements of operations",
        "statements of operations and comprehensive income",
        "statement of operations and comprehensive income",
        "consolidated statements of operations"
        "consolidated statements of comprehensive income",
    ],
    "cash_flow": ["statements of cash flows", "statement of cash flows"],
    "equity_statement": [
        "statements of changes in equity",
        "statement of changes in equity",
        "consolidated statements of changes in equity",
        "consolidated statement of changes in equity",
        "consolidated statements of shareholders equity",
    ],
}
