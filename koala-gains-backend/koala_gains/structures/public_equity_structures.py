import re
from typing import List, Optional, Literal, Any
import os
from pydantic import BaseModel, Field

ProcessingStatus = Literal["Completed", "Failed", "InProgress"]

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


class IndustryGroup(BaseModel):
    id: int
    name: str


class Sector(BaseModel):
    id: int
    name: str


class MetricValueItem(BaseModel):
    metricKey: str
    value: str
    calculationExplanation: str


class ImportantMetrics(BaseModel):
    status: ProcessingStatus
    metrics: List[MetricValueItem]


class ReportValueItem(BaseModel):
    reportKey: str
    status: ProcessingStatus
    outputFileUrl: Optional[str]


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
    reports: Optional[List[ReportValueItem]]
    performanceChecklist: Optional[List[PerformanceChecklistItem]]


class SecFilingAttachment(BaseModel):
    sequenceNumber: str
    documentName: str
    purpose: Optional[str] = None
    url: str
    relevance: Optional[float] = None
    content: Optional[str] = None


class CriterionMatch(BaseModel):
    criterionKey: str
    matchedAttachments: List[SecFilingAttachment]
    matchedContent: str


class CriterionMatchesOfLatest10Q(BaseModel):
    criterionMatches: Optional[List[CriterionMatch]] = None
    status: ProcessingStatus
    failureReason: Optional[str] = None


class TickerReport(BaseModel):
    tickerKey: str
    industryGroupId: int
    sectorId: int
    latest10QFinancialStatements: Optional[str] = None
    evaluationsOfLatest10Q: Any = None
    criteriaMatchesOfLatest10Q: Optional[CriterionMatchesOfLatest10Q] = None


class Markdown(BaseModel):
    markdown: str


class MetricDefinitionItem(BaseModel):
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


class CriterionReportDefinitionItem(BaseModel):
    key: str = Field(
        description="Unique identifier for the report associated with the criteria."
    )
    name: str = Field(description="Name of the report.")
    description: str = Field(
        description="Comprehensive description outlining the content and purpose of the report."
    )
    outputType: Literal["Text", "BarGraph", "PieChart", "WaterfallChart"] = Field(
        description="Specifies the type of output to produced Text, BarGraph, WaterfallChart or PieChart."
    )


class IndustryGroupCriterion(BaseModel):
    key: str = Field(
        description="Unique identifier for the criteria, formatted in lower case with underscores."
    )
    name: str = Field(description="Descriptive name of the criteria.")
    shortDescription: str = Field(
        description="Brief overview of the criteria and its intended evaluation purpose."
    )
    importantMetrics: List[MetricDefinitionItem] = Field(
        description="List of key metrics that are used to evaluate this criteria."
    )
    reports: List[CriterionReportDefinitionItem] = Field(
        description="List of reports generated based on the criteria's evaluation."
    )


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
    outputType: Literal[
        "Text", "BarGraph", "PieChart", "WaterfallChart", "DoughnutChart"
    ] = Field(
        description="Specifies the type of output to produce: Text, BarGraph, PieChart, WaterfallChart or DoughnutChart."
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
    full_key = f"public-equities/US/gics/{slugify(sector_name)}/{slugify(industry_group_name)}/custom-criteria.json"
    return full_key


def get_ticker_file_key(ticker: str):
    full_key = f"public-equities/US/tickers/{ticker}/latest-10q-report.json"
    return full_key


def get_criterion_report_key(
    ticker: str,
    criterion_key: str,
    report_key: str,
    report_type: Literal["Text", "PieChart", "BarGraph", "WaterfallChart"],
):
    if report_type == "Text":
        return f"public-equities/US/tickers/{ticker}/criterion-reports/{criterion_key}/{report_key}.md"
    else:
        return f"public-equities/US/tickers/{ticker}/criterion-reports/{criterion_key}/{report_key}.json"


def get_criterion_performance_checklist_key(ticker: str, criterion_key: str):
    return f"public-equities/US/tickers/{ticker}/criterion-reports/{criterion_key}/performance_checklist.json"
