import json
import requests
from datetime import datetime
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Message

class CompleteReportComponent(Component):
    display_name = "Complete Report Status"
    description = "Marks a report as completed, uploads structured output to S3, and updates the project status."
    documentation = "https://docs.langflow.org/components/complete_report_status"
    icon = "check-circle"
    name = "CompleteReportStatus"

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
            name="outputString",
            display_name="Report Output (Markdown)",
            info="The report content to be uploaded as a Markdown file.",
            value="# Report Title\n\nThis is a sample report.",
            tool_mode=True,
        ),
        MessageTextInput(
            name="oneLineSummary",
            display_name="One-Line Summary",
            info="A short summary of the report.",
            value="This report provides insights on financial health.",
            tool_mode=True,
        ),
        MessageTextInput(
            name="confidence",
            display_name="Confidence Score",
            info="The confidence score of the report (e.g., High, Medium, Low).",
            value="High",
            tool_mode=True,
        ),
        MessageTextInput(
            name="performanceChecklist",
            display_name="Performance Checklist",
            info="Checklist items in JSON format.",
            value='[{"checklistItem": "Revenue Growth", "explanation": "Revenue has increased by 20%.", "score": 8}]',
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Markdown Content", name="markdown_content", method="get_markdown_content"),
        Output(display_name="Markdown Path", name="markdown_path", method="get_markdown_path"),
        Output(display_name="Agent Status Content", name="agent_status_content", method="get_agent_status_content"),
        Output(display_name="Agent Status Path", name="agent_status_path", method="get_agent_status_path"),
    ]

    def get_project_status_file_path(self, project_id: str) -> str:
        """Returns the S3 path for the project's status file."""
        return f"crowd-fund-analysis/{project_id}/agent-status.json"

    def get_project_file(self, project_id: str):
        """Fetches the project status data from S3 and ensures valid JSON."""
        s3_path = self.get_project_status_file_path(project_id)
        response = requests.get(f"https://bucket-381-131.s3.amazonaws.com/{s3_path}")

        try:
            return json.loads(response.text.strip())
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in S3 file: {s3_path}")

    def build_output(self):
        """Updates the report status, uploads the markdown file, and updates project status."""
        project_file_contents = self.get_project_file(self.project_id)

        # Define file path for markdown report
        report_file_path = f"crowd-fund-analysis/{self.project_id}/{self.report_type}.md"

        # Generate Markdown link
        self.markdown_path = f"s3://bucket-381-131/{report_file_path}"
        markdown_link=f"https://bucket-381-131.s3.us-east-1.amazonaws.com/{report_file_path}"
        self.markdown_content = self.outputString  # Store Markdown content

        # Retrieve or initialize report
        report = project_file_contents["reports"].get(self.report_type, {
            "status": "not_started",
            "startTime": datetime.now().isoformat(),
            "performanceChecklist": []
        })

        # Update report details
        report["status"] = "completed"
        report["endTime"] = datetime.now().isoformat()
        report["markdownLink"] = markdown_link
        report["summary"] = self.oneLineSummary
        report["confidence"] = self.confidence
        report["performanceChecklist"] = json.loads(self.performanceChecklist)

        # Update the project file contents
        project_file_contents["reports"][self.report_type] = report

        # Check if all reports are completed
        all_completed = all(r["status"] == "completed" for r in project_file_contents["reports"].values())
        project_file_contents["status"] = "completed" if all_completed else "in_progress"

        # Define agent status path
        agent_status_path = self.get_project_status_file_path(self.project_id)
        self.agent_status_path = f"s3://bucket-381-131/{agent_status_path}"

        # Store updated JSON for agent status
        self.agent_status_content = json.dumps(project_file_contents, indent=4)

    def get_markdown_content(self) -> Message:
        """Returns the Markdown content as a message output."""
        self.build_output()  # Ensure output is built before accessing it
        return Message(text=self.markdown_content, status=True)

    def get_markdown_path(self) -> Message:
        """Returns the Markdown file path as a message output."""
        self.build_output()  # Ensure output is built before accessing it
        return Message(text=self.markdown_path, status=True)

    def get_agent_status_content(self) -> Message:
        """Returns the updated agent-status.json content as a message output."""
        self.build_output()  # Ensure output is built before accessing it
        return Message(text=self.agent_status_content, status=True)

    def get_agent_status_path(self) -> Message:
        """Returns the agent-status.json file path as a message output."""
        self.build_output()  # Ensure output is built before accessing it
        return Message(text=self.agent_status_path, status=True)
