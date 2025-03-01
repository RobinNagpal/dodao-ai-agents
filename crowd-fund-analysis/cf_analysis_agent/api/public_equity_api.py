import json
from flask import Blueprint, request, jsonify
from cf_analysis_agent.utils.criteria_utils import generate_ai_criteria ,upload_ai_criteria_to_s3, update_custom_criteria,fetch_criteria_file
from cf_analysis_agent.structures.criteria_structures import StructuredIndustryGroupCriteriaResponse, EquityDeatils, IndustryGroupData


public_equity_api = Blueprint("public_equity_api", __name__)



@public_equity_api.route("/create-ai-criteria", methods=["POST"])
def create_ai_criteria():
    try:
        equity_details = request.json
        criteria_file, sector, industry_group = fetch_criteria_file(equity_details)

        if criteria_file:
            return jsonify({"success": True, "message": "Criteria file already exists."}), 200

        final_data = generate_ai_criteria(equity_details, sector, industry_group)
        ai_criteria_url = upload_ai_criteria_to_s3(final_data, sector, industry_group)
        update_custom_criteria(equity_details, ai_criteria_url)

        return jsonify({"success": True, "message": "AI criteria file created successfully.","filePath":ai_criteria_url}), 200

    except Exception as e:
        print("Error creating AI criteria:", str(e))
        return jsonify({"success": False, "message": "Internal server error."}), 500

@public_equity_api.route("/regenerate-ai-criteria", methods=["POST"])
def regenerate_ai_criteria():
    try:
        equity_details = request.json
        criteria_file, sector, industry_group = fetch_criteria_file(equity_details)

        if not criteria_file:
            return jsonify({"success": False, "message": "AI criteria file does not exist. Create it first before regenerating."}), 404

        final_data = generate_ai_criteria(equity_details, sector, industry_group)
        ai_criteria_url = upload_ai_criteria_to_s3(final_data, sector, industry_group)
        update_custom_criteria(equity_details, ai_criteria_url)

        return jsonify({"success": True, "message": "AI criteria successfully regenerated and updated.","filePath":ai_criteria_url}), 200

    except Exception as e:
        print("Error regenerating AI criteria:", str(e))
        return jsonify({"success": False, "message": "Internal server error."}), 500
