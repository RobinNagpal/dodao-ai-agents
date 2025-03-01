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


# Report Structure (Initial/Not Processed)

The json schema for the initial report structure can be found in [002_z05_z05_paths_and_json_structures.md](./002_z05_z05_paths_and_json_structures.md)




