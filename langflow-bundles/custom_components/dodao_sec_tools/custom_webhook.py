import json

from langflow.custom import Component
from langflow.io import MultilineInput, Output
from langflow.schema import Data
from langflow.schema.message import Message


class WebhookComponent(Component):
    display_name = "Webhook"
    description = "Defines a webhook input for the flow."
    name = "Webhook"
    icon = "webhook"

    inputs = [
        MultilineInput(
            name="data",
            display_name="Payload",
            info="Receives a payload from external systems via HTTP POST.",
        )
    ]
    outputs = [
        Output(display_name="Data", name="output_data", method="build_data"),
        Output(display_name="ticker", name="ticker", method="build_ticker"),
        Output(display_name="criterionKey", name="criterionKey", method="build_criterion_key"),
        Output(display_name="reportKey", name="reportKey", method="build_report_key"),
    ]
    
    def build_data(self) -> Data:
        message: str | Data = ""
        if not self.data:
            self.status = "No data provided."
            return Data(data={})
        try:
            body = json.loads(self.data or "{}")
        except json.JSONDecodeError:
            body = {"payload": self.data}
            message = f"Invalid JSON payload. Please check the format.\n\n{self.data}"
        data = Data(data=body)
        if not message:
            message = data
        self.status = message
        return data

    def _parse_payload(self) -> dict:
        """Helper method to parse JSON payload and handle errors."""
        if not self.data:
            self.status = "No data provided."
            return {}
        try:
            return json.loads(self.data)
        except json.JSONDecodeError:
            self.status = f"Invalid JSON payload. Please check the format.\n\n{self.data}"
            # Return the raw payload under a dedicated key if needed
            return {"payload": self.data}

    def build_ticker(self) -> Message:
        """Extracts the 'ticker' value from the payload."""
        payload = self._parse_payload()
        ticker = payload.get("ticker", "")
        return Message(text=ticker)

    def build_criterion_key(self) -> Message:
        """Extracts the 'key' from the nested 'criterion' field."""
        payload = self._parse_payload()
        criterion = payload.get("criterion", {})
        criterion_key = criterion.get("key", "")
        return Message(text=criterion_key)

    def build_report_key(self) -> Message:
        """Extracts the 'reportKey' value from the payload."""
        payload = self._parse_payload()
        report_key = payload.get("reportKey", "")
        return Message(text=report_key)
