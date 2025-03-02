import traceback

from koala_gains.agent_state import (
    AgentState,
    get_combined_content,
    ReportType,
    get_combined_content_for_valuation,
)
from koala_gains.structures.report_structures import StructuredReportResponse
from koala_gains.utils.llm_utils import structured_report_response
from koala_gains.utils.prompt_utils import create_prompt_for_checklist
from koala_gains.utils.report_utils import (
    update_report_status_failed,
    update_report_status_in_progress,
    update_report_with_structured_output,
)


def generate_valuation_report(state: AgentState) -> StructuredReportResponse:
    """
    Uses the LLM to perform critical valuation analysis of the startup:
      - Detailed TAM, SAM, SOM analysis specific to the startup's sector
      - Traction validation with realistic numbers
      - Team evaluation and progress assessment
      - Critical analysis of startup's claims
    """
    combined_content = get_combined_content_for_valuation(state)
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

    # Prompt for comprehensive valuation analysis
    prompt = f"""
    You are an expert startup valuation analyst. Analyze that the valuation set by the company for the crowdfunding round is fair or not:
    
    Then rate the valuation set by the company for the crowdfunding round on the following criteria and also explain 
    if the valuation is justified, undervalued or overvalued:
    1. Valuation based on the type of industry, sector, and the market size (TAM, SAM, and SOM). Make sure to include numerical data to support your analysis.
    2. Valuation based on the traction and progress of the startup i.e. the traction the startup has achieved so far. Make sure to include numerical data to support your analysis.
    3. Valuation based on the past sales the startup has achieved so far. Make to find and consider only the sales done so far. Make sure to include numerical data to support your analysis.
    4. Valuation based on the realistic revenue in next 1, 3, and 5 years. This should be realistic and conservative. Make sure to include numerical data to support your analysis.
    5. Valuation based on the realistic profit margins and profits which can be generated in the next 1, 3, and 5 years. This should be realistic and conservative. Make sure to include numerical data to support your analysis.

    Make sure to evaluate on these criteria and to use as much numerical data as possible to make your analysis more accurate.
    
    Make sure to include numerical data for each of the points support your analysis.

    Here is some information related to the sector of such a startup:
    {sector_info}
    
    Here is some information related to the sector of such a startup:
    {sub_sector_info}
    
    {create_prompt_for_checklist('Company Valuation')}

    for TAM, SAM, SOM, and profit margins consider the following:
    - TAM: {tam}
    - SAM: {sam}
    - SOM: {som}
    - Profit Margins: {pm} 

    Here is the information you have about the startup:
    {combined_content}
    
    
    Make sure to evaluate if the valuation set by the company for the crowdfunding round is fair or not. Make sure to
    consider realistic yearly current and projected ARR 
    """

    return structured_report_response(
        state.get("config"), "detailed_valuation_report", prompt
    )


def create_valuation_report(state: AgentState) -> None:
    print("Generating valuation report")
    project_id = state.get("project_info").get("project_id")
    try:
        update_report_status_in_progress(project_id, ReportType.VALUATION)
        report_output = generate_valuation_report(state)
        update_report_with_structured_output(
            project_id, ReportType.VALUATION, report_output
        )
    except Exception as e:
        print(traceback.format_exc())
        error_message = str(e)
        print(f"An error occurred:\n{error_message}")
        update_report_status_failed(
            project_id, ReportType.VALUATION, error_message=error_message
        )
