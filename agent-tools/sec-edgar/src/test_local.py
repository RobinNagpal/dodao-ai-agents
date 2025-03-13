import json
from src.app import lambda_handler


def local_invoke_search(ticker, report_type):
    """
    Simulate an HTTP POST to /search
    with a JSON body containing "ticker" and "report_type".
    """
    event = {
        # For Lambda Function URLs or HTTP API, "rawPath" is used.
        # If you were simulating API Gateway REST, you'd do "path": "/search" instead.
        "rawPath": "/search",
        "requestContext": {"http": {"method": "POST"}},
        # The event body must be a string (JSON-encoded).
        "body": json.dumps({"ticker": ticker, "report_type": report_type}),
    }
    context = {}  # Unused in this example
    response = lambda_handler(event, context)
    print("=== /search response ===")
    print("statusCode:", response["statusCode"])
    # Parse the JSON in the response body
    response_body = json.loads(response["body"])
    print("body:", json.dumps(response_body, indent=2))


def local_invoke_financials(ticker):
    """
    Simulate an HTTP POST to /financials
    with a JSON body containing "ticker".
    """
    event = {
        "rawPath": "/financials",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({"ticker": ticker}),
    }
    context = {}
    response = lambda_handler(event, context)
    print("=== /financials response ===")
    print("statusCode:", response["statusCode"])
    response_body = json.loads(response["body"])
    print("body:", json.dumps(response_body, indent=2))


def local_invoke_populate_criteria(ticker):
    """
    Simulate an HTTP POST to /populate-criteria-matches
    with a JSON body containing "ticker".
    """
    event = {
        "rawPath": "/populate-criteria-matches",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({"ticker": ticker}),
    }
    context = {}
    response = lambda_handler(event, context)
    print("=== /populate-criteria-matches response ===")
    print("statusCode:", response["statusCode"])
    response_body = json.loads(response["body"])
    print("body:", json.dumps(response_body, indent=2))

def local_get_all_filings(ticker):
    """
    Simulate an HTTP POST to /populate-criteria-matches
    with a JSON body containing "ticker".
    """
    event = {
        "rawPath": "/populate-criteria-matches",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({"ticker": ticker}),
    }
    context = {}
    response = lambda_handler(event, context)
    print("=== /populate-criteria-matches response ===")
    print("statusCode:", response["statusCode"])
    response_body = json.loads(response["body"])
    print("body:", json.dumps(response_body, indent=2))


def local_invoke_get_criteria(ticker, criterion_key):
    """
    Simulate an HTTP POST to /get-matching-criteria-attachments
    with a JSON body containing "ticker".
    """
    event = {
        "rawPath": "/get-matching-criteria-attachments",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({"ticker": ticker, "criterion_key": criterion_key}),
    }
    context = {}
    response = lambda_handler(event, context)
    print("=== /get-matching-criteria-attachments response ===")
    print("statusCode:", response["statusCode"])
    response_body = json.loads(response["body"])
    print("body:", json.dumps(response_body, indent=2))


if __name__ == "__main__":
    # EXAMPLES OF LOCAL CALLS:
    # 1) Search route with ticker=AMT, report_type=balance_sheet
    # local_invoke_search("AMT", "balance_sheet")
    # print()

    # 2) Financials route for ticker=AMT
    local_invoke_populate_criteria("FVR")
    # local_invoke_get_criteria("FVR", "financial_performance")
