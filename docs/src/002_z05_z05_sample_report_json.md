# Sample Report JSON
Things to Note:
- We have kept provision for multiple sub-industries as larger companies like apple, google, etc will belong to multiple 
sub-industries.
- For now we will only focus on evaluating the company based on a single sub-industry.


```json
{
  "ticker": "AMT",
  "sectors": [
    {
      "id": 6,
      "name": "Real Estate"
    }
  ],
  "industryGroups": [
    {
      "id": 60,
      "name": "Equity REITs"
    }
  ],
  "industries": [
    {
      "id": 6010,
      "name": "Specialized REITs"
    }
  ],
  "subIndustries": [
    {
      "id": 601010,
      "name": "Specialized REITs"
    }
  ],
  "processedInformation": {
    "subIndustryReports": [
      {
        "id": 601010,
        "name": "Specialized REITs",
        "criteriaEvaluationsOfLatest10Q": [
          {
            "criterion": "rental_health",
            "importantMetrics": {
              "status": "Completed",
              "metrics": [[
                {
                  "metric": "rental_rates",
                  "value": 1000,
                  "calculationExplanation": "Explains which values were used to calculate the metric."
                },
                {
                  "metric": "rental_vacancy",
                  "value": 0.1,
                  "calculationExplanation": "Explains which values were used to calculate the metric."
                }
            ]]            },
            "reports": [
              {
                "key": "rental_health_summary",
                "name": "Rental Health Summary",
                "outputType": "TextReport",
                "status": "Completed",
                "outputFile": "https://s3.amazonaws.com/koalagains/public-equities/US/tickers-reports/<ticker>/<sub-industry>/<criteria>/{report-key}.md"
              },
              {
                "key": "rental_health_table",
                "name": "Rental Health Summary",
                "outputType": "TextReport",
                "status": "InProgress"
              },
              {
                "key": "rental_health_trend",
                "name": "Rental Health Trend",
                "outputType": "BarGraph",
                "status": "Completed",
                "outputFileUrl": "https://s3.amazonaws.com/koalagains/public-equities/US/tickers-reports/<ticker>/<sub-industry>/<criteria>/{report-key}.json"
              }
            ],
            "performanceChecklist": [
              {
                "checklistItem": "The item to be checked. Explain in 7-10 words.",
                "oneLinerExplanation": "A brief explanation of how the item was evaluated.",
                "informationUsed": "The information used to evaluate the item.",
                "detailedExplanation": "A detailed explanation of how the item was evaluated.",
                "evaluationLogic": "The logic used to evaluate the item.",
                "score": 1
              }
            ]
          }
        ]
      }
    ]
  }
}
```

```
