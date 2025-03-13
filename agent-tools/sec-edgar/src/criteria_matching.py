import json
import boto3
import os
from edgar import *
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import Optional, Literal, List, TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from src.public_equity_structures import (
    IndustryGroupCriteriaDefinition,
    CriterionMatchesOfLatest10Q,
    get_criteria_file_key,
    TickerReport,
    CriterionMatch,
    get_ticker_file_key,
    Sector,
    IndustryGroup,
    CriterionDefinition,
    SecFilingAttachment,
)
from collections import defaultdict
import traceback

load_dotenv()

s3_client = boto3.client("s3")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


class TickersInfoAndAttachments(TypedDict):
    cik: str
    acc_number_no_dashes: str
    attachments: List[Attachment]


class AttachmentWithContent(BaseModel):
    attachmentSequenceNumber: str
    attachmentDocumentName: str
    attachmentPurpose: Optional[str]
    attachmentUrl: str
    matchedPercentage: float
    attachmentContent: str


class AttachmentsByCriterion(BaseModel):
    criterion_key: str
    attachments: List[SecFilingAttachment]


class CriterionMatchItem(BaseModel):
    """Criterion match item"""

    criterion_key: str = Field(description="The key of the matched criterion")
    matched: bool = Field(description="Whether the criterion matched")
    matched_amount: float = Field(
        description="The percentage of the content that matched the keyword"
    )


class CriterionMatchResponse(BaseModel):
    """Return LLM response in a structured format"""

    criterion_matches: List[CriterionMatchItem] = Field(
        description="List of criterion matches"
    )
    status: Literal["success", "failure"] = Field(
        description="If successful in processing the prompt and producing the output."
    )
    failureReason: Optional[str] = Field(
        description="The reason for the failure if the status is failed."
    )


def get_object_from_s3(key: str) -> dict:
    try:
        s3_obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        body = s3_obj["Body"].read().decode("utf-8")
        data = json.loads(body)
        return data
    except Exception as e:
        print(f"Error while fetching object from S3: {key} = {str(e)}")
        print(traceback.format_exc())
        raise Exception(f"Error: {str(e)}")


def get_criteria(
    sector_name: str, industry_group_name: str
) -> IndustryGroupCriteriaDefinition:
    key = get_criteria_file_key(sector_name, industry_group_name)
    data = get_object_from_s3(key)
    return IndustryGroupCriteriaDefinition(**data)


def get_ticker_report(ticker: str) -> TickerReport:
    key = get_ticker_file_key(ticker)
    data = get_object_from_s3(key)
    return TickerReport(**data)


def put_ticker_report_to_s3(ticker: str, report: TickerReport):
    """Writes the updated info JSON to S3."""
    key = get_ticker_file_key(ticker)
    data = report.model_dump_json(indent=2)
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=data.encode("utf-8"),
        ContentType="application/json",
        ACL="public-read",
    )


def create_criteria_match_analysis(
    attachment_name: str, attachment_content: str, criteria: List[CriterionDefinition]
) -> CriterionMatchResponse:
    """
    Calls GPT-4o-mini to analyze if the content is relevant to provided topics.
    """

    criteria_json = json.dumps(
        [
            {"key": kw.key, "name": kw.name, "shortDescription": kw.shortDescription, "matchingInstruction": kw.matchingInstruction}
            for kw in criteria
        ],
        indent=2,
    )

    prompt = f"""
    You are analyzing a section from an SEC 10-Q filing named '{attachment_name}'.
    Determine how relevant the section is to each of the following criteria.

    ### **Importance of Precision**
        - We are collecting only **highly relevant** sections, as they will later be analyzed for financial ratios and investment insights.
        - **Loose or partial relevance is NOT enough**—a section should match **only if it contains direct, substantial information** about a topic.
        - A section **must be strongly and directly related** to the topic to be considered a match.

    For each criterion, output:
    - 'matched': true or false
    - 'matched_amount': a percentage (0-100) indicating how much of the section is directly relevant based on matchingInstruction
    (Only return true if the given matchingInstruction is satisfied for the criterion).
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
    "failureReason": "optional"
    }}

    Criteria:
    {criteria_json}

    ATTACHMENT CONTENT:
    {attachment_content}
    """

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = model.with_structured_output(CriterionMatchResponse)
    response: CriterionMatchResponse = structured_llm.invoke(
        [HumanMessage(content=prompt)]
    )
    # print(f"LLM analysis response: \n\n{response.model_dump_json(indent=2)}")
    return response


def get_ticker_info_and_attachments(ticker: str) -> TickersInfoAndAttachments:
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

    return TickersInfoAndAttachments(
        cik=cik, acc_number_no_dashes=acc_number_no_dashes, attachments=attachments
    )


