import json
import os
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from edgar import *
os.environ["OPENAI_API_KEY"] = ""

# Define structured response model for LLM
class StructuredLLMResponse(BaseModel):
    outputString: str = Field(description="The output string expected as the response to the prompt.")
    status: Literal['success', 'failure'] = Field(description="Processing status.")
    failureReason: Optional[str] = Field(description="Reason for failure if applicable.")
    confidence: Optional[float] = Field(description="Confidence score (0.0 - 1.0).")

# GPT-4o-mini analysis function
def get_analysis(content: str, keywords: list, section: str) -> dict:
    prompt = f"""
    You are analyzing a section from an SEC 10-Q filing. Your task is to analyze the content 
    and determine whether the section solely focuses to one or two of the provided topics.
    
    For example if the section focuses a lot on:
    In case of rent - Rental Income of REIT, above and below market rents etc, and shares quantitave or qualitative data for it,
                    Rental Income Growth Over Time, Occupancy Rates, Lease Terms, Rental Reversion, Tenant Concentration
    In case of debt - Debt obligations, Mortgage Loans Payable, Lines of Credit and Term Loan, Schedule of Debt
    In case of fixed and variable cost - Property-Related Fixed Costs, Mortgage Payments & Debt Servicing, Property Taxes, Depreciation & Amortization,
                    Operational Variable Costs, Utilities & Maintenance, Marketing & Leasing Expenses
    
    ### **Importance of Precision**
    - We are collecting only **highly relevant** sections, as they will later be analyzed for financial ratios and investment insights.
    - **Loose or partial relevance is NOT enough**—a section should match **only if it contains direct, substantial information** about a topic.
    - The purpose is to assess whether this company (REIT) is worth investing in.

    ### **Matching Criteria:**
    - A section **must be strongly and directly related** to the topic to be considered a match.
    - **Avoid keyword-based matches**—evaluate meaning and financial relevance instead.
    - A section **can match at most two topics**.
    - Matching is based on **semantic relevance**, not just keyword appearance.
    - If a topic matches, set `"matched": true` and provide the confidence score and percentage of the content matched
    - Only return true if more than 70% of the section is very relevant to the topic.
    - If a topic does not match, set `"matched": false` and provide a low confidence score and percentage of the content matched

    ### **Response Format (JSON)**
    Return the response in JSON format where **each topic has a matched flag and a confidence score**: """ + """

    {
        "topic_rent": {"matched": true, "match_confidence": 0.85, "percentage_of_content_matched": "50%"},
        "topic_debt": {"matched": false, "match_confidence": 0.40, "percentage_of_content_matched": "20%"},
    }
    """ + f"""

    Topics: {keywords}
    
    Section content:
    {content}
    """

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = model.with_structured_output(StructuredLLMResponse)

    try:
        response = structured_llm.invoke([HumanMessage(content=prompt)])
        print(f'Response from gpt for section {section}: {response.outputString}')
        return json.loads(response.outputString)
    except Exception as e:
        print(f"Error analyzing content: {str(e)}")
        return {}

# Local storage function (simulates S3)
def append_to_file(filename: str, content: str):
    os.makedirs("local_results", exist_ok=True)
    path = os.path.join("local_results", filename)

    # Append content
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n\n" + content)
    print(f"Updated file: {path}")

# Main processing function
def process_attachments(ticker: str, keywords: List[str]):
    set_identity("dawoodmehmood52@gmail.com")
    company = Company(ticker)
    filings = company.get_filings(form="10-Q")
    
    if not filings:
        return {"error": f"No 10-Q filings found for ticker '{ticker}'."}

    latest_10q = filings.latest()
    attachments = latest_10q.attachments
    
    excluded_purposes = [
        "balance sheet", "statements of cash flows", "income statement", "document and entity information", "statements of operations"
    ]

    results = {}

    for attach in attachments:
        if not attach.purpose:
            continue
        attach_purpose = attach.purpose.lower()

        # Skip excluded financial statements
        if any(excluded in attach_purpose for excluded in excluded_purposes):
            continue

        try:
            content = attach.text()
            analysis = get_analysis(content, keywords, attach_purpose)

            # Store matching sections in relevant keyword files
            matched_topics = {k: v for k, v in analysis.items() if v["matched"]}
            for topic, match_data in matched_topics.items():
                topic_name = topic.replace("topic_", "")

                if topic_name not in results:
                    results[topic_name] = []

                results[topic_name].append({
                    "source": attach_purpose,
                    "confidence": match_data["match_confidence"],
                    "percentange": match_data["percentage_of_content_matched"],
                    "content": content
                })

        except Exception as e:
            print(f"Error processing attachment '{attach_purpose}': {str(e)}")

    # Sort and filter top 10 per keyword
    final_results = {}
    for topic_name, sections in results.items():
        # Sort by confidence score (highest first)
        sorted_sections = sorted(sections, key=lambda x: x["confidence"], reverse=True)
        
        # Keep only top 10
        top_sections = sorted_sections[:10]
        
        # Store only these in the file
        filename = f"{topic_name}.txt"
        content_to_store = "\n\n".join([sec["content"] for sec in top_sections])
        append_to_file(filename, content_to_store)

        # Store only the top 10 results in final results
        final_results[topic_name] = [
            {"source": sec["source"], "confidence": sec["confidence"]} for sec in top_sections
        ]

    return final_results if final_results else {"error": "No relevant topics found."}

# Run test locally
if __name__ == "__main__":
    ticker = "FVR"
    keywords = ["rent", "debt", "fixed and variable cost"]

    print(f"Processing 10-Q report for {ticker} with topics: {keywords}...")
    results = process_attachments(ticker, keywords)
    
    print("\n🎉 **Final Results:**")
    # Print results with section count
    for keyword, sections in results.items():
        print(f"\n🔹 **Keyword: {keyword}** (Matched Sections: {len(sections)})")
        print(json.dumps(sections, indent=2))

