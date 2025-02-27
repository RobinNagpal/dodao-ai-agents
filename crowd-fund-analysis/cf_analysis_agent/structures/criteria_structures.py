from typing import List
from pydantic import BaseModel, Field


class SubIndustry(BaseModel):
    id: int = Field(description="ID of the sub-industry.")
    name: str = Field(description="Name of the sub-industry.")


class Sector(BaseModel):
    id: int = Field(description="ID of the sector.")
    name: str = Field(description="Name of the sector.")


class IndustryGroup(BaseModel):
    id: int = Field(description="ID of the industry group.")
    name: str = Field(description="Name of the industry group.")


class Industry(BaseModel):
    id: int = Field(description="ID of the industry.")
    name: str = Field(description="Name of the industry.")



class ImportantMetric(BaseModel):
    id: str = Field(description="name of metric in lower case seperated by '_'.", alias="id")
    name: str = Field(description="Name of the important metric.", alias="name")
    description: str = Field(description="Description of the important metric.", alias="description")


class Criteria(BaseModel):
    id: str = Field(description="name of criteria in lower case seperated by '_'", alias="id")
    name: str = Field(description="Name of the criteria.", alias="name")
    short_description: str = Field(description="Short description of the criteria.", alias="short-description")
    important_metrics: List[ImportantMetric] = Field(description="List of important metrics related to the criteria.", alias="important-metrics")


class ProcessedInformation(BaseModel):
    criteria: List[Criteria] = Field(description="List of criteria associated with the sub-industry.", alias="criteria")


class StructuredIndustryGroupCriteriaResponse(BaseModel):
    tickers: List[str] = Field(description="List of tickers associated with the industry group.", alias="tickers")
    processed_information: ProcessedInformation = Field(description="Processed information related to the sub-industry.", alias="processed-information")
    
class IndustryGroupData(BaseModel):
    tickers: List[str] 
    id: int
    name: str
    subIndustry: SubIndustry 
    sector: Sector 
    industryGroup: IndustryGroup 
    industry: Industry 
    processedInformation: ProcessedInformation 

class EquityDeatils(BaseModel):
    sector: Sector
    industryGroup: IndustryGroup
    industry: Industry
    subIndustry: SubIndustry