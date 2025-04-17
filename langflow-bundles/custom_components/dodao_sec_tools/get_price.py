from langflow.custom import Component
from langflow.io import MessageTextInput, Output, MultilineInput
from langflow.schema.message import Message
import requests

class PriceComponent(Component):
    display_name = "Price"
    description = "A custom component for getting price for the given date otherwise price at reporting period of latest 10Q."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "custom_components"
    name = "Price"

    PRICE_ENDPOINT = "https://4mbhgkl77s4gubn7i2rdcllbru0wzyxl.lambda-url.us-east-1.on.aws/price-at-period-of-report"
    
    inputs = [
        MessageTextInput(
            name="ticker",
            display_name="Ticker",
            info="The ticker to retrieve data for (e.g., MDV, FVR).",
            required=True
        ),
        MultilineInput(
            name="period_of_report",
            display_name="Date",
            info="Date to get the price at (optional).",
        )
    ]

    outputs = [
        Output(
            display_name="Price",
            name="text",
            method="get_price",
        ),
    ]

    def get_price(self) -> Message:
        ticker = self.ticker
        period_of_report = self.period_of_report if self.period_of_report else None

        payload = {
            "ticker": ticker,
            "period_of_report": period_of_report,
        }
        try:
            response = requests.post(self.PRICE_ENDPOINT, json=payload)
            resp_data = response.json()
            return Message(text=resp_data["data"])
        except Exception as exc:
            return Message(text=str(exc))

