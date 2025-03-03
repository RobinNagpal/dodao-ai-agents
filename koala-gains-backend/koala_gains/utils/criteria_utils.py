import json
from typing import Any

from koala_gains.structures.criteria_structures import (
    IndustryGroupCriteria,
    CriteriaLookupItem,
    CriteriaLookupList,
)
from koala_gains.structures.public_equity_structures import slugify
from koala_gains.utils.env_variables import BUCKET_NAME, REGION
from koala_gains.utils.llm_utils import structured_criteria_response, NORMAL_4_0_CONFIG
from koala_gains.utils.s3_utils import s3_client, upload_to_s3_public_equities


def get_industry_group_criteria(
    criteria_lookup: CriteriaLookupItem,
) -> IndustryGroupCriteria:
    """
    Generates a structured report with 6-8 evaluation criteria for a company operating in a specific sector and industry group.
    """

    sector = criteria_lookup.get("sectorName")
    industry_group = criteria_lookup.get("industryGroupName")

    prompt: str = f"""
    You are an expert in startup evaluation and industry analysis. Provide 6-8 key criteria 
    to evaluate a company in the {sector} sector and {industry_group} industry group.
    
    Also find some tickers related to industry group {industry_group} and sector {sector}.
    
    Ensure the criteria cover the most relevant aspects such as financial performance, 
    market positioning, operational efficiency, rent for Real Estate, etc. It should be specific to the 
    {sector} sector and {industry_group} industry group.

    Each criterion should include:
    - Name of the evaluation criteria
    - A short description explaining its importance
    - A list of important metrics that should be considered when evaluating this criterion

    Each report should include:
    - key of the report
    - name of the report
    - description of the report
    - outputType of the report like text or graph if graph also give its type like if text then (Text Report) if any chart like bar chart  give (Bar Chart).
    
    Please ensure there are 4 criteria and they are most relevant when evaluating companies in {sector} sector and {industry_group} industry group.
    
    Each criterion should be able to be evaluated using the SEC 10Q filings.
    """
    return structured_criteria_response(
        NORMAL_4_0_CONFIG, f"industry_group_criteria_{sector}_{industry_group}", prompt
    )


def get_criteria_lookup_list() -> CriteriaLookupList:
    """
    Fetches and returns the custom criteria file from S3.
    """

    response: Any = s3_client.get_object(
        Bucket=BUCKET_NAME, Key="public-equities/US/gics/custom-criterias.json"
    )
    return json.loads(response["Body"].read().decode("utf-8"))


def get_matching_criteria(
    custom_criteria_list: CriteriaLookupList, sector_id: int, industry_group_id: int
) -> CriteriaLookupItem:
    """
    Fetches the matching criteria for the given sector and industry group.
    """
    matching_criteria = next(
        (
            x
            for x in custom_criteria_list["criteria"]
            if x.get("sectorId") == sector_id
            and x.get("industryGroupId") == industry_group_id
        ),
        None,
    )
    if matching_criteria is None:
        raise ValueError("Criteria not found for the given sector and industry group.")
    return matching_criteria


def generate_ai_criteria(criteria_lookup: CriteriaLookupItem) -> IndustryGroupCriteria:
    """
    Generate AI criteria data using industry group information.
    """
    return get_industry_group_criteria(criteria_lookup)


def upload_ai_criteria_to_s3(
    criteria_lookup: CriteriaLookupItem, final_data: IndustryGroupCriteria
) -> str:
    """
    Upload AI criteria data to S3 and return the S3 URL.
    """
    s3_key: str = (
        f"{get_s3_base_path_for_criteria_lookup(criteria_lookup)}/ai-criteria.json"
    )
    upload_to_s3_public_equities(
        final_data.model_dump_json(indent=2), s3_key, content_type="application/json"
    )
    return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/public-equities/US/gics/{s3_key}"


def update_criteria_lookup_list(
    criteria_lookup_item: CriteriaLookupItem, ai_criteria_url: str
) -> None:
    """
    Update the custom criteria file with AI criteria information.
    """
    custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()

    # Find criteria for the given sector and industry group in the list
    matching_criteria = get_matching_criteria(
        custom_criteria_list,
        criteria_lookup_item.get("sectorId"),
        criteria_lookup_item.get("industryGroupId"),
    )

    matching_criteria["aiCriteriaFileUrl"] = ai_criteria_url
    upload_to_s3_public_equities(
        json.dumps(custom_criteria_list, indent=2),
        "gics/custom-criterias.json",
        content_type="application/json",
    )


def get_s3_base_path_for_criteria_lookup(criteria_lookup: CriteriaLookupItem):
    """
    Returns the S3 base path for the criteria file for the given sector and industry group.
    """
    sector_name = criteria_lookup.get("sectorName")
    industry_group_name = criteria_lookup.get("industryGroupName")
    return f"{slugify(sector_name)}/{slugify(industry_group_name)}"
