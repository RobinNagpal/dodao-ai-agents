from typing import List, TypedDict, Optional, Literal
from pydantic import BaseModel, Field

from koala_gains.structures.public_equity_structures import IndustryGroupCriterion


class IndustryGroupCriteriaStructure(BaseModel):
    tickers: List[str] = Field(
        description="List of ticker symbols representing the companies."
    )
    criteria: List[IndustryGroupCriterion] = Field(
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
