import json
import requests
from datetime import datetime
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Message

class UpdateReportStatusComponent(Component):
    display_name = "Update Report Status to Fail or In Progress"
    description = "Updates the report status to 'in_progress' and returns the S3 path and updated content as messages."
    documentation = "https://docs.langflow.org/components/update_report_status"
    icon = "edit"
    name = "UpdateReportStatus"

    inputs = [
        MessageTextInput(
            name="project_id",
            display_name="Project ID",
            info="Enter the project ID.",
            value="12345",
            tool_mode=True,
        ),
        MessageTextInput(
            name="report_type",
            display_name="Report Type",
            info="Specify the type of report to update.",
            value="finalReport",
            tool_mode=True,
        ),
        MessageTextInput(
            name="triggered_by",
            display_name="Triggered By",
            info="Who triggered this update?",
            value="system",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="S3 Path", name="s3_path_output", method="get_s3_path"),
        Output(display_name="Updated Content", name="updated_content_output", method="get_updated_content"),
    ]

    def get_project_status_file_path(self, project_id: str) -> str:
        """Returns the S3 path for the project's status file."""
        return f"crowd-fund-analysis/{project_id}/agent-status.json"

    def get_project_file(self, project_id: str):
        """Fetches the project status data from S3 and ensures valid JSON."""
        s3_path = self.get_project_status_file_path(project_id)
        response = requests.get(f"https://bucket-381-131.s3.amazonaws.com/{s3_path}")

        try:
            project_data = response.text.strip()
            return json.loads(project_data)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in S3 file: {s3_path}")

    def get_init_data_for_report(self, report_type: str, triggered_by: str = ""):
        """Initializes the report with default values."""
        report_data = {
            "status": "in_progress",
            "markdownLink": None,
            "startTime": datetime.now().isoformat(),
            "estimatedTimeInSec": 240 if report_type in ["FOUNDER_AND_TEAM", "FINANCIAL_HEALTH"] else 150,
            "performanceChecklist": []
        }
        if triggered_by:
            report_data["lastTriggeredBy"] = triggered_by
        return report_data

    def build_output(self):
        """Updates the report status to 'in_progress' and stores the values for message outputs."""
        project_file_contents = self.get_project_file(self.project_id)
        existing_report_data = project_file_contents["reports"].get(self.report_type, {})

        # Get default values for the report update
        updated_fields = self.get_init_data_for_report(self.report_type, self.triggered_by)

        # Only update fields that exist in `updated_fields`
        for field, value in updated_fields.items():
            existing_report_data[field] = value

        # Ensure status is updated to "in_progress"
        existing_report_data["status"] = "in_progress"

        # Update project file contents
        project_file_contents["reports"][self.report_type] = existing_report_data

        # Store results for outputs
        self.s3_path = f"s3://bucket-381-131/{self.get_project_status_file_path(self.project_id)}"

        # Convert JSON to a safe single-line string
        self.updated_content = json.dumps(project_file_contents,indent=4)


    def get_s3_path(self) -> Message:
        """Returns the S3 path as a message output."""
        self.build_output()  # Ensure output is built before accessing it
        return Message(text=self.s3_path, status=True)

    def get_updated_content(self) -> Message:
        """Returns the updated JSON content as a message output."""
        self.build_output()  # Ensure output is built before accessing it
        return Message(text=self.updated_content, status=True)
