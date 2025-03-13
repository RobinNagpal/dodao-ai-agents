from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict


class SecFilingAttachment(BaseModel):
    sequenceNumber: str
    description: Optional[str] = None
    purpose: Optional[str] = None
    url: str
    documentType: str


class SecFiling(BaseModel):
    filingDate: str
    form: str
    filingUrl: str
    accessionNumber: str
    periodOfReport: str
    attachments: List[SecFilingAttachment]


class SecForm(BaseModel):
    formName: str = Field(description="Name of the SEC form.")
    formDescription: str = Field(description="Description of the SEC form.")
    importantItems: list[str] = Field(
        description="List of all the important items to look for in this SEC form."
    )
    averagePageCount: int = Field(
        description="Unique identifier for the metric, formatted in lower case with underscores."
    )
    size: Literal["xs", "s", "m", "l", "xl"] = Field(
        description="Size of the SEC form."
    )


class SecFormsInfo(BaseModel):
    forms: list[SecForm] = Field(
        description="Dictionary of form names and their corresponding details."
    )
