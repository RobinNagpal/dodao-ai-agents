import json
from typing import List
from cf_analysis_agent.utils.s3_utils import s3_client, BUCKET_NAME
from cf_analysis_agent.structures.criteria_structures import StructuredIndustryGroupCriteriaResponse,IndustryGroupData,IndustryGroupCriteria
from cf_analysis_agent.utils.llm_utils import structured_criteria_response


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