def get_matched_attachments(
    ticker: str, criteria: List[CriterionDefinition]
) -> CriterionMatchesOfLatest10Q:
    """
    Fetches the latest 10-Q filing, extracts attachments, analyzes content, and stores results.
    """

    attachments_by_criterion_map = defaultdict(list[AttachmentWithContent])

    ticker_info = get_ticker_info_and_attachments(ticker)
    cik = ticker_info.get("cik")
    acc_number_no_dashes = ticker_info.get("acc_number_no_dashes")
    attachments = ticker_info.get("attachments")

    excluded_purposes = [
        "cover",
        "balance sheet",
        "statements of cash flows",
        "statement of cash flows",
        "statements of comprehensive income",
        "statements of operations and comprehensive income",
        "statement of operations and comprehensive income",
        "statements of operations",
        "statements of equity",
    ]

    attachment_start_index = 0

    for attach in attachments:

        attachment_start_index += 1

        if attach.document_type != "HTML":
            continue

        attachment_purpose = str(attach.purpose or "").lower()
        attachment_document_name = str(attach.document or "")  # e.g. "R10.htm"
        attachment_sequence_number: str = attach.sequence_number  # e.g. "R10.htm"
        attachment_content = str(attach.text() or "")
        attachment_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_number_no_dashes}/{attachment_document_name}"

        print(
            f"Processing attachment: {attachment_sequence_number} - {attachment_document_name} - {attachment_purpose} - {attachment_url}"
        )
        # Skipping conditions
        if any(excluded in attachment_purpose for excluded in excluded_purposes):
            continue

        if not attachment_purpose:
            print(f"Warning: Attachment {attach.purpose} has empty purpose; skipping.")
            continue
        if not attachment_document_name:
            print(f"Warning: Attachment {attach.purpose} has empty filename; skipping.")
            continue
        if not attachment_content:
            print(f"Warning: Attachment {attach.purpose} has empty content; skipping.")
            continue

        match_analysis = create_criteria_match_analysis(
            attachment_name=attachment_purpose,
            attachment_content=attachment_content,
            criteria=criteria,
        )

        if match_analysis and match_analysis.status == "failure":
            print(
                f"Error: LLM analysis failed for attachment {attachment_document_name}."
            )
            continue

        for criterion_match_result in match_analysis.criterion_matches:
            if criterion_match_result.matched:
                print(
                    f"Matched criterion: {criterion_match_result.criterion_key} - {criterion_match_result.matched_amount}"
                )
                attachments_by_criterion_map[
                    criterion_match_result.criterion_key
                ].append(
                    AttachmentWithContent(
                        attachmentSequenceNumber=attachment_sequence_number,
                        attachmentDocumentName=attachment_document_name,
                        attachmentPurpose=attachment_purpose,
                        attachmentUrl=attachment_url,
                        attachmentContent=attachment_content,
                        matchedPercentage=criterion_match_result.matched_amount,
                    )
                )
                print(
                    f"Number of matched attachments for {criterion_match_result.criterion_key} - {len(attachments_by_criterion_map[criterion_match_result.criterion_key])}"
                )

    criterion_to_matched_attachments: List[CriterionMatch] = []

    for c_key, matched_list in attachments_by_criterion_map.items():
        print(
            f"Criterion: {c_key} - Number of matched attachments: {len(matched_list)}"
        )
        for attachment in matched_list:
            print(
                f"Matched attachment: {attachment.attachmentDocumentName} - {attachment.matchedPercentage}- {attachment.attachmentUrl}"
            )
        top_attachments = sorted(   
            matched_list,
            key=lambda x: x.matchedPercentage,
            reverse=True,
        )[:5]

        refined_texts: list[str] = list()
        matched_attachments: list[SecFilingAttachment] = list()
        for attachment in top_attachments:
            print(
                f"Top attachment: {attachment.attachmentDocumentName} - {attachment.matchedPercentage}"
            )
            matched_attachment_content = filter_text_to_latest_quarter(
                attachment.attachmentContent
            )
            print(
                f"Done with filtering latest 10q content for : {attachment.attachmentDocumentName}"
            )
            sec_attachment = SecFilingAttachment(
                attachmentSequenceNumber=attachment.attachmentSequenceNumber,
                attachmentDocumentName=attachment.attachmentDocumentName,
                attachmentPurpose=attachment.attachmentPurpose,
                attachmentUrl=attachment.attachmentUrl,
                matchedPercentage=attachment.matchedPercentage,
                latest10QContent=matched_attachment_content,
            )
            matched_attachments.append(sec_attachment)
            refined_texts.append(
                filter_text_to_latest_quarter(attachment.attachmentContent)
            )

        criterion_to_matched_attachments.append(
            CriterionMatch(
                criterionKey=c_key,
                matchedAttachments=matched_attachments,
                matchedContent="\n\n".join(refined_texts),
            )
        )
        print(
            f"Done with adding matched attachments latest 10q content for criterion: {c_key}"
        )

    return CriterionMatchesOfLatest10Q(
        criterionMatches=criterion_to_matched_attachments,
        status="Completed",
        failureReason=None,
    )


# TODO: This prompt should be generic. Right now its a bit specific like “3 months ended” vs “9 months ended,” or “Sep. 30, 2024” vs “Dec. 31, 2023”
def filter_text_to_latest_quarter(raw_text: str) -> str:
    """
    Calls GPT-4o-mini to filter out older periods and keep only
    the latest quarter. Preserves original formatting.
    """
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini",
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

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    return response.content


def populate_criteria_matches(ticker: str):
    report: TickerReport = get_ticker_report(ticker)
    try:
        sector: Sector = report.selectedSector
        industry_group: IndustryGroup = report.selectedIndustryGroup
        industry_group_criteria = get_criteria(sector.name, industry_group.name)
        criteria: List[CriterionDefinition] = industry_group_criteria.criteria
        criteria_matches = get_matched_attachments(ticker, criteria)
        report.criteriaMatchesOfLatest10Q = criteria_matches
        put_ticker_report_to_s3(ticker, report)
    except Exception as e:
        print(f"Error: {str(e)}")
        criteria_matches = CriterionMatchesOfLatest10Q(
            criterionMatches=[], status="Failed", failureReason=str(e)
        )
        report.criteriaMatchesOfLatest10Q = criteria_matches
        put_ticker_report_to_s3(ticker, report)
        raise e


def get_criterion_attachments_content(ticker: str, criterion_key: str) -> str:
    """
    This function:
      - Retrieves existing data from S3.
      - Extracts and processes the top 5 matched attachments.
      - Calls GPT-4o-mini to keep only the latest quarter's content.
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
