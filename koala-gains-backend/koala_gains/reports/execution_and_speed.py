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


def generate_execution_and_speed_report(state: AgentState) -> StructuredReportResponse:
    """
    Analyzes the company's execution speed and milestone achievement:
      - Key milestone tracking and timeline analysis
      - Development velocity metrics
      - Team productivity benchmarks
      - Industry-specific pace comparisons
      - Bottleneck identification
    """
    combined_content = get_combined_content(state)

    sector_info = (
        state.get("processed_project_info")
        .get("industry_details")
        .get("sector_details")
        .get("basic_info")
    )
    sub_sector_info = (
        state.get("processed_project_info")
        .get("industry_details")
        .get("sub_sector_details")
        .get("basic_info")
    )

    # Prompt to instruct the LLM to focus only on traction
    prompt = f"""
    You are an expert startup valuation and assessment analyst. Analyze that the speed and progress claimed by the startup is good or not:
    
    Make sure to be conservative based on the sales and the progress the startup has done so far. Make sure to include numerical data to support your analysis.

    Then rate the execution and speed, and also explain if the speed is bad, okay or great:
    1. Evidence of market validation (pilots, LOIs, testimonials) and number of overall reach of users or customers done so far. Make sure to 
       include numerical data to support your analysis.
    2. Amount of real paid order or customers that the startup has achieved so far(in the past), and in how much time. Make sure to include numerical data to support your analysis.   
    3. Number of iterations and the progress done on the product or service done so far. Make sure to include numerical data to support your analysis. 
    4. Speed of growth of the startup in terms of overall progress, customers, and revenue. When did the startup start, and from the time it started to now how much progress it has made. 
       Make sure to include numerical data to support your analysis.
    5. How does the progress compare to other incumbents in the industry? Based on the current progress can the startup compete with the incumbents in in the next 1, 3, and 5 years.
       This should be based on the progress startup has made so far. Make sure to include numerical data to support your analysis.
    
    Make sure to evaluate on these criteria and to use as much numerical data as possible to make your analysis more accurate.
    
    Make sure to be conservative based on the sales and the progress the startup has done so far. Make sure to include numerical data to support your analysis.
    
    Make sure to include numerical data for each of the points support your analysis.

    Here is some information related to the sector of such a startup:
    {sector_info}
    
    Here is some information related to the sector of such a startup:
    {sub_sector_info}

    
    {create_prompt_for_checklist('Execution and Speed of the startup')}
    
    Here is the information you have about the startup:
    
    {combined_content}
    """

    return structured_report_response(
        state.get("config"), "detailed_traction_report", prompt
    )

    return structured_report_response(
        state.get("config"), "detailed_execution_speed_report", prompt
    )


def create_execution_and_speed_report(state: AgentState) -> None:
    print("Generating execution and speed report")
    project_id = state.get("project_info").get("project_id")
    try:
        update_report_status_in_progress(project_id, ReportType.EXECUTION_AND_SPEED)
        report_output = generate_execution_and_speed_report(state)
        update_report_with_structured_output(
            project_id, ReportType.EXECUTION_AND_SPEED, report_output
        )
    except Exception as e:
        print(traceback.format_exc())
        error_message = str(e)
        print(f"An error occurred:\n{error_message}")
        update_report_status_failed(
            project_id, ReportType.EXECUTION_AND_SPEED, error_message=error_message
        )
