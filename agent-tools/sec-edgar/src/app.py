import json

from edgar import Company, use_local_storage, set_identity
from typing import Any, Dict, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from src.all_financial_reports import get_xbrl_financials
from src.specific_10Q_report import specific_report_text
from src.criteria_matching import get_matching_criteria_attachments

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")

def lambda_handler(event, context):
    try:
        # event["rawPath"] is for Lambda Function URLs and new HTTP API Gateway
        # Or event["path"] if you're using REST API Gateway
        path = event.get("rawPath") or event.get("path") or ""
        method = event.get("requestContext", {}).get("http", {}).get("method", "POST")

        # parse JSON body
        body = json.loads(event["body"]) if "body" in event and event["body"] else {}

        ticker = body.get("ticker", "AAPL")

        # Simple routing logic:
        if path == "/search":  # route 1
            report_type = body.get("report_type", "balance_sheet")
            result_text, error = specific_report_text(ticker, report_type)
            if error:
                return json_response(404, {"status": 404, "message": error})
            return json_response(200, {"status": 200, "data": result_text})

        elif path == "/financials":  # route 2
            try:
                data = get_xbrl_financials(ticker)
                return json_response(200, {"status": 200, "data": data})
            except Exception as e:
                return json_response(500, {"status": 500, "message": str(e)})
            
        elif path == "/save-attachment-criteria-matches":  # route 3
            try:
                data = get_matching_criteria_attachments(ticker)
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
