import json
from datetime import datetime
from typing import List, Dict, Optional

from dotenv import load_dotenv
from typing_extensions import TypedDict, NotRequired

from enum import Enum
from cf_analysis_agent.agent_state import ProjectInfo, ProcessingStatus, ReportType
from cf_analysis_agent.structures.report_structures import StructuredReportResponse
from cf_analysis_agent.structures.startup_metrics import InformationStatus
from cf_analysis_agent.utils.env_variables import REGION
from cf_analysis_agent.utils.s3_utils import s3_client, BUCKET_NAME, upload_to_s3

load_dotenv()


# ---------------------------------------------------------
# 1) TypedDict Definitions
# ---------------------------------------------------------


class RepopulatableFields(str, Enum):
    INDUSTRY_DETAILS = "industryDetails"
    STARTUP_METRICS = "startupMetrics"
    STARTUP_SUMMARY = "startupSummary"
    SEC_INFO = "secInfo"
    CROWDFUNDING_CONTENT = "contentOfCrowdfundingUrl"
    WEBSITE_CONTENT = "contentOfWebsiteUrl"

    @classmethod
    def list(cls):
        """Returns a list of all valid repopulatable field names."""
        return [field.value for field in cls]

class ProjectInfoInputSchema(TypedDict):
    """
    Represents the user-provided project input
    (URLs, etc.) that we need to track in the agent status.
    """
    crowdFundingUrl: str
    secFilingUrl: str
    additionalUrls: List[str]
    websiteUrl: str


class PerformanceChecklistItemSchema(TypedDict):
    """
    Represents a single item in the performance checklist
    for a specific report.
    """
    checklistItem: str
    explanation: str
    score: int


class ReportSchema(TypedDict, total=False):
    """
    Represents the status and metadata of a single report
    (e.g., "team_info", "financial_review", etc.).
    Fields marked as `total=False` are optional
    (e.g., endTime, errorMessage) and may only appear
    under certain conditions.
    """
    status: ProcessingStatus
    lastTriggeredBy: NotRequired[Optional[str]]
    markdownLink: Optional[str]
    startTime: str
    estimatedTimeInSec: int
    endTime: Optional[str]
    errorMessage: NotRequired[str]
    summary: NotRequired[str]
    confidence: NotRequired[float]
    performanceChecklist: List[PerformanceChecklistItemSchema]


class FinalReportSchema(ReportSchema, total=False):
    spiderGraphJsonFileUrl: NotRequired[str]

class ProcessedSecInfoSchema(TypedDict):
    """
    Stores the processed SEC filing content in various formats.
    """
    secJsonContent: str
    secMarkdownContent: str
    secRawContent: str

class MetricSchema(TypedDict):
    explanation: str
    opinion: str
    informationStatus: InformationStatus

class ProcessesStartupMetricsSchema(TypedDict, total=False):
    growthRate: MetricSchema
    organicVsPaidGrowth: MetricSchema
    virality: MetricSchema
    networkEffect: MetricSchema
    customerAcquisitionCost: MetricSchema
    unitEconomics: MetricSchema
    retentionRate: MetricSchema
    magicMoment: MetricSchema
    netPromoterScore: MetricSchema
    customerLifetimeValue: MetricSchema
    paybackPeriod: MetricSchema
    revenueGrowth: MetricSchema
    churnRate: MetricSchema
    
class SectorDetailSchema(TypedDict):
    basicInfo: str
    growthRate: str
    
class MarketDetailSchema(TypedDict):
    details: str
    calculationLogic: str

class ProcessedIndustryAndForecastsSchema(TypedDict):
    sectorDetails: SectorDetailSchema
    subSectorDetails: SectorDetailSchema
    totalAddressableMarket: MarketDetailSchema
    serviceableAddressableMarket: MarketDetailSchema
    serviceableObtainableMarket: MarketDetailSchema
    profitMargins: MarketDetailSchema

class ProcessedProjectInfoSchema(TypedDict):
    """
    Stores combined text results after scraping the various
    URLs for this project, plus a timestamp for when it was last updated.
    """
    startupSummary: str
    additionalUrlsUsed: List[str]
    contentOfAdditionalUrls: str
    contentOfCrowdfundingUrl: str
    contentOfWebsiteUrl: str
    industryDetails: ProcessedIndustryAndForecastsSchema
    secInfo: ProcessedSecInfoSchema
    startupMetrics: ProcessesStartupMetricsSchema
    lastUpdated: str
    status: ProcessingStatus


