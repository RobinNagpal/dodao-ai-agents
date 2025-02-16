import traceback

from cf_analysis_agent.agent_state import AgentState, get_combined_content, ReportType
from cf_analysis_agent.structures.report_structures import StructuredReportResponse
from cf_analysis_agent.utils.llm_utils import structured_report_response
from cf_analysis_agent.utils.prompt_utils import create_prompt_for_checklist
from cf_analysis_agent.utils.report_utils import update_report_status_failed, \
    update_report_status_in_progress, update_report_with_structured_output


def generate_valuation_report(state: AgentState) -> StructuredReportResponse:
    """
    Uses the LLM to perform critical valuation analysis of the startup:
      - Detailed TAM, SAM, SOM analysis specific to the startup's sector
      - Traction validation with realistic numbers
      - Team evaluation and progress assessment
      - Critical analysis of startup's claims
    """
    combined_content = get_combined_content(state)

    # Prompt for comprehensive valuation analysis
    prompt = f"""
    You are an expert startup valuation analyst. Analyze that the valuation set by the company for the crowdfunding round is fair or not:
    
    When considering the valuation consider 
    1. Total Addressable Market (TAM)
    2. Serviceable Available Market (SAM) 
    3. Serviceable Obtainable Market (SOM)
    
    Based on the information available, calculate 
    1. Yearly revenue based valuation using realistic revenue projections. Do it next 1, 3, and 5 years.
    2. Calculate the profit margins and the profits which can be generated in the next 1, 3, and 5 years.
    
    Then based on this information calculate the valuation.
    
    Then rate the valuation set by the company for the crowdfunding round on the following criteria:
    1. Valuation based on the type of industry, sector, and the market size.
    2. Valuation based on the traction and progress of the startup.
    3. Valuation based on TAM, SAM, and SOM.
    4. Valuation based on the yearly revenue in next 1, 3, and 5 years.
    5. Valuation based on the profit margins and profits which can be generated in the next 1, 3, and 5 years

    Make sure to use as much numerical data as possible to make your analysis more accurate.
    
    Return final valuation analysis only.
    
    {create_prompt_for_checklist('Company Valuation')}
    
    Here is the information you have about the startup:
    {combined_content}
    
    
    Make sure to evaluate if the valuation set by the company for the crowdfunding round is fair or not. Make sure to
    consider realistic yearly current and projected ARR 
    """

    return structured_report_response(
        state.get("config"),
        "detailed_valuation_report",
        prompt
    )

def create_valuation_report(state: AgentState) -> None:
    print("Generating valuation report")
    project_id = state.get("project_info").get("project_id")
    try:
        update_report_status_in_progress(project_id, ReportType.VALUATION)
        report_output = generate_valuation_report(state)
        update_report_with_structured_output(project_id, ReportType.VALUATION, report_output)
    except Exception as e:
        print(traceback.format_exc())
        error_message = str(e)
        print(f"An error occurred:\n{error_message}")
        update_report_status_failed(
            project_id,
            ReportType.VALUATION,
            error_message=error_message
        )
