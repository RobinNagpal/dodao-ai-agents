import json
import traceback
from typing import List

from langchain_core.messages import HumanMessage

from koala_gains.agent_state import MarketDetailPoints, ProcessingStatus, ProcessedProjectInfo, ProcessedSecInfo, \
    SectorDetailPoints, \
    IndustryDetailsAndForecast
from koala_gains.structures.form_c_structures import StructuredFormCResponse
from koala_gains.structures.industry_details import MarketDetailStructure, SectorDetailStructure, \
    IndustryDetailsAndForecastStructure
from koala_gains.utils.llm_utils import get_startup_summary, structured_llm_response, MINI_4_0_CONFIG, \
    scrape_and_clean_content_with_same_details, get_llm, NORMAL_4_0_CONFIG
from koala_gains.utils.project_utils import scrape_urls
from koala_gains.utils.report_utils import MarketDetailSchema, RepopulatableFields, SectorDetailSchema, \
    get_project_status_file_path, ProcessedProjectInfoSchema, \
    ProjectStatusFileSchema, ProjectInfoInputSchema, ProcessedSecInfoSchema, ProcessedIndustryAndForecastsSchema
from koala_gains.utils.s3_utils import s3_client, BUCKET_NAME, upload_to_s3


def get_sec_structured_response(raw_content: str) -> StructuredFormCResponse:
    """
    Convert the raw SEC content to JSON format.
    """
    prompt = """Parse the following Form C document and return it in a structured JSON format based on the provided schema. Ensure that:

    * All fields are extracted correctly.
    * Numerical values are formatted as numbers, and missing values are set to null.
    * Lists are properly structured.
    * The structured output adheres to the schema.
    
    {
      "filing_status": "LIVE",
      "issuer": {
        "name": "Qnetic Corporation",
        "form": "Corporation",
        "jurisdiction": "DELAWARE",
        "incorporation_date": "09-20-2022",
        "physical_address": {
          "address_1": "276 5th Avenue",
          "address_2": "Suite 704 - 3137",
          "city": "New York",
          "state_country": "NEW YORK",
          "postal_code": "10001"
        },
        "website": "http://www.qnetic.energy",
        "is_co_issuer": true,
        "co_issuer": "Qnetic II, a series of Wefunder SPV, LLC"
      },
      "co_issuer": {
        "name": "Qnetic II, a series of Wefunder SPV, LLC",
        "form": "Limited Liability Company",
        "jurisdiction": "DELAWARE",
        "incorporation_date": "10-11-2024",
        "physical_address": {
          "address_1": "4104 24TH ST",
          "address_2": "PMB 8113",
          "city": "San Francisco",
          "state_country": "CALIFORNIA",
          "postal_code": "94114"
        },
        "website": "https://wefunder.com/"
      },
      "offering": {
        "intermediary_name": "Wefunder Portal LLC",
        "intermediary_cik": "0001670254",
        "commission_file_number": "007-00033",
        "crd_number": "283503",
        "compensation": "7.0% of the offering amount upon a successful fundraise...",
        "intermediary_interest": "No",
        "security_type": "Other",
        "security_specification": "Simple Agreement for Future Equity (SAFE)",
        "target_number_of_securities": 50000,
        "price_per_security": 1.00000,
        "price_determination_method": "Pro-rated portion of total principal value...",
        "target_offering_amount": 50000.00,
        "max_offering_amount": 618000.00,
        "oversubscriptions_accepted": true,
        "oversubscription_allocation": "As determined by the issuer",
        "deadline": "04-30-2025"
      },
      "financials": {
        "total_assets": {
          "most_recent": 1374533.00,
          "prior": 63476.00
        },
        "cash_and_equivalents": {
          "most_recent": 1254186.00,
          "prior": 60390.00
        },
        "accounts_receivable": {
          "most_recent": 0.00,
          "prior": 0.00
        },
        "short_term_debt": {
          "most_recent": 248047.00,
          "prior": 91065.00
        },
        "long_term_debt": {
          "most_recent": 1862592.00,
          "prior": 137974.00
        },
        "revenue": {
          "most_recent": 0.00,
          "prior": 0.00
        },
        "cost_of_goods_sold": {
          "most_recent": 0.00,
          "prior": 0.00
        },
        "taxes_paid": {
          "most_recent": 11634.00,
          "prior": 10361.00
        },
        "net_income": {
          "most_recent": -807523.00,
          "prior": -158546.00
        }
      },
      "jurisdictions_offered": [
        "ALABAMA", "ALASKA", "ARIZONA", "ARKANSAS", "CALIFORNIA", "COLORADO", 
        "CONNECTICUT", "DELAWARE", "DISTRICT OF COLUMBIA", "FLORIDA", "GEORGIA",
        "HAWAII", "IDAHO", "ILLINOIS", "INDIANA", "IOWA", "KANSAS", "KENTUCKY",
        "LOUISIANA", "MAINE", "MARYLAND", "MASSACHUSETTS", "MICHIGAN", "MINNESOTA",
        "MISSISSIPPI", "MISSOURI", "MONTANA", "NEBRASKA", "NEVADA", "NEW HAMPSHIRE",
        "NEW JERSEY", "NEW MEXICO", "NEW YORK", "NORTH CAROLINA", "NORTH DAKOTA",
        "OHIO", "OKLAHOMA", "OREGON", "PENNSYLVANIA", "RHODE ISLAND", "SOUTH CAROLINA",
        "SOUTH DAKOTA", "TENNESSEE", "TEXAS", "UTAH", "VERMONT", "VIRGINIA",
        "WASHINGTON", "WEST VIRGINIA", "WISCONSIN", "WYOMING"
      ],
      "signatures": [
        {
          "name": "Michael Pratt",
          "title": "Founder, CEO",
          "date": "10-16-2024"
        },
        {
          "name": "Loic Bastard",
          "title": "Founder, CTO",
          "date": "10-16-2024"
        }
      ]
    }
    
    
    SEC Content:
    """ + raw_content
    structured_llm = get_llm(NORMAL_4_0_CONFIG).with_structured_output(StructuredFormCResponse)
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    return response