class ProjectStatusFileSchema(TypedDict, total=False):
    """
    The top-level structure that gets stored in
    `crowd-fund-analysis/<project_id>/agent-status.json`.
    """
    id: str
    name: str
    imgUrl:str
    projectInfoInput: ProjectInfoInputSchema
    status: ProcessingStatus
    reports: Dict[str, ReportSchema]
    finalReport: FinalReportSchema
    processedProjectInfo: ProcessedProjectInfoSchema


# ---------------------------------------------------------
# 2) Example usage of these schemas in code
# ---------------------------------------------------------
ALL_REPORT_TYPES: list[ReportType] = ReportType.list()


def get_project_status_file_path(project_id: str) -> str:
    """
    Returns the path to the status file for the given project ID.
    """
    return f"{project_id}/agent-status.json"


def get_project_info_from_s3(project_id: str) -> ProjectInfo:
    """
    Extracts variables from the agent-status.json file stored in S3.
    Returns a dictionary representing the essential project info.
    """
    # Define the S3 key for the status file
    agent_status_file_path = get_project_status_file_path(project_id)

    # Fetch the agent-status.json file from S3
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"crowd-fund-analysis/{agent_status_file_path}")
    project_file_contents: ProjectStatusFileSchema = json.loads(response['Body'].read().decode('utf-8'))

    # Extract required variables
    project_name = project_file_contents.get("name", "").strip()
    crowdfunding_link = project_file_contents.get("projectInfoInput", {}).get("crowdFundingUrl", "").strip()
    website_url = project_file_contents.get("projectInfoInput", {}).get("websiteUrl", "").strip()
    latest_sec_filing_link = project_file_contents.get("projectInfoInput", {}).get("secFilingUrl", "").strip()
    additional_links: list[str] = project_file_contents.get("projectInfoInput", {}).get("additionalUrls", [])

    # Validate required fields
    if not all([project_name, crowdfunding_link, website_url, latest_sec_filing_link]):
        raise ValueError("Missing required data in agent-status.json.")

    # Return extracted variables
    return {
        "project_id": project_id,
        "project_name": project_name,
        "crowdfunding_link": crowdfunding_link,
        "website_url": website_url,
        "latest_sec_filing_link": latest_sec_filing_link,
        "additional_links": additional_links
    }


def get_init_data_for_report(report_type: ReportType, triggered_by = '') -> ReportSchema:
    """
    Returns an initialized ReportSchema dictionary
    for the given report_type.
    """
    report_data = {
        "status": ProcessingStatus.NOT_STARTED,
        "markdownLink": None,
        "startTime": datetime.now().isoformat(),
        "estimatedTimeInSec": 240 if report_type in [ReportType.FOUNDER_AND_TEAM, ReportType.FINANCIAL_HEALTH] else 150,
        "performanceChecklist": []
    }
    
    if triggered_by:
        report_data["lastTriggeredBy"] = triggered_by
        
    return report_data


def initialize_project_in_s3(project_id: str, project_details: ProjectInfo, triggered_by = ''):
    """
    Creates or re-initializes the agent-status.json file for a project,
    setting all reports to 'in_progress' along with basic metadata.
    """
    agent_status_file_path = get_project_status_file_path(project_id)
    current_time = datetime.now().isoformat()

    # Initialize all reports
    reports_data = {}
    for r_type in ALL_REPORT_TYPES:
        reports_data[r_type] = get_init_data_for_report(r_type, triggered_by)
    # Construct the status data
    project_file_contents: ProjectStatusFileSchema = {
        "id": project_id,
        "name": project_details["project_name"],
        "imgUrl": project_details["project_img_url"],
        "projectInfoInput": {
            "crowdFundingUrl": project_details["crowdfunding_link"],
            "secFilingUrl": project_details["latest_sec_filing_link"],
            "additionalUrls": project_details["additional_links"],
            "websiteUrl": project_details["website_url"]
        },
        "status": ProcessingStatus.IN_PROGRESS,
        "reports": reports_data,
        "finalReport": {
            "status": ProcessingStatus.NOT_STARTED,
            "markdownLink": None,
            "startTime": current_time,
            "estimatedTimeInSec": 260
        }
    }

    # Upload the file to S3
    upload_to_s3(json.dumps(project_file_contents, indent=4), agent_status_file_path, content_type="application/json")
    print(
        f"Initialized status file: https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/crowd-fund-analysis/{agent_status_file_path}")


def get_project_file(project_id: str) -> ProjectStatusFileSchema:
    """
    Fetches and returns the project status data from S3.
    """
    agent_status_file_path = get_project_status_file_path(project_id)
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key="crowd-fund-analysis/" + agent_status_file_path)
    return json.loads(response['Body'].read().decode('utf-8'))


