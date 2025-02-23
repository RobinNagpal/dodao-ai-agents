import requests
import json

from langflow.custom import Component
from langflow.inputs import MessageTextInput
from langflow.template import Output
from langflow.schema.message import Message

class SecEdgarComponent(Component):
    display_name = "SEC Edgar 10-Q Fetcher"
    description = "Fetch the latest 10-Q for a given ticker and report type."
    icon = "custom_components"  # or any icon name you like
    name = "SecEdgarSearchComponent"

    # Define the inputs your component needs
    inputs = [
        MessageTextInput(
            name="ticker", 
            display_name="Ticker", 
            value="AAPL", 
            info="The stock ticker symbol, e.g., AAPL for Apple.",
            tool_mode=True,
        ),
        MessageTextInput(
            name="report_type", 
            display_name="Report Type", 
            value="balance_sheet", 
            info="Options: balance_sheet, income_statement, operation_statement, cash_flow.",
            tool_mode=True,
        ),
    ]

    # Define how the output is produced
    outputs = [
        Output(display_name="EDGAR 10-Q Result", name="edgar_result", method="call_edgar_lambda"),
    ]

    def call_edgar_lambda(self) -> Message:
        """
        Call the SEC Edgar Lambda Function URL with ticker & report_type,
        and return the text from the 10-Q if available.
        """
        # The Lambda Function URL you got after deployment
        lambda_url = "https://mob4uein6xutxmhajtqswwz3vu0plhtu.lambda-url.us-east-1.on.aws/search"
        
        # Build the request payload
        payload = {
            "ticker": self.ticker,
            "report_type": self.report_type
        }

        try:
            # Send POST request with JSON body
            response = requests.post(lambda_url, json=payload)

            # Parse the JSON body from your Lambda
            data = response.json()  # e.g. {"status": 200, "message": "..."}
            message_text = data.get("data", "")

            # Return as a Langflow Message object
            return Message(text=message_text)

        except Exception as e:
            # In case something goes wrong (like a network error or JSON parse error)
            error_text = f"Error calling SEC Edgar Lambda: {e}"
            return Message(text=error_text)
