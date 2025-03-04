import re
from typing import TypedDict, List, Optional, Literal
import os
from pydantic import BaseModel

ProcessingStatus = Literal["Completed", "Failed", "InProgress"]

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


class IndustryGroup(BaseModel):
    id: int
    name: str


class Sector(BaseModel):
    id: int  # ID of the sector.
    name: str  # Name of the sector.


class Metric(BaseModel):
    metric: str
    value: float  # Use float; adjust if integers are expected sometimes.
    calculationExplanation: str


class ImportantMetrics(BaseModel):
    status: str
    metrics: List[List[Metric]]  # Nested list structure as provided.


class Report(BaseModel):
    key: str
    name: str
    outputType: str
    status: str
    outputFile: Optional[str]  # Optional since some reports use "outputFileUrl"
    outputFileUrl: Optional[str]  # Optional field.


class PerformanceChecklistItem(BaseModel):
    checklistItem: str
    oneLinerExplanation: str
    informationUsed: str
    detailedExplanation: str
    evaluationLogic: str
    score: int


class CriteriaEvaluation(BaseModel):
    criterionKey: str
    importantMetrics: Optional[ImportantMetrics]
    reports: Optional[List[Report]]
    performanceChecklist: Optional[List[PerformanceChecklistItem]]


class SecFilingAttachment(BaseModel):
    attachmentSequenceNumber: str
    attachmentDocumentName: str
    attachmentPurpose: Optional[str]
    attachmentUrl: str
    matchedPercentage: float


class CriterionMatch(BaseModel):
    criterionKey: str
    matchedAttachments: List[SecFilingAttachment]
    matchedContent: str


class CriterionMatchesOfLatest10Q(BaseModel):
    criterionMatches: List[CriterionMatch]
    status: ProcessingStatus
    failureReason: Optional[str]


class TickerReport(BaseModel):
    ticker: str
    selectedIndustryGroup: IndustryGroup
    selectedSector: Sector
    evaluationsOfLatest10Q: Optional[List[CriteriaEvaluation]]
    criteriaMatchesOfLatest10Q: Optional[CriterionMatchesOfLatest10Q]


class CriterionImportantMetricItem(BaseModel):
    key: str  # Unique identifier for the metric, formatted in lower case with underscores.
    name: str  # Descriptive name of the metric.
    description: str  # Detailed explanation of what the metric measures.
    formula: str  # Mathematical formula used to calculate the metric (e.g., 'occupied_units / total_units').


class CriterionReportItem(BaseModel):
    key: str  # Unique identifier for the report associated with the criteria.
    name: str  # Name of the report.
    description: str  # Comprehensive description outlining the content and purpose of the report.
    outputType: Literal[
        "Text", "BarGraph", "PieChart"
    ]  # Specifies the type of output: Text, BarGraph or PieChart.


class IndustryGroupCriterion(BaseModel):
    key: str
    name: str
    shortDescription: str
    importantMetrics: List[CriterionImportantMetricItem]
    reports: List[CriterionReportItem]


class IndustryGroupCriteria(BaseModel):
    tickers: List[str]
    selectedSector: Sector
    selectedIndustryGroup: IndustryGroup
    criteria: List[IndustryGroupCriterion]


class CriteriaLookupItem(BaseModel):
    sectorId: int
    sectorName: str
    industryGroupId: int
    industryGroupName: str
    aiCriteriaFileUrl: Optional[str] = None
    customCriteriaFileUrl: Optional[str] = None


class CriteriaLookupList(BaseModel):
    criteria: list[CriteriaLookupItem]


class CreateAllReportsRequest(BaseModel):
    ticker: str
    selectedIndustryGroup: IndustryGroup
    selectedSector: Sector


class CreateSingleReportsRequest(BaseModel):
    ticker: str
    criterionKey: str
    selectedIndustryGroup: IndustryGroup
    selectedSector: Sector


# Exactly same as the typescript implementation we have here
# https://github.com/RobinNagpal/dodao-ui/blob/main/shared/web-core/src/utils/auth/slugify.ts
def slugify(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^\w-]+", "", s)
    s = re.sub(r"-+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def get_criteria_file_url(sector_name: str, industry_group_name: str):
    full_key = get_criteria_file_key(sector_name, industry_group_name)
    full_url = f"https://{BUCKET_NAME}.s3.us-east-1.amazonaws.com/{full_key}"
    return full_url


def get_criteria_file_key(sector_name: str, industry_group_name: str):
    full_key = f"public-equities/US/gcis/{slugify(sector_name)}/{slugify(industry_group_name)}/custom-criteria.json"
    return full_key


def get_ticker_file_key(ticker: str):
    full_key = f"public-equities/US/gcis/{ticker}/latest-10q-report.json"
    return full_key
