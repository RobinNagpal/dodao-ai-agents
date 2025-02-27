import json
from flask import Blueprint, request, jsonify
from cf_analysis_agent.utils.s3_utils import upload_equity_project_to_s3
from cf_analysis_agent.utils.get_criteria import get_industry_group_criteria,get_criteria_file
from cf_analysis_agent.structures.criteria_structures import StructuredIndustryGroupCriteriaResponse,EquityDeatils,IndustryGroupData,Criteria

public_equity_api = Blueprint("public_equity_api", __name__)

@public_equity_api.route("/submit", methods=["POST"])
def submit_equity_project():
    try:
        equity_details:EquityDeatils = request.json  # Get the JSON request body
        sector = equity_details.get("sector", "").get("name","").lower().replace(" ", "-")
        industryGroup = equity_details.get("industryGroup", "").get("name","").lower().replace(" ", "-")
        industry = equity_details.get("industry", "").get("name","").lower().replace(" ", "-")
        subIndustry = equity_details.get("subIndustry", "").get("name","").lower().replace(" ", "-")
        s3_key = f"{sector}/{industryGroup}/{industry}/{subIndustry}/agent-status.json"
        print("Received Equity Details:", equity_details)
        upload_equity_project_to_s3(json.dumps(equity_details), s3_key , content_type="application/json")
        criteria_file=get_criteria_file(sector,industryGroup)
        if criteria_file:
            print("criteria file already exists.")
            return jsonify({
                "success": True,
                "message": "criteria file already exists."
            }), 200
        industry_group_criteria:StructuredIndustryGroupCriteriaResponse  = get_industry_group_criteria(sector, industryGroup)
        final_data:IndustryGroupData ={
            "tickers": industry_group_criteria.tickers,
            "id": equity_details["industryGroup"]["id"],
            "name": equity_details["industryGroup"]["name"],
            "subIndustry": equity_details["subIndustry"],
            "sector": equity_details["sector"],
            "industryGroup": equity_details["industryGroup"],
            "industry": equity_details["industry"],
            "processed_information": industry_group_criteria.processed_information.model_dump()
        }
        upload_equity_project_to_s3(json.dumps(final_data, indent=2), f"{sector}/{industryGroup}/criteria.json", content_type="application/json")
    
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
