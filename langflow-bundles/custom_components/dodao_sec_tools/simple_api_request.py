import json
import asyncio
from typing import Any, Dict

import httpx

from langflow.custom import Component
from langflow.io import (
    StrInput,
    DropdownInput,
    DataInput,
    Output,
)
from langflow.schema import Data


class SimpleAPIRequestComponent(Component):
    display_name = "Simple API Request"
    description = "Makes an HTTP request with JSON-based body input."
    icon = "Globe"
    name = "SimpleAPIRequest"

    inputs = [
        StrInput(
            name="url",
            display_name="URL",
            info="Enter the HTTP endpoint to call (e.g., https://api.example.com).",
        ),
        DropdownInput(
            name="method",
            display_name="Method",
            options=["GET", "POST", "PATCH", "PUT", "DELETE"],
            info="Select the HTTP method to use.",
        ),
        DataInput(
            name="body_data",
            display_name="Body (JSON Data)",
            info="Parsed JSON from the JSONPayloadComponent (or any Data).",
            advanced=False,
        ),
        TableInput(
            name="headers_data",
            display_name="Headers",
            info="The headers to send with the request as a dictionary.",
            table_schema=[
                {
                    "name": "key",
                    "display_name": "Header",
                    "type": "str",
                    "description": "Header name",
                },
                {
                    "name": "value",
                    "display_name": "Value",
                    "type": "str",
                    "description": "Header value",
                },
            ],
            value=[],
            advanced=True,
            input_types=["Data"],
        ),
    ]

    outputs = [
        Output(display_name="Response", name="response", method="make_request"),
    ]

    async def make_request(self) -> Data:
        """Executes an HTTP request using the provided URL, method, body_data, and headers_data."""
        url = self.url
        method = self.method.upper()

        # Extract the actual data from the Data objects
        # If "body_data" was from JSONPayloadComponent, it might be a dict or a string.
        # We'll assume dictionary is intended for JSON body. If it's something else, handle gracefully.
        body_content = self.body_data.data if self.body_data else None
        if not isinstance(body_content, (dict, list)) and body_content is not None:
            # If it's a plain string or something else, wrap it or parse it as needed
            # For a real app, you could refine this logic. For now, we'll just send it as-is.
            body_content = {"data": body_content}

        # Same for headers
        headers = {}
        if self.headers_data and isinstance(self.headers_data.data, dict):
            # Convert all header values to strings just to be safe
            headers = {str(k): str(v) for k, v in self.headers_data.data.items()}

        try:
            async with httpx.AsyncClient() as client:
                if method in {"GET", "DELETE"}:
                    # GET/DELETE usually send no JSON body
                    response = await client.request(method, url, headers=headers, timeout=10)
                else:
                    response = await client.request(method, url, headers=headers, json=body_content, timeout=10)

                # Attempt to parse the response as JSON
                try:
                    resp_data = response.json()
                except json.JSONDecodeError:
                    # If not valid JSON, just return the raw text
                    resp_data = {"raw_text": response.text}

                return Data(
                    data={
                        "status_code": response.status_code,
                        "response": resp_data,
                    }
                )

        except Exception as exc:
            # If there's a network error, timeouts, etc., return an error structure
            return Data(
                    data={
                        "status_code": 500,
                        "response": str(exc),
                    }
                )
