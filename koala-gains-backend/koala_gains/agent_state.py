import json
from enum import Enum
from typing import Annotated, List, Optional
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ProcessingStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class InformationStatus(str, Enum):
    MISSING = "missing"  # No clue at all, and it can"t be derived
    DERIVED = "derived"  # Not mentioned explicitly but can be inferred or extrapolated
    EXTRACTED = "extracted"  # Explicitly mentioned in the content
    NOT_APPLICABLE = "not_applicable"  # Not applicable for the given context


class ReportType(str, Enum):
    GENERAL_INFO = ("general_info",)
    FOUNDER_AND_TEAM = ("founder_and_team",)
    TRACTION = ("traction",)
    MARKET_OPPORTUNITY = ("market_opportunity",)
    VALUATION = ("valuation",)
    EXECUTION_AND_SPEED = ("execution_and_speed",)
    FINANCIAL_HEALTH = ("financial_health",)
    RELEVANT_LINKS = "relevant_links"
    FINAL = "final"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class Configurable(TypedDict):
    model: str


class Config(TypedDict):
    configurable: Configurable


class ProjectInfo(TypedDict):
    project_name: str
    crowdfunding_link: str
    website_url: str
    latest_sec_filing_link: str
    additional_links: list
    project_id: str


class ProcessedSecInfo(TypedDict):
    sec_json_content: str
    sec_markdown_content: str
    sec_raw_content: str


class SectorDetailPoints(TypedDict):
    basic_info: str
    growth_rate: str


class MarketDetailPoints(TypedDict):
    details: str
    calculation_logic: str


class IndustryDetailsAndForecast(TypedDict):
    sector_details: SectorDetailPoints
    sub_sector_details: SectorDetailPoints
    total_addressable_market: MarketDetailPoints
    serviceable_addressable_market: MarketDetailPoints
    serviceable_obtainable_market: MarketDetailPoints
    profit_margins: MarketDetailPoints


class ProcessedProjectInfo(TypedDict, total=False):
    additional_urls_used: Optional[list[str]]
    content_of_additional_urls: Optional[str]
    content_of_crowdfunding_url: str
    content_of_website_url: str
    sec_info: ProcessedSecInfo
    industry_details: IndustryDetailsAndForecast
    last_updated: str
    status: ProcessingStatus


class FinalReport(TypedDict):
    final_report_contents: str
    spider_graph_json_file_url: str | None


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    project_info: ProjectInfo
    report_input: str
    reports_to_generate: List[str] | None
    processed_project_info: ProcessedProjectInfo | None
    config: Config
    final_report: FinalReport | None


def get_combined_content_for_valuation(state: AgentState) -> str:
    processes_project_info: ProcessedProjectInfo = state.get("processed_project_info")
    content_of_additional_urls = processes_project_info.get(
        "content_of_additional_urls"
    )
    content_of_crowdfunding_url = processes_project_info.get(
        "content_of_crowdfunding_url"
    )
    content_of_website_url = processes_project_info.get("content_of_website_url")

    combined_content = f"""
    {content_of_crowdfunding_url}
    
    
    {content_of_website_url}
    
    
    {content_of_additional_urls}  
    """
    return combined_content


def get_combined_content(state: AgentState) -> str:
    """
    Combines all the content from different reports into a single report.
    """
    processes_project_info: ProcessedProjectInfo = state.get("processed_project_info")
    content_of_additional_urls = processes_project_info.get(
        "content_of_additional_urls"
    )
    content_of_crowdfunding_url = processes_project_info.get(
        "content_of_crowdfunding_url"
    )
    content_of_website_url = processes_project_info.get("content_of_website_url")

    sec_markdown_content = processes_project_info.get("sec_info").get(
        "sec_markdown_content"
    )

    industry_details_and_forecast: IndustryDetailsAndForecast = (
        processes_project_info.get("industry_details")
    )

    combined_content = f"""
    {content_of_crowdfunding_url}
    
    
    {content_of_website_url}
    
    
    {content_of_additional_urls} 
    
    
    {sec_markdown_content} 
    
    
    {json.dumps(industry_details_and_forecast.get('sector_details'))} 
    {json.dumps(industry_details_and_forecast.get('sub_sector_details'))} 
    """
    return combined_content
