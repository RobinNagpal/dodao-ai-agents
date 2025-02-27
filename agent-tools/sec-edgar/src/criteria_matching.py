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
import os
from edgar import *
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import Optional, Literal, List, Union
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

s3_client = boto3.client("s3")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

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
    content: str = Field(description="The content of the attachment")
    matched_amount: float = Field(description="The percentage of the content that matched the criterion")

class CriterionMatches(BaseModel):
    key: str = Field(description="The key of the criterion")
    matched_attachments: List[MatchedAttachment] = Field(description="The list of attachments that matched the criterion")

class CriterialInfoOutput(BaseModel):
    ticker: str = Field(description="")
    sector: str = Field(description="The sector of the company")
    industry_group: str = Field(description="The industry group of the company")
    industry: str = Field(description="The industry of the company")
    sub_industry: str = Field(description="The sub-industry of the company")
    status: Literal['success', 'failure', 'processing'] = Field(description="If successful in processing the prompt and producing the output.")
    failureReason: Optional[str] = Field(description="The reason for the failure if the status is failed.")
    criterion_matches: List[CriterionMatches] = Field(description="The list of criteria that matched the criterion")
    
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

def s3_key_for_criterial_info(ticker: str) -> str:
    """Construct the S3 key/path for the JSON file."""
    return f"public-equities/US/{ticker}/latest-10q-criterial-info.json"

def get_criterial_info_from_s3(ticker: str) -> CriterialInfoOutput:
    """
    Attempts to load <bucket>/public-equities/US/{ticker}/latest-10q-criterial-info.json
    If not found, creates a new record with 'processing' status.
    """
    key = s3_key_for_criterial_info(ticker)
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        body = obj['Body'].read().decode("utf-8")
        data = json.loads(body)
        return CriterialInfoOutput(**data)
    except s3_client.exceptions.NoSuchKey:
        # File doesn't exist, create new
        info = CriterialInfoOutput(
            ticker=ticker,
            sector=reit_criteria.sector,
            industry_group=reit_criteria.industry_group,
            industry=reit_criteria.industry,
            sub_industry=reit_criteria.sub_industry,
            status="processing",
            failureReason=None,
            criterion_matches=[]
        )
        return info

def put_criterial_info_to_s3(ticker: str, info: CriterialInfoOutput):
    """Writes the updated info JSON to S3."""
    key = s3_key_for_criterial_info(ticker)
    data = json.dumps(info.dict(), indent=2)
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=data.encode("utf-8"),
        ContentType="application/json"
    )

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

