import traceback

from cf_analysis_agent.agent_state import AgentState, get_combined_content, ReportType
from cf_analysis_agent.structures.report_structures import StructuredReportResponse
from cf_analysis_agent.utils.llm_utils import structured_report_response
from cf_analysis_agent.utils.prompt_utils import create_prompt_for_checklist
from cf_analysis_agent.utils.report_utils import update_report_status_failed, \
    update_report_status_in_progress, update_report_with_structured_output


def generate_financial_health_report(state: AgentState) -> StructuredReportResponse:
    """
    Analyzes the company's financial health based on SEC Form C filings and industry comparisons:
      - Historical spending analysis
      - Burn rate and runway calculations
      - Fund utilization efficiency
      - Industry benchmark comparisons
      - New funds allocation clarity
    """
    combined_content = get_combined_content(state)

    sector_info = state.get("processed_project_info").get('industry_details').get('sector_details').get('basic_info')
    sub_sector_info = state.get("processed_project_info").get('industry_details').get('sub_sector_details').get('basic_info')
    
    prompt = f"""
    You are an expert startup valuation analyst. Analyze that the financial health claimed by the startup is good or not:

    Make sure to be conservative based on the sales and the progress the startup has done so far. Make sure to include numerical data to support your analysis.

    Then rate the financial health and also explain if the financial health is bad, okay or great:
    1. Yearly revenue of the startup and the growth rate of the revenue. Make sure to include numerical data to support your analysis.
    2. The burn rate of the startup and the runway of the startup. Compare it with the industry benchmarks. Make sure to include numerical data to support your analysis.
    3. The fund utilization efficiency of the startup. Do historical spending analysis and compare with industry benchmarks. Make sure to include numerical data to support your analysis.
    4  The clarity of the new funds allocation. Make sure to include numerical data to support your analysis.
    5. Runway of the startup. Make sure to include numerical data to support your analysis.    
    Make sure to evaluate on these criteria and to use as much numerical data as possible to make your analysis more accurate.
    
    Make sure to be conservative based on the sales and the progress the startup has done so far. Make sure to include numerical data to support your analysis.
    
    Make sure to include numerical data for each of the points support your analysis.
    
    Here is some information related to the sector of such a startup:
    {sub_sector_info}

    
    {create_prompt_for_checklist('Financial Health of the startup')}
    
    Here is the information you have about the startup:
    
    {combined_content}
    """

    return structured_report_response(
        state.get("config"),
        "detailed_financial_health_report",
        prompt
    )


def create_financial_health_report(state: AgentState) -> None:
    print("Generating financial health report")
    project_id = state.get("project_info").get("project_id")
    try:
        update_report_status_in_progress(project_id, ReportType.FINANCIAL_HEALTH)
        report_output = generate_financial_health_report(state)
        update_report_with_structured_output(project_id, ReportType.FINANCIAL_HEALTH, report_output)
    except Exception as e:
        print(traceback.format_exc())
        error_message = str(e)
        print(f"An error occurred:\n{error_message}")
        update_report_status_failed(
            project_id,
            ReportType.FINANCIAL_HEALTH,
            error_message=error_message
        )
