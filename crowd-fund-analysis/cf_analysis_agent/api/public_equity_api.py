import json
from flask import Blueprint, request, jsonify
from cf_analysis_agent.utils.s3_utils import upload_equity_project_to_s3

public_equity_api = Blueprint("public_equity_api", __name__)

@public_equity_api.route("/submit", methods=["POST"])
def submit_equity_project():
    try:
        equity_details = request.json  # Get the JSON request body
        sector = equity_details.get("sector", "").lower().replace(" ", "-")
        industryGroup = equity_details.get("industryGroup", "").lower().replace(" ", "-")
        industry = equity_details.get("industry", "").lower().replace(" ", "-")
        subIndustry = equity_details.get("subIndustry", "").lower().replace(" ", "-")
        s3_key = f"{sector}/{industryGroup}/{industry}/{subIndustry}/agent-status.json"
        print("Received Equity Details:", equity_details)
        upload_equity_project_to_s3(json.dumps(equity_details), s3_key , content_type="application/json")
    
        return jsonify({
            "success": True,
            "message": "agent_status file uploaded successfully."
        }), 200
    except Exception as e:
        print("Error processing equity data:", str(e))
        return jsonify({
            "success": False,
            "message": "Internal server error."
        }), 500
