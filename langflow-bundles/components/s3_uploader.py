import json
import requests
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data

class CustomComponent(Component):
    display_name = "S3 Uploader via Lambda"
    description = "Uploads a file to S3 via an AWS Lambda function."
    documentation: str = "http://docs.langflow.org/components/custom"
    icon = "upload"
    name = "S3Uploader"

    # AWS Lambda Function URL
    LAMBDA_URL = "https://gdv375i43mstvtcto7mrek6gfi0hysps.lambda-url.us-east-1.on.aws/"

    inputs = [
        MessageTextInput(
            name="path",
            display_name="S3 Path",
            info="Provide the full S3 path (e.g., s3://bucket-name/uploads/file.json).",
            value="s3://bucket-381-131/uploads/file.json",
            tool_mode=True,
        ),
        MessageTextInput(
            name="content",
            display_name="File Content",
            info="Provide the content to upload.",
            value='{"message": "Hello, World!"}',
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Upload Status", name="output", method="build_output"),
    ]

    def build_output(self) -> Data:
        """Uploads the provided content to the specified S3 path via the AWS Lambda function."""
        try:
            # Prepare request payload
            payload = {
                "path": self.path,
                "content": self.content
            }

            # Make POST request to AWS Lambda function
            response = requests.post(self.LAMBDA_URL, json=payload)

            # Check response
            if response.status_code == 200:
                response_data = response.json()
                public_url = response_data.get("public_url", "Unknown URL")
                result = {"message": "File uploaded successfully", "url": public_url}
            else:
                result = {"error": f"Failed to upload. Status: {response.status_code}", "details": response.text}

            return Data(value=result)

        except Exception as e:
            return Data(value={"error": str(e)})
