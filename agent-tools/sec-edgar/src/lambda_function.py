import json
import pandas as pd
from edgar import *
use_local_storage()

set_identity("your_email@example.com")

search_map = {
    "balance_sheet": [
        "balance sheet"
    ],
    "income_statement": [
        "statements of comprehensive income",
        "statements of operations and comprehensive income",
    ],
    "cash_flow": [
        "statements of cash flows"
    ],
    "operation_statement": [
        "statements of operations",
        "statements of operations and comprehensive income"
    ]
}

def get_raw_10q_text(ticker, report_type):
    print("get_raw_10q_text")
    print(report_type)
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    if not filings:
        return None, f"No 10-Q filings found for ticker '{ticker}'."

    latest_10q = filings.latest()
    attachments = latest_10q.attachments

    keywords = search_map.get(report_type.lower())
    if not keywords:
        return None, f"Error: unrecognized report_type '{report_type}'."

    matched_texts = []
    for attach in attachments:
        purpose = (attach.purpose or "").lower()
        if any(k in purpose for k in keywords):
            try:
                matched_texts.append(attach.text())
            except Exception as e:
                matched_texts.append(
                    f"Error reading attachment seq={attach.sequence_number}: {str(e)}"
                )

            if report_type.lower() in ["income_statement", "cash_flow", "operation_statement"] and len(matched_texts) == 1:
                break
            if report_type.lower() == "balance_sheet" and len(matched_texts) == 2:
                break

    if not matched_texts:
        return None, f"No attachments found for '{report_type}' in the latest 10-Q for '{ticker}'."

    return "\n\n".join(matched_texts), None

def get_xbrl_financials(ticker):
    print("get_xbrl_financials")
    print("ticker", ticker)
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    if not filings:
        return None, f"No 10-Q filings found for ticker '{ticker}'."

    latest_10q = filings.latest()
    tenq = latest_10q.obj()  
    if not tenq or not tenq.financials:
        return None, "No XBRL-based financials found in the latest 10-Q."

    fin = tenq.financials

    balance_sheet = str(fin.balance_sheet.get_base_items) if fin.balance_sheet else None
    income_stmt   = str(fin.income.get_base_items) if fin.income else None
    cash_flow     = str(fin.cashflow.get_base_items) if fin.cashflow else None
    equity        = str(fin.equity.get_base_items) if fin.equity else None
    comp_income   = str(fin.comprehensive_income.get_base_items) if fin.comprehensive_income else None

    financials_data = {
        "balance_sheet": balance_sheet,
        "income_statement": income_stmt,
        "cash_flow": cash_flow,
        "equity_changes": equity,
        "comprehensive_income": comp_income
    }

    print(financials_data)

    return financials_data, None

def lambda_handler(event, context):
    """
    We'll parse the path from the Lambda Function URL or API Gateway event.
    Then branch logic:
      - /search     => calls get_raw_10q_text
      - /financials => calls get_xbrl_financials

    We return consistent JSON: { "status": <code>, "data" or "message": ... }
    plus 'statusCode' and 'headers' for the HTTP response.
    """

    try:
        # event["rawPath"] is for Lambda Function URLs and new HTTP API Gateway
        # Or event["path"] if you're using REST API Gateway
        path = event.get("rawPath") or event.get("path") or ""
        method = event.get("requestContext", {}).get("http", {}).get("method", "POST")

        # parse JSON body
        body = {}
        if "body" in event and event["body"]:
            body = json.loads(event["body"])

        ticker = body.get("ticker", "AAPL")

        # Simple routing logic:
        if path == "/search":  # route 1
            report_type = body.get("report_type", "balance_sheet")
            result_text, error = get_raw_10q_text(ticker, report_type)
            if error:
                return json_response(404, {"status": 404, "message": error})
            return json_response(200, {"status": 200, "data": result_text})

        elif path == "/financials":  # route 2
            data, error = get_xbrl_financials(ticker)
            if error:
                return json_response(404, {"status": 404, "message": error})
            return json_response(200, {"status": 200, "data": data})

        else:
            # If path not recognized, return 404
            return json_response(404, {
                "status": 404,
                "message": f"No route found for path={path}"
            })

    except Exception as e:
        # If something goes really wrong, return 500
        return json_response(500, {
            "status": 500,
            "message": f"Internal server error: {str(e)}"
        })

def json_response(http_status, payload):
    """
    Helper to format a Lambda Function URL / API Gateway response consistently.
    """
    return {
        "statusCode": http_status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload)
    }