def get_sec_info(sec_url: str) -> ProcessedSecInfoSchema:
    raw_content = scrape_and_clean_content_with_same_details(sec_url, NORMAL_4_0_CONFIG)
    json_data = get_sec_structured_response(raw_content)
    markdown_content = get_markdown_content_from_json(json_data.model_dump_json(indent=4))
    return {
        "secJsonContent": json_data.model_dump_json(indent=4),
        "secMarkdownContent": markdown_content,
        "secRawContent": raw_content,
    }


def get_project_industry_and_forecasts_info(project_text: str) -> IndustryDetailsAndForecastStructure:
    print("Getting project industry and forecasts info")
    prompt = """
    You are the expert in investing in startups and have been asked to provide a detailed analysis of the industry 
    and forecasts for the following project. When providing details of the industry, include the overall industry
    information and information about the specific sector the project is in. 
    
    Be as narrow as possible while choosing the sub-sector. Provide detailed how did you choose this sub-sector with
    the industry analysis.
    
    When providing forecasts, consider the growth rate of the sub-sector that matches the project.
    
    You have to be a critical thinker and provide detailed information about the Total addressable market, serviceable
    addressable market, and serviceable obtainable market.
    
    Make sure to consider only the relevant sub-sector while calculating the market sizes.
    
    Dont reply on the information shared in the project details. You have to provide the information based on your own knowledge.
    
    Output the information in a structured format and in the following JSON format: 
    { 
      "sector_details": {
        "basic_info": "Your detailed analysis of the sector/industry.",
        "growth_rate": "Growth rate of the sector/industry"
      },
      "sub_sector_details": {
        "basic_info": "Your detailed analysis of the sub-sector.",
        "growth_rate": "Growth rate of the sub-sector"
      },
      "total_addressable_market": {
        "details": "Total addressable market. Make sure to include the numerical figures.",
        "calculation_logic": "How calculation of the total addressable market was done"
      },
      "serviceable_addressable_market": {
        "details": "Serviceable addressable market. Make sure to include the numerical figures.",
        "calculation_logic": "How calculation of the serviceable addressable market was done"
      },
      "serviceable_obtainable_market": {
        "details": "Serviceable obtainable market. Make sure to include the numerical figures.",
        "calculation_logic": "How calculation of the serviceable obtainable market was done"
      },
      "profit_margins": {
        "details": "Profitability of the sector/industry. Make sure to include the numerical figures.",
        "calculation_logic": "How calculation of the profit margins was done"
      }
    }
    
    """ + project_text

    structured_llm = get_llm(NORMAL_4_0_CONFIG).with_structured_output(IndustryDetailsAndForecastStructure)

    response = structured_llm.invoke([HumanMessage(content=prompt)])
    print(response.model_dump_json(indent=4))
    return response


