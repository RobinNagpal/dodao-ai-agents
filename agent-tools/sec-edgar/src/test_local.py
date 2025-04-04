import json
from src.app import lambda_handler


def _invoke_endpoint(raw_path, body_data):
    """
    Helper function to simulate an HTTP POST to the specified endpoint.
    """
    event = {
        "rawPath": raw_path,
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps(body_data),
    }
    context = {}
    response = lambda_handler(event, context)
    print(f"=== {raw_path} response ===")
    print("statusCode:", response["statusCode"])
    response_body = json.loads(response["body"])
    # print("body:", json.dumps(response_body, indent=2))
    return response_body


def local_invoke_search(ticker, report_type):
    _invoke_endpoint("/search", {"ticker": ticker, "report_type": report_type})


def local_invoke_financials(ticker, force_refresh=False):
    body = _invoke_endpoint(
        "/financials", {"ticker": ticker, "force_refresh": force_refresh}
    )
    print("=== Financials ===")
    print(body.get("data"))


def local_invoke_populate_criteria(ticker):
    _invoke_endpoint("/populate-criteria-matches", {"ticker": ticker})


def local_get_all_filings(ticker):
    _invoke_endpoint(
        "/all-filings-for-ticker", {"ticker": ticker, "page": 0, "pageSize": 2}
    )


def local_invoke_get_criteria(ticker, criterion_key):
    _invoke_endpoint(
        "/get-matching-criteria-attachments",
        {"ticker": ticker, "criterion_key": criterion_key},
    )


def local_invoke_get_single_criteria(ticker, sequence_no):
    response = _invoke_endpoint(
        "/criteria-matching-for-an-attachment",
        {"ticker": ticker, "sequence_no": sequence_no},
    )
    print(response)


def local_invoke_get_single_management_discussion(ticker, criterion_key):
    response = _invoke_endpoint(
        "/criteria-matching-for-management-discussion",
        {"ticker": ticker, "criterion_key": criterion_key},
    )
    print(response)

def local_invoke_get_reporting_period_and_filing_link(ticker):
    response = _invoke_endpoint(
        "/reporting_period_and_filing_link",
        {"ticker": ticker},
    )
    print(response)

if __name__ == "__main__":
    # EXAMPLES OF LOCAL CALLS:
    # 1) Search route with ticker=AMT, report_type=balance_sheet
    # local_invoke_search("AMT", "balance_sheet")
    # print()

    # 2) Financials route for ticker=AMT
    # local_invoke_populate_criteria("CCI")
    local_invoke_get_reporting_period_and_filing_link("FVR")
    # local_invoke_financials("AMT", force_refresh=True)
    # local_invoke_get_single_management_discussion("FVR", "debt_and_leverage")
    # local_invoke_get_criteria("FVR", "financial_performance")
