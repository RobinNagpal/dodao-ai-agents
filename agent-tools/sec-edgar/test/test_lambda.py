import sys
import os
import json
from typing import Any, Dict

import pytest

# Ensure the root folder is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lambda_function import lambda_handler

# Dummy context implementing the LambdaContext protocol
class DummyLambdaContext:
    function_name = "test_lambda"
    function_version = "$LATEST"
    invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_lambda"
    memory_limit_in_mb = "128"
    aws_request_id = "test-request-id"
    log_group_name = "test-log-group"
    log_stream_name = "test-log-stream"

    def get_remaining_time_in_millis(self) -> int:
        return 300000

@pytest.fixture
def context() -> DummyLambdaContext:
    return DummyLambdaContext()

def test_lambda_handler_success(context: DummyLambdaContext):
    # Set the required environment variable for the EDGAR tool.
    os.environ["EDGAR_LOCAL_DATA_DIR"] = "/tmp/edgar_data_test"

    event: Dict[str, Any] = {
        "ticker": "AAPL",
        "report_type": "balance_sheet"
    }
    response = lambda_handler(event, context)

    # Check the response structure
    assert "statusCode" in response
    assert "message" in response

    message = response["message"]
    print("Response message:", message)
    assert response["statusCode"] == 200

def test_lambda_handler_invalid_report_type(context: DummyLambdaContext):
    event: Dict[str, Any] = {
        "ticker": "AAPL",
        "report_type": "invalid_report"
    }
    response = lambda_handler(event, context)
    assert response["statusCode"] == 404
