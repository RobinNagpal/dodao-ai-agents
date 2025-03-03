from typing import TypedDict

from flask import Blueprint, request, jsonify

from koala_gains.api.api_helper import handle_exception
from koala_gains.structures.criteria_structures import IndustryGroupCriteriaStructure

from koala_gains.structures.public_equity_structures import (
    IndustryGroup,
    IndustryGroupCriteria,
    Sector,
    CriteriaLookupList,
)
from koala_gains.utils.criteria_utils import (
    generate_ai_criteria,
    get_matching_criteria_using_slugs,
    update_criteria_lookup_list_for_custom_criteria,
    upload_ai_criteria_to_s3,
    update_criteria_lookup_list,
    get_matching_criteria,
    get_criteria_lookup_list,
    upload_custom_criteria_to_s3,
)


class CreateCriteriaRequest(TypedDict):
    sectorId: int
    industryGroupId: int


class CreateAllReportsRequest(TypedDict):
    ticker: str
    selectedIndustryGroup: IndustryGroup
    selectedSector: Sector


public_equity_api = Blueprint("public_equity_api", __name__)


@public_equity_api.route("/upsert-ai-criteria", methods=["POST"])
def create_ai_criteria():
    try:
        # It is assumed that request.json matches the EquityDetailsDict type.
        criteria_request: CreateCriteriaRequest = request.json
        print(f"Creating AI criteria for: {criteria_request}")
        custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()
        mathing_criteria = get_matching_criteria(
            custom_criteria_list,
            criteria_request.get("sectorId"),
            criteria_request.get("industryGroupId"),
        )

        final_data: IndustryGroupCriteriaStructure = generate_ai_criteria(
            mathing_criteria
        )
        ai_criteria_url: str = upload_ai_criteria_to_s3(mathing_criteria, final_data)
        update_criteria_lookup_list(mathing_criteria, ai_criteria_url)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "AI criteria file created successfully.",
                    "filePath": ai_criteria_url,
                }
            ),
            200,
        )

    except Exception as e:
        return handle_exception(e)

@public_equity_api.route("/upsert-custom-criteria", methods=["POST"])
def create_custom_criteria():
    try:
        # Get request JSON
        criteria_request: CreateCriteriaRequest = request.json

        # Validate required fields
        sector_id = criteria_request.get("sectorId")
        industry_group_id = criteria_request.get("industryGroupId")
        criteria = criteria_request.get("criteria")  # Expecting a list of criteria
        print(f"Creating Custom criteria for Sector ID: {sector_id}, Industry Group ID: {industry_group_id}")
        if not sector_id or not industry_group_id or not criteria:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        print(f"Creating Custom criteria for Sector ID: {sector_id}, Industry Group ID: {industry_group_id}")

        # Get the existing criteria lookup list
        custom_criteria_list: CriteriaLookupList = get_criteria_lookup_list()
        # Find matching criteria
        matching_criteria = get_matching_criteria_using_slugs(custom_criteria_list, sector_id, industry_group_id)

        # Generate final criteria data using provided criteria
        final_data = IndustryGroupCriteria(
            tickers=["AMT"],  # Hardcoded for now
            selectedSector={
                "id": matching_criteria.get("sectorId"),
                "name": matching_criteria.get("sectorName")},
            selectedIndustryGroup={
                "id": matching_criteria.get("industryGroupId"),
                "name": matching_criteria.get("industryGroupName")
            },
            criteria=criteria  # Use the provided criteria
        )
        # Upload criteria to S3
        custom_criteria_url = upload_custom_criteria_to_s3(matching_criteria, final_data)

        # Update criteria lookup list with the new custom criteria
        update_criteria_lookup_list_for_custom_criteria(matching_criteria, custom_criteria_url)

        return jsonify({
            "success": True,
            "message": "Custom criteria file upserted successfully.",
            "filePath": custom_criteria_url
        }), 200

    except Exception as e:
        return handle_exception(e)


@public_equity_api.route("/re-populate-matching-attachments", methods=["POST"])
def process_ticker():
    # Step 1 - Populate matching criteria for the ticker if it does not exist
    return jsonify({"success": True, "message": "Ticker processed successfully."}), 200

@public_equity_api.route("/create-all-reports", methods=["POST"])
def process_ticker():
    # Step 1 - Create a ticker report file if it does not exist
    # Step 2 - Populate matching criteria for the ticker if it does not exist
    # Step 3 - Generate report for the ticker using the criteria
        # For the first criterion, trigger the report, and pass shouldTriggerNext as True
    return jsonify({"success": True, "message": "Ticker processed successfully."}), 200


@public_equity_api.route("/create-single-reports", methods=["GET"])
def process_single_ticker():
    # Step 1 - Create a ticker report file if it does not exist
    # Step 2 - Populate matching criteria for the ticker if it does not exist
    # Step 3 - Generate report for the ticker using the criteria
    # Trigger the next criterion report. and pass shouldTriggerNext as False
    return jsonify({"success": True, "message": "Ticker processed successfully."}), 200


@public_equity_api.route("/save-criterion-report-and-trigger-next", methods=["POST"])
def process_single_ticker():
    # This will send ticker, criterionKey, and reportKey
    # Save the report in s3
    # Trigger the next criterion report if not last. Then pass shouldTriggerNext as True
    # IF last in the list - Then pass shouldTriggerNext as False
    return jsonify({"success": True, "message": "Ticker processed successfully."}), 200
