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
    print("body:", json.dumps(response_body, indent=2))


def local_invoke_search(ticker, report_type):
    _invoke_endpoint("/search", {"ticker": ticker, "report_type": report_type})


def local_invoke_financials(ticker):
    _invoke_endpoint("/financials", {"ticker": ticker})


def local_invoke_populate_criteria(ticker):
    _invoke_endpoint("/populate-criteria-matches", {"ticker": ticker})


def local_get_all_filings(ticker):
    _invoke_endpoint(
        "/all-filings-for-ticker", {"ticker": ticker, "page": 0, "limit": 2}
    )


def local_invoke_get_criteria(ticker, criterion_key):
    _invoke_endpoint(
        "/get-matching-criteria-attachments",
        {"ticker": ticker, "criterion_key": criterion_key},
    )


if __name__ == "__main__":
    # EXAMPLES OF LOCAL CALLS:
    # 1) Search route with ticker=AMT, report_type=balance_sheet
    # local_invoke_search("AMT", "balance_sheet")
    # print()

    # 2) Financials route for ticker=AMT
    local_get_all_filings("FVR")
    # local_invoke_get_criteria("FVR", "financial_performance")
