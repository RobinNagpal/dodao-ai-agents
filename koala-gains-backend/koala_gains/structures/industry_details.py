from pydantic import BaseModel, Field


class SectorDetailStructure(BaseModel):
    basic_info: str = Field(
        description="General information about the sector, including its key players, market positioning, and relevance to the startup's product."
    )
    growth_rate: str = Field(
        description="Historical and projected growth rate of the sector, providing insight into its expansion potential."
    )


class MarketDetailStructure(BaseModel):
    details: str = Field(
        description="An overview of the market, including key trends, demand drivers, and competitive landscape."
    )
    calculation_logic: str = Field(
        description="Explanation of how the market size was estimated, including data sources and methodology."
    )


class IndustryDetailsAndForecastStructure(BaseModel):
    sector_details: SectorDetailStructure = Field(
        description="Detailed information about the industry sector relevant to the startup."
    )
    sub_sector_details: SectorDetailStructure = Field(
        description="More specific details about a niche or sub-sector within the broader industry."
    )
    total_addressable_market: MarketDetailStructure = Field(
        description="The total potential revenue opportunity if the startup captured 100% of its relevant market."
    )
    serviceable_addressable_market: MarketDetailStructure = Field(
        description="The portion of the total addressable market (TAM) that the startup can realistically serve based on its business model and resources."
    )
    serviceable_obtainable_market: MarketDetailStructure = Field(
        description="The subset of the serviceable addressable market (SAM) that the startup can reasonably capture given current capabilities and competition."
    )
    profit_margins: MarketDetailStructure = Field(
        description="The expected profit margins within the industry, considering operational costs and revenue potential."
    )
