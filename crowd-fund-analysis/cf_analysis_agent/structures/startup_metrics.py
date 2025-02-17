from pydantic import BaseModel, Field

from cf_analysis_agent.agent_state import InformationStatus


class MetricStructure(BaseModel):
    explanation: str = Field(None, description="Description of the metric, including the KPI and the startup's achieved number. If the information is extracted, derived, or missing explain detail how it was determined.")
    opinion: str = Field(None, description="Assessment of whether the number is good, okay, or bad compared to industry benchmarks, with detailed industry standards.")
    information_status: InformationStatus = Field(InformationStatus, description="Status indicating whether the information is missing, derived, extracted or not_applicable.")


class StartupMetricsStructure(BaseModel):
    growth_rate: MetricStructure = Field(description="The monthly user growth rate, with benchmarks of 15%, 10%, and 5%.")
    organic_vs_paid_growth: MetricStructure = Field(description="Ratio of organic to paid growth, with a good benchmark of 80%+ organic.")
    virality: MetricStructure = Field(description="The ability of users to bring new users naturally, often measured via viral coefficient.")
    network_effect: MetricStructure = Field(description="How much the product improves as more users join, based on Metcalfe's Law.")
    customer_acquisition_cost: MetricStructure = Field(description="The cost of acquiring a new customer, calculated per marketing channel.")
    unit_economics: MetricStructure = Field(description="Revenue per user minus variable costs, determining profitability at the customer level.")
    retention_rate: MetricStructure = Field(description="The percentage of users who continue using the product after a certain period.")
    magic_moment: MetricStructure = Field(description="A key user action that predicts long-term retention, e.g., Facebook's '7 friends in 10 days'.")
    net_promoter_score: MetricStructure = Field(description="Measure of customer satisfaction and likelihood of referrals, with 50+ as a minimum benchmark.")
    customer_lifetime_value: MetricStructure = Field(description="Projected revenue a customer will generate over their lifetime.")
    payback_period: MetricStructure = Field(description="Time it takes to recover customer acquisition costs, ideally as short as possible.")
    revenue_growth: MetricStructure = Field(description="Increase in revenue over time, typically the primary KPI for consumer startups.")
    churn_rate: MetricStructure = Field(description="The percentage of customers who stop using the product within a certain period.")

class SectorDetailStructure(BaseModel):
    basic_info: str = Field(description="General information about the sector, including its key players, market positioning, and relevance to the startup's product.")
    growth_rate: str = Field(description="Historical and projected growth rate of the sector, providing insight into its expansion potential.")

class MarketDetailStructure(BaseModel):
    details: str = Field(description="An overview of the market, including key trends, demand drivers, and competitive landscape.")
    calculation_logic: str = Field(description="Explanation of how the market size was estimated, including data sources and methodology.")
    
class IndustryDetailsAndForecastStructure(BaseModel):
    sector_details: SectorDetailStructure = Field(description="Detailed information about the industry sector relevant to the startup.")
    sub_sector_details: SectorDetailStructure = Field(description="More specific details about a niche or sub-sector within the broader industry.")
    total_addressable_market: MarketDetailStructure = Field(description="The total potential revenue opportunity if the startup captured 100% of its relevant market.")
    serviceable_addressable_market: MarketDetailStructure = Field(description="The portion of the total addressable market (TAM) that the startup can realistically serve based on its business model and resources.")
    serviceable_obtainable_market: MarketDetailStructure = Field(description="The subset of the serviceable addressable market (SAM) that the startup can reasonably capture given current capabilities and competition.")
    profit_margins: MarketDetailStructure = Field(description="The expected profit margins within the industry, considering operational costs and revenue potential.")
