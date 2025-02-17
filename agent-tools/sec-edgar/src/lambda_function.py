import os

from edgar import *
import json
use_local_storage()

def get_latest_10q_report_text(ticker: str, report_type: str = "balance_sheet") -> str:
    """
    Fetch the latest 10-Q for the given ticker, identify attachments
    that match the desired report_type (balance_sheet, income_statement,
    or cash_flow), and return the combined text of those attachments.
    
    :param ticker: e.g. "VICI", "AAPL"
    :param report_type: "balance_sheet", "income_statement", or "cash_flow"
    :return: The combined text of the matched attachments, or an error message.
    """

    # Identify ourselves to the SEC via EDGAR
    set_identity("your_email@example.com")

    # Define keywords for each type of report, matched against attachment.purpose
    search_map = {
        "balance_sheet": ["balance sheet"],
        "income_statement": ["statements of comprehensive income"],
        "cash_flow": ["statements of cash flows"],
    }

    keywords = search_map.get(report_type.lower(), [])
    if not keywords:
        return f"Error: unrecognized report_type '{report_type}'."

    # Fetch the latest 10-Q
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")

    if not filings:
        return f"No 10-Q filings found for ticker '{ticker}'."

    latest_10q = filings.latest()  # This returns a Filing object
    attachments = latest_10q.attachments  # List of attachments

    # Search attachments by .purpose
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

            if report_type.lower() in ["income_statement", "cash_flow"] and len(matched_texts) == 1:
                break
            if report_type.lower() == "balance_sheet" and len(matched_texts) == 2:
                break

    if not matched_texts:
        return (
            f"No attachments found for '{report_type}' "
            f"in the latest 10-Q for '{ticker}'."
        )

    return "\n\n".join(matched_texts)

def lambda_handler(event, context):
    """
    This Lambda takes:
      {
        "ticker": "AAPL",
        "report_type": "balance_sheet"  # optional, defaults to "balance_sheet"
      }
    and returns the combined text of the matching statements
    from the latest 10-Q.
    """
    print("EDGAR_LOCAL_DATA_DIR:", os.environ.get("EDGAR_LOCAL_DATA_DIR"))

    try:
        body = json.loads(event["body"])
        # Grab parameters from the event with defaults
        ticker = body.get("ticker", "AAPL")
        report_type = body.get("report_type", "balance_sheet")

        # Perform extraction
        result_text = get_latest_10q_report_text(ticker, report_type)

        # If the function returned an error-like string, handle that
        if result_text.startswith("Error:") or result_text.startswith("No "):
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "status": 404,
                    "message": result_text
                }),
            }

        # Success
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "status": 200,
                "message": result_text
            }),
        }

    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "status": 500,
                "message": f"Internal server error: {str(e)}"
            }),
        }