def get_markdown_content_from_json(json_content: str) -> str:
    prompt = f"""Convert the following JSON content into a tables in markdown format. 
    
    Ensure that the markdown content is well-structured and easy to read.

    {json_content}
    """

    llm = get_llm(NORMAL_4_0_CONFIG)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def convert_sector_structure(sector: SectorDetailStructure) -> SectorDetailSchema:
    return {
        "basicInfo": sector.basic_info,
        "growthRate": sector.growth_rate,
    }


def convert_market_structure(market: MarketDetailStructure) -> MarketDetailSchema:
    return {
        "details": market.details,
        "calculationLogic": market.calculation_logic,
    }


def convert_s3_sector(sector_points_in_s3: SectorDetailSchema) -> SectorDetailPoints:
    if sector_points_in_s3 and isinstance(sector_points_in_s3, dict):
        sector: SectorDetailPoints = {
            "basic_info": sector_points_in_s3.get('basicInfo'),
            "growth_rate": sector_points_in_s3.get('growthRate'),
        }

        return sector
    else:
        return None


def convert_s3_market_points(market_points_in_s3: MarketDetailSchema) -> MarketDetailPoints:
    market: MarketDetailPoints = {
        "details": market_points_in_s3.get('details'),
        "calculation_logic": market_points_in_s3.get('calculationLogic'),
    }

    return market


def convert_s3_processed_info_to_state(project_info_in_s3: ProcessedProjectInfoSchema) -> ProcessedProjectInfo:
    sec_info_in_s3: ProcessedSecInfoSchema = project_info_in_s3.get("secInfo")
    sec_info: ProcessedSecInfo = {
        "sec_json_content": sec_info_in_s3.get("secJsonContent"),
        "sec_markdown_content": sec_info_in_s3.get("secMarkdownContent"),
        "sec_raw_content": sec_info_in_s3.get("secRawContent"),
    }

    industry_details_in_s3: ProcessedIndustryAndForecastsSchema = project_info_in_s3.get("industryDetails")

    industry_details: IndustryDetailsAndForecast = {
        "sector_details": convert_s3_sector(industry_details_in_s3.get("sectorDetails")),
        "sub_sector_details": convert_s3_sector(industry_details_in_s3.get("subSectorDetails")),
        "total_addressable_market": convert_s3_market_points(industry_details_in_s3.get("totalAddressableMarket")),
        "serviceable_addressable_market": convert_s3_market_points(
            industry_details_in_s3.get("serviceableAddressableMarket")),
        "serviceable_obtainable_market": convert_s3_market_points(
            industry_details_in_s3.get("serviceableObtainableMarket")),
        "profit_margins": convert_s3_market_points(industry_details_in_s3.get("profitMargins")),
    }

    processed_info: ProcessedProjectInfo = {
        "additional_urls_used": project_info_in_s3.get("additionalUrlsUsed"),
        "content_of_additional_urls": project_info_in_s3.get("contentOfAdditionalUrls"),
        "content_of_crowdfunding_url": project_info_in_s3.get("contentOfCrowdfundingUrl"),
        "content_of_website_url": project_info_in_s3.get("contentOfWebsiteUrl"),
        "sec_info": sec_info,
        "industry_details": industry_details,

        "last_updated": project_info_in_s3.get("lastUpdated"),
        "status": project_info_in_s3.get("status"),
    }
    return processed_info


