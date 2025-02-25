# Purpose:
#     This lambda will be called to extract data related to few topics from the reports.
#     Parameters like - rent, lease, debt, stock distribution

# There will be a function which will get the latest 10Q report from the SEC and all the attachments from the report.
# For each attachment(ignore balance_sheet, ic, cf), the function will call chatgpt 4o-mini to see if know if the attachments has data specific to
# the topic. At a time max 2 topics can match. The output will a json
# {
#    "topic_rent": {matched: true, match_confidence: 0.8},
#    "topic_debt": {matched: true, match_confidence: 0.8},
#  }

# We can keep a status file at the top to see if the process is completed or not.

# We can probably collect all this information and for each topic pick the top 10(or less) and store it in a file in s3 bucket.

# we create a file related to each topic in s3 bucket and store the attachments in the file.
#  So the path will be <ProjectTicker>/Latest10QReport/<TopicName>.txt
#  So the path will be FVR/Latest10QReport/rent.txt
#  So the path will be FVR/Latest10QReport/debt.txt

# We need to see how lambda executes in the background, as we want to say that it has started processing, and the
# lambda should die only after processing and collecting information for each topic.

# There can be another tool which can just read the file and return it to the agent for analysis. And the tool can
# throw an error if the file is not present.

import json
import boto3
from edgar import *
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from typing import Optional, Literal, List
from pydantic import BaseModel, Field



# Initialize S3 client
s3_client = boto3.client("s3")
S3_BUCKET_NAME = "your-s3-bucket-name"

class StructuredLLMResponse(BaseModel):
    """Return LLM response in a structured format"""
    outputString: str = Field(description="The output string expected as the response to the prompt.")
    status: Literal['success', 'failure'] = Field(
        description="If successful in processing the prompt and producing the output."
                    "Fail if no proper input was provided.")
    failureReason: Optional[str] = Field(description="The reason for the failure if the status is failed.")
    confidence: Optional[float] = Field(
        description="The confidence of the response in the range of 0.0-1.0, where 1.0 is very confident.")

def get_analysis(content: str, keywords: list) -> dict:
    """
    Calls GPT-4o-mini to analyze if the content is relevant to provided topics.
    """
    prompt = f"""
    You are analyzing a section from an SEC 10-Q filing. Your task is to analyze the content 
    and determine whether the section solely focuses to one or two of the provided topics.
    
    For example if the section focuses a lot on:
    In case of rent - Rental Income of REIT, above and below market rents etc, and shares quantitave or qualitative data for it,
                    Rental Income Growth Over Time, Occupancy Rates, Lease Terms, Rental Reversion, Tenant Concentration
    In case of debt - Debt obligations, Mortgage Loans Payable, Lines of Credit and Term Loan, Schedule of Debt
    
    ### **Importance of Precision**
    - We are collecting only **highly relevant** sections, as they will later be analyzed for financial ratios and investment insights.
    - **Loose or partial relevance is NOT enough**—a section should match **only if it contains direct, substantial information** about a topic.
    - The purpose is to assess whether this company (REIT) is worth investing in.

    ### **Matching Criteria:**
    - A section **must be strongly and directly related** to the topic to be considered a match.
    - **Avoid keyword-based matches**—evaluate meaning and financial relevance instead.
    - A section **can match at most two topics**.
    - Matching is based on **semantic relevance**, not just keyword appearance.
    - If a topic matches, set `"matched": true` and provide the confidence score.
    - Only return true if more than 40% of the section is very relevant to the topic.
    - If a topic does not match, set `"matched": false` and provide a low confidence score.

    ### **Response Format (JSON)**
    Return the response in JSON format where **each topic has a matched flag and a confidence score**: """ + """

    {
        "topic_rent": {"matched": true, "match_confidence": 0.85},
        "topic_debt": {"matched": false, "match_confidence": 0.40},
        ...
    }
    """ + f"""

    Topics: {keywords}
    
    Section content:
    {content}
    """

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = model.with_structured_output(StructuredLLMResponse)
    
    try:
        response = structured_llm.invoke([HumanMessage(content=prompt)])
        return json.loads(response.outputString)
    except Exception as e:
        print(f"Error analyzing content: {str(e)}")
        return {}

