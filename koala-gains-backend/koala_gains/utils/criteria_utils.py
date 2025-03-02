import json
from typing import List
from koala_gains.utils.s3_utils import s3_client, upload_equity_project_to_s3
from koala_gains.structures.criteria_structures import StructuredIndustryGroupCriteriaResponse,IndustryGroupData,IndustryGroupCriteria
from koala_gains.utils.llm_utils import structured_criteria_response
from koala_gains.utils.env_variables import BUCKET_NAME, REGION

def get_industry_group_criteria(sector: str, industry_group: str) -> StructuredIndustryGroupCriteriaResponse:
    """
    Generates a structured report with 6-8 evaluation criteria for a company operating in a specific sector and industry group.
    """

    # Construct the AI prompt
    prompt = f"""
    You are an expert in startup evaluation and industry analysis. Provide 6-8 key criteria 
    to evaluate a company in the {sector} sector and {industry_group} industry group.
    
    Also find some tickers related to industry group {industry_group} and sector {sector}.
    
    Ensure the criteria cover the most relevant aspects such as financial performance, 
    market positioning, operational efficiency, competitive landscape, and regulatory considerations.


    Each criterion should include:
    - Name of the evaluation criteria
    - A short description explaining its importance
    - A list of important metrics that should be considered when evaluating this criterion

    Each report should include:
    - Key of the report
    - Name of the report
    - Description of the report
    - Output type of the report like text or graph if graph also give its type like if text then (Text Report) if any chart like bar chart  give (Bar Chart).
    
    Please ensure their are 6-8 criteria and  are applicable to most companies in this sector/industry group.
    """

    return structured_criteria_response(
        {},
        f"industry_group_criteria_{sector}_{industry_group}",
        prompt
    )


def get_criteria_file(sector:str,industry_group:str) -> IndustryGroupData:
    """
    Fetches and returns the project status data from S3.
    """
    try:
        criteria_file_path = get_criteria_file_path(sector,industry_group)
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key="public-equities/US/gics/" + criteria_file_path)
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        return None
def get_custom_criterias_file() -> List[IndustryGroupCriteria]:
    """
    Fetches and returns the project status data from S3.
    """
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key="public-equities/US/gics/custom-criterias.json")
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        return None
def get_criteria_file_path(sector:str,industry_group:str) -> str:
    """
    Returns the path to the status file for the given project ID.
    """
    return f"{sector}/{industry_group}/ai-criteria.json"

def fetch_criteria_file(equity_details):
    """Fetch the AI criteria file for a given sector and industry group."""
    sector = equity_details.get("sectorName", "").lower().replace(" ", "-")
    industry_group = equity_details.get("industryGroupName", "").lower().replace(" ", "-")
    return get_criteria_file(sector, industry_group), sector, industry_group

def generate_ai_criteria(equity_details, sector, industry_group):
    """Generate AI criteria data using industry group information."""
    industry_group_criteria = get_industry_group_criteria(sector, industry_group)
    return {
        "tickers": industry_group_criteria.tickers,
        "id": equity_details["industryGroupId"],
        "name": equity_details["industryGroupName"],
        "sector": {"id": equity_details["sectorId"], "name": equity_details["sectorName"]},
        "industryGroup": {"id": equity_details["industryGroupId"], "name": equity_details["industryGroupName"]},
        "processedInformation": industry_group_criteria.processedInformation.model_dump()
    }

def upload_ai_criteria_to_s3(final_data, sector, industry_group):
    """Upload AI criteria to S3 and return the S3 URL."""
    s3_key = f"{sector}/{industry_group}/ai-criteria.json"
    upload_equity_project_to_s3(json.dumps(final_data, indent=2), s3_key, content_type="application/json")
    return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/public-equities/US/gics/{s3_key}"

def update_custom_criteria(equity_details, ai_criteria_url):
    """Update the custom-criterias.json file with AI criteria information."""
    custom_criteria = get_custom_criterias_file()
    if not custom_criteria:
        custom_criteria = {"criteria": []}

    found = False
    for criteria in custom_criteria["criteria"]:
        if criteria["sectorId"] == equity_details["sectorId"] and criteria["industryGroupId"] == equity_details["industryGroupId"]:
            criteria["aiCriteriaFileLocation"] = ai_criteria_url
            found = True
            break

    if not found:
        custom_criteria["criteria"].append({
            "sectorId": equity_details["sectorId"],
            "sectorName": equity_details["sectorName"],
            "industryGroupId": equity_details["industryGroupId"],
            "industryGroupName": equity_details["industryGroupName"],
            "aiCriteriaFileLocation": ai_criteria_url
        })

    upload_equity_project_to_s3(json.dumps(custom_criteria, indent=2), "custom-criterias.json", content_type="application/json")