def get_criterion_matched_attachments_list(ticker: str, keywords: list[Criterion]) -> list[CriterionMatches]:
    """
    Fetches the latest 10-Q filing, extracts attachments, analyzes content, and stores results.
    """
    print(f"Fetching latest 10-Q report for {ticker}...")
    print(f"Keywords: {keywords}")
    set_identity("dodao@gmail.com")
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    
    if not filings:
        raise Exception(f"Error: No 10-Q filings found for {ticker}.")

    latest_10q = filings.latest()
    cik = latest_10q.cik
    raw_acc_number = latest_10q.accession_number  # e.g. "0000950170-24-127114"
    acc_number_no_dashes = raw_acc_number.replace("-", "")
    
    attachments = latest_10q.attachments

    if not keywords:
        raise Exception("Error: No keywords provided for analysis.")
    
    excluded_purposes = [
        "cover",
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

        attach_purpose = str(attach.purpose or "").lower()
        filename = str(attach.document or "")  # e.g. "R10.htm"
        content = str(attach.text() or "")

        attachment_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_number_no_dashes}/{filename}"

        # Skipping conditions
        if any(excluded in attach_purpose for excluded in excluded_purposes):
            continue

        if not attach_purpose:
            print(f"Warning: Attachment {attach.purpose} has empty purpose; skipping.")
            continue
        if not filename:
            print(f"Warning: Attachment {attach.purpose} has empty filename; skipping.")
            continue
        if not content:
            print(f"Warning: Attachment {attach.purpose} has empty content; skipping.")
            continue
        
        matched_result = create_criteria_match_analysis(
            attachment_name=attach_purpose,
            content=content,
            keywords=keywords
        )
        if matched_result and matched_result.status == "success":
            for item in matched_result.criterion_matches:
                if item.matched:
                    attachments_per_criterion[item.criterion_key].append(
                        MatchedAttachment(
                            name=attach_purpose,
                            content=content,
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

def refine_financial_text(raw_text: str) -> str:
    """
    Calls GPT-4o-mini to filter out older periods and keep only
    the latest quarter. Preserves original formatting.
    """
    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-4o-mini",
    )

    system_prompt = """
    You are a financial data extraction assistant. The user has provided some
    text from a 10-Q attachment. It may contain multiple time periods
    (e.g. “3 months ended” vs “9 months ended,” or “Sep. 30, 2024” vs “Dec. 31, 2023”).

    Your job:
    1) Remove any older periods/columns, retaining only the latest quarter or period.
    2) Preserve the rest of the text exactly as it is, including spacing and line breaks,
    except for the removed columns/rows.
    3) Do not reformat or summarize; do not alter numbers or wording.
    4) If there is only one set of data, keep it entirely.
    5) Preserve all headings and subheadings as lines above the table.
    6) Return the final data in Markdown tabular format.
    """

    user_prompt = f"""
    Here is the raw financial statement text from one 10-Q attachment.
    Please remove older periods but keep the latest quarter/period.

    Raw text:
    {raw_text}
    """

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    return response.content

def process_top_attachments(criterion_match) -> str:
    """
    Helper function to process the top 5 attachments:
    - Sorts by matched_amount (highest first).
    - Refines each attachment individually.
    - Combines all refined texts into a single output.
    """
    if not criterion_match or not criterion_match.matched_attachments:
        return None
    
    # Sort and select the top 5 attachments
    top_attachments = sorted(criterion_match.matched_attachments, key=lambda x: x.matched_amount, reverse=True)[:5]
    refined_texts = [refine_financial_text(attachment.content) for attachment in top_attachments]
    return "\n\n".join(refined_texts)


def get_matching_criteria_attachments(ticker: str, criterion_key: str, keywords_from_input: Optional[List[dict]] = None) -> dict:
    """
    This function:
      - Retrieves existing data from S3.
      - Extracts and processes the top 5 matched attachments.
      - Calls GPT-4o-mini to keep only the latest quarter's content.
      - If data is missing, runs the full process and then returns results.
    """
    try:
        # Fetch existing criteria info from S3
        info = get_criterial_info_from_s3(ticker)

        # Check if file exists and contains matches
        if info.status == "success" and info.criterion_matches:
            # Find the criterion match for the given key
            criterion_match = next((cm for cm in info.criterion_matches if cm.key == criterion_key), None)

            # Process and return the refined content if available
            final_text = process_top_attachments(criterion_match)
            if final_text:
                return {"status": "success", "content": final_text}

        # If file does not exist or criterion_matches is empty, invoke the full process
        print("Data not found or incomplete. Running full extraction process.")
        info.status = "processing"
        put_criterial_info_to_s3(ticker, info)

        # Use keywords from input if provided, otherwise default to predefined criteria
        keywords = [Criterion(**kw) for kw in keywords_from_input] if keywords_from_input else reit_criteria.criteria

        # Run the full analysis process
        results = get_criterion_matched_attachments_list(ticker, keywords)
        info.status = "success"
        info.criterion_matches = results
        put_criterial_info_to_s3(ticker, info)

        # Fetch and process the top 5 attachments after populating
        criterion_match = next((cm for cm in results if cm.key == criterion_key), None)
        final_text = process_top_attachments(criterion_match)

        if final_text:
            return {"status": "success", "content": final_text}

        return {"status": "failure", "message": "No matching attachments found after processing."}

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")

        # Update S3 with failure status
        info = CriterialInfoOutput(
            ticker=ticker,
            sector=reit_criteria.sector,
            industry_group=reit_criteria.industry_group,
            industry=reit_criteria.industry,
            sub_industry=reit_criteria.sub_industry,
            status="failure",
            failureReason=error_msg,
            criterion_matches=[]
        )
        put_criterial_info_to_s3(ticker, info)
        return {"status": "failure", "message": error_msg}
