import json
from dotenv import load_dotenv
from edgar import use_local_storage, set_identity

from src.all_filings import get_all_filings_and_update_forms_info_in_s3
from src.all_financial_reports import get_xbrl_financials
from src.criteria_matching import (
    get_criteria_matching_for_management_discussion,
    get_criterion_attachments_content,
    get_criteria_matching_for_an_attachment,
    get_price_at_period_of_report,
    get_latest_10q_info,
)
from src.specific_10Q_report import specific_report_text
import traceback

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")


def lambda_handler(event, context):
    try:
        # event["rawPath"] is for Lambda Function URLs and new HTTP API Gateway
        # Or event["path"] if you're using REST API Gateway
        path = event.get("rawPath") or event.get("path") or ""

        # parse JSON body
        body = json.loads(event["body"]) if "body" in event and event["body"] else {}

        ticker = body.get("ticker", "")
        if not ticker:
            raise Exception(f"Ticker is missing in the request body.")

        criterion_key = body.get("criterion_key", "")

        # Simple routing logic:
        if path == "/search":  # route 1
            report_type = body.get("report_type", "balance_sheet")
            result_text = specific_report_text(ticker, report_type)
            return json_response(200, {"status": 200, "data": result_text})

        elif path == "/financials":  # route 2
            force_refresh = body.get("force_refresh", False)
            data = get_xbrl_financials(ticker, force_refresh)
            return json_response(200, {"status": 200, "data": data})

        elif path == "/get-matching-criteria-attachments":  # route 3
            data = get_criterion_attachments_content(ticker, criterion_key)
            return json_response(200, {"status": 200, "data": data})

        elif path == "/all-filings-for-ticker":  # route 4
            page = body.get("page", 0)
            page_size = body.get("pageSize", 50)
            data = get_all_filings_and_update_forms_info_in_s3(ticker, page, page_size)

            return json_response(200, data)

        elif path == "/criteria-matching-for-an-attachment":  # route 5
            sequence_no = body.get("sequence_no")
            data = get_criteria_matching_for_an_attachment(ticker, sequence_no)

            return json_response(200, data)

        elif path == "/criteria-matching-for-management-discussion":  # route 6
            data = get_criteria_matching_for_management_discussion(
                ticker, criterion_key
            )

            return json_response(200, {"data": data})

        elif path == "/latest-10q-info":  # route 7
            data = get_latest_10q_info(ticker)

            return json_response(200, {"data": data})

        elif path == "/price-at-period-of-report":  # route 8
            period_of_report = body.get("period_of_report")
            data = get_price_at_period_of_report(ticker, period_of_report)

            return json_response(200, {"data": data})

        else:
            # If path not recognized, return 404
            return json_response(404, {"message": f"No route found for path={path}"})

    except Exception as e:
        # If something goes really wrong, return 500
        print(traceback.format_exc())
        return json_response(500, {"message": f"Internal server error: {str(e)}"})


def json_response(http_status, payload):
    """
    Helper to format a Lambda Function URL / API Gateway response consistently.
    """
    return {
        "statusCode": http_status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, indent=2),
    }
