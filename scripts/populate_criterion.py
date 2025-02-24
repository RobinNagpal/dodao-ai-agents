from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

industry_sectors = {
    "name": "US Public Equities",
    "id": "us-public-equities",
    "children": [
        {
            "name": "Information Technology (IT)",
            "id": "information-technology-it",
            "children": [
                {
                    "name": "Software & Services",
                    "id": "information-technology-it-software-services",
                    "children": [
                        {
                            "name": "Application Software",
                            "id": "information-technology-it-software-services-application-software"
                        },
                        {
                            "name": "Systems Software",
                            "id": "information-technology-it-software-services-systems-software"
                        }
                    ]
                },
                {
                    "name": "Technology Hardware & Equipment",
                    "id": "information-technology-it-technology-hardware-equipment",
                    "children": [
                        {
                            "name": "Communications Equipment",
                            "id": "information-technology-it-technology-hardware-equipment-communications-equipment"
                        },
                        {
                            "name": "Technology Hardware, Storage & Peripherals",
                            "id": "information-technology-it-technology-hardware-equipment-technology-hardware-storage-peripherals"
                        }
                    ]
                },
                {
                    "name": "Semiconductors & Semiconductor Equipment",
                    "id": "information-technology-it-semiconductors-semiconductor-equipment",
                    "children": [
                        {
                            "name": "Semiconductor Materials & Equipment",
                            "id": "information-technology-it-semiconductors-semiconductor-equipment-semiconductor-materials-equipment"
                        },
                        {
                            "name": "Semiconductors (Design & Manufacturing)",
                            "id": "information-technology-it-semiconductors-semiconductor-equipment-semiconductors-design-manufacturing"
                        }
                    ]
                }
            ]
        },
        {
            "name": "Health Care",
            "id": "health-care",
            "children": [
                {
                    "name": "Health Care Equipment & Services",
                    "id": "health-care-health-care-equipment-services",
                    "children": [
                        {
                            "name": "Health Care Equipment",
                            "id": "health-care-health-care-equipment-services-health-care-equipment"
                        },
                        {
                            "name": "Health Care Supplies",
                            "id": "health-care-health-care-equipment-services-health-care-supplies"
                        }
                    ]
                },
                {
                    "name": "Pharmaceuticals, Biotechnology & Life Sciences",
                    "id": "health-care-pharmaceuticals-biotechnology-life-sciences",
                    "children": [
                        {
                            "name": "Pharmaceuticals",
                            "id": "health-care-pharmaceuticals-biotechnology-life-sciences-pharmaceuticals"
                        },
                        {
                            "name": "Biotechnology",
                            "id": "health-care-pharmaceuticals-biotechnology-life-sciences-biotechnology"
                        }
                    ]
                }
            ]
        }
    ]
}

#  1. Write structured output
class DataPoint(BaseModel):
    name: str = Field(..., description="Name of the data point")
    description: str = Field(..., description="What this data point represents")
    source: Optional[str] = Field(None, description="Possible sources of data")


class NormalizedDataPoint(BaseModel):
    name: str = Field(..., description="Name of the normalized data point")
    formula: str = Field(..., description="Normalization method or formula")
    unit: str = Field(..., description="Unit of measurement")


class Benchmark(BaseModel):
    metric: str = Field(..., description="Name of the benchmark metric")
    ideal_value: str = Field(..., description="Ideal value for the metric")
    range: str = Field(..., description="Acceptable range for the metric")


class Company(BaseModel):
    name: str = Field(..., description="Company name")
    ticker: str = Field(..., description="Stock ticker symbol")
    market_cap: Optional[str] = Field(None, description="Market capitalization")
    revenue: Optional[str] = Field(None, description="Company revenue")


class ChartRecommendation(BaseModel):
    type: str = Field(..., description="Type of chart")
    usage: str = Field(..., description="Why this chart is useful")