def scrape_additional_links_and_update_project_info(
        project_info: ProcessedProjectInfoSchema) -> ProcessedProjectInfoSchema:
    """
    Scrape the URLs in 'project_info' and update the 'processed_project_info' with the scraped content.
    """
    print(
        f"Scraping URLs and updating 'processed_project_info' in S3 for project: {project_info.get('additionalUrlsUsed')}")
    current_urls = project_info.get("additionalUrlsUsed") or []
    scraped_content_list: List[str] = []
    if current_urls:
        scraped_content_list = scrape_urls(current_urls)

    # Combine the general scraped content
    if len(current_urls) > 0:
        combined_scrapped_content = "\n\n".join(scraped_content_list)

        prompt = "Remove the duplicates from the below content, but don't remove any information. Be as detailed as possible. Don't remove any information at all \n\n" + combined_scrapped_content
        content_of_scrapped_urls = structured_llm_response(MINI_4_0_CONFIG, "summarize_scraped_content", prompt)

        project_info["additionalUrlsUsed"] = current_urls
        project_info["contentOfAdditionalUrls"] = content_of_scrapped_urls
    return project_info


def get_agent_status_file_content(agent_status_file_path: str):
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"crowd-fund-analysis/{agent_status_file_path}")
        project_file_contents: ProjectStatusFileSchema = json.loads(response['Body'].read().decode('utf-8'))
        return project_file_contents
    except s3_client.exceptions.NoSuchKey:
        print(traceback.format_exc())
        raise FileNotFoundError(
            f"agent-status.json not found in S3 at path: s3://{BUCKET_NAME}/crowd-fund-analysis/{agent_status_file_path}"
        )


def repopulate_project_field(project_id: str, field: RepopulatableFields):
    """
    Generic function to repopulate a specific field in 'processedProjectInfo'.
    Only updates the specified field and keeps other data intact.
    """
    agent_status_file_path = get_project_status_file_path(project_id)
    project_file_contents = get_agent_status_file_content(agent_status_file_path)
    project_info_in_s3 = project_file_contents.get("processedProjectInfo", {})

    # Gather required text data for some fields
    combined_text = (
            project_info_in_s3.get("contentOfCrowdfundingUrl", "") +
            project_info_in_s3.get("contentOfWebsiteUrl", "") +
            project_info_in_s3.get("secInfo", {}).get("secMarkdownContent", "")
    )

    if field == RepopulatableFields.INDUSTRY_DETAILS.value:
        print("Repopulating industry details...")
        industry_and_forecast_structure = get_project_industry_and_forecasts_info(combined_text)
        project_info_in_s3["industryDetails"] = {
            "sectorDetails": convert_sector_structure(industry_and_forecast_structure.sector_details),
            "subSectorDetails": convert_sector_structure(industry_and_forecast_structure.sub_sector_details),
            "totalAddressableMarket": convert_market_structure(
                industry_and_forecast_structure.total_addressable_market),
            "serviceableAddressableMarket": convert_market_structure(
                industry_and_forecast_structure.serviceable_addressable_market),
            "serviceableObtainableMarket": convert_market_structure(
                industry_and_forecast_structure.serviceable_obtainable_market),
            "profitMargins": convert_market_structure(industry_and_forecast_structure.profit_margins)
        }

    elif field == RepopulatableFields.STARTUP_SUMMARY.value:
        print("Repopulating startup summary...")
        project_info_in_s3["startupSummary"] = get_startup_summary(
            project_info_in_s3.get("contentOfCrowdfundingUrl", "") +
            project_info_in_s3.get("contentOfWebsiteUrl", "")
        )

    elif field == RepopulatableFields.SEC_INFO.value:
        print("Repopulating SEC info...")
        sec_filing_url = project_file_contents.get("projectInfoInput", {}).get("secFilingUrl", "").strip()
        project_info_in_s3["secInfo"] = get_sec_info(sec_filing_url)

    elif field == RepopulatableFields.CROWDFUNDING_CONTENT.value:
        print("Repopulating crowdfunding content...")
        project_input = project_file_contents.get("projectInfoInput", {})
        project_info_in_s3["contentOfCrowdfundingUrl"] = scrape_and_clean_content_with_same_details(
            project_input.get("crowdFundingUrl")
        )

    elif field == RepopulatableFields.WEBSITE_CONTENT.value:
        print("Repopulating website content...")
        project_input = project_file_contents.get("projectInfoInput", {})
        project_info_in_s3["contentOfWebsiteUrl"] = scrape_and_clean_content_with_same_details(
            project_input.get("websiteUrl")
        )

    # Save back to S3
    project_file_contents["processedProjectInfo"] = project_info_in_s3
    upload_to_s3(json.dumps(project_file_contents, indent=4), f"{project_id}/agent-status.json", "application/json")

    print(f"Repopulated '{field}' uploaded to S3 for project {project_id}.")


