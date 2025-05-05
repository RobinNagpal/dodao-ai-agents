import json
import requests
import boto3
import json
import os
import traceback
from dotenv import load_dotenv
from edgar import *
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, TypedDict

from src.public_equity_structures import (
    IndustryGroupCriteriaDefinition,
    CriterionMatchesOfLatest10Q,
    TickerReport,
    CriterionMatch,
    CriterionDefinition,
    SecFilingAttachment,
    Markdown,
)

load_dotenv()

s3_client = boto3.client("s3")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


class TickersInfoAndAttachments(TypedDict):
    cik: str
    period_of_report: str
    filing_date: str
    acc_number_no_dashes: str
    attachments: List[Attachment]
    management_discussions: str


class AttachmentWithContent(BaseModel):
    sequenceNumber: str
    documentName: str
    purpose: Optional[str]
    url: str
    relevance: float
    content: str


class AttachmentsByCriterion(BaseModel):
    criterion_key: str
    attachments: List[SecFilingAttachment]


class CriterionMatchTextItem(BaseModel):
    """Criterion match item"""

    criterion_key: str = Field(description="The key of the matched criterion")
    relevant_text: str = Field(
        description="The information that is relevant to the criterion which is extracted as per the matching instruction. Leave blank if no relevant information is found."
    )
    relevance_amount: float = Field(
        description="On the scale of 0-100 how relevant was the extracted content based on the matching instruction provided for this particular criterion"
    )


class CriterionMatchResponseNew(BaseModel):
    """Return LLM response in a structured format"""

    criterion_matches: List[CriterionMatchTextItem] = Field(
        description="List of criterion matches"
    )
    status: Literal["success", "failure"] = Field(
        description="If successful in processing the prompt and producing the output."
    )
    failureReason: Optional[str] = Field(
        description="The reason for the failure if the status is failed."
    )


class Latest10QInfo(BaseModel):
    filingUrl: str
    periodOfReport: str
    filingDate: str
    priceAtPeriodEnd: float


def get_ticker_report(ticker: str) -> TickerReport:
    base_url = os.environ.get("KOALAGAINS_BACKEND_URL", "http://localhost:3000")
    endpoint = f"{base_url}/api/tickers/{ticker}"
    response = requests.get(endpoint)
    response.raise_for_status()  # This will raise an error if the response is not 200 OK

    data = response.json()
    return TickerReport(**data)


def get_criteria_definition(ticker: str) -> IndustryGroupCriteriaDefinition:
    base_url = os.environ.get("KOALAGAINS_BACKEND_URL", "http://localhost:3000")
    endpoint = f"{base_url}/api/tickers/{ticker}/criteria-definition"
    response = requests.get(endpoint)
    response.raise_for_status()  # This will raise an error if the response is not 200 OK
    data = response.json()
    return IndustryGroupCriteriaDefinition(**data)


def save_latest10Q_financial_statements(
    ticker: str, latest10Q_financial_statements: str
):
    """
    Sends the updated ticker report JSON to an API endpoint via POST.
    """
    base_url = os.environ.get("KOALAGAINS_BACKEND_URL", "http://localhost:3000")
    endpoint = f"{base_url}/api/tickers/{ticker}/financial-statements"
    payload = {"latest10QFinancialStatements": latest10Q_financial_statements}
    data = json.dumps(payload, indent=2)
    print(f"Sending POST request to {endpoint} with data:")
    print(data)
    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, data=data.encode("utf-8"), headers=headers)
    response.raise_for_status()  # Raises an error if the response status is not 2xx

    print(f"Saved latest10Q Financial Statements for {ticker}.")


