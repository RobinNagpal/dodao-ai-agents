import os
import subprocess
import sys
import traceback

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
from cf_analysis_agent.utils.env_variables import BUCKET_NAME, OPEN_AI_DEFAULT_MODEL, REGION, ADMIN_CODES
from cf_analysis_agent.utils.agent_utils import generate_hashed_key, get_admin_name_from_request
from cf_analysis_agent.utils.report_utils import (
    RepopulatableFields,
    update_status_to_not_started_for_all_reports,
    initialize_project_in_s3,
    update_report_status_in_progress,
)
from cf_analysis_agent.controller import prepare_processing_command
from cf_analysis_agent.utils.process_project_utils import repopulate_project_field

# Add the parent directory of app.py to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)  # Allow all origins by default


def build_processing_command(project_id, project_name, crowdfunding_link, website_url, latest_sec_filing_link, additional_links, model=OPEN_AI_DEFAULT_MODEL):
    """Helper to build the processing command."""
    command = [
        "poetry", "run", "python", "cf_analysis_agent/controller.py",
        project_id,
        project_name,
        crowdfunding_link,
        website_url,
        latest_sec_filing_link,
    ]
    if additional_links:
        command.extend(["--additional_links", ",".join(additional_links)])
    command.extend(["--model", model])
    return command


def handle_exception(e):
    """Helper to handle exceptions uniformly."""
    print(traceback.format_exc())
    if isinstance(e, FileNotFoundError):
        return jsonify({"status": "error", "message": str(e)}), 404
    elif isinstance(e, ValueError):
        return jsonify({"status": "error", "message": str(e)}), 400
    else:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500


@app.route("/")
def index():
    """Renders the home page with the form."""
    return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
    """
    Handles form submission, starts processing, and redirects to the status page.
    """
    # Retrieve form data
    project_id = request.form.get("project_id").strip()
    project_name = request.form.get("project_name").strip()
    crowdfunding_link = request.form.get("crowdfunding_link").strip()
    website_url = request.form.get("website_url").strip()
    latest_sec_filing_link = request.form.get("latest_sec_filing_link").strip()
    additional_links = request.form.getlist("additional_links")  # Collect additional links

    project_details = {
        "project_id": project_id,
        "project_name": project_name,
        "crowdfunding_link": crowdfunding_link,
        "website_url": website_url,
        "latest_sec_filing_link": latest_sec_filing_link,
        "additional_links": additional_links,
    }
    # Initialize project in S3
    initialize_project_in_s3(project_id=project_id, project_details=project_details)

    # Build and run the processing command asynchronously
    command = build_processing_command(project_id, project_name, crowdfunding_link, website_url, latest_sec_filing_link, additional_links)
    subprocess.Popen(command)

    # Redirect to the status page with the project ID
    return redirect(url_for("status", project_id=project_id))


@app.route("/api/submit", methods=["POST"])
def api_submit():
    """
    Handles JSON-based form submission, starts processing, and returns a JSON response.
    """
    admin_name, error_response = get_admin_name_from_request()
    if error_response:
        return error_response  # Return error if any

    if not request.is_json:
        return jsonify({"error": "Invalid request. JSON expected."}), 400

    data = request.get_json()
    # Retrieve data safely
    project_id = data.get("projectId", "").strip()
    project_name = data.get("projectName", "").strip()
    project_img_url = data.get("projectImgUrl", "").strip()
    crowdfunding_link = data.get("crowdFundingUrl", "").strip()
    website_url = data.get("websiteUrl", "").strip()
    latest_sec_filing_link = data.get("secFilingUrl", "").strip()
    additional_links = data.get("additionalUrls", [])  # JSON sends this as an array

    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    project_details = {
        "project_id": project_id,
        "project_name": project_name,
        "project_img_url": project_img_url,
        "crowdfunding_link": crowdfunding_link,
        "website_url": website_url,
        "latest_sec_filing_link": latest_sec_filing_link,
        "additional_links": additional_links,
    }
    # Initialize project (store in S3 or DB)
    initialize_project_in_s3(project_id=project_id, project_details=project_details, triggered_by=admin_name)

    # Build and run the processing command asynchronously
    command = build_processing_command(project_id, project_name, crowdfunding_link, website_url, latest_sec_filing_link, additional_links)
    subprocess.Popen(command)

    return jsonify({"status": "success", "project_id": project_id, "message": "Project processing started"}), 200


@app.route("/status/<project_id>")
def status(project_id):
    """
    Render the status monitoring page.
    """
    bucket_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com"
    print(bucket_url)
    return render_template("status.html", project_id=project_id, bucket_url=bucket_url)


