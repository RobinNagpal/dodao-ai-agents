import json
from cf_analysis_agent.utils.s3_utils import s3_client, BUCKET_NAME
from cf_analysis_agent.structures.criteria_structures import StructuredIndustryGroupCriteriaResponse,IndustryGroupData
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
    
    Please ensure the criteria are applicable to most companies in this sector/industry group.
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
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key="US/" + criteria_file_path)
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        return None

def get_criteria_file_path(sector:str,industry_group:str) -> str:
    """
    Returns the path to the status file for the given project ID.
    """
    return f"{sector}/{industry_group}/criteria.json"