def update_project_file(project_id: str, project_file_contents: ProjectStatusFileSchema):
    """
    Uploads the updated project status data to S3.
    """
    # populate agent-status.json file with the updated data and upload it to S3

    reports = project_file_contents["reports"]
    new_reports: dict[str, ReportSchema] = {}
    for report_type in ALL_REPORT_TYPES:
        report: ReportSchema = reports.get(report_type) or get_init_data_for_report(report_type)

        performance_checklist = report.get("performanceChecklist") or []
        new_performance_checklist = []
        for item in performance_checklist:
            new_item = {
                "checklistItem": item["checklistItem"],
                "explanation": item["explanation"],
                "score": item["score"]
            }
            new_performance_checklist.append(new_item)
        new_report = {
            "status": report["status"],
            "markdownLink": report["markdownLink"],
            "startTime": report["startTime"],
            "estimatedTimeInSec": report["estimatedTimeInSec"],
            # check report["endTime"] exists and is not None
            "endTime": datetime.now().isoformat() if report.get("endTime") else None,
            "summary": report.get("summary"),
            "confidence": report.get("confidence"),
            "performanceChecklist": new_performance_checklist
        }
        if report.get("lastTriggeredBy"):
            new_report["lastTriggeredBy"] = report["lastTriggeredBy"]
        new_reports[report_type] = new_report

    sec_info = project_file_contents["processedProjectInfo"].get("secInfo") or {}
    startup_metrics = project_file_contents["processedProjectInfo"].get("startupMetrics") or {}
    industry_details = project_file_contents["processedProjectInfo"].get("industryDetails") or {}

    new_project_file_contents: ProjectStatusFileSchema = {
        "id": project_id,
        "name": project_file_contents["name"],
        "projectInfoInput": project_file_contents["projectInfoInput"],
        "status": project_file_contents["status"],
        "finalReport": {
            "status": project_file_contents["finalReport"]["status"],
            "markdownLink": project_file_contents["finalReport"]["markdownLink"],
            "startTime": project_file_contents["finalReport"]["startTime"],
            "estimatedTimeInSec": project_file_contents["finalReport"]["estimatedTimeInSec"],
            # check report["endTime"] exists and if not then set it empty
            "endTime":  datetime.now().isoformat() if project_file_contents["finalReport"].get("endTime") else None
        },
        "processedProjectInfo": {
            "additionalUrlsUsed": project_file_contents["processedProjectInfo"].get("additionalUrlsUsed"),
            "contentOfAdditionalUrls": project_file_contents["processedProjectInfo"].get("contentOfAdditionalUrls"),
            "contentOfCrowdfundingUrl": project_file_contents["processedProjectInfo"].get("contentOfCrowdfundingUrl"),
            "contentOfWebsiteUrl": project_file_contents["processedProjectInfo"].get("contentOfWebsiteUrl"),
            "secInfo": {
               "secJsonContent": sec_info.get("secJsonContent"),
                "secMarkdownContent": sec_info.get("secMarkdownContent"),
                "secRawContent": sec_info.get("secRawContent")
            },
            "startupMetrics": {
               "growthRate": startup_metrics.get("growthRate"),
                "organicVsPaidGrowth": startup_metrics.get("organicVsPaidGrowth"),
                "virality": startup_metrics.get("virality"),
                "networkEffect": startup_metrics.get("networkEffect"),
                "customerAcquisitionCost": startup_metrics.get("customerAcquisitionCost"),
                "unitEconomics": startup_metrics.get("unitEconomics"),
                "retentionRate": startup_metrics.get("retentionRate"),
                "magicMoment": startup_metrics.get("magicMoment"),
                "netPromoterScore": startup_metrics.get("netPromoterScore"),
                "customerLifetimeValue": startup_metrics.get("customerLifetimeValue"),
                "paybackPeriod": startup_metrics.get("paybackPeriod"),
                "revenueGrowth": startup_metrics.get("revenueGrowth"),
                "churnRate": startup_metrics.get("churnRate"),

            },
            "industryDetails": {
                "industryDetailsAndForecast": industry_details.get("industryDetailsAndForecast"),
                "totalAddressableMarket": industry_details.get("totalAddressableMarket"),
                "serviceableAddressableMarket": industry_details.get("serviceableAddressableMarket"),
                "serviceableObtainableMarket": industry_details.get("serviceableObtainableMarket")
            },
            "lastUpdated": project_file_contents["processedProjectInfo"].get("lastUpdated"),
            "status": project_file_contents["processedProjectInfo"].get("status"),
            "startupSummary": project_file_contents["processedProjectInfo"].get("startupSummary")
        },
        "reports": new_reports
    }

    agent_status_file_path = get_project_status_file_path(project_id)
    upload_to_s3(json.dumps(new_project_file_contents, indent=4), agent_status_file_path,
                 content_type="application/json")
    print(
        f"Updated status file: https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/crowd-fund-analysis/{agent_status_file_path}")


