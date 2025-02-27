from dotenv import load_dotenv
from edgar import Company, use_local_storage, set_identity
from typing import Optional, Tuple

from reports_search_map import search_map

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")


def specific_report_text(ticker: str, report_type: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve raw text from the latest 10-Q filing attachments based on report type.
    """
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    if not filings:
        return None, f"No 10-Q filings found for ticker '{ticker}'."

    latest_10q = filings.latest()
    attachments = latest_10q.attachments

    keywords = search_map.get(report_type.lower())
    if not keywords:
        return None, f"Error: unrecognized report_type '{report_type}'."

    matched_texts = []
    for attach in attachments:
        purpose = (attach.purpose or "").lower()
        if any(k in purpose for k in keywords):
            try:
                matched_texts.append(attach.text())
            except Exception as e:
                matched_texts.append(
                    f"Error reading attachment seq={attach.sequence_number}: {str(e)}"
                )
            # For certain report types, only one or two attachments are needed.
            if report_type.lower() in ["income_statement", "cash_flow", "operation_statement"] and len(
                    matched_texts) == 1:
                break
            if report_type.lower() == "balance_sheet" and len(matched_texts) == 2:
                break

    if not matched_texts:
        return None, f"No attachments found for '{report_type}' in the latest 10-Q for '{ticker}'."

    return "\n\n".join(matched_texts), None

