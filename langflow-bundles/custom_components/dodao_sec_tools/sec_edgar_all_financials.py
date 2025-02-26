import requests
import json

from langflow.custom import Component
from langflow.inputs import MessageTextInput
from langflow.template import Output
from langflow.schema.message import Message

class SecEdgarFinancialsComponent(Component):
    display_name = "All 10Q Financials"
    description = "Fetch the structured XBRL-based financial statements for a given ticker."
    icon = "custom_components"
    name = "SecEdgarFinancialsComponent"

    inputs = [
        MessageTextInput(
            name="ticker", 
            display_name="Ticker", 
            value="AAPL", 
            info="The stock ticker symbol, e.g., AAPL for Apple.",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="EDGAR 10-Q Financials", name="financials_result", method="call_financials_lambda"),
    ]

    def call_financials_lambda(self) -> Message:
        """
        Call the SEC Edgar Lambda Function URL with ticker only, 
        hitting the /financials route for XBRL-based financial statements.
        """
        # Example: If your base is https://xyz123.lambda-url.us-east-1.on.aws
        # then we append /financials
        lambda_url = "https://4mbhgkl77s4gubn7i2rdcllbru0wzyxl.lambda-url.us-east-1.on.aws/financials"

        payload = {
            "ticker": self.ticker,
        }

        try:
            response = requests.post(lambda_url, json=payload)
            response_data = response.json()  # e.g. { "status": 200, "data": {...} } or { "message": "error" }

            if "message" in response_data:
                # Typically means error
                return Message(text=response_data["message"])
            elif "data" in response_data:
                # Might be a big JSON structure
                # So let's pretty-print it as a string for now
                return Message(text=json.dumps(response_data["data"], indent=2))
            else:
                # Just dump the whole response if uncertain
                return Message(text=json.dumps(response_data, indent=2))

        except Exception as e:
            error_text = f"Error calling SEC Edgar Lambda (/financials): {e}"
            return Message(text=error_text)
