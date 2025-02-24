from edgar import Company, use_local_storage, set_identity
from flask import Flask, request, jsonify
from typing import Any, Dict, Optional, Tuple
from awsgi import response
from langchain_openai import ChatOpenAI

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")

# Define search keywords for different report types
search_map: Dict[str, list[str]] = {
    "balance_sheet": ["balance sheet"],
    "income_statement": [
        "statements of comprehensive income",
        "statements of operations and comprehensive income",
    ],
    "cash_flow": ["statements of cash flows"],
    "operation_statement": [
        "statements of operations",
        "statements of operations and comprehensive income",
    ]
}


def get_raw_10q_text(ticker: str, report_type: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve raw text from the latest 10-Q filing attachments based on report type.
    """
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
            # For certain report types, only one or two attachments are needed.
            if report_type.lower() in ["income_statement", "cash_flow", "operation_statement"] and len(
                    matched_texts) == 1:
                break
            if report_type.lower() == "balance_sheet" and len(matched_texts) == 2:
                break

    if not matched_texts:
        return None, f"No attachments found for '{report_type}' in the latest 10-Q for '{ticker}'."

    return "\n\n".join(matched_texts), None


def get_xbrl_financials(ticker: str) -> Tuple[Optional[Dict[str, Optional[str]]], Optional[str]]:
    """
    Retrieve XBRL-based financials from the latest 10-Q filing.
    """
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    if not filings:
        return None, f"No 10-Q filings found for ticker '{ticker}'."

    latest_10q = filings.latest()
    tenq = latest_10q.obj()
    if not tenq or not tenq.financials:
        return None, "No XBRL-based financials found in the latest 10-Q."

    fin = tenq.financials

    financials_data: Dict[str, Optional[str]] = {
        "balance_sheet": str(fin.balance_sheet.get_base_items) if fin.balance_sheet else None,
        "income_statement": str(fin.income.get_base_items) if fin.income else None,
        "cash_flow": str(fin.cashflow.get_base_items) if fin.cashflow else None,
        "equity_changes": str(fin.equity.get_base_items) if fin.equity else None,
        "comprehensive_income": str(fin.comprehensive_income.get_base_items) if fin.comprehensive_income else None,
    }

    return financials_data, None


def is_financial_attachment(attachment_name: str) -> bool:
    """
    Check if the report type is a valid financial report type.
    """
    return any(k in attachment_name for k in [
        "balance sheet",
        "statements of comprehensive income",
        "statements of operations and comprehensive income",
        "statements of cash flows", "statements of operations"
    ])


def get_xbrl_financials_new(ticker: str) -> str:
    """
    Retrieve XBRL-based financials from the latest 10-Q filing.
    """
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    if not filings:
        raise Exception(f"No 10-Q filings found for ticker '{ticker}'.")

    latest_10q = filings.latest()
    attachments = latest_10q.attachments

    matched_texts = []
    for attach in attachments:
        purpose = (attach.purpose or "").lower()
        if any(k in purpose for k in "statements of"):
            try:
                matched_texts.append(attach.text())
            except Exception as e:
                matched_texts.append(
                    f"Error reading attachment seq={attach.sequence_number}: {str(e)}"
                )

    if not matched_texts:
        return f"No relevant attachments found for in the latest 10-Q for '{ticker}'."

    return "\n\n".join(matched_texts)


# Create the Flask application
app = Flask(__name__)


@app.route("/search", methods=["POST"])
def search_endpoint() -> Any:
    """
    Flask endpoint to search for a specific report in the 10-Q filing.
    """
    body: Dict[str, Any] = request.get_json(force=True)
    ticker: str = body.get("ticker", "AAPL")
    report_type: str = body.get("report_type", "balance_sheet")
    result_text, error = get_raw_10q_text(ticker, report_type)
    if error:
        return jsonify({"status": 404, "message": error}), 404
    return jsonify({"status": 200, "data": result_text}), 200


@app.route("/financials", methods=["POST"])
def financials_endpoint() -> Any:
    """
    Flask endpoint to retrieve XBRL-based financial data from the 10-Q filing.
    """
    body: Dict[str, Any] = request.get_json(force=True)
    ticker: str = body.get("ticker", "AAPL")
    try:
        data = get_xbrl_financials_new(ticker)
        return jsonify({"status": 200, "data": data}), 200
    except Exception as e:
        return jsonify({"status": 400, "message": str(e)}), 400


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entry point that adapts API Gateway events to the Flask WSGI app.
    """
    return response(app, event, context)
