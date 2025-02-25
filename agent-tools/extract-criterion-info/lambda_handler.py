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
# import boto3
from edgar import *
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from typing import Optional, Literal, List, Union
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Initialize S3 client
# s3_client = boto3.client("s3")
# S3_BUCKET_NAME = "your-s3-bucket-name"

class Criterion(BaseModel):
    """Criterion for which we need to extract data from SEC filings"""
    key: str = Field(description="The key for the criterion")
    name: str = Field(description="The name of the criterion")
    short_description: str = Field(description="A short description of the criterion")

class Criteria(BaseModel):
    sector: str = Field(description="The sector of the company")
    industry_group: str = Field(description="The industry group of the company")
    industry: str = Field(description="The industry of the company")
    sub_industry: str = Field(description="The sub-industry of the company")
    criteria: list[Criterion] = Field(description="The list of criteria to be matched")

class CriterionMatchItem(BaseModel):
    """Criterion match item"""
    criterion_key: str = Field(description="The key of the matched criterion")
    matched: bool = Field(description="Whether the criterion matched")
    matched_amount: float = Field(description="The percentage of the content that matched the keyword")

class CriterionMatchResponse(BaseModel):
    """Return LLM response in a structured format"""
    criterion_matches: List[CriterionMatchItem] = Field(description="List of criterion matches")
    status: Literal['success', 'failure'] = Field(description="If successful in processing the prompt and producing the output.")
    confidence: Optional[float] = Field(description="The confidence of the response in the range of 1-10.0, where 10.0 is very confident.")
    failureReason: Optional[str] = Field(description="The reason for the failure if the status is failed.")

class MatchedAttachment(BaseModel):
    name: str = Field(description="The name of the attachment")
    matched_amount: float = Field(description="The percentage of the content that matched the criterion")

class CriterionMatches(BaseModel):
    key: str = Field(description="The key of the criterion")
    matched_attachments: List[MatchedAttachment] = Field(description="The list of attachments that matched the criterion")

reit_criteria: Criteria = Criteria(
    sector="Real Estate",
    industry_group="Equity Real Estate Investment Trusts (REITs)",
    industry="Residential REITs",
    sub_industry="Multi-Family Residential REITs",
    criteria=[
        Criterion(key="rent", name="Rental Income of REIT", short_description="Rental Income of REIT, above and below market rents etc, and shares quantitative or qualitative data for it"),
        Criterion(key="debt", name="Debt obligations", short_description="Debt obligations, Mortgage Loans Payable, Lines of Credit and Term Loan, Schedule of Debt"),
        Criterion(key="cost_of_operations", name="Cost of Operations", short_description="Cost of Operations, Operating Expenses, Property Management Expenses, General and Administrative Expenses"),
        Criterion(key="stock_types", name="Stock Types", short_description="Stock Distribution, Common State, Preferred Shares, Dividends, Dividend Payout")
    ])

def create_criteria_match_analysis(attachment_name: str, content: str, keywords: list[Criterion]) -> Union[CriterionMatchResponse, None]:
    """
    Calls GPT-4o-mini to analyze if the content is relevant to provided topics.
    """

    criteria_json = json.dumps([kw.dict() for kw in keywords], indent=2)

    prompt = f"""
    You are analyzing a section from an SEC 10-Q filing named '{attachment_name}'.
    Determine how relevant the section is to each of the following criteria.

    ### **Importance of Precision**
        - We are collecting only **highly relevant** sections, as they will later be analyzed for financial ratios and investment insights.
        - **Loose or partial relevance is NOT enough**—a section should match **only if it contains direct, substantial information** about a topic.
        - A section **must be strongly and directly related** to the topic to be considered a match.

    For each criterion, output:
    - 'matched': true or false
    - 'matched_amount': a percentage (0-100) indicating how much of the section is directly relevant
    (Only return true if more than 60% is genuinely relevant).
    - You can match at most two criteria as 'true'.

    Return JSON that fits the EXACT structure of 'CriterionMatchResponse':
    {{
    "criterion_matches": [
        {{
        "criterion_key": "...",
        "matched": true/false,
        "matched_amount": 0-100
        }},
        ...
    ],
    "status": "success" or "failure",
    "confidence": 1-10,
    "failureReason": "optional"
    }}

    Criteria:
    {criteria_json}

    ATTACHMENT CONTENT:
    {content}
    """

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = model.with_structured_output(CriterionMatchResponse)
    
    try:
        response: CriterionMatchResponse = structured_llm.invoke([HumanMessage(content=prompt)])
        return response
    except Exception as e:
        print(f"Error analyzing content: {attachment_name} - {str(e)}")
        return None

