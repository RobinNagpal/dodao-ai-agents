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


def generate_market_opportunity_report(state: AgentState) -> StructuredReportResponse:
    """
    Uses the LLM to critically evaluate market opportunity including TAM, SAM, SOM analysis
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

    tam = (
        state.get("processed_project_info")
        .get("industry_details")
        .get("total_addressable_market")
        .get("details")
    )
    sam = (
        state.get("processed_project_info")
        .get("industry_details")
        .get("serviceable_addressable_market")
        .get("details")
    )
    som = (
        state.get("processed_project_info")
        .get("industry_details")
        .get("serviceable_obtainable_market")
        .get("details")
    )
    pm = (
        state.get("processed_project_info")
        .get("industry_details")
        .get("total_addressable_market")
        .get("details")
    )

    prompt = f"""
    You are an expert startup investor. Analyze that the market opportunity that can be captured by this startup:
    
    Make sure to be conservative based on the sales and the progress the startup has done so far. Make sure to include numerical data to support your analysis.
    
    Then rate the market opportunity on the following parameters and also explain:
    1. Total Addressable Market (TAM), Serviceable Available Market (SAM) applicable to this startup specifically. 
       Make sure to include numerical data to support your analysis.
    2. Serviceable Obtainable Market (SOM) and Unique value proposition applicable to this startup specifically. Make sure to consider the 
       sales done in the past by the startup to calculate this. Consider the real sales done so far to calculate this. 
       Make sure to include numerical data to support your analysis.
    3. Competition in the sector and how the startup is positioned in the sector. How many other startups are there. How 
       much money is needed etc. If there are multiple 200M+ startups in the sector, then the competition is high. Make sure 
       to include numerical data to support your analysis. Make sure to consider the amount of money needed to compete in the
       sector.
    4. Profit margins of the startup and other startups in this sector. Make sure to include numerical data to support your analysis.
    5. The growth rate of the startup in terms of users, customers, and revenue. Make sure to consider for this sector and not take the 
       sector's growth rate as such. Consider the real sales done so far to calculate this. We should calculate this conservatively. Make sure 
       to include numerical data to support your analysis.
    
    Make sure to evaluate on these criteria and to use as much numerical data as possible to make your analysis more accurate.
    
    Make sure to include numerical data for each of the points support your analysis.

    For sector based TAM, SAM, SOM, and profit margins consider the following:
    - TAM: {tam}
    - SAM: {sam}
    - SOM: {som}
    - Profit Margins: {pm} 
    Make sure you evaluate the TAM, SAM, SOM, and profit margins based this sector and explain how this startup compares to the sector. We just dont
    want to take the same numbers as the sector but we want to evaluate the startup based on specific things applicable to the startup.
    
    {create_prompt_for_checklist('Market opportunity of the startup')}

    Make sure to be conservative based on the sales and the progress the startup has done so far. Make sure to include numerical data to support your analysis.
    
    Here is the information you have about the startup:
    
    {combined_content}
    """

    return structured_report_response(
        state.get("config"), "detailed_market_opportunity_report", prompt
    )


def create_market_opportunity_report(state: AgentState) -> None:
    print("Generating market opportunity report")
    project_id = state.get("project_info").get("project_id")
    try:
        update_report_status_in_progress(project_id, ReportType.MARKET_OPPORTUNITY)
        report_output = generate_market_opportunity_report(state)
        update_report_with_structured_output(
            project_id, ReportType.MARKET_OPPORTUNITY, report_output
        )
    except Exception as e:
        print(traceback.format_exc())
        error_message = str(e)
        print(f"An error occurred:\n{error_message}")
        update_report_status_failed(
            project_id, ReportType.MARKET_OPPORTUNITY, error_message=error_message
        )
