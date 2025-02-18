import requests

# IMPORTANT:
# If you're using a Lambda Function URL, e.g.:
#   https://xyz123.lambda-url.us-east-1.on.aws
# add the path manually, like: https://xyz123.lambda-url.us-east-1.on.aws/search
# or https://xyz123.lambda-url.us-east-1.on.aws/financials
#
# If you're using API Gateway with a proxy integration, your base URL may look like:
#   https://abc456.execute-api.us-east-1.amazonaws.com/prod
# and you can append /search or /financials to that.

base_lambda_url = "your_lambda_url_here"

def test_search_route():
    """
    Test the /search route for raw 10-Q text attachments.
    """
    url = base_lambda_url + "/search"
    payload = {
        "ticker": "AMT",
        "report_type": "income_statement",  
    }
    response = requests.post(url, json=payload)
    print("=== /search Route ===")
    print("Status code:", response.status_code)
    try:
        print("JSON response:", response.json())
    except ValueError:
        print("Raw text response:", response.text)

def test_financials_route():
    """
    Test the /financials route for XBRL-based financial statements.
    """
    url = base_lambda_url + "/financials"
    payload = {
        "ticker": "AMT"
    }
    response = requests.post(url, json=payload)
    print("=== /financials Route ===")
    print("Status code:", response.status_code)
    try:
        print("JSON response:", response.json())
    except ValueError:
        print("Raw text response:", response.text)


if __name__ == "__main__":
    test_search_route()
    print()
    test_financials_route()
