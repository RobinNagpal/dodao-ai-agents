from typing import TypedDict

from flask import Blueprint, request, jsonify

from koala_gains.api.api_helper import handle_exception
from koala_gains.structures.criteria_structures import IndustryGroupCriteriaStructure

from koala_gains.structures.public_equity_structures import (
    IndustryGroup,
    Sector,
    CriteriaLookupList,
)
from koala_gains.utils.criteria_utils import (
    generate_ai_criteria,
    upload_ai_criteria_to_s3,
    update_criteria_lookup_list,
    get_matching_criteria,
    get_criteria_lookup_list,
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


@public_equity_api.route("/create-all-reports", methods=["GET"])
def process_ticker():

    return jsonify({"success": True, "message": "Ticker processed successfully."}), 200


@public_equity_api.route("/create-single-reports", methods=["GET"])
def process_ticker():

    return jsonify({"success": True, "message": "Ticker processed successfully."}), 200
