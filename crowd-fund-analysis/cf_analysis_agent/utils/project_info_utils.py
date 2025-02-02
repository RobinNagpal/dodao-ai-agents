import json
import traceback
from typing import List

from cf_analysis_agent.agent_state import ProcessingStatus, ProcessedProjectInfo
from cf_analysis_agent.utils.llm_utils import structured_llm_response, DEFAULT_LLM_CONFIG, MINI_4_0_CONFIG, \
    scrape_and_clean_content_with_same_details
from cf_analysis_agent.utils.project_utils import scrape_urls, scrape_url
from cf_analysis_agent.utils.report_utils import get_project_status_file_path, ProcessedProjectInfoSchema, \
    ProjectStatusFileSchema, ProjectInfoInputSchema
from cf_analysis_agent.utils.s3_utils import s3_client, BUCKET_NAME, upload_to_s3


def convert_s3_processed_info_to_state(project_info_in_s3: ProcessedProjectInfoSchema) -> ProcessedProjectInfo:
    processed_info: ProcessedProjectInfo = {
        "additional_urls_used": project_info_in_s3.get("additionalUrlsUsed"),
        "content_of_additional_urls": project_info_in_s3.get("contentOfAdditionalUrls"),
        "content_of_crowdfunding_url": project_info_in_s3.get("contentOfCrowdfundingUrl"),
        "content_of_website_url": project_info_in_s3.get("contentOfWebsiteUrl"),
        "sec_raw_content": project_info_in_s3.get("secRawContent"),
        "last_updated": project_info_in_s3.get("lastUpdated"),
        "status": project_info_in_s3.get("status"),
    }
    return processed_info


def scrape_additional_links_and_update_project_info(
        project_info: ProcessedProjectInfoSchema) -> ProcessedProjectInfoSchema:
    """
    Scrape the URLs in 'project_info' and update the 'processed_project_info' with the scraped content.
    """
    print(
        f"Scraping URLs and updating 'processed_project_info' in S3 for project: {project_info.get('urlsUsedForScraping')}")
    current_urls = project_info.get("additionalUrlsUsed") or []
    scraped_content_list: List[str] = []
    if current_urls:
        scraped_content_list = scrape_urls(current_urls)

    # Combine the general scraped content
    if len(current_urls) > 0:
        combined_scrapped_content = "\n\n".join(scraped_content_list)

        prompt = "Remove the duplicates from the below content, but don't remove any information. Be as detailed as possible. Don't remove any information at all \n\n" + combined_scrapped_content
        content_of_scrapped_urls = structured_llm_response(MINI_4_0_CONFIG, "summarize_scraped_content", prompt)

        project_info["additionalUrlsUsed"] = current_urls
        project_info["contentOfAdditionalUrls"] = content_of_scrapped_urls
    return project_info


def ensure_processed_project_info(project_id: str) -> ProcessedProjectInfo:
    """
    Ensures that 'processed_project_info' is present in agent-status.json in S3.
    This function checks if the URLs have changed. If they haven't and 'processed_project_info'
    exists, it does nothing. If they have changed (or don't exist), it scrapes the URLs again,
    then updates and uploads the new content back to S3.

    Returns the updated 'processed_project_info' from the status file.
    """
    # ----------------------- 1) Download agent-status.json -----------------------
    agent_status_file_path = get_project_status_file_path(project_id)

    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"crowd-fund-analysis/{agent_status_file_path}")
        project_file_contents: ProjectStatusFileSchema = json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        print(traceback.format_exc())
        raise FileNotFoundError(
            f"agent-status.json not found in S3 at path: s3://{BUCKET_NAME}/crowd-fund-analysis/{agent_status_file_path}"
        )

    # ----------------------- 2) Gather the current URLs -------------------------
    project_input: ProjectInfoInputSchema = project_file_contents.get("projectInfoInput", {})
    sec_filing_url = project_input.get("secFilingUrl", "").strip()
    additional_urls = project_input.get("additionalUrls", [])

    # Combine all project-related URLs (except the SEC link, which we'll handle separately if needed)
    current_urls = []
    if additional_urls:
        current_urls.extend(additional_urls)

    # Sort for stable comparison
    current_urls_sorted = sorted(set(current_urls))

    project_info_in_s3: ProcessedProjectInfoSchema = project_file_contents.get("processedProjectInfo", {})
    previous_urls = project_info_in_s3.get("additionalUrlsUsed") or []

    # Also sort for stable comparison
    previous_urls_sorted = sorted(set(previous_urls))

    urls_changed = (current_urls_sorted != previous_urls_sorted)
    print(f"URLs Changed: {urls_changed}")
    needs_processing = (project_info_in_s3 is None
                        or urls_changed
                        or project_info_in_s3.get("status") != ProcessingStatus.COMPLETED
                        or project_info_in_s3.get("contentOfAdditionalUrls") is None
                        or project_info_in_s3.get("contentOfAdditionalUrls") == ""
                        or project_info_in_s3.get("contentOfCrowdfundingUrl") is None
                        or project_info_in_s3.get("contentOfCrowdfundingUrl") == ""
                        or project_info_in_s3.get("secRawContent") is None
                        or project_info_in_s3.get("secRawContent") == "")

    print(f"Project Info Needs Processing: {needs_processing}")
    if not needs_processing:
        print("URLs have not changed and 'processed_project_info' already exists. No re-scraping needed.")
        return convert_s3_processed_info_to_state(project_info_in_s3)

    if (urls_changed
            or project_info_in_s3.get("status") != ProcessingStatus.COMPLETED
            or project_info_in_s3.get("contentOfAdditionalUrls") is None
            or project_info_in_s3.get("contentOfAdditionalUrls") == ""):
        print("URLs have changed or 'processed_project_info' is incomplete. Re-scraping URLs.")
        project_info_in_s3 = scrape_additional_links_and_update_project_info(project_info_in_s3)

    if project_info_in_s3.get("secRawContent") is None or project_info_in_s3.get("secRawContent") == "":
        print("SEC Raw Content is missing. Scraping SEC Filing URL.")
        project_info_in_s3["secRawContent"] = scrape_and_clean_content_with_same_details(sec_filing_url)

    if project_info_in_s3.get("contentOfCrowdfundingUrl") is None or project_info_in_s3.get(
            "contentOfCrowdfundingUrl") == "":
        print("SEC Raw Content is missing. Scraping SEC Filing URL.")
        project_info_in_s3["contentOfCrowdfundingUrl"] = scrape_and_clean_content_with_same_details(
            project_input.get("crowdFundingUrl"))

    if project_info_in_s3.get("contentOfWebsiteUrl") is None or project_info_in_s3.get("contentOfWebsiteUrl") == "":
        print("SEC Raw Content is missing. Scraping SEC Filing URL.")
        project_info_in_s3["contentOfWebsiteUrl"] = scrape_and_clean_content_with_same_details(
            project_input.get("websiteUrl"))

    project_file_contents["processedProjectInfo"] = project_info_in_s3

    upload_to_s3(
        content=json.dumps(project_file_contents, indent=4),
        s3_key=f"{project_id}/agent-status.json",
        content_type="application/json"
    )
    print(
        f"Updated 'processed_project_info' uploaded to https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/crowd-fund-analysis/{agent_status_file_path}")

    return convert_s3_processed_info_to_state(project_info_in_s3)
