import os

# from rich import print
import requests
from dotenv import load_dotenv
from edgar import use_local_storage, set_identity, Company
from lxml import html
from lxml.etree import _Element
from rich import print

from src.ten_q.ten_q_content import parse_html_to_sections
from src.ten_q.ten_q_toc import (
    find_table_elements_with_toc,
    create_table_of_contents_structure,
)

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")

SEC_HEADERS = {
    "User-Agent": "Your Name (your.email@domain.com)",  # SEC requires valid contact info
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov",
}


def fetch_sec_html(url):
    try:
        sec_response = requests.get(url, headers=SEC_HEADERS, timeout=10)
        sec_response.raise_for_status()
        return sec_response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching document: {str(e)}")
        return None


if __name__ == "__main__":
    ticker = "ELS"
    company = Company(ticker)
    tenq = Company(ticker).latest_tenq.balance_sheet.data
    filings = company.get_filings(form="10-Q")

    if not filings:
        raise Exception(f"Error: No 10-Q filings found for {ticker}.")

    latest_10q = filings.latest()

    f = latest_10q
    sec_attachments = []
    f_url_base = f.filing_url.rsplit("/", 1)[0]
    html_url = str(f.document.url).replace(
        "https://www.sec.gov/<SGML FILE>", f_url_base
    )

    response = requests.get(html_url, headers=SEC_HEADERS, timeout=10)
    if response.status_code != 200:
        print(f"Error fetching document: HTTP {response.status_code}")
        raise Exception(f"Error fetching document: HTTP {response.status_code}")

    # Parse the fetched HTML document.
    doc: _Element = html.fromstring(response.content)
    eligible_tables = find_table_elements_with_toc(doc, limit=20)
    combined_tables = "\n".join(
        [f"{table.xpath}\n{table.cleaned_html}" for table in eligible_tables]
    )
    toc = create_table_of_contents_structure(combined_tables)
    parsed_contents = parse_html_to_sections(response.text, toc)

    # Convert parsed content to markdown.
    markdown_string = parsed_contents.to_markdown_string()
    print(markdown_string)

    # Save the markdown string to a file in the same directory.
    output_filename = "10q_content.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(markdown_string)
    print(f"Markdown content saved to {os.path.abspath(output_filename)}")
