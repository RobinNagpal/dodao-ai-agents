


# Paths and Structures


# Table of Contents
1. [Criteria File Path](#criteria-file-path)
   - [AI Criteria Files](#ai-criteria-files)
   - [Custom Criteria Files](#custom-criteria-files)
2. [Reports File Path](#reports-file-path)
   - [Initial Report](#initial-report)
   - [Criteria Data Extraction](#criteria-data-extraction)
   - [Ticker Report - InProgress Status](#ticker-report---inprogress-status)
   - [Ticker Report - Completed Status](#ticker-report---completed-status)

At various places in the docs we mention where the file should be saved. This file should be treated as a 
reference for that. We will try to remove the information from other files and keep it here.

## Criteria File Path

### Lookup File
We can have a lookup file for the criteria. This file will be saved in the following path:
`public-equities/US/gics/criterias.json`

Contents of the file can look like this

```json
{

   "criteria": [
      {
         "sectorId": 10,
         "sectorName": "Energy",
         "industryGroupId": 1010,
         "industryGroupName": "Energy",
         "aiCriteriaFileLocation": "https://dodao-ai-insights-agent.s3.us-east-1.amazonaws.com/public-equities/US/gics/energy/energy/ai-criteria.json"
      },
      {
         "sectorId": 15,
         "sectorName": "Materials",
         "industryGroupId": 1510,
         "industryGroupName": "Materials",
         "aiCriteriaFileLocation": "https://dodao-ai-insights-agent.s3.us-east-1.amazonaws.com/public-equities/US/gics/materials/materials/ai-criteria.json"
      },
      {
         "sectorId": 20,
         "sectorName": "Industrials",
         "industryGroupId": 2010,
         "industryGroupName": "Capital Goods",
         "aiCriteriaFileLocation": "https://dodao-ai-insights-agent.s3.us-east-1.amazonaws.com/public-equities/US/gics/industrials/capital-goods/ai-criteria.json"
      }
   ]
}
```
This array will have an entry when we generate an ai-criteria file, or a custom-criteria file, or both.

We might be generating ai-criteria files before hand to make sure that they are quite accurate.

### AI Criteria Files
Location `public-equities/US/gics/<sector>/<industry-group>/ai-criteria.json`


### Custom Criteria Files
Location `public-equities/US/gics/<sector>/<industry-group>/custom-criteria.json`

## Reports File Path
The reports file will be saved in the following path:


`public-equities/US/ticker-reports/<ticker>.json`

and the detailed reports for each criterion will be saved in the following path:

`public-equities/US/ticker-reports/<ticker>/<criteria>/<report-key>.md`

or 

`public-equities/US/ticker-reports/<ticker>/<criteria>/<report-key>.json`



### Initial Report

See full report sample JSON here - [Full Report JSON](002_z05_z07_sample_report_json)


Note - We can treat null as not started status for reports

```json
{
    "ticker": "AMT",
    "selectedIndustryGroup": {
       "id": 60,
       "name": "Equity REITs"
    },
   "criteriaEvaluationsOfLatest10Q": [{
      "criterion": "rental_health",
      "importantMetricsResults": null,
      "reports": null,
      "performanceChecklist": null
   }]
}
```

### Criteria Data Extraction
This information can be saved in the same ticker file.

```json
{
   "ticker": "AMT",
   "selectedIndustryGroup": {
      "id": 60,
      "name": "Equity REITs"
   },
   "criterionMatchesOfLatest10Q": {
      "criterionMatches": [
         {
            "criterionKey": "rental_health",
            "matchedAttachments": [
               {
                  "attachmentIndex": 1,
                  "attachmentName": "Consolidated Financial Statements",
                  "attachmentUrl": "SEC-Edgar-URL"
               },
               {
                  "attachmentIndex": 2,
                  "attachmentName": "Notes to the Financial Statements",
                  "attachmentUrl": "SEC-Edgar-URL"
               }
            ]
         }
      ],
      "status": "InProgress",
      "failureReason": "The reason for the failure if it happens"
   }
}
```

### Ticker Report - InProgress Status

```json
{
   "ticker": "AMT",
   "selectedIndustryGroup": {
      "id": 60,
      "name": "Equity REITs"
   },
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
               "status": "InProgress"
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
               "status": "InProgress"
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
```


### Ticker Report - Completed Status

```json
{
   "ticker": "AMT",
   "selectedIndustryGroup": {
      "id": 60,
      "name": "Equity REITs"
   },
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
               "outputFile": "https://s3.amazonaws.com/koalagains/public-equities/US/tickers-reports/<ticker>/<criterion>/{report-key}.md"
            },
            {
               "key": "rental_health_table",
               "name": "Rental Health Summary",
               "outputType": "TextReport",
               "status": "Completed",
                "outputFile": "https://s3.amazonaws.com/koalagains/public-equities/US/tickers-reports/<ticker>/<criterion>/{report-key}.md"
            },
            {
               "key": "rental_health_trend",
               "name": "Rental Health Trend",
               "outputType": "BarGraph",
               "status": "Completed",
               "outputFileUrl": "https://s3.amazonaws.com/koalagains/public-equities/US/tickers-reports/<ticker>/<criterion>/{report-key}.json"
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
```
