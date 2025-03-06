from typing import Dict

# Define search keywords for different report types
search_map: Dict[str, list[str]] = {
    "balance_sheet": ["balance sheet"],
    "income_statement": [
        "statements of comprehensive income",
        "statements of operations and comprehensive income",
        "statement of operations and comprehensive income",
    ],
    "cash_flow": ["statements of cash flows", "statement of cash flows"],
    "operation_statement": [
        "statements of operations",
        "statements of operations and comprehensive income",
        "statement of operations and comprehensive income",
    ],
}
