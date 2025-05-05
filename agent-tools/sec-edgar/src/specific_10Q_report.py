from dotenv import load_dotenv
from edgar import Company, use_local_storage, set_identity

from src.reports_search_map import search_map

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")


def specific_report_text(ticker: str, report_type: str, fetch_raw_content = False) -> str:
    """
    Retrieve raw text from the latest 10-Q filing attachments based on report type.
    """
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    if not filings:
        raise ValueError(f"No 10-Q filings found for ticker '{ticker}'.")

    latest_10q = filings.latest()
    attachments = latest_10q.attachments

    keywords = search_map.get(report_type.lower())
    if not keywords:
        raise ValueError(f"Report type '{report_type}' not found in search map.")

    matched_texts = []
    for attach in attachments:
        purpose = (attach.purpose or "").lower()
        if any(k in purpose for k in keywords):

            if fetch_raw_content:
                # If fetch_raw_content is True, return the raw content of the attachment
                matched_texts.append(attach.content)
            else:
                matched_texts.append(attach.text())

            # For certain report types, only one or two attachments are needed.
            if (
                report_type.lower()
                in ["income_statement", "cash_flow", "operation_statement", "equity_statement"]
                and len(matched_texts) == 1
            ):
                break
            if report_type.lower() == "balance_sheet" and len(matched_texts) == 2:
                break

    if not matched_texts:
        raise ValueError(
            f"No matching attachments found for ticker: {ticker} and report type '{report_type}'."
        )
    return "\n\n".join(matched_texts)