def append_to_s3(bucket: str, key: str, content: str):
    """
    Appends content to an existing file in S3 or creates a new file if it does not exist.
    """
    try:
        # Try to fetch existing content
        existing_content = ""
        try:
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            existing_content = obj['Body'].read().decode("utf-8")
        except s3_client.exceptions.NoSuchKey:
            pass  # File does not exist yet, so we'll create it

        # Append new content
        updated_content = existing_content + "\n\n" + content if existing_content else content

        # Store updated content
        s3_client.put_object(Bucket=bucket, Key=key, Body=updated_content.encode("utf-8"))
        print(f"Updated S3 file: {key}")
    except Exception as e:
        print(f"Error updating file {key}: {str(e)}")

def update_status(bucket: str, ticker: str, status: str):
    """
    Updates a status file in S3 to track processing.
    """
    key = f"{ticker}/Latest10QReport/status.json"
    status_data = json.dumps({"status": status})
    s3_client.put_object(Bucket=bucket, Key=key, Body=status_data.encode("utf-8"))

def get_raw_10q_text(ticker: str, keywords: List[str]) -> dict:
    """
    Fetches the latest 10-Q filing, extracts attachments, analyzes content, and stores results.
    """
    print(f"Fetching latest 10-Q report for {ticker}...")
    set_identity("dawoodmehmood52@gmail.com")
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    
    if not filings:
        return {"error": f"No 10-Q filings found for ticker '{ticker}'."}

    latest_10q = filings.latest()
    attachments = latest_10q.attachments

    if not keywords:
        return {"error": "Error: Empty keywords list."}

    # Update processing status
    update_status(S3_BUCKET_NAME, ticker, "Processing")

    results = {}

    for attach in attachments:
        # Get the purpose of the attachment and normalize it to lowercase
        attach_purpose = (attach.purpose or "").lower()

        # Define a set of terms indicating financial statements that should be skipped
        excluded_purposes = [
            "balance sheet",
            "statements of cash flows",
            "statement of cash flows",
            "statements of comprehensive income",
            "statements of operations and comprehensive income",
            "statement of operations and comprehensive income",
            "statements of operations",
            "statements of equity"
        ]

        # Skip attachments that match the excluded purposes
        if any(excluded in attach_purpose for excluded in excluded_purposes):
            continue

        try:
            content = attach.text()
            analysis = get_analysis(content, keywords)

            # Check matched topics
            matched_topics = {k: v for k, v in analysis.items() if v["matched"]}
            if matched_topics:
                for topic, match_data in matched_topics.items():
                    topic_name = topic.replace("topic_", "")
                    s3_path = f"{ticker}/Latest10QReport/{topic_name}.txt"
                    
                    append_to_s3(S3_BUCKET_NAME, s3_path, content)
                    
                    if topic_name not in results:
                        results[topic_name] = []
                    
                    results[topic_name].append({
                        "source": attach_purpose,
                        "confidence": match_data["match_confidence"]
                    })

        except Exception as e:
            print(f"Error processing attachment {attach_purpose}: {str(e)}")

    # Update status file
    update_status(S3_BUCKET_NAME, ticker, "Completed")

    return results if results else {"error": "No relevant topics found in the latest 10-Q report."}

def lambda_handler(event, context):
    """
    AWS Lambda function to handle API requests.
    """
    try:
        # Parse JSON body
        body = json.loads(event["body"]) if "body" in event and event["body"] else {}

        ticker = body.get("ticker", "").upper()
        keywords = body.get("keywords", [])

        if not ticker or not keywords:
            return json_response(400, {"error": "Missing 'ticker' or 'keywords' parameter."})

        results = get_raw_10q_text(ticker, keywords)

        return json_response(200 if "error" not in results else 400, results)

    except Exception as e:
        return json_response(500, {"error": f"Internal server error: {str(e)}"})

def json_response(http_status, payload):
    """
    Helper to format a Lambda Function response consistently.
    """
    return {
        "statusCode": http_status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload)
    }