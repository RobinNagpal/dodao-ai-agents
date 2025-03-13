from typing import Set, Dict, List
import json
import boto3
import os
from dotenv import load_dotenv
from edgar import Company, use_local_storage, set_identity, CompanyFilings
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from src.sec_filing_structures import (
    SecFiling,
    SecFilingAttachment,
    SecForm,
    SecFormsInfo,
)

# Load environment variables and initialize EDGAR settings
load_dotenv()
use_local_storage()
set_identity("your_email@example.com")

bucket = os.getenv("S3_BUCKET_NAME")
sec_forms_key = "sec-timeline/sec-forms/sec-forms-info.json"
s3_client = boto3.client("s3")


# --- Existing function to get filings ---
def get_all_filings_for_ticker(ticker: str, page: int, limit: int) -> List[SecFiling]:
    """
    Retrieve filings for a given ticker with pagination.

    The 'page' parameter is zero-indexed.
    """
    company = Company(ticker)
    filings_obj = company.get_filings()  # This is a CompanyFilings instance
    total_filings = filings_obj.data.num_rows  # Get total number of filings

    start = page * limit
    if start >= total_filings:
        print(f"No filings found on page {page}. Total filings: {total_filings}")
        return []

    # Calculate how many records to take (in case fewer filings remain)
    slice_length = min(limit, total_filings - start)
    # Slice the underlying PyArrow table
    paged_table = filings_obj.data.slice(start, slice_length)
    # Create a new CompanyFilings object from the sliced table
    paged_filings = CompanyFilings(
        paged_table, cik=filings_obj.cik, company_name=filings_obj.company_name
    )

    sec_filings: list[SecFiling] = list()
    for i in range(paged_filings.data.num_rows):
        # Get the filing at the current index
        f = paged_filings.get_filing_at(i)
        sec_attachments = []
        for a in f.attachments:
            if a.extension in [".html", ".htm", ".xml"]:
                # Compute base URL for attachment replacement
                f_url_base = f.filing_url.rsplit("/", 1)[0]
                sec_attachment = SecFilingAttachment(
                    sequenceNumber=a.sequence_number,
                    description=a.description,
                    purpose=a.purpose,
                    url=str(a.url).replace(
                        "https://www.sec.gov/<SGML FILE>", f_url_base
                    ),
                    documentType=a.document_type,
                )
                sec_attachments.append(sec_attachment)

        sec_filing = SecFiling(
            filingDate=str(f.filing_date),
            form=f.form,
            filingUrl=f.filing_url,
            accessionNumber=f.accession_number,
            periodOfReport=str(f.period_of_report),
            attachments=sec_attachments,
        )
        print(sec_filing.model_dump_json(indent=2))
        sec_filings.append(sec_filing)

    print(f"Found {len(sec_filings)} filings for {ticker} on page {page}")
    return sec_filings


# --- New LLM function for multiple forms ---
def get_forms_info(forms: Set[str]) -> Dict[str, dict]:
    """
    Given a set of form names, ask the LLM in a single call to provide detailed information
    for each SEC filing form. The LLM should return a JSON object where each key is a form name and its value
    is a JSON object conforming to the SecForm structure.
    """
    forms_list = list(forms)
    prompt = f"""
    Provide detailed information about the following SEC forms: {', '.join(forms_list)}.
    For each form, include a brief description, its common uses, an estimated average page count,
    and assign a size category (one of: xs, s, m, l, or xl).
    
    For bigger forms which have quite a bit of information like 10-K, 10-Q include at least six to eight important items to look for in the form.
    
    form 424B4 or 10-K or similar length forms should be categorized as xl.

    form 3,4,5 or similar length forms should be categorized as xs.
    
    Return the result as a JSON object where each key is the form name and its value is a JSON object with the following structure:
    {{
       "formName": "<form name>",
       "formDescription": "...",
       "importantItems": "...",
       "averagePageCount": <number>,
       "size": "xs"|"s"|"m"|"l"|"xl"
    }}

    Ensure that the JSON is valid.
    """
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = model.with_structured_output(SecFormsInfo)
    result: SecFormsInfo = structured_llm.invoke([HumanMessage(content=prompt)])

    forms_dict: Dict[str, dict] = {}
    # Iterate through the list of forms returned in the response
    for form in result.forms:
        forms_dict[form.formName] = form.model_dump()
    return forms_dict