# def append_to_s3(bucket: str, key: str, content: str):
#     """
#     Appends content to an existing file in S3 or creates a new file if it does not exist.
#     """
#     try:
#         # Try to fetch existing content
#         existing_content = ""
#         try:
#             obj = s3_client.get_object(Bucket=bucket, Key=key)
#             existing_content = obj['Body'].read().decode("utf-8")
#         except s3_client.exceptions.NoSuchKey:
#             pass  # File does not exist yet, so we'll create it

#         # Append new content
#         updated_content = existing_content + "\n\n" + content if existing_content else content

#         # Store updated content
#         s3_client.put_object(Bucket=bucket, Key=key, Body=updated_content.encode("utf-8"))
#         print(f"Updated S3 file: {key}")
#     except Exception as e:
#         print(f"Error updating file {key}: {str(e)}")

# def update_status(bucket: str, ticker: str, status: str):
#     """
#     Updates a status file in S3 to track processing.
#     """
#     key = f"{ticker}/Latest10QReport/status.json"
#     status_data = json.dumps({"status": status})
#     s3_client.put_object(Bucket=bucket, Key=key, Body=status_data.encode("utf-8"))

def get_raw_10q_text(ticker: str, keywords: list[Criterion]) -> list[CriterionMatches]:
    """
    Fetches the latest 10-Q filing, extracts attachments, analyzes content, and stores results.
    """
    print(f"Fetching latest 10-Q report for {ticker}...")
    print(f"Keywords: {keywords}")
    set_identity("dawoodmehmood52@gmail.com")
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    
    if not filings:
        raise Exception(f"Error: No 10-Q filings found for {ticker}.")

    latest_10q = filings.latest()
    attachments = latest_10q.attachments

    if not keywords:
        raise Exception("Error: No keywords provided for analysis.")
    
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

    from collections import defaultdict
    attachments_per_criterion = defaultdict(list)

    for attach in attachments:
        if attach.document_type != "HTML":
            continue

        attach_purpose = (attach.purpose or "").lower()
        if any(excluded in attach_purpose for excluded in excluded_purposes):
            continue

        content = attach.text()
        matched_result = create_criteria_match_analysis(
            attachment_name=attach_purpose or "Unnamed Attachment",
            content=content,
            keywords=keywords
        )
        if matched_result and matched_result.status == "success":
            for item in matched_result.criterion_matches:
                if item.matched:
                    attachments_per_criterion[item.criterion_key].append(
                        MatchedAttachment(
                            name=attach.purpose,
                            matched_amount=item.matched_amount
                        )
                    )

    criterion_to_matched_attachments: List[CriterionMatches] = []
    for c_key, matched_list in attachments_per_criterion.items():
        criterion_to_matched_attachments.append(
            CriterionMatches(
                key=c_key,
                matched_attachments=matched_list
            )
        )

    return criterion_to_matched_attachments

def lambda_handler(event, context):
    """
    AWS Lambda function to handle API requests.
    """
    try:
        # Parse JSON body
        body = json.loads(event["body"]) if "body" in event and event["body"] else {}

        ticker = body.get("ticker", "").upper()
        keywords_from_body = body.get("keywords", [])

        if not ticker:
            return json_response(400, {"error": "Missing 'ticker' parameter."})

        if not keywords_from_body:
            keywords = reit_criteria.criteria
        else:
            keywords = [Criterion(**kw) for kw in keywords_from_body]
        
        results = get_raw_10q_text(ticker, keywords)

        return json_response(200, [r.dict() for r in results])

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
