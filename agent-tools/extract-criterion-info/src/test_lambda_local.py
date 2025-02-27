import json
from lambda_function import lambda_handler

# Example local test
if __name__ == "__main__":
    event = {
        # In Lambda Proxy integration, "body" is a string of JSON
        "body": json.dumps({
            "ticker": "FVR",  # Replace with a real ticker if needed
            # "keywords": [
            #     {"key": "rent", "name": "Rental Income", "short_description": "Income from rentals"},
            #     {"key": "debt", "name": "Debt Obligations", "short_description": "Long term debts, etc."}
            # ]
            # If left commented, the code will fallback to reit_criteria
        })
    }
    # Context is not used in this example
    context = {}

    response = lambda_handler(event, context)
    # Print out the full response
    print("Lambda Response:")
    print(response)
    # print("\nResponse Body (JSON-decoded):")
    # print(json.loads(response["body"]))