# --- S3 Utility Functions ---
def get_forms_info_from_s3() -> Dict[str, dict]:
    """
    Retrieve the existing forms information JSON from S3.
    Returns an empty dict if the object does not exist.
    """
    try:
        s3_obj = s3_client.get_object(Bucket=bucket, Key=sec_forms_key)
        body = s3_obj["Body"].read().decode("utf-8")
        return json.loads(body)
    except Exception as e:
        print(f"S3 object not found or error reading {sec_forms_key}: {e}")
        return {}


def update_forms_info_in_s3(forms: Set[str]):
    """
    For each unique form not already in S3, fetch info via a single LLM call and update the JSON file.
    """
    existing_forms_info = get_forms_info_from_s3()
    if not isinstance(existing_forms_info, dict):
        existing_forms_info = {}

    missing_forms = {form for form in forms if form not in existing_forms_info}
    if missing_forms:
        print(f"Fetching info for new forms: {missing_forms}")
        new_forms_info = get_forms_info(missing_forms)
        existing_forms_info.update(new_forms_info)
        json_data = json.dumps(existing_forms_info, indent=2)
        s3_client.put_object(
            Bucket=bucket,
            Key=sec_forms_key,
            Body=json_data.encode("utf-8"),
            ContentType="application/json",
            ACL="public-read",
        )
        print("Updated forms info uploaded to S3.")
    else:
        print("No new forms to update.")


def recreate_forms_info_in_s3():
    """
    Re-create the SEC forms info in S3 by fetching the latest details for all given form names via a single LLM call.
    This method overwrites the existing file with new information for every form.
    Use this when you update the SecForm model or want to refresh all the form details.
    """
    existing_forms_info = get_forms_info_from_s3()
    if not isinstance(existing_forms_info, dict):
        existing_forms_info = {}

    print(f"Recreating info for all forms: {set(existing_forms_info.keys())}")
    new_forms_info = get_forms_info(set(existing_forms_info.keys()))
    json_data = json.dumps(new_forms_info, indent=2)
    s3_client.put_object(
        Bucket=bucket,
        Key=sec_forms_key,
        Body=json_data.encode("utf-8"),
        ContentType="application/json",
        ACL="public-read",
    )
    print("SEC forms info in S3 has been recreated successfully.")


def get_all_filings_and_update_forms_info_in_s3(
    ticker: str, page: int = 0, limit: int = 50
) -> dict:
    """
    Retrieve all filings for a given ticker, and update the forms info in S3.
    """
    sec_filings = get_all_filings_for_ticker(ticker, page, limit)
    unique_forms = {filing.form for filing in sec_filings}
    update_forms_info_in_s3(unique_forms)
    return {"secFilings": [filing.model_dump() for filing in sec_filings]}


# --- Main Function ---
def main():
    ticker = "FVR"  # or any other ticker

    sec_filings = get_all_filings_for_ticker(ticker, page=0, limit=50)
    print("=== SEC Filings ===")
    print(json.dumps([f.model_dump() for f in sec_filings], indent=2))
    print("\n\n=== Forms Info ===")
    unique_forms = {filing.form for filing in sec_filings}
    print(f"Unique forms found: {unique_forms}")
    update_forms_info_in_s3(unique_forms)

    # To recreate (refresh) info for all forms, uncomment the following:
    # recreate_forms_info_in_s3()


# if __name__ == "__main__":
#     main()
