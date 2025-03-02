import traceback

from koala_gains.agent_state import AgentState, get_combined_content, ReportType
from koala_gains.structures.report_structures import StructuredReportResponse
from koala_gains.utils.llm_utils import structured_report_response
from koala_gains.utils.prompt_utils import create_prompt_for_checklist
from koala_gains.utils.report_utils import (
    create_report_file_and_upload_to_s3,
    update_report_status_failed,
    update_report_status_in_progress,
    update_report_with_structured_output,
)


def generate_traction_report(state: AgentState) -> StructuredReportResponse:
    """
    Uses the LLM to evaluate traction gained by the startup:
      - If no traction is found, explicitly state that there is no traction.
      - If there is traction, indicate how strong it is, referencing
        the startup's industry and sector.
      - Explain how this conclusion was reached based on the provided content.
    """
    combined_content = get_combined_content(state)

    industry_details = state.get("processed_project_info").get("industry_details")
    sector_info = industry_details.get("sector_details").get("basic_info")
    sub_sector_info = industry_details.get("sub_sector_details").get("basic_info")

    # Prompt to instruct the LLM to focus only on traction
    prompt = f"""
    You are an expert startup valuation analyst. Analyze that the traction claimed by the startup is good or not:

    Make sure to be conservative based on the sales and the progress the startup has done so far. Make sure to include numerical data to support your analysis.

    Then rate the traction and also explain if the traction is bad, okay or great:
    1. Evidence of market validation (pilots, LOIs, testimonials) and number of overall reach of users or customers done so far. Make sure to include numerical data to support your analysis.
    2. Number of paying users or customers that the startup has achieved so far. Make sure to include numerical data to support your analysis.
    3. The revenue generated so far by the startup. Make sure to include numerical data to support your analysis.
    4. The growth rate of the startup in terms of users, customers, and revenue. Make sure to include numerical data to support your analysis.
    5. The partnerships and collaborations the startup has achieved so far. Make sure to include numerical data to support your analysis.
    
    Make sure to evaluate on these criteria and to use as much numerical data as possible to make your analysis more accurate.
    
    Make sure to be conservative based on the sales and the progress the startup has done so far. Make sure to include numerical data to support your analysis.
    
    Make sure to include numerical data for each of the points support your analysis.

    Here is some information related to the sector of such a startup:
    {sector_info}
    
    Here is some information related to the sector of such a startup:
    {sub_sector_info}

    
    {create_prompt_for_checklist('Traction of the startup')}
    
    Here is the information you have about the startup:
    
    {combined_content}
    """

    return structured_report_response(
        state.get("config"), "detailed_traction_report", prompt
    )


def create_traction_report(state: AgentState) -> None:
    print("Generating traction report")
    project_id = state.get("project_info").get("project_id")
    try:
        update_report_status_in_progress(project_id, ReportType.TRACTION)
        report_output = generate_traction_report(state)
        update_report_with_structured_output(
            project_id, ReportType.TRACTION, report_output
        )
    except Exception as e:
        # Capture full stack trace
        print(traceback.format_exc())
        error_message = str(e)
        print(f"An error occurred:\n{error_message}")
        update_report_status_failed(
            project_id, ReportType.TRACTION, error_message=error_message
        )
