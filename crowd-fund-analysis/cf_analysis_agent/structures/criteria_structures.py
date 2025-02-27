from typing import List
from pydantic import BaseModel, Field



class Sector(BaseModel):
    id: int = Field(description="ID of the sector.")
    name: str = Field(description="Name of the sector.")


class IndustryGroup(BaseModel):
    id: int = Field(description="ID of the industry group.")
    name: str = Field(description="Name of the industry group.")


class ImportantMetric(BaseModel):
    key: str = Field(description="name of metric in lower case seperated by '_'.", alias="id")
    name: str = Field(description="Name of the important metric.", alias="name")
    description: str = Field(description="Description of the important metric.", alias="description")


class Criteria(BaseModel):
    key: str = Field(description="name of criteria in lower case seperated by '_'", alias="id")
    name: str = Field(description="Name of the criteria.", alias="name")
    shortDescription: str = Field(description="Short description of the criteria.", alias="short-description")
    importantMetrics: List[ImportantMetric] = Field(description="List of important metrics related to the criteria.", alias="important-metrics")

class Report(BaseModel):
    key: str = Field(description="Key of the report.their will be report for each criteria", alias="key")
    name: str = Field(description="Name of the report.", alias="name")
    description: str = Field(description="Description of the report.", alias="description")
    outputType: str = Field(description="Output type of the report or graph if graph also give its type.", alias="output-type")
    
class ProcessedInformation(BaseModel):
    criteria: List[Criteria] = Field(description="List of criteria associated with the industry group.", alias="criteria")
    reports: List[Report] = Field(description="List of reports associated with the industry group.", alias="reports")

class StructuredIndustryGroupCriteriaResponse(BaseModel):
    tickers: List[str] = Field(description="List of tickers associated with the industry group.", alias="tickers")
    processedInformation: ProcessedInformation = Field(description="Processed information related to the industry group.", alias="processed-information")
    
class IndustryGroupData(BaseModel):
    tickers: List[str] 
    id: int
    name: str
    sector: Sector 
    industryGroup: IndustryGroup 
    processedInformation: ProcessedInformation 

class EquityDeatils(BaseModel):
    sectorId: int
    sectorName: str
    industryGroupId: int
    industryGroupName: str
    
    
class IndustryGroupCriteria(BaseModel):
    sectorId: int = Field(description="ID of the sector.", alias="sectorId")
    sectorName: str = Field(description="Name of the sector.", alias="sectorName")
    industryGroupId: int = Field(description="ID of the industry group.", alias="industryGroupId")
    industryGroupName: str = Field(description="Name of the industry group.", alias="industryGroupName")
    aiCriteriaFileLocation: str = Field(default=None, description="Location of the AI criteria file.", alias="aiCriteriaFileLocation")
    customCriteriaFileLocation: str = Field(default=None, description="Location of the custom criteria file.", alias="customCriteriaFileLocation")