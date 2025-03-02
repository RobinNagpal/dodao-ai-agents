from typing import List, TypedDict, Optional, Literal
from pydantic import BaseModel, Field



class Sector(BaseModel):
    id: int = Field(description="ID of the sector.")
    name: str = Field(description="Name of the sector.")


class IndustryGroup(BaseModel):
    id: int = Field(description="ID of the industry group.")
    name: str = Field(description="Name of the industry group.")

class ImportantMetric(BaseModel):
    key: str = Field(
        description="Unique identifier for the metric, formatted in lower case with underscores."
    )
    name: str = Field(description="Descriptive name of the metric.")
    description: str = Field(
        description="Detailed explanation of what the metric measures."
    )
    formula: str = Field(
        description="Mathematical formula used to calculate the metric (e.g., 'occupied_units / total_units')."
    )


class Report(BaseModel):
    key: str = Field(
        description="Unique identifier for the report associated with the criteria."
    )
    name: str = Field(description="Name of the report.")
    description: str = Field(
        description="Comprehensive description outlining the content and purpose of the report."
    )
    outputType: Literal["Text", "BarGraph", "PieChart"] = Field(
        description="Specifies the type of output to produced Text, BarGraph or PieChart."
    )


class Criteria(BaseModel):
    key: str = Field(
        description="Unique identifier for the criteria, formatted in lower case with underscores."
    )
    name: str = Field(description="Descriptive name of the criteria.")
    shortDescription: str = Field(
        description="Brief overview of the criteria and its intended evaluation purpose."
    )
    importantMetrics: List[ImportantMetric] = Field(
        description="List of key metrics that are used to evaluate this criteria."
    )
    reports: List[Report] = Field(
        description="List of reports generated based on the criteria's evaluation."
    )


class IndustryGroupCriteria(BaseModel):
    tickers: List[str] = Field(
        description="List of ticker symbols representing the companies."
    )
    selectedIndustryGroup: IndustryGroup = Field(
        description="Information about the selected industry group."
    )
    criteria: List[Criteria] = Field(
        description="Collection of evaluation criteria, including their metrics and reports."
    )


    
class CriteriaLookupItem(BaseModel):
    sectorId: int = Field(description="ID of the sector.", alias="sectorId")
    sectorName: str = Field(description="Name of the sector.", alias="sectorName")
    industryGroupId: int = Field(description="ID of the industry group.", alias="industryGroupId")
    industryGroupName: str = Field(description="Name of the industry group.", alias="industryGroupName")
    aiCriteriaFileLocation: Optional[str] = Field(default=None, description="Location of the AI criteria file.", alias="aiCriteriaFileLocation")
    customCriteriaFileLocation: Optional[str] = Field(default=None, description="Location of the custom criteria file.", alias="customCriteriaFileLocation")

class CriteriaLookupList(TypedDict):
    criteria: List[CriteriaLookupItem]