def update_report_status_in_progress(project_id: str, report_type: ReportType, triggered_by = ''):
    """
    Updates the `agent-status.json` file in S3 to set a report's status to "in_progress".
    Handles both individual reports and `finalReport`.
    """
    project_file_contents = get_project_file(project_id)
    existing_report_data = project_file_contents["reports"].get(report_type, {})
    
    # Get default values (including "lastTriggeredBy" if provided)
    updated_fields = get_init_data_for_report(report_type, triggered_by)
    
    # Only update fields that exist in `updated_fields`
    for field, value in updated_fields.items():
        existing_report_data[field] = value

    # Ensure status is always updated to IN_PROGRESS
    existing_report_data["status"] = ProcessingStatus.IN_PROGRESS

    # Save updated report data
    project_file_contents["reports"][report_type] = existing_report_data
    
    update_project_file(project_id, project_file_contents)
    print(f"Updated status of report '{report_type}' to 'in_progress'.")

def update_report_with_structured_output(project_id: str, report_type: ReportType, structured_output: StructuredReportResponse):
    report_file_path = f"{project_id}/{report_type.value}.md"

    output_string = generate_markdown_report(structured_output)

    upload_to_s3(output_string, report_file_path)
    # Update status file to "completed"
    markdown_link = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/crowd-fund-analysis/{report_file_path}"
    project_file_contents = get_project_file(project_id)

    report: ReportSchema = project_file_contents["reports"].get(report_type) or get_init_data_for_report(report_type)

    report["status"] = ProcessingStatus.COMPLETED
    report["endTime"] = datetime.now().isoformat()
    report["markdownLink"] = markdown_link
    report["summary"] = structured_output.oneLine_summary
    report["confidence"] = structured_output.confidence
    report["performanceChecklist"] = []
    performance_checklist = structured_output.performance_checklist or []

    for item in performance_checklist:
        new_item = {
            "checklistItem": item.checklist_item,
            "explanation": item.one_line_explanation,
            "score": item.score
        }
        report["performanceChecklist"].append(new_item)



    project_file_contents["reports"][report_type] = report
    # Check if all other reports are completed
    report_statuses = [r["status"] for r in project_file_contents["reports"].values()]
    project_file_contents["status"] = ProcessingStatus.COMPLETED if all(rs == ProcessingStatus.COMPLETED for rs in report_statuses) else ProcessingStatus.IN_PROGRESS

    update_project_file(project_id, project_file_contents)
    print(f"Updated status of report '{report_type}' to 'completed'.")


def update_report_status_completed(project_id: str, report_type: ReportType, markdown_link: str, summary: str):
    """
    Updates the `agent-status.json` file in S3 to set a report's status to "completed" and adds the markdown link.
    Handles both individual reports and `finalReport`.
    """
    project_file_contents = get_project_file(project_id)

    report = project_file_contents["reports"].get(report_type) or get_init_data_for_report(report_type)

    report["status"] = ProcessingStatus.COMPLETED
    report["endTime"] = datetime.now().isoformat()
    report["markdownLink"] = markdown_link
    report["summary"] = summary

    project_file_contents["reports"][report_type] = report
    # Check if all other reports are completed
    report_statuses = [r["status"] for r in project_file_contents["reports"].values()]
    project_file_contents["status"] = ProcessingStatus.COMPLETED if all(rs == ProcessingStatus.COMPLETED for rs in report_statuses) else ProcessingStatus.IN_PROGRESS

    update_project_file(project_id, project_file_contents)
    print(f"Updated status of report '{report_type}' to 'completed'.")


def update_report_status_failed(project_id: str, report_type: ReportType, error_message: str):
    """
    Updates the `agent-status.json` file in S3 to set a report's status to "failed" and logs the error message.
    Handles both individual reports and `finalReport`.
    """
    project_file_contents = get_project_file(project_id)
    report = project_file_contents["reports"].get(report_type) or get_init_data_for_report(report_type)

    report["status"] = ProcessingStatus.FAILED
    report["endTime"] = datetime.now().isoformat()
    report["errorMessage"] = error_message

    project_file_contents["reports"][report_type] = report
    # Set overall project status as failed
    project_file_contents["status"] = ProcessingStatus.FAILED

    update_project_file(project_id, project_file_contents)
    print(f"Updated status of report '{report_type}' to 'failed' with error message: {error_message}")


