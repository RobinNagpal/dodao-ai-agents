import json

from edgar import Company, use_local_storage, set_identity
from typing import Any, Dict, Optional, Tuple
from langchain_openai import ChatOpenAI

from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")

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
        "statement of operations and comprehensive income"
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

def refine_financial_text(raw_text: str) -> str:
    """
    Call an LLM (e.g., GPT-4) to filter out older periods and keep only
    the latest quarter. Preserves original formatting as much as possible.
    """
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-4o-mini",  
    )

    system_prompt = """
    You are a financial data extraction assistant. The user has provided some
    text from a 10-Q attachment. It may contain multiple time periods
    (e.g. “3 months ended” vs “9 months ended,” or “Sep. 30, 2024” vs “Dec. 31, 2023”).

    Your job:
    1) Remove any older periods/columns, retaining only the latest quarter or period.
    2) Preserve the rest of the text exactly as it is, including spacing and line breaks,
    except for the removed columns/rows.
    3) Do not reformat or summarize; do not alter numbers or wording.
    4) If there is only one set of data, keep it entirely.
    5) Preserve all headings and subheadings as lines above the table.
    6) Return the final data in Markdown tabular format.
    7) Include headings or subheadings as lines immediately above the table (in plain text or bold text). Do not remove them.
    """

    user_prompt = f"""
    Here is the raw financial statement text from one 10-Q attachment.
    Please remove older periods but keep the latest quarter/period.

    Raw text:
    {raw_text}
    """

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    return response.content

def get_xbrl_financials_new(ticker: str) -> str:
    """
    Retrieve all attachments (raw text) from the latest 10-Q whose purpose
    matches *any* of the financial statement keywords (balance sheet, 
    income statement, cash flow, operation statement). Returns a single
    concatenated string of all matched texts.
    """

    all_keywords = set()
    for keywords in search_map.values():
        all_keywords.update(keywords)

    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    if not filings:
        raise Exception(f"No 10-Q filings found for ticker '{ticker}'.")

    latest_10q = filings.latest()
    attachments = latest_10q.attachments

    matched_texts = []
    for attach in attachments:
        purpose = (attach.purpose or "").lower()
        if any(k in purpose for k in all_keywords):
            try:
                raw_attachment_text = attach.text()
                refined_text = refine_financial_text(raw_attachment_text)
                matched_texts.append(refined_text)
            except Exception as e:
                matched_texts.append(
                    f"Error reading attachment seq={attach.sequence_number}: {str(e)}"
                )

    if not matched_texts:
        return f"No relevant attachments found for in the latest 10-Q for '{ticker}'."

    return "\n\n".join(matched_texts)


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
            try:
                data = get_xbrl_financials_new(ticker)
                return json_response(200, {"status": 200, "data": data})
            except Exception as e:
                return json_response(500, {"status": 500, "message": str(e)})

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
