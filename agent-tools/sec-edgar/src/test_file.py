from typing import List

import copy
import re
# from rich import print
import requests
from dotenv import load_dotenv
from edgar import use_local_storage, set_identity, Company
from lxml import html, etree
from lxml.etree import _Element
from pydantic import BaseModel, Field
from rich import print
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")

SEC_HEADERS = {
    "User-Agent": "Your Name (your.email@domain.com)",  # SEC requires valid contact info
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}




class TocEligibleElements(BaseModel):
    xpath: str
    cleaned_html: str

class TenQSubSubItem(BaseModel):
    name: str = Field(description="Name of the sub-sub-item.")
    anchorId: str = Field(description="This is the id of the html element to which the hyperlink points")

class TenQSubItem(BaseModel):
    name: str = Field(description="Name of the sub-item.")
    anchorId: str = Field(description="This is the id of the html element to which the hyperlink points")
    subItems: List[TenQSubSubItem] = Field(description="List of sub-sub-items in the sub-item.")

class TenQItem(BaseModel):
    name: str = Field(description="Name of the item.")
    anchorId: str = Field(description="This is the id of the html element to which the hyperlink points")
    subItems: List[TenQSubItem] = Field(description="List of sub-items in the item.")

class Part(BaseModel):
    name: str = Field(description="Name of the part.")
    items: List[TenQItem] = Field(description="List of items in the part.")

class TableOfContents(BaseModel):
    """
    Represents the table of contents of a 10-Q filing. A 10-Q filing typically consists of two parts and the following
    items under the two parts. Each of the items then contains sub-items, and each sub-item may contains sub-sub-items.


    """
    parts: List[Part] = Field(
        description="List of parts in the 10-Q filing."
    )


def fetch_sec_html(url):
    try:
        sec_response = requests.get(url, headers=SEC_HEADERS, timeout=10)
        sec_response.raise_for_status()
        return sec_response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching document: {str(e)}")
        return None

def create_table_of_contents(combined_tables_str: str) -> TableOfContents:
    prompt = """
    The table elements below might have information about the sections and subsections of the 10-Q form.

    Below are the parts and items that are mostly present in the 10-Q form. Each of the items then contains sub-items, and each sub-item may contains sub-sub-items.
    
    {
        "PART I": {
            "ITEM 1": {
                "Title": "Financial Statements"
            },
            "ITEM 2": {
                "Title": "Management’s Discussion and Analysis of Financial Condition and Results of Operations"
            },
            "ITEM 3": {
                "Title": "Quantitative and Qualitative Disclosures About Market Risk"
            },
            "ITEM 4": {
                "Title": "Controls and Procedures"
            }
        },
        "PART II": {
            "ITEM 1": {
                "Title": "Legal Proceedings"
            },
            "ITEM 1A": {
                "Title": "Risk Factors"
            },
            "ITEM 2": {
                "Title": "Unregistered Sales of Equity Securities and Use of Proceeds"
            },
            "ITEM 3": {
                "Title": "Defaults Upon Senior Securities"
            },
            "ITEM 4": {
                "Title": "Mine Safety Disclosures"
            },
            "ITEM 5": {
                "Title": "Other Information"
            },
            "ITEM 6": {
                "Title": "Exhibits"
            }
        }
    }
    
    A part has items and items has sbitems, and subitems can have subitems.
    
    We want to create a nested json structure to represent the above information and include the id of the item and subitem whenever present in the table.
    
    These parts, items, subitems, and subsubitems should would be pointing to the element using an anchor tag which will be the id of the element and this is what
    we will be using in the json structure.
    
    Dont give me the code, just the json structure and try not using code for evaluating the json structure.
    
    Here are the tables:
    
    
    """ + combined_tables_str
    model = ChatOpenAI(model="gpt-4o", temperature=1)

    structured_llm = model.with_structured_output(TableOfContents)
    toc_response: TableOfContents = structured_llm.invoke(
        [HumanMessage(content=prompt)]
    )
    print(f"LLM analysis response: \n\n{toc_response.model_dump_json(indent=2)}")
    return toc_response

def get_xpath(element):
    """
    Mimics the JavaScript getXPath function.
    If the element has an id attribute, return an XPath using that id.
    Otherwise, build the XPath by traversing up the parent chain.
    """
    if element is None or not hasattr(element, "tag"):
        return ""

    # If the element has an id, return an XPath based on it.
    id_attr = element.get("id")
    if id_attr:
        return "//*[@id='%s']" % id_attr

    parts = []
    while element is not None and element.tag is not None:
        parent = element.getparent()
        if parent is not None:
            # Find all siblings of the same tag.
            siblings = parent.findall(element.tag)
            # Determine the index (1-based) among siblings.
            index = siblings.index(element) + 1
        else:
            index = 1
        parts.insert(0, "{}[{}]".format(element.tag.lower(), index))
        element = parent

    return "/" + "/".join(parts)


def remove_style_attributes(element):
    """
    Removes the "style" attribute from the element and all its descendants.
    """
    if 'style' in element.attrib:
        del element.attrib['style']
    for child in element.iterdescendants():
        if 'style' in child.attrib:
            del child.attrib['style']


def find_and_print_tables(html_doc: _Element, limit=20) -> list[TocEligibleElements]:
    """
    Finds table elements that:
      - Contain a nested <a> element, and
      - Have text content that contains "Part" or "Item" (case-insensitive).
    For each matching table, prints its XPath, original HTML, and cleaned HTML (without inline styles).
    """
    tables = html_doc.xpath("//table")
    table_xpaths: list[TocEligibleElements] = list()
    count = 0

    for table in tables:
        if count >= limit:
            break

        # Check for a nested <a> element
        has_anchor = table.xpath(".//a")
        # Check for text content matching "Part" or "Item" (case-insensitive)
        text_match = re.search(r"(part|item)", table.text_content(), re.IGNORECASE)

        if has_anchor and text_match:
            xpath = get_xpath(table)
            # Clone the table element so the original remains unchanged.
            cloned_table = copy.deepcopy(table)
            remove_style_attributes(cloned_table)
            # Convert the cleaned clone to an HTML string.
            cleaned_html = etree.tostring(cloned_table, pretty_print=True, encoding="unicode")

            table_xpaths.append(TocEligibleElements(
                xpath=xpath,
                cleaned_html=cleaned_html
            ))

            # print(f"Table {count + 1}: XPath: {xpath}")
            # print(f"Table {count + 1}: Original Element:\n{etree.tostring(table, pretty_print=True, encoding='unicode')}")
            print(f"Table {count + 1}: Cleaned HTML (without style attributes):\n{cleaned_html}\n")
            count += 1

    if count == 0:
        print("No table found meeting the specified criteria.")

    return table_xpaths


if __name__ == "__main__":
    ticker = "FVR"
    company = Company(ticker)
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
    eligible_tables = find_and_print_tables(doc, limit=20)
    combined_tables = "\n".join([f"{table.xpath}\n{table.cleaned_html}" for table in eligible_tables])
    toc = create_table_of_contents(combined_tables)