def update_status_to_not_started_for_all_reports(project_id, triggered_by):
    agent_status_file_path = f"{project_id}/agent-status.json"

    project_file_contents = get_project_file(project_id)

    # Initialize all reports to "in_progress" and set timestamps
    for report_type in ALL_REPORT_TYPES:
        project_file_contents["reports"][report_type] = get_init_data_for_report(report_type, triggered_by)
        print(f"Set status of report '{report_type}' to 'not_started'. Initialized startTime and estimatedTimeInSec.")

    print(f"Set status of report 'finalReport' to 'not_started'. Initialized startTime and estimatedTimeInSec.")
    
    upload_to_s3(json.dumps(project_file_contents, indent=4), agent_status_file_path, content_type="application/json")
    print(
        f"Updated status file: https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/crowd-fund-analysis/{agent_status_file_path}")


def create_report_file_and_upload_to_s3(project_id: str, report_type: ReportType, report_content: str):
    report_file_path = f"{project_id}/{report_type}.md"
    upload_to_s3(report_content, report_file_path)
    # Update status file to "completed"
    markdown_link = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/crowd-fund-analysis/{report_file_path}"
    update_report_status_completed(project_id, report_type, markdown_link=markdown_link)

def fetch_markdown_from_s3(markdown_url: str) -> str:
    """
    Fetches the markdown content from S3 using the provided URL.
    """
    if not markdown_url:
        return ""
    # Extract the S3 key from the URL
    s3_key = markdown_url.replace(f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/", "")

    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        markdown_content = response['Body'].read().decode('utf-8')
        return markdown_content
    except s3_client.exceptions.NoSuchKey:
        print(f"File not found in S3: {s3_key}")
        return ""

def get_combined_reports_from_s3(project_id: str) -> str:
    """
    Fetches all markdown reports (excluding final report) from S3 for a given project
    and returns a single combined markdown string.
    """
    agent_status_file_path = get_project_status_file_path(project_id)

    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"crowd-fund-analysis/{agent_status_file_path}")
        status_data = json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        raise FileNotFoundError(
            f"agent-status.json not found in S3 at path: s3://{BUCKET_NAME}/crowd-fund-analysis/{agent_status_file_path}"
        )
    
    content_sections = []
    
    processed_info = status_data.get("processedProjectInfo", {})

    content_mapping = {
        "Content of Crowdfunding URL": processed_info.get("contentOfCrowdfundingUrl", ""),
        "Content of Website URL": processed_info.get("contentOfWebsiteUrl", ""),
        "SEC Information": processed_info.get("secInfo", {}).get("secMarkdownContent", ""),
    }
    
    # Append extracted content
    for section_title, content in content_mapping.items():
        if content:
            content_sections.append(f"### {section_title}\n\n{content}\n\n---\n")

    # Fetch and append team_info report if available
    team_info_report = status_data.get("reports", {}).get("team_info", {})
    team_info_markdown_link = team_info_report.get("markdownLink")
    
    if team_info_markdown_link:
        team_info_content = fetch_markdown_from_s3(team_info_markdown_link)
        if team_info_content:
            content_sections.append(f"### Team Information\n\n{team_info_content}\n\n---\n")

    return "".join(content_sections).strip()  # Remove trailing newlines


def generate_markdown_report(report: StructuredReportResponse) -> str:
    """
    Generates a Markdown formatted string report.

    The format includes:
      - A summary section.
      - For each checklist item:
          - The item as a heading.
          - informationUsed.
          - detailedExplanation.
          - calculationLogic.
    """
    md_lines = []

    # Add the summary
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append(report.summary)
    md_lines.append("")

    # Add each checklist item with an index
    for i, item in enumerate(report.performance_checklist, start=1):
        # Use the checklist item as a sub-heading with the index and score icon
        score_icon = '✅' if item.score == 1 else '❌'
        md_lines.append(f"### {i}. {score_icon} {item.checklist_item} ")
        md_lines.append("")
        md_lines.append(f"**Information Used:** {item.information_used}")
        md_lines.append("")
        md_lines.append(f"**Detailed Explanation:** {item.detailed_explanation}")
        md_lines.append("")
        md_lines.append(f"**Calculation Logic:** {item.evaluation_logic}")
        md_lines.append("")

    # Join all the lines into a single string
    return "\n".join(md_lines)
