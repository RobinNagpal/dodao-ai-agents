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

from koala_gains.structures.public_equity_structures import (
    IndustryGroupCriteriaDefinition,
    CriterionMatchesOfLatest10Q,
    CriterionMatch,
    CriterionDefinition,
    Markdown,
)

load_dotenv()

s3_client = boto3.client("s3")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


class TickersInfoAndAttachments(TypedDict):
    cik: str
    period_of_report: str
    acc_number_no_dashes: str
    attachments: List[Attachment]
    management_discussions: str


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


def get_criteria_definition(ticker: str) -> IndustryGroupCriteriaDefinition:
    base_url = os.environ.get("KOALAGAINS_BACKEND_URL", "http://localhost:3000")
    endpoint = f"{base_url}/api/tickers/{ticker}/criteria-definition"
    response = requests.get(endpoint)
    response.raise_for_status()  # This will raise an error if the response is not 200 OK
    data = response.json()
    return IndustryGroupCriteriaDefinition(**data)


def save_criteria_matches(ticker: str, criteria_matches: CriterionMatchesOfLatest10Q):
    """
    Sends the updated ticker report JSON to an API endpoint via POST.
    """
    base_url = os.environ.get("KOALAGAINS_BACKEND_URL", "http://localhost:3000")
    endpoint = f"{base_url}/api/tickers/{ticker}/criteria-matches"
    payload = {"criterionMatchesOfLatest10Q": criteria_matches.model_dump()}
    data = json.dumps(payload, indent=2)

    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, data=data.encode("utf-8"), headers=headers)
    response.raise_for_status()  # Raises an error if the response status is not 2xx

    print(f"Saved criteria matches for {ticker}.")


def save_criteria_matches_attachment_count(ticker: str, count: int):
    """
    Sends the updated ticker report JSON to an API endpoint via POST.
    """
    base_url = os.environ.get("KOALAGAINS_BACKEND_URL", "http://localhost:3000")
    endpoint = (
        f"{base_url}/api/actions/tickers/{ticker}/save-matching-attachments-count"
    )
    payload = {"count": count}
    data = json.dumps(payload, indent=2)

    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, data=data.encode("utf-8"), headers=headers)
    response.raise_for_status()  # Raises an error if the response status is not 2xx

    print(f"Saved criteria matches attachment count for {ticker}.")


def save_criteria_matches_attachment_processed_count(ticker: str, count: int):
    """
    Sends the updated ticker report JSON to an API endpoint via POST.
    """
    base_url = os.environ.get("KOALAGAINS_BACKEND_URL", "http://localhost:3000")
    endpoint = (
        f"{base_url}/api/actions/tickers/{ticker}/save-matching-attachments-processed"
    )
    payload = {"count": count}
    data = json.dumps(payload, indent=2)

    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, data=data.encode("utf-8"), headers=headers)
    response.raise_for_status()  # Raises an error if the response status is not 2xx

    print(f"Saved criteria matches attachment processed count for {ticker}.")


def create_criteria_match_analysis(
    period_of_report: str,
    attachment_name: Optional[str],
    attachment_content: str,
    criteria: List[CriterionDefinition],
) -> CriterionMatchResponseNew:
    """
    Calls GPT-4o to analyze if the content is relevant to provided topics.
    """

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
    """
    Calls GPT-4o-mini to filter out older periods and keep only
    the latest quarter. Preserves original formatting.
    """
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

    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, data=data.encode("utf-8"), headers=headers)
    response.raise_for_status()  # Raises an error if the response status is not 2xx

    data = response.json()
    return Markdown(**data)


