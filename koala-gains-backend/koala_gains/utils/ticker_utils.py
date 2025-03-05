from koala_gains.structures.public_equity_structures import CriteriaLookupList, TickerReport, Sector, IndustryGroup, \
    get_ticker_file_key
from koala_gains.utils.criteria_utils import get_criteria_lookup_list, get_matching_criteria_lookup_item
from koala_gains.utils.s3_utils import upload_to_s3, BUCKET_NAME


def initialize_new_ticker_report(ticker: str, sector_id: int, industry_group_id: int) -> str:
    custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()
    # Find matching criteria
    matching_criteria = get_matching_criteria_lookup_item(custom_criteria_list, sector_id, industry_group_id)

    report = TickerReport(
        ticker=ticker,
        selectedSector=Sector(
            id=matching_criteria.sectorId,
            name=matching_criteria.sectorName
        ),
        selectedIndustryGroup=IndustryGroup(
            id=matching_criteria.industryGroupId,
            name=matching_criteria.industryGroupName
        ),
        evaluationsOfLatest10Q=None,
        criteriaMatchesOfLatest10Q=None
    )

    ticker_file_key = get_ticker_file_key(ticker)

    upload_to_s3(report.model_dump_json(indent=2), ticker_file_key, content_type="application/json")

    return f"https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/{ticker_file_key}"
