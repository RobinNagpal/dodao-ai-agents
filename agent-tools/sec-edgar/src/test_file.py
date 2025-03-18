import json

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
    TableOfContents,
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


toc_json = """
{
  "parts": [
    {
      "name": "Part I - Financial Information",
      "items": [
        {
          "name": "Item 1: Financial Statements (unaudited)",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_10",
          "subItems": [
            {
              "name": "Index To Financial Statements",
              "anchorId": "",
              "subItems": [
                {
                  "name": "Consolidated Balance Sheets as of September 30, 2024 and December 31, 2023",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_16"
                },
                {
                  "name": "Consolidated Statements of Income and Comprehensive Income for the quarters and nine months ended September 30, 2024 and 2023",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_19"
                },
                {
                  "name": "Consolidated Statements of Changes in Equity for the quarters and nine months ended September 30, 2024 and 2023",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_22"
                },
                {
                  "name": "Consolidated Statements of Cash Flows for the nine months ended September 30, 2024 and 2023",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_28"
                },
                {
                  "name": "Notes to Consolidated Financial Statements",
                  "anchorId": "id3dda453371b496d93ed3b3548b5c007_31"
                }
              ]
            }
          ]
        },
        {
          "name": "Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_79",
          "subItems": []
        },
        {
          "name": "Item 3: Quantitative and Qualitative Disclosures About Market Risk",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_100",
          "subItems": []
        },
        {
          "name": "Item 4: Controls and Procedures",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_103",
          "subItems": []
        }
      ]
    },
    {
      "name": "Part II - Other Information",
      "items": [
        {
          "name": "Item 1: Legal Proceedings",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_109",
          "subItems": []
        },
        {
          "name": "Item 1A: Risk Factors",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_112",
          "subItems": []
        },
        {
          "name": "Item 2: Unregistered Sales of Equity Securities and Use of Proceeds",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_115",
          "subItems": []
        },
        {
          "name": "Item 3: Defaults Upon Senior Securities",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_118",
          "subItems": []
        },
        {
          "name": "Item 4: Mine Safety Disclosures",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_121",
          "subItems": []
        },
        {
          "name": "Item 5: Other Information",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_124",
          "subItems": []
        },
        {
          "name": "Item 6: Exhibits",
          "anchorId": "id3dda453371b496d93ed3b3548b5c007_127",
          "subItems": [
            {
              "name": "10.1 (a) Second Amendment, dated July 18, 2024",
              "anchorId": "link_placeholder_1",
              "subItems": []
            },
            {
              "name": "10.2 (b) Third Amended and Restated Credit Agreement, dated as of April 19, 2021",
              "anchorId": "link_placeholder_2",
              "subItems": []
            },
            {
              "name": "31.1 Certification of Chief Financial Officer Pursuant to Section 302 of the Sarbanes-Oxley Act of 2002",
              "anchorId": "link_placeholder_3",
              "subItems": []
            },
            {
              "name": "31.2 Certification of Chief Executive Officer Pursuant to Section 302 of the Sarbanes-Oxley Act of 2002",
              "anchorId": "link_placeholder_4",
              "subItems": []
            },
            {
              "name": "32.1 Certification of Chief Financial Officer Pursuant to 18 U.S.C. Section 1350",
              "anchorId": "link_placeholder_5",
              "subItems": []
            },
            {
              "name": "32.2 Certification of Chief Executive Officer Pursuant to 18 U.S.C. Section 1350",
              "anchorId": "link_placeholder_6",
              "subItems": []
            },
            {
              "name": "Inline XBRL Documents",
              "anchorId": "",
              "subItems": [
                {
                  "name": "101.INS XBRL Instance Document",
                  "anchorId": ""
                },
                {
                  "name": "101.SCH Inline XBRL Taxonomy Extension Schema Document",
                  "anchorId": ""
                },
                {
                  "name": "101.CAL Inline XBRL Taxonomy Extension Calculation Linkbase Document",
                  "anchorId": ""
                },
                {
                  "name": "101.LAB Inline XBRL Taxonomy Extension Label Linkbase Document",
                  "anchorId": ""
                },
                {
                  "name": "101.PRE Inline XBRL Taxonomy Extension Presentation Linkbase Document",
                  "anchorId": ""
                },
                {
                  "name": "101.DEF Inline XBRL Taxonomy Extension Definition Linkbase Document",
                  "anchorId": ""
                },
                {
                  "name": "104 Cover Page Interactive Data File included as Exhibit 101",
                  "anchorId": ""
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
"""

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
    print(f"Fetching HTML document from {html_url}...")
    response = requests.get(html_url, headers=SEC_HEADERS, timeout=10)
    if response.status_code != 200:
        print(f"Error fetching document: HTTP {response.status_code}")
        raise Exception(f"Error fetching document: HTTP {response.status_code}")

    # Parse the fetched HTML document.
    # doc: _Element = html.fromstring(response.content)
    # eligible_tables = find_table_elements_with_toc(doc, limit=20)
    # combined_tables = "\n".join(
    #     [f"{table.xpath}\n{table.cleaned_html}" for table in eligible_tables]
    # )
    # toc: TableOfContents = create_table_of_contents_structure(combined_tables)

    # parse the toc_json
    toc_parsed = TableOfContents(**json.loads(toc_json))
    parsed_contents = parse_html_to_sections(response.text, toc_parsed)

    # Convert parsed content to markdown.
    markdown_string = parsed_contents.to_markdown_string()
    print(markdown_string)

    # Save the markdown string to a file in the same directory.
    output_filename = "10q_content.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(markdown_string)
    # print(f"Markdown content saved to {os.path.abspath(output_filename)}")
