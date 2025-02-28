# Backend

From frontend we just need to make a call to the backend to generate the reports.

## Generating All Reports
URL can be `/api/public-equities/US/genrate-all-reports` with the following payload

```json
{
  "ticker": "AMT",
   "sector": {
      "id": 60,
      "name": "Real Estate"
   },
   "industryGroup": {
      "id": 60,
      "name": "Equity REITs"
   },
   "industry": {
      "id": 6010,
      "name": "Specialized REITs"
   },
   "subIndustry": {
        "id": 601010,
        "name": "Specialized REITs"
   }
}
```

The backend will also trigger the extraction of data.

## Generating Report Structure
This route will help in generating the report one step at a time, and the first step being generating the report structure.

URL can be `/api/public-equities/US/genrate-report-structure` with the following payload

```json
{
  "ticker": "AMT",
  "sector": {
      "id": 60,
      "name": "Real Estate"
   },
   "industryGroup": {
      "id": 60,
      "name": "Equity REITs"
   },
   "industry": {
      "id": 6010,
      "name": "Specialized REITs"
   },
   "subIndustry": {
        "id": 601010,
        "name": "Specialized REITs"
   }
}
```

## Extracting Data
This route will help trigger the extraction of data from the UI. We already have the lambda for extracting the data,
so the backend will just have to call it.

## Generating a single report

URL can be `/api/public-equities/US/genrate-report` with the following payload

```json
{
  "ticker": "AMT",
  "criteria": "rental_health"
}
```

This will throw an error if the criteria is not found, or an existing report structure is not found.

This will not trigger the extraction of data if the data is not found.


# Report Structure
The report structure should be saved in the `public-equities/US/tickers-evaluations/<ticker>.json` folder.

It can have the following structure

Note - We can treat null as not started status for reports

See full report sample JSON here - [Full Report JSON](002_z05_z05_sample_report_json)

```json
{
    "ticker": "AMT",
    "sectors": [{"id": 6, "name": "Real Estate"}], 
    "industryGroups": [{"id": 60, "name": "Equity REITs"}],  
    "industries": [{"id": 6010, "name": "Specialized REITs"}], 
    "subIndustries": [{"id": 601010, "name": "Specialized REITs"}
    ],
    "processedInformation": {
    "subIndustryReports": [{
      "id": 601010,
      "name": "Specialized REITs",
      "criteriaEvaluationsOfLatest10Q": [{
          "criterion": "rental_health",
          "importantMetricsResults": null,
          "reports": null,
          "performanceChecklist": null
      }]
    }]
  }
}
```

```
