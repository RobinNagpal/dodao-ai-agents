from flask import Blueprint, request, jsonify

from koala_gains.structures.criteria_structures import IndustryGroupCriteria
from koala_gains.utils.criteria_utils import generate_ai_criteria, upload_ai_criteria_to_s3, \
    update_criteria_lookup_list, \
    get_matching_criteria


class CreateCriteriaRequest:
    sectorId: int
    industryGroupId: int

public_equity_api = Blueprint("public_equity_api", __name__)


@public_equity_api.route("/upsert-ai-criteria", methods=["POST"])
def create_ai_criteria():
    try:
        # It is assumed that request.json matches the EquityDetailsDict type.
        equity_details: CreateCriteriaRequest = request.json  # type: ignore
        mathing_criteria = get_matching_criteria(equity_details)

        final_data: IndustryGroupCriteria = generate_ai_criteria(mathing_criteria)
        ai_criteria_url: str = upload_ai_criteria_to_s3(mathing_criteria, final_data)
        update_criteria_lookup_list(mathing_criteria, ai_criteria_url)

        return jsonify({
            "success": True,
            "message": "AI criteria file created successfully.",
            "filePath": ai_criteria_url
        }), 200

    except Exception as e:
        print("Error creating AI criteria:", str(e))
        return jsonify({"success": False, "message": "Internal server error."}), 500