def create_criteria_match_analysis(
    period_of_report: str,
    attachment_name: Optional[str],
    attachment_content: str,
    criteria: List[CriterionDefinition],
) -> CriterionMatchResponseNew:

    criteria_json = json.dumps(
        [
            {
                "key": kw.key,
                "name": kw.name,
                "matchingInstruction": kw.matchingInstruction,
            }
            for kw in criteria
        ],
        indent=2,
    )

    prompt = f"""
    You are analyzing a section from an SEC 10-Q filing named '{attachment_name}'.
    Extract the relevant information based on the matching instructions provided for each criterion. Don't exclude any 
    relevant information.

    For each criterion item, output:
    - 'relevantText': All the relevant information that is extracted as per the matching instruction provided for this criterion.
    - 'relevance_amount': on a scale of (0-100) how relevant was the extracted content based on the matching instruction provided for this particular criterion.

    When extracting the relevant information:
    - Extract all the tabular data in the form of markdown tables.
    - Extract information only for the period_of_report: {period_of_report}
    - If the dats is present for three months ending for {period_of_report}, then only consider that column and ignore other columns like nine months ending, etc.
    - If three months ending data is not present, then consider the data for other columns also
    - Don't extract any other time periods.
    - Always Always Always capture the information about if the numbers are in thousands or millions, and include that information in the extracted content.
    - Always Always Always capture the information about if the numbers are in thousands or millions, and include that information in the extracted content.
    - There can be html tables in the attachment content, so make sure to consider the colspan to locate the correct values.
    
    For formatting the content:
    - Make sure there are three empty lines above and below each table.
    
    Return JSON that fits the EXACT structure of 'CriterionMatchResponse':
    {{
    "criterion_matches": [
        {{
        "criterion_key": "...",
        "relevant_text": "All the relevant information that is extracted as per the matching instruction provided for this criterion. Leave blank if no relevant information is found."
        "relevance_amount": 0-100
        }},
        ...
    ],
    "status": "success" or "failure",
    "failureReason": "optional"
    }}

    Criteria:
    {criteria_json}

    ATTACHMENT CONTENT:
    {attachment_content}
    """

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = model.with_structured_output(CriterionMatchResponseNew)
    response: CriterionMatchResponseNew = structured_llm.invoke(
        [HumanMessage(content=prompt)]
    )
    # print(f"LLM analysis response: \n\n{response.model_dump_json(indent=2)}")
    return response


def get_content_for_criterion_and_latest_quarter(
    period_of_report: str, raw_text: str, current_criterion: CriterionDefinition
) -> str:

    llm = ChatOpenAI(
        temperature=1,
        model="o4-mini",
    )

    system_prompt = f"""
    You are a financial data extraction assistant. The user has provided some
    text from a 10-Q attachment. It may contain multiple time periods
    (e.g. “3 months ended” vs “9 months ended,” or “Sep. 30, 2024” vs “Dec. 31, 2023”).

    Your job:
    - Make sure the keep the information matching the following criterion: {current_criterion.key} - {current_criterion.name} - {current_criterion.matchingInstruction}
    - Extract all the tabular data in the form of markdown tables.
    - Extract information only for the period_of_report: {period_of_report}
    - If the dats is present for three months ending for {period_of_report}, then only consider that column and ignore other columns like nine months ending, etc.
    - If three months ending data is not present, then consider the data for other columns also
    - Don't extract any other time periods.
    - Always Always Always capture the information about if the numbers are in thousands or millions, and include that information in the extracted content.
    - Always Always Always capture the information about if the numbers are in thousands or millions, and include that information in the extracted content.
    
    """

    user_prompt = f"""
    Here is part of the raw content from 10q.

    Raw text:
    {raw_text}
    """

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    return response.content


def get_ticker_info_and_attachments(ticker: str) -> TickersInfoAndAttachments:
    set_identity("dodao@gmail.com")
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    period_of_report = company.latest_tenq.period_of_report
    filing_date = company.latest_tenq.filing_date.isoformat()

    if not filings:
        raise Exception(f"Error: No 10-Q filings found for {ticker}.")

    latest_10q = filings.latest()
    cik = latest_10q.cik
    raw_acc_number = latest_10q.accession_number  # e.g. "0000950170-24-127114"
    acc_number_no_dashes = raw_acc_number.replace("-", "")

    attachments = latest_10q.attachments

    filing_obj = latest_10q.obj()

    return TickersInfoAndAttachments(
        cik=cik,
        period_of_report=period_of_report,
        filing_date=filing_date,
        acc_number_no_dashes=acc_number_no_dashes,
        attachments=attachments,
        management_discussions=filing_obj["Item 2"],
    )


def get_markdown_content(html_content: str) -> Markdown:
    """
    Sends HTML content to the backend endpoint and returns the resulting Markdown.
    """
    base_url = os.environ.get("KOALAGAINS_BACKEND_URL", "http://localhost:3000")
    endpoint = f"{base_url}/api/actions/html-to-markdown"
    payload = {"htmlContent": html_content}
    data = json.dumps(payload, indent=2)
    print(f"Sending POST request to {endpoint} with data:")
    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, data=data.encode("utf-8"), headers=headers)
    response.raise_for_status()  # Raises an error if the response status is not 2xx

    data = response.json()
    return Markdown(**data)


def get_criteria_matching_for_an_attachment(ticker_key: str, sequence_no: str) -> dict:
    if not sequence_no:
        raise Exception("Error: Sequence number is required.")

    industry_group_criteria = get_criteria_definition(ticker_key)
    ticker_info = get_ticker_info_and_attachments(ticker_key)
    attachments = ticker_info.get("attachments")

    attachment = next(a for a in attachments if a.sequence_number == sequence_no)

    attachment_content = str(attachment.content or "")
    if not attachment_content:
        raise Exception(f"Error: Attachment {sequence_no} has empty content.")

    attachment_purpose = str(attachment.purpose or "").lower()
    attachment_markdown = get_markdown_content(attachment_content).markdown

    match_analysis: CriterionMatchResponseNew = create_criteria_match_analysis(
        period_of_report=ticker_info.get("period_of_report"),
        attachment_name=attachment_purpose,
        attachment_content=attachment_markdown,
        criteria=industry_group_criteria.criteria,
    )

    return match_analysis.model_dump()


