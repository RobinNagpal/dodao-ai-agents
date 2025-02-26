# Analyzing public equities
We definitely want to focus on REITs first but we want to write the code in a generic way so that we can use it for 
other public equities as well. This will allow us to create some basic reports for any public company.

# Spider Charts
At the core will be spider charts. Which means analyzing the company based on some criteria. 

We already have GICS sectors and industries. See - https://en.wikipedia.org/wiki/Global_Industry_Classification_Standard

Based on the type of company we can ask AI to give us 6-8 right criteria to evaluate the company.

### Step 1 - Find Relevant Criteria
The criteria we use will also depend on the information we have. Since we are working just on Latest 10Q, we can ask 
for criteria that can be evaluated from that. So the prompt will be 

```
Give me 6-8 criteria to evaluate a company in xxx Sector/Industry/Industry Group/Sub-Industry. Make sure I am able to 
find information for evaluating this criteria from information represented in 10Q`.
```

So we can either provide the Sector, Industry Group, Industry, or Sub-Industry when asking for the criteria. Or we can
ask AI to find the matching Sector, Industry Group, Industry, or Sub-Industry from the SEC filings, and then find
the matching criteria.

### Step 2 - Saving Criteria information in sub-industry-info.json
Agent Status File can look something like

These files will be saved in the `public-equities/US/gics/<sector>/<industry-group>/<industry>/<sub-industry>/` folder.

Where the folder names are slugs of the sector, industry group, industry, and sub-industry. 

```js
const subIndustry = {
  "tickers": ["AMT"], // These are just for exmaple purpose to make sure we can write some code to test it out later
  "id": 601010,
  "name": "Specialized REITs",
  "subIndustry": {id: 601010, name: "Specialized REITs"},
  "sector": {id: 6, name: "Real Estate"}, 
  "industryGroup": {id: 60, name: "Equity REITs"}, 
  "industry": {id: 6010, name: "Specialized REITs"},
  "processedInformation": {
    "criteria": [
      {
        id: 'rental_health',
        name: 'Rental Health',
        shortDescription: 'Rental Health is a measure of the health of the rental market. It includes metrics like occupancy rates, lease expirations, and rental rates.',
        importantMetrics: [
          {
            id: 'occupancy_rates',
            name: 'Occupancy Rates',
            description: 'The percentage of occupied units in a property or portfolio.'
          },
          {
            id: 'lease_expirations',
            name: 'Lease Expirations',
            description: 'The percentage of leases expiring in the next 12 months.'
          },
          {
            id: 'rental_rates',
            name: 'Rental Rates',
            description: 'The average rental rates for the company’s properties.'
          }
        ],
        reports: [
          {
            id: 'rental_health_summary',
            name: 'Rental Health Summary',
            description: 'A summary of the company’s rental health based on key metrics.',
            prompt: "Give me a summary of the rental health ..........." ,
            outputType: 'TextReport'
          },
          {
            id: 'rental_health_trend',
            name: 'Rental Health Trend',
            description: 'A trend analysis of the company’s rental health over time.',
            prompt: "Give me a trend analysis of the rental trend ...........",
            outputType: 'BarGraph'
          }
        ]
      }
    ]
  }
}
```

We can override the `processedInformation` field in the `sub-industry-info.json` file. This will allow us to have 
very relevant information for the sub-industry. We can then use this information to create the reports.



### Step 3 - Criteria Related Information Extraction

This has already been implemented in [004_z02_latest_10Q_criterion_info.md](./004_z02_latest_10Q_criterion_info.md).

This file will be saved in the `public-equities/US/tickers/latest-10q-criterial-info.json` folder.
```js

const latest10QCriterionInfo = {
  "ticker": "AMT",
  "sector": {id: 6, name: "Real Estate"},
  "industryGroup": {id: 60, name: "Equity REITs"},
  "industry": {id: 6010, name: "Specialized REITs"},
  "subIndustry": {id: 601010, name: "Specialized REITs"},
  "latest10QSecURL": "https://www.sec.gov/Archives/edgar/data/1053507/000105350721000013/0001053507-21-000013-index.htm",
  "criteriaExtractedInfo": [
    {
      criterionId: 'rental_health',
        criterionName: 'Rental Health',
      relevantAttachments: [
        {
          attachmentName: 'Exhibit 99.1',
          attachmentURL: 'https://www.sec.gov/Archives/edgar/data/1053507/000105350721000013/amt-ex991_6.htm',
          mathcingAmount: 80 // Percentage of matching information
        }
      ]
    }
  ]
}



```

### Step 4 - File for Each Equity / Ticker
Based on the information we have, we can create a file for the ticker for which we have processed the latest 10Q information.

This file will be saved in the `public-equities/US/tickers/<ticker>.json` folder.

```js
const agentStatusFile = {
  "ticker": "AMT",
  "sectors": [{id: 6, name: "Real Estate"}], // id and name from GICS. A ticker can belong to multiple sectors 
  "industryGroups": [{id: 60, name: "Equity REITs"}], // can belong to multiple industry groups 
  "industries": [{id: 6010, name: "Specialized REITs"}], // can belong to multiple industries 
  "subIndustries": [
    {
      id: 601010, 
      name: "Specialized REITs"
    }
  ],
  processedInformation: {
    subSectorReports: [{
      id: 601010,
      name: "Specialized REITs",
      criteraEvaluations: [{
          criterion: 'rental_health',
          reports: [
            {
              id: 'rental_health_summary',
              name: 'Rental Health Summary',
              output: 'TextReport'
            },
            {
              id: 'rental_health_trend',
              output: {
                type: 'BarGraph',
                data: {
                  x: ['2020-12-31', '2021-03-31', '2021-06-30', '2021-09-30'],
                  y: [0.8, 0.85, 0.9, 0.95]
                }
              }
            }
          ],
          performanceChecklist: [{
            checklist_item: "The item to be checked. Explain in 7-10 words.",
            oneLinerExplanation: "A brief explanation of how the item was evaluated.",
            informationUsed: "The information used to evaluate the item.",
            detailedExplanation: "A detailed explanation of how the item was evaluated.",
            evaluationLogic: "The logic used to evaluate the item.",
            score: 1 // 1 for tick, 0 for cross
          }]
        }
      ]
    }]
  }
}
```

Open questions
1. How will Langflow come into play here?







### Step 3 - Create the Spider Chart
