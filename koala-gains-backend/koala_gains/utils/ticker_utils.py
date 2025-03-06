from typing import List

import json

from koala_gains.structures.public_equity_structures import (
    CriteriaLookupList,
    TickerReport,
    Sector,
    IndustryGroup,
    get_ticker_file_key,
    CriterionReportDefinitionItem,
    IndustryGroupCriteria,
    IndustryGroupCriterion,
    get_criterion_report_key,
    PerformanceChecklistItem,
    get_criterion_performance_checklist_key,
)
from koala_gains.utils.criteria_utils import (
    get_criteria_lookup_list,
    get_matching_criteria_lookup_item,
)
from koala_gains.utils.s3_utils import upload_to_s3, BUCKET_NAME, get_object_from_s3
import requests


def initialize_new_ticker_report(
    ticker: str, sector_id: int, industry_group_id: int
) -> str:
    custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()
    # Find matching criteria
    matching_criteria = get_matching_criteria_lookup_item(
        custom_criteria_list, sector_id, industry_group_id
    )

    report = TickerReport(
        ticker=ticker,
        selectedSector=Sector(
            id=matching_criteria.sectorId, name=matching_criteria.sectorName
        ),
        selectedIndustryGroup=IndustryGroup(
            id=matching_criteria.industryGroupId,
            name=matching_criteria.industryGroupName,
        ),
        evaluationsOfLatest10Q=None,
        criteriaMatchesOfLatest10Q=None,
    )

    ticker_file_key = get_ticker_file_key(ticker)

    return upload_to_s3(
        report.model_dump_json(indent=2),
        ticker_file_key,
        content_type="application/json",
    )

def get_ticker_report(ticker: str) -> TickerReport:
    ticker_file_key = get_ticker_file_key(ticker)
    ticker_json = get_object_from_s3(ticker_file_key)
    report = TickerReport.model_load_json(ticker_json)
    return report


def get_criteria_report_definition(
    sector_id: int, industry_group_id: int, criteria_key: str, report_key: str
) -> CriterionReportDefinitionItem:
    criteria_lookup_list = get_criteria_lookup_list()

    matching_criteria = get_matching_criteria_lookup_item(
        criteria_lookup_list, sector_id, industry_group_id
    )

    if matching_criteria.customCriteriaFileUrl is None:
        raise Exception(
            f"Custom criteria file not found for sector and industry group: {sector_id}, {industry_group_id}"
        )

    response = requests.get(matching_criteria.customCriteriaFileUrl)
    json_response = json.loads(response.text)
    industry_group_criteria = IndustryGroupCriteria.model_load_json(json_response)
    criterion = next(
        criterion
        for criterion in industry_group_criteria.criteria
        if criterion.key == criteria_key
    )
    report_definition = next(
        report for report in criterion.reports if report.key == report_key
    )

    return report_definition


def save_criteria_evaluation(
    ticker: str, criterion_key: str, report_key: str, data: any
) -> str:
    report = get_ticker_report(ticker)
    report_definition = get_criteria_report_definition(
        report.selectedSector.id,
        report.selectedIndustryGroup.id,
        criterion_key,
        report_key,
    )

    criterion_report_key = get_criterion_report_key(
        ticker, criterion_key, report_key, report_definition.outputType
    )

    return upload_to_s3(
        data,
        criterion_report_key,
        content_type=(
            "text/plain"
            if report_definition.outputType == "Text"
            else "application/json"
        ),
    )


def save_performance_checklist(
    ticker: str, criterion_key: str, checklist: List[PerformanceChecklistItem]
) -> str:
    file_key = get_criterion_performance_checklist_key(ticker, criterion_key)

    checklist_json = json.dumps([item.dict() for item in checklist], indent=2)

    return upload_to_s3(checklist_json, file_key, content_type="application/json")


def trigger_criteria_matching(ticker: str, force: bool) -> str:
    report = get_ticker_report(ticker)

    if not force and report.criteriaMatchesOfLatest10Q is not None and report.criteriaMatchesOfLatest10Q.status == "Completed":
        return f"Criteria matching already done for {ticker}"

    report.criteriaMatchesOfLatest10Q = None

    ticker_file_key = get_ticker_file_key(ticker)

    upload_to_s3(
        report.model_dump_json(indent=2),
        ticker_file_key,
        content_type="application/json",
    )
    url = "https://4mbhgkl77s4gubn7i2rdcllbru0wzyxl.lambda-url.us-east-1.on.aws/populate-criteria-matches"
    payload = {"ticker": "FVR"}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    return response.text