def is_industry_details_missing(project_info: ProcessedProjectInfoSchema) -> bool:
    """
    Check if 'industryDetails' is missing in 'processedProjectInfo'.
    """
    industry_details = project_info.get("industryDetails")
    if industry_details is None:
        return True

    sector_details = industry_details.get("sectorDetails")
    if sector_details is None or not  isinstance(sector_details, dict):
        return True

    sector_basic_info = industry_details.get("sectorDetails").get("basicInfo")
    if sector_basic_info is None:
        return True

    sub_sector_details = industry_details.get("subSectorDetails")
    if sub_sector_details is None:
        return True

    sub_sector_basic_info = industry_details.get("subSectorDetails").get("basicInfo")
    if sub_sector_basic_info is None:
        return True

    total_addressable_market = industry_details.get("totalAddressableMarket")
    if total_addressable_market is None:
        return True

    serviceable_addressable_market = industry_details.get("serviceableAddressableMarket")
    if serviceable_addressable_market is None:
        return True

    serviceable_obtainable_market = industry_details.get("serviceableObtainableMarket")
    if serviceable_obtainable_market is None:
        return True

    profit_margins = industry_details.get("profitMargins")
    if profit_margins is None:
        return True


def is_content_of_additional_urls_missing(project_input: ProjectInfoInputSchema,
                                          project_info: ProcessedProjectInfoSchema) -> bool:
    """
    Check if 'contentOfAdditionalUrls' is missing in 'processedProjectInfo'.
    """
    if project_input.get("additionalUrls") is None:
        return False

    if len(project_input.get("additionalUrls")) == 0:
        return False

    if project_input.get("additionalUrls") == project_info.get("additionalUrlsUsed") and project_info.get(
            "contentOfAdditionalUrls") is not None:
        return False

    return True


def is_content_of_crowdfunding_url_missing(project_input: ProjectInfoInputSchema,
                                           project_info: ProcessedProjectInfoSchema) -> bool:
    """
    Check if 'contentOfCrowdfundingUrl' is missing in 'processedProjectInfo'.
    """
    if project_input.get("crowdFundingUrl") is None:
        return False

    if project_input.get("crowdFundingUrl") == project_info.get("contentOfCrowdfundingUrl") and project_info.get(
            "contentOfCrowdfundingUrl") is not None:
        return False

    return True