def get_criteria_matching_for_management_discussion(
    ticker_key: str, criterion_key: str
) -> str:
    if not criterion_key:
        raise Exception("Criterion key is required.")

    industry_group_criteria = get_criteria_definition(ticker_key)
    criterion = next(
        c for c in industry_group_criteria.criteria if c.key == criterion_key
    )
    ticker_info = get_ticker_info_and_attachments(ticker_key)
    management_discussions_content = ticker_info.get("management_discussions")

    matched_management_discussion_content = (
        get_content_for_criterion_and_latest_quarter(
            ticker_info.get("period_of_report"),
            management_discussions_content,
            criterion,
        )
    )

    return matched_management_discussion_content


def get_criterion_attachments_content(ticker: str, criterion_key: str) -> str:
    """
    This function:
      - Retrieves existing data from S3.
      - Extracts and processes the top 5 matched attachments.
      - Calls GPT to keep only the latest quarter's content.
      - If data is missing, runs the full process and then returns results.
    """
    public_equity_report: TickerReport = get_ticker_report(ticker)
    criteria_matches: Optional[CriterionMatchesOfLatest10Q] = (
        public_equity_report.criteriaMatchesOfLatest10Q
    )
    if criteria_matches is None:
        raise Exception(f"Error: No criterion matches found for {ticker}.")
    if criteria_matches.status != "Completed":
        raise Exception(f"Error: Criterion match process failed for {ticker}.")

    matches: List[CriterionMatch] = criteria_matches.criterionMatches
    if not matches:
        raise Exception(f"No matches available for criterion key: {criterion_key}.")

    criterion_match = next(
        (cm for cm in matches if cm.criterionKey == criterion_key), None
    )

    if criterion_match is None:
        raise Exception(f"Error: No criterion match found for {criterion_key}.")

    return criterion_match.matchedContent


def get_latest_10q_info(ticker: str) -> Latest10QInfo:
    """
    This function retrieves the 10-Q filing link (using the first attachment)
    and the reporting period for a given ticker.
    """
    ticker_info = get_ticker_info_and_attachments(ticker)
    cik = ticker_info.get("cik")
    acc_number_no_dashes = ticker_info.get("acc_number_no_dashes")
    period_of_report = ticker_info.get("period_of_report")
    filing_date = ticker_info.get("filing_date")
    attachments = ticker_info.get("attachments")

    if (
        not cik
        or not acc_number_no_dashes
        or not period_of_report
        or not attachments
        or not filing_date
    ):
        raise Exception(f"Error: Missing required information for {ticker}.")
    attach = attachments[1]
    attachment_document_name = str(attach.document or "")  # e.g. "R10.htm"
    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_number_no_dashes}/{attachment_document_name}"

    price_at_period_end = get_price_at_period_of_report(ticker)

    data: Latest10QInfo = {
        "filingUrl": filing_url,
        "periodOfReport": period_of_report,
        "filingDate": filing_date,
        "priceAtPeriodEnd": price_at_period_end,
    }
    return data


def get_price_at_period_of_report(
    ticker: str, period_of_report: Optional[str] = None
) -> float:
    """
    Retrieve the stock closing price for a given ticker on its reporting date.
    If `period_of_report` is provided, use it and return 0.0 if no data.
    If not provided, look it up; if that first query returns no data, then
    hit the `/prev` endpoint to get the last completed day’s bar.
    """
    explicit = bool(period_of_report)

    # Lookup if not explicit
    if not explicit:
        period_of_report = get_ticker_info_and_attachments(ticker).get(
            "period_of_report"
        )
        if not period_of_report:
            raise ValueError(f"Could not determine reporting period for {ticker}")

    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing POLYGON_API_KEY in environment")

    def fetch_for(date_str: str) -> float:
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
            f"{date_str}/{date_str}"
            f"?adjusted=true&sort=asc&limit=1&apiKey={api_key}"
        )
        resp = requests.get(url)
        resp.raise_for_status()
        payload = resp.json()
        return payload["results"][0]["c"] if payload.get("results") else 0.0

    # 1) Try the reporting‐period date
    price = fetch_for(period_of_report)

    # 2) If implicit lookup and no bar, hit `/prev`
    if not explicit and price == 0.0:
        prev_url = (
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev"
            f"?adjusted=true&apiKey={api_key}"
        )
        resp = requests.get(prev_url)
        resp.raise_for_status()
        payload = resp.json()
        price = payload["results"][0]["c"] if payload.get("results") else 0.0

    return price
