# Tasks
- [ ] Add more information about industry and sector in the `ProcessedProjectInfoSchema`
- [ ] Add another request method which is "PopulateProjectInfoField". For now we can hardcode the filed name in app.py. Later on we can change the field name to be dynamic or change 
to the one we are working on at that time.


## Add more information about industry and sector in the `ProcessedProjectInfoSchema`
There are three main things that influence the startup valuation:
- How big is the industry and how much can a company make in one year? (Both revenue, and profit are important)? - Basic Industry Information
- How good is the team and how fast can they move? - Team Report
- How much money are they asking for? and is it a fair price? - Valuation Report


Current fields
```json
{ 
      "industry_details_and_forecast": "Your detailed analysis of the industry and forecasts for the project. Make sure it is as per the guidelines provided.",
      "total_addressable_market": "Total addressable market",
      "serviceable_addressable_market": "Serviceable addressable market",
      "serviceable_obtainable_market": "Serviceable obtainable market"
}
```
For Industry Information, we need to add the following fields:

```json
{ 
      "sectorDetails": {
        "basicInfo": "Your detailed analysis of the sector/industry.",
        "growthRate": "Growth rate of the sector/industry"
      },
      "sub_sector_details": {
        "basicInfo": "Your detailed analysis of the sub-sector.",
        "growthRate": "Growth rate of the sub-sector"
      },
      "total_addressable_market": {
        "details": "Total addressable market",
        "calculation logic": "How Calculation of the total addressable market was done"
      },
      "serviceable_addressable_market": {
        "details": "Serviceable addressable market",
        "calculation logic": "How Calculation of the serviceable addressable market was done"
      },
      "serviceable_obtainable_market": {
        "details": "Serviceable obtainable market",
        "calculation logic": "How Calculation of the serviceable obtainable market was done"
      },
      "profitMargins": {
        "details": "Profitability of the sector/industry",
        "calculation logic": "How Calculation of the profitability was done"
      }
}
```




## Pull/Push agent-status.json to s3 using tool
- Explain what we are trying to do here
- Explain how this tool will be used in langflow
- Explain how the full flow will work
- Explain the list of things you are changing or adding in the code
