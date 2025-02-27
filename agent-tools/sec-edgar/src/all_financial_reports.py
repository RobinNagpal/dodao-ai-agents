from dotenv import load_dotenv
from edgar import Company, use_local_storage, set_identity
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.reports_search_map import search_map

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")

def refine_financial_text(raw_text: str) -> str:
    """
    Call an LLM (e.g., GPT-4) to filter out older periods and keep only
    the latest quarter. Preserves original formatting as much as possible.
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
    7) Include headings or subheadings as lines immediately above the table (in plain text or bold text). Do not remove them.
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


def get_xbrl_financials(ticker: str) -> str:
    """
    Retrieve all attachments (raw text) from the latest 10-Q whose purpose
    matches *any* of the financial statement keywords (balance sheet,
    income statement, cash flow, operation statement). Returns a single
    concatenated string of all matched texts.
    """

    all_keywords = set()
    for keywords in search_map.values():
        all_keywords.update(keywords)

    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    if not filings:
        raise Exception(f"No 10-Q filings found for ticker '{ticker}'.")

    latest_10q = filings.latest()
    attachments = latest_10q.attachments

    matched_texts = []
    for attach in attachments:
        purpose = (attach.purpose or "").lower()
        if any(k in purpose for k in all_keywords):
            try:
                raw_attachment_text = attach.text()
                refined_text = refine_financial_text(raw_attachment_text)
                matched_texts.append(refined_text)
            except Exception as e:
                matched_texts.append(
                    f"Error reading attachment seq={attach.sequence_number}: {str(e)}"
                )

    if not matched_texts:
        return f"No relevant attachments found for in the latest 10-Q for '{ticker}'."

    return "\n\n".join(matched_texts)