def get_matched_attachments(
    ticker: str, criteria: List[CriterionDefinition]
) -> CriterionMatchesOfLatest10Q:
    """
    Fetches the latest 10-Q filing, extracts attachments, analyzes content, and stores results.
    """

    ticker_info = get_ticker_info_and_attachments(ticker)
    cik = ticker_info.get("cik")
    acc_number_no_dashes = ticker_info.get("acc_number_no_dashes")
    attachments = ticker_info.get("attachments")

    print(
        f"Processing {len(attachments)} attachments for {ticker} for {ticker_info.get('period_of_report')}."
    )
    save_criteria_matches_attachment_count(ticker, len(attachments))
    excluded_purposes = [
        "balance sheet",
        "cash flows",
        "statements of comprehensive income",
        "operations and comprehensive income",
        "statements of operations",
        "statement of operations",
        "statements of income",
        "statement of income",
    ]

    attachment_start_index = 0

    criterion_to_matched_attachments_map: dict[str, CriterionMatch] = dict(
        {
            criterion.key: CriterionMatch(criterionKey=criterion.key, matchedContent="")
            for criterion in criteria
        }
    )

    for index, attach in enumerate(attachments):
        attachment_purpose = str(attach.purpose or "").lower()
        attachment_document_name = str(attach.document or "")  # e.g. "R10.htm"
        attachment_sequence_number: str = attach.sequence_number  # e.g. "R10.htm"
        attachment_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_number_no_dashes}/{attachment_document_name}"
        try:
            attachment_start_index += 1

            if attach.document_type != "HTML":
                continue

            attachment_content = str(attach.content or "")

            print(
                f"Processing attachment: {attachment_sequence_number} - {attachment_document_name} - {attachment_purpose} - {attachment_url}"
            )
            # Skipping conditions
            if any(excluded in attachment_purpose for excluded in excluded_purposes):
                continue

            if not attachment_content:
                print(
                    f"Warning: Attachment {attach.purpose} has empty content; skipping."
                )
                continue

            attachment_markdown = get_markdown_content(attachment_content).markdown
            match_analysis: CriterionMatchResponseNew = create_criteria_match_analysis(
                period_of_report=ticker_info.get("period_of_report"),
                attachment_name=attachment_purpose,
                attachment_content=attachment_markdown,
                criteria=criteria,
            )
            if match_analysis.status == "failure":
                print(
                    f"Error: LLM analysis failed for attachment {attachment_document_name}."
                )
                continue

            for criterion_match_result in match_analysis.criterion_matches:
                relevant_text = criterion_match_result.relevant_text
                if (
                    not relevant_text
                    or not relevant_text.strip()
                    or len(relevant_text) == 0
                ):
                    continue

                relevant_text = f"### {attachment_document_name} - {attachment_purpose}\n\n\n{relevant_text.strip()}\n\n\n"

                criterion_to_matched_attachments_map[
                    criterion_match_result.criterion_key
                ].matchedContent += f"\n{relevant_text}\n"
                save_criteria_matches_attachment_processed_count(ticker, index + 1)
        except Exception as e:
            print(
                f"Error processing attachment: {attachment_sequence_number} - {attachment_document_name} - {attachment_purpose} - {attachment_url}"
            )
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            continue
    for criterion in criteria:
        # Add another prompt to extract information from management discussion for the criteria
        management_discussions_content = ticker_info.get("management_discussions")
        matched_management_discussion_content = (
            get_content_for_criterion_and_latest_quarter(
                ticker_info.get("period_of_report"),
                management_discussions_content,
                criterion,
            )
        )
        matched_content = criterion_to_matched_attachments_map[
            criterion.key
        ].matchedContent
        all_matched_content = f"{matched_content}\n\n\n## From Management Discussion\n\n{matched_management_discussion_content}"
        criterion_to_matched_attachments_map[criterion.key].matchedContent = (
            all_matched_content
        )

    return CriterionMatchesOfLatest10Q(
        criterionMatches=list(criterion_to_matched_attachments_map.values()),
        status="Completed",
        failureReason=None,
    )


def populate_criteria_matches(ticker_key: str):
    try:
        industry_group_criteria = get_criteria_definition(ticker_key)
        criteria: List[CriterionDefinition] = industry_group_criteria.criteria
        criteria_matches = get_matched_attachments(ticker_key, criteria)
        save_criteria_matches(ticker_key, criteria_matches)
    except Exception as e:
        print(f"Error: {str(e)}")
        criteria_matches = CriterionMatchesOfLatest10Q(
            criterionMatches=[], status="Failed", failureReason=str(e)
        )
        save_criteria_matches(ticker_key, criteria_matches)
        raise e
