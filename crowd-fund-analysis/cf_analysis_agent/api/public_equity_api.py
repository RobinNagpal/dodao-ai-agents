import json
from flask import Blueprint, request, jsonify
from cf_analysis_agent.utils.s3_utils import upload_equity_project_to_s3
from cf_analysis_agent.utils.get_criteria import get_industry_group_criteria,get_criteria_file,get_custom_criterias_file
from cf_analysis_agent.structures.criteria_structures import StructuredIndustryGroupCriteriaResponse,EquityDeatils,IndustryGroupData,Criteria
from cf_analysis_agent.utils.env_variables import BUCKET_NAME
from cf_analysis_agent.utils.env_variables import REGION
public_equity_api = Blueprint("public_equity_api", __name__)

@public_equity_api.route("/create-ai-criteria", methods=["POST"])
def submit_equity_project():
    try:
        equity_details:EquityDeatils = request.json  # Get the JSON request body
        sector = equity_details.get("sectorName", "").lower().replace(" ", "-")
        industryGroup = equity_details.get("industryGroupName", "").lower().replace(" ", "-")
        print("Received Equity Details:", equity_details)
        # upload_equity_project_to_s3(json.dumps(equity_details), s3_key , content_type="application/json")
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
            "id": equity_details["industryGroupId"],
            "name": equity_details["industryGroupName"],
            "sector": {"id":equity_details["sectorId"],"name":equity_details["sectorName"]},
            "industryGroup": {"id":equity_details["industryGroupId"],"name":equity_details["industryGroupName"]},
            "processedInformation": industry_group_criteria.processedInformation.model_dump()
        }
        upload_equity_project_to_s3(json.dumps(final_data, indent=2), f"{sector}/{industryGroup}/ai-criteria.json", content_type="application/json")
        custom_criteria=get_custom_criterias_file()
        if custom_criteria:
            found = False
            for criteria in custom_criteria["criteria"]:
                if criteria["sectorId"] == equity_details["sectorId"] and criteria["industryGroupId"] == equity_details["industryGroupId"]:
                    criteria["aiCriteriaFileLocation"] = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/public-equities/US/gics/{sector}/{industryGroup}/ai-criteria.json"
                    found = True
                    break
            if not found:
                custom_criteria.append({
                    "sectorId": equity_details["sectorId"],
                    "sectorName": equity_details["sectorName"],
                    "industryGroupId": equity_details["industryGroupId"],
                    "industryGroupName": equity_details["industryGroupName"],
                    "aiCriteriaFileLocation": f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/public-equities/US/gics/{sector}/{industryGroup}/ai-criteria.json"
                })
        else:
            custom_criteria=[{
                "sectorId": equity_details["sectorId"],
                "sectorName": equity_details["sectorName"],
                "industryGroupId": equity_details["industryGroupId"],
                "industryGroupName": equity_details["industryGroupName"],
                "aiCriteriaFileLocation": f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/public-equities/US/gics/{sector}/{industryGroup}/ai-criteria.json"
            }]
        upload_equity_project_to_s3(json.dumps(custom_criteria, indent=2), "custom-criterias.json", content_type="application/json")
        
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
