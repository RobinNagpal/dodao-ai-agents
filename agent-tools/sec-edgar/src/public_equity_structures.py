import re
from typing import List, Optional, Literal, Dict, Any
import os
from pydantic import BaseModel, Field

# Updated ProcessingStatus including "NotStarted"
ProcessingStatus = Literal["Completed", "Failed", "InProgress", "NotStarted"]

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


class IndustryGroup(BaseModel):
    id: int
    name: str


class Sector(BaseModel):
    id: int
    name: str


class SecFilingAttachment(BaseModel):
    attachmentSequenceNumber: str
    attachmentDocumentName: Optional[str] = None
    attachmentPurpose: Optional[str] = None
    attachmentUrl: str
    relevance: Optional[float] = None
    attachmentContent: Optional[str] = None


class CriterionMatch(BaseModel):
    criterionKey: str
    matchedAttachments: List[SecFilingAttachment]
    matchedContent: str


# In TS, the criterionMatches field is optional
class CriterionMatchesOfLatest10Q(BaseModel):
    criterionMatches: Optional[List[CriterionMatch]] = None
    status: ProcessingStatus
    failureReason: Optional[str] = None


class TickerReport(BaseModel):
    ticker: str
    selectedIndustryGroup: IndustryGroup
    selectedSector: Sector
    evaluationsOfLatest10Q: Any = None
    criteriaMatchesOfLatest10Q: Optional[CriterionMatchesOfLatest10Q] = None


# Renamed to align with TS "MetricItemDefinition"
class MetricItemDefinition(BaseModel):
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


# Renamed to align with TS "CriterionReportDefinition"
class CriterionReportDefinition(BaseModel):
    key: str = Field(
        description="Unique identifier for the report associated with the criteria."
    )
    name: str = Field(description="Name of the report.")
    description: str = Field(
        description="Comprehensive description outlining the content and purpose of the report."
    )
    outputType: Literal["Text", "BarGraph", "PieChart", "WaterfallChart"] = Field(
        description="Specifies the type of output to produce: Text, BarGraph, PieChart, or WaterfallChart."
    )


# Renamed from IndustryGroupCriterion to CriterionDefinition and updated field types.
class CriterionDefinition(BaseModel):
    key: str = Field(
        description="Unique identifier for the criteria, formatted in lower case with underscores."
    )
    name: str = Field(description="Descriptive name of the criteria.")
    shortDescription: str = Field(
        description="Brief overview of the criteria and its intended evaluation purpose."
    )
    matchingInstruction: str = Field(
        description="Instructions on how to match the criteria with the latest 10-Q report."
    )
    importantMetrics: List[MetricItemDefinition] = Field(
        description="List of key metrics that are used to evaluate this criteria."
    )
    reports: List[CriterionReportDefinition] = Field(
        description="List of reports generated based on the criteria's evaluation."
    )


# Renamed to align with TS "IndustryGroupCriteriaDefinition"
class IndustryGroupCriteriaDefinition(BaseModel):
    tickers: List[str]
    selectedSector: Sector
    selectedIndustryGroup: IndustryGroup
    criteria: List[CriterionDefinition]


class CriteriaLookupItem(BaseModel):
    sectorId: int
    sectorName: str
    industryGroupId: int
    industryGroupName: str
    aiCriteriaFileUrl: Optional[str] = None
    customCriteriaFileUrl: Optional[str] = None


class CriteriaLookupList(BaseModel):
    criteria: List[CriteriaLookupItem]


# Updated CreateSingleReportsRequest based on TS:
# Now it takes industryGroupId and sectorId as integers.
class CreateSingleReportsRequest(BaseModel):
    ticker: str
    criterionKey: str
    industryGroupId: int
    sectorId: int


# New request type as defined in TS.
class RegenerateSingleCriterionReportsRequest(BaseModel):
    ticker: str
    criterionKey: str


# SpiderScore model
class SpiderScore(BaseModel):
    comment: str
    score: int


# SpiderGraphPie model
class SpiderGraphPie(BaseModel):
    key: str
    name: str
    summary: str
    scores: List[SpiderScore]


# SpiderGraphForTicker is a mapping from string to SpiderGraphPie.
SpiderGraphForTicker = Dict[str, SpiderGraphPie]


# Exactly the same as the TypeScript implementation:
# https://github.com/RobinNagpal/dodao-ui/blob/main/shared/web-core/src/utils/auth/slugify.ts
def slugify(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^\w-]+", "", s)
    s = re.sub(r"-+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def get_criteria_file_url(sector_name: str, industry_group_name: str) -> str:
    full_key = get_criteria_file_key(sector_name, industry_group_name)
    full_url = f"https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/{full_key}"
    return full_url


def get_criteria_file_key(sector_name: str, industry_group_name: str) -> str:
    full_key = f"public-equities/US/gics/{slugify(sector_name)}/{slugify(industry_group_name)}/custom-criteria.json"
    return full_key


def get_ticker_file_key(ticker: str) -> str:
    full_key = f"public-equities/US/tickers/{ticker}/latest-10q-report.json"
    return full_key