class Criterion(BaseModel):
    name: str = Field(..., description="Criterion name")
    description: str = Field(..., description="Detailed description of the criterion")
    importance_rank: Optional[str] = Field(None, description="Rank of importance (Low, Medium, High, Critical)")
    reason: Optional[str] = Field(None, description="Explanation of why this criterion is important")
    examples: Optional[List[str]] = Field(None, description="Examples of the criterion")
    data_points: Optional[List[DataPoint]] = Field(None, description="List of specific data points")
    normalized_data_points: Optional[List[NormalizedDataPoint]] = Field(None, description="Normalized data points for comparison")
    benchmarks: Optional[List[Benchmark]] = Field(None, description="Ideal values and benchmarks")
    companies: Optional[List[Company]] = Field(None, description="List of public companies in this sub-subsector")
    key_points: Optional[List[str]] = Field(None, description="Five key points for analyzing this criterion")
    charts: Optional[List[ChartRecommendation]] = Field(None, description="Recommended charts for visualization")


class StructuredResponse(BaseModel):
    subsubsector: str = Field(..., description="Name of the sub-subsector")
    subsector: str=Field(..., description="Name of the subsector")  # Added subsector name for context
    id: str = Field(..., description="Unique ID of the sub-subsector")
    criteria: List[Criterion] = Field(..., description="List of 8 evaluation criteria")

# Function to call LLM and get structured response with context
def get_criteria_from_llm(subsector: str, subsubsector: str, subsubsector_id: str):
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY).with_structured_output(StructuredResponse)
    
    prompt = (
        f"You are analyzing the **{subsubsector}** industry, which is a part of the **{subsector}** subsector.\n"
        f"Generate evaluation criteria for the **{subsubsector}**.\n"
        f"Their must be 8 criterion for evaluating the **{subsubsector}** industry.\n"
        f"Provide a structured JSON output with the following fields for each criterion: "
        f"name, description, importance_rank, reason, examples, data_points (list of name, description, source), "
        f"normalized_data_points (list of name, formula, unit), benchmarks (list of metric, ideal_value, range), "
        f"public companies working same {subsubsector} industry (list of name, ticker, market_cap, revenue), "
        f"Five most important points to consider while analyzing the criterion, "
        f"and type of charts that can be used to represent the information for the criterion. Explain the chart type and why it is useful charts (list of type, usage)."
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    print(response)

    # Ensure the response includes the subsector name
    structured_response = response.dict()
    structured_response["subsector"] = subsector  # Add subsector for better organization
    structured_response["id"] = subsubsector_id  # Ensure the correct subsubsector ID is included
    
    return StructuredResponse(**structured_response)


# Function to save structured output to a JSON file
def save_structured_output(structured_response:StructuredResponse, sector_id, subsector_id):
    output_dir = f"output/{sector_id}/{structured_response.subsubsector.replace(' ', '_').lower()}/"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"{structured_response.subsubsector.replace(' ', '_').lower()}.json")

    # Save JSON file
    with open(file_path, "w") as f:
        json.dump(structured_response.dict(), f, indent=4)

    print(f"✅ Saved structured output: {file_path}")


# Function to process all sub-subsectors
def process_industry_sectors(industry_sectors):
    for sector in industry_sectors["children"]:  # Loop through each sector
        sector_id = sector["id"]
        for subsector in sector["children"]:  # Loop through each subsector
            subsector_name = subsector["name"]
            subsector_id = subsector["id"]
            for subsubsector in subsector["children"]:  # Loop through each sub-subsector
                subsubsector_name = subsubsector["name"]
                subsubsector_id = subsubsector["id"]

                print(f"🚀 Processing: {subsubsector_name} (Subsector: {subsector_name})...")

                # Fetch structured response from LLM with context
                structured_response = get_criteria_from_llm(subsector_name, subsubsector_name, subsubsector_id)

                # Save structured response to file
                save_structured_output(structured_response, sector_id, subsector_id)


# Run the process
if __name__ == "__main__":
    process_industry_sectors(industry_sectors)