@app.route("/commit-info")
def commit_info():
    """
    Display the latest git commit hash and message.
    """
    commit_file_path = os.path.join(os.path.dirname(__file__), "commit_info.txt")
    if os.path.exists(commit_file_path):
        with open(commit_file_path, "r") as file:
            lines = file.readlines()
        commit_hash = lines[0].strip().split("=")[1] if len(lines) > 0 else "Unavailable"
        commit_message = lines[1].strip().split("=")[1] if len(lines) > 1 else "Unavailable"
    else:
        commit_hash = "Unavailable"
        commit_message = "Unavailable"
    return render_template("commit_info.html", commit_hash=commit_hash, commit_message=commit_message)


@app.route('/api/projects/<projectId>/reports/regenerate', methods=['POST'])
def regenerate_reports(projectId):
    """
    Regenerates reports for a given project using values from agent-status.json in S3.
    """
    try:
        admin_name, error_response = get_admin_name_from_request()
        if error_response:
            return error_response

        data = request.get_json(silent=True) or {}
        model = data.get("model", OPEN_AI_DEFAULT_MODEL)

        update_status_to_not_started_for_all_reports(project_id=projectId, triggered_by=admin_name)
        command = prepare_processing_command(projectId, model)
        subprocess.Popen(command)

        return jsonify({
            "status": "success",
            "message": f"Regeneration of reports for {projectId} has started successfully."
        }), 200

    except Exception as e:
        return handle_exception(e)


@app.route('/api/projects/<projectId>/reports/<report_type>/regenerate', methods=['POST'])
def regenerate_specific_report(projectId, report_type):
    """
    Regenerates a specific report for a given project.
    """
    try:
        admin_name, error_response = get_admin_name_from_request()
        if error_response:
            return error_response

        data = request.get_json(silent=True) or {}
        model = data.get("model", OPEN_AI_DEFAULT_MODEL)

        update_report_status_in_progress(project_id=projectId, report_type=report_type, triggered_by=admin_name)
        command = prepare_processing_command(projectId, model)
        command.extend(["--report_type", report_type])
        subprocess.Popen(command)

        return jsonify({
            "status": "success",
            "message": f"Regeneration of {report_type} report for {projectId} has started successfully."
        }), 200

    except Exception as e:
        return handle_exception(e)


@app.route('/api/projects/reports/<report_type>/regenerate', methods=['POST'])
def regenerate_specific_report_for_multiple_projects(report_type):
    """
    Regenerates a specific report for multiple projects sequentially.
    """
    try:
        admin_name, error_response = get_admin_name_from_request()
        if error_response:
            return error_response

        data = request.get_json(silent=True) or {}
        project_ids = data.get("projectIds", [])
        model = data.get("model", OPEN_AI_DEFAULT_MODEL)

        if not isinstance(project_ids, list) or not project_ids:
            return jsonify({
                "status": "error",
                "message": "Invalid or missing 'projectIds'. It should be a non-empty list."
            }), 400

        for project_id in project_ids:
            try:
                update_report_status_in_progress(project_id=project_id, report_type=report_type, triggered_by=admin_name)
                command = prepare_processing_command(project_id, model)
                command.extend(["--report_type", report_type])
                subprocess.run(command, check=True)
                print(f"Successfully regenerated {report_type} report for {project_id}")
            except Exception as e:
                print(f"Failed to regenerate {report_type} report for {project_id}: {str(e)}")
                continue

        return jsonify({
            "status": "success",
            "message": f"Regeneration of {report_type} report for multiple projects has completed."
        }), 200

    except Exception as e:
        return handle_exception(e)


@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    code = data.get("code")

    if not code:
        return jsonify({"status": "error", "message": "Code is required"}), 400

    if code in ADMIN_CODES:
        hashed_key = generate_hashed_key(code)
        return jsonify({
            "status": "success",
            "message": "Authenticated successfully.",
            "key": hashed_key
        }), 200

    return jsonify({"status": "error", "message": "Invalid code"}), 401


@app.route('/api/projects/<projectId>/repopulate/<projectField>', methods=['POST'])
def populate_project_info_field(projectId, projectField):
    try:
        admin_name, error_response = get_admin_name_from_request()
        if error_response:
            return error_response

        if projectField not in RepopulatableFields.list():
            return jsonify({
                "status": "error",
                "message": f"Invalid field '{projectField}'. Allowed fields: {RepopulatableFields.list()}"
            }), 400

        repopulate_project_field(projectId, projectField)
        return jsonify({
            "status": "success",
            "message": f"Repopulation of '{projectField}' for project {projectId} has started successfully."
        }), 200

    except Exception as e:
        return handle_exception(e)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