def is_content_of_website_url_missing(project_input: ProjectInfoInputSchema,
                                      project_info: ProcessedProjectInfoSchema) -> bool:
    """
    Check if 'contentOfWebsiteUrl' is missing in 'processedProjectInfo'.
    """
    if project_input.get("websiteUrl") is None:
        return False

    if project_input.get("websiteUrl") == project_info.get("contentOfWebsiteUrl") and project_info.get(
            "contentOfWebsiteUrl") is not None:
        return False

    return True


def ensure_processed_project_info(project_id: str, generate_all: bool = False) -> ProcessedProjectInfo:
    """
    Ensures that 'processed_project_info' is present in agent-status.json in S3.
    This function checks if the URLs have changed. If they haven't and 'processed_project_info'
    exists, it does nothing. If they have changed (or don't exist), it scrapes the URLs again,
    then updates and uploads the new content back to S3.

    Returns the updated 'processed_project_info' from the status file.
    """
    # ----------------------- 1) Download agent-status.json -----------------------
    agent_status_file_path = get_project_status_file_path(project_id)
    project_file_contents = get_agent_status_file_content(agent_status_file_path)

    # ----------------------- 2) Gather the current URLs -------------------------
    project_input: ProjectInfoInputSchema = project_file_contents.get("projectInfoInput", {})
    sec_filing_url = project_input.get("secFilingUrl", "").strip()
    additional_urls = project_input.get("additionalUrls", [])

    # Combine all project-related URLs (except the SEC link, which we'll handle separately if needed)
    current_urls = []
    if additional_urls:
        current_urls.extend(additional_urls)

    # Sort for stable comparison
    current_urls_sorted = sorted(set(current_urls))

    project_info_in_s3: ProcessedProjectInfoSchema = project_file_contents.get("processedProjectInfo", {})
    previous_urls = project_info_in_s3.get("additionalUrlsUsed") or []

    # Also sort for stable comparison
    previous_urls_sorted = sorted(set(previous_urls))

    urls_changed = (current_urls_sorted != previous_urls_sorted)
    print(f"URLs Changed: {urls_changed}")
    needs_processing = (generate_all or
                        project_info_in_s3 is None
                        or urls_changed
                        or project_info_in_s3.get("status") != ProcessingStatus.COMPLETED
                        or is_content_of_crowdfunding_url_missing(project_input, project_info_in_s3)
                        or is_content_of_website_url_missing(project_input, project_info_in_s3)
                        or is_content_of_additional_urls_missing(project_input, project_info_in_s3)
                        or project_info_in_s3.get("secInfo") is None
                        or is_industry_details_missing(project_info_in_s3)
                        or project_info_in_s3.get("startupSummary") is None
                        )

    print(f"Project Info Needs Processing: {needs_processing}")

    if needs_processing:
        changed_dict = {
            "generate_all": generate_all,
            "project_info_in_s3": project_info_in_s3 is None,
            "urls_changed": urls_changed,
            "project_info_in_s3_status": project_info_in_s3.get("status"),
            "is_content_of_crowdfunding_url_missing": is_content_of_crowdfunding_url_missing(project_input,
                                                                                             project_info_in_s3),
            "is_content_of_website_url_missing": is_content_of_website_url_missing(project_input, project_info_in_s3),
            "is_content_of_additional_urls_missing": is_content_of_additional_urls_missing(project_input,
                                                                                           project_info_in_s3),
            "is_industry_details_missing": is_industry_details_missing(project_info_in_s3),
            "startup_summary_missing": project_info_in_s3.get("startupSummary") is None
        }
        print(f"Need Processing because of the following reasons: {changed_dict}")

    if not generate_all and not needs_processing:
        print("Project Info is up-to-date. No need to re-scrape project URLs.")
        return convert_s3_processed_info_to_state(project_info_in_s3)

    if generate_all or (urls_changed
                        or project_info_in_s3.get("status") != ProcessingStatus.COMPLETED
                        or project_info_in_s3.get("contentOfAdditionalUrls") is None
                        or project_info_in_s3.get("contentOfAdditionalUrls") == ""):
        print("URLs have changed or 'processed_project_info' is incomplete. Re-scraping URLs.")
        project_info_in_s3 = scrape_additional_links_and_update_project_info(project_info_in_s3)

    if generate_all or (project_info_in_s3.get("contentOfCrowdfundingUrl") is None or project_info_in_s3.get(
            "contentOfCrowdfundingUrl") == ""):
        print("Crowd Funding Website Content is missing. Scraping Crowd Funding URL.")
        project_info_in_s3["contentOfCrowdfundingUrl"] = scrape_and_clean_content_with_same_details(
            project_input.get("crowdFundingUrl"))

    if generate_all or project_info_in_s3.get("contentOfWebsiteUrl") is None or project_info_in_s3.get(
            "contentOfWebsiteUrl") == "":
        print("Website Content is missing. Scraping Website URL.")
        project_info_in_s3["contentOfWebsiteUrl"] = scrape_and_clean_content_with_same_details(
            project_input.get("websiteUrl"))

    if generate_all or project_info_in_s3.get("secInfo") is None or project_info_in_s3.get("secInfo").get(
            "secMarkdownContent") is None or project_info_in_s3.get("secInfo").get("secMarkdownContent") == "":
        print("SEC Info is missing. Scraping SEC Filing URL.")
        project_info_in_s3["secInfo"] = get_sec_info(sec_filing_url)

    crowd_funding_and_website_content = project_info_in_s3.get("contentOfCrowdfundingUrl") + project_info_in_s3.get(
        "contentOfWebsiteUrl")
    combined_text = crowd_funding_and_website_content + project_info_in_s3.get("secInfo").get("secMarkdownContent")

    if generate_all or is_industry_details_missing(project_info_in_s3):
        print("Industry Details are missing. Scraping Industry Details.")
        industry_and_forecast_structure = get_project_industry_and_forecasts_info(
            combined_text
        )
        sector_details: SectorDetailSchema = convert_sector_structure(industry_and_forecast_structure.sector_details)
        sub_sector_details: SectorDetailSchema = convert_sector_structure(
            industry_and_forecast_structure.sub_sector_details)
        total_addressable_market: MarketDetailSchema = convert_market_structure(
            industry_and_forecast_structure.total_addressable_market)
        serviceable_addressable_market: MarketDetailSchema = convert_market_structure(
            industry_and_forecast_structure.serviceable_addressable_market)
        serviceable_obtainable_market: MarketDetailSchema = convert_market_structure(
            industry_and_forecast_structure.serviceable_obtainable_market)
        profit_margins: MarketDetailSchema = convert_market_structure(industry_and_forecast_structure.profit_margins)
        project_info_in_s3["industryDetails"] = {
            "sectorDetails": sector_details,
            "subSectorDetails": sub_sector_details,
            "totalAddressableMarket": total_addressable_market,
            "serviceableAddressableMarket": serviceable_addressable_market,
            "serviceableObtainableMarket": serviceable_obtainable_market,
            "profitMargins": profit_margins
        }

    # or check any of the fields in none
    if generate_all or (
            project_info_in_s3.get("startupSummary") is None or project_info_in_s3.get("startupSummary") == ""):
        print("Startup Summary is missing. Generating Startup Summary.")
        project_info_in_s3["startupSummary"] = get_startup_summary(crowd_funding_and_website_content)

    project_file_contents["processedProjectInfo"] = project_info_in_s3
    upload_to_s3(
        content=json.dumps(project_file_contents, indent=4),
        s3_key=f"{project_id}/agent-status.json",
        content_type="application/json"
    )
    print(
        f"Updated 'processed_project_info' uploaded to https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/crowd-fund-analysis/{agent_status_file_path}")

    return convert_s3_processed_info_to_state(project_info_in_s3)
