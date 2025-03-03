from typing import List, TypedDict, Optional, Literal
from pydantic import BaseModel, Field


class CriterionImportantMetricDefinitionStructure(BaseModel):
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


class CriterionReportDefinitionStructure(BaseModel):
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


class CriteriaStructure(BaseModel):
    key: str = Field(
        description="Unique identifier for the criteria, formatted in lower case with underscores."
    )
    name: str = Field(description="Descriptive name of the criteria.")
    shortDescription: str = Field(
        description="Brief overview of the criteria and its intended evaluation purpose."
    )
    importantMetrics: List[CriterionImportantMetricDefinitionStructure] = Field(
        description="List of key metrics that are used to evaluate this criteria."
    )
    reports: List[CriterionReportDefinitionStructure] = Field(
        description="List of reports generated based on the criteria's evaluation."
    )


class IndustryGroupCriteriaStructure(BaseModel):
    tickers: List[str] = Field(
        description="List of ticker symbols representing the companies."
    )
    criteria: List[CriteriaStructure] = Field(
        description="Collection of evaluation criteria, including their metrics and reports."
    )


class CriteriaLookupItem(TypedDict):
    sectorId: int
    sectorName: str
    industryGroupId: int
    industryGroupName: str
    aiCriteriaFileUrl: Optional[str]
    customCriteriaFileUrl: Optional[str]


class CriteriaLookupList(TypedDict):
    criteria: List[CriteriaLookupItem]
