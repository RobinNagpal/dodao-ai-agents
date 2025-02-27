# Reports for Each Ticker

The report will be generated for each ticker. The report file will be saved in the `public-equities/US/tickers-evaluations/<ticker>.json` folder.

The report will contain the following information:

Few things to note:
- Many times a single company can belong to multiple sectors, industry groups, industries, and sub-industries. For example tesla, google, etc.
- For now we will only focus on evaluating the company based on a single sub-industry. But in the schema, we are keeping that provision.

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
      "criteriaEvaluations": [{
          "criterion": "rental_health",
          "reports": [
            {
              "key": "rental_health_summary",
              "name": "Rental Health Summary",
              "outputType": "TextReport",
              "outputFile": "https://s3.amazonaws.com/koalagains/public-equities/US/tickers-reports/<ticker>/<sub-industry>/<criteria>/{report-key}.md"
            },
            {
              "key": "rental_health_trend",
              "name": "Rental Health Trend",
              "outputType": "BarGraph",
              "outputFileUrl": "https://s3.amazonaws.com/koalagains/public-equities/US/tickers-reports/<ticker>/<sub-industry>/<criteria>/{report-key}.json"
            }
          ],
          "performanceChecklist": [{
            "checklistItem": "The item to be checked. Explain in 7-10 words.",
            "oneLinerExplanation": "A brief explanation of how the item was evaluated.",
            "informationUsed": "The information used to evaluate the item.",
            "detailedExplanation": "A detailed explanation of how the item was evaluated.",
            "evaluationLogic": "The logic used to evaluate the item.",
            "score": 1
          }]
        }
      ]
    }]
  }
}
```

# Criterion Reports
For crowdfunding we just had a single report for each criterion. But for public equities, we can have multiple 
reports for each criterion.

For example this page - https://koalagains.com/crowd-funding/projects/nightware/reports/traction shows the report
for the criterion `traction`. 

There is just text on this page. But we would want to have charts etc, and for this reason we have added the `outputType` field.

Then we can have a UI Component that can show the report based on the `outputType` field.

### Text Reports
We can have a simple MarkdownReportViewer component that can show the text report.

### Barchart/Piechart Reports
We can have a BarChartReportViewer component that can show the bar chart.

We can have a PieChartReportViewer component that can show the pie chart.

It will be the responsibility of the prompt to make sure the report generated is in the correct format. They can
just use a structured output.



# Report Generation Logic/Process/Code
We would want to write this part in Langflow. The reasons for writing this in Langflow are:
1. We need to have at-least 25 agents if we write custom criteria for each industry group. This will be a lot of code to write.
2. Langflow allows any non-technical person to write the agent
3. Non-devs can use the tools, and keep updating the prompts to make sure a right report is generated.
4. We can hire interns in Summer to cover 5-10 Industry Groups. They can write the prompts for the agents.

### Invoking the Agent
An agent can have a webhook url which can be invoked to generate the report. This component is already present in Langflow.

See WebhookComponent - https://docs.langflow.org/components-data#webhook

To the agent we need to pass the following information:

```json
{
   "ticker": "AMT",
   "criteria": [
      {
         "key": "rental_health",
         "name": "Rental Health",
         "shortDescription": "Rental Health is a measure of the health of the rental market. It includes metrics like occupancy rates, lease expirations, and rental rates.",
         "importantMetrics": [
            {
               "key": "occupancy_rates",
               "name": "Occupancy Rates",
               "description": "The percentage of occupied units in a property or portfolio.",
               "abbreviation": "OR",
               "calculationFormula": "occupiedUnits/totalUnits"
            },
            {
               "key": "lease_expirations",
               "name": "Lease Expirations",
               "description": "The percentage of leases expiring in the next 12 months.",
               "abbreviation": "LE",
               "calculationFormula": "leasesExpiring/totalLeases"

            },
            {
               "key": "rental_rates",
               "name": "Rental Rates",
               "description": "The average rental rates for the company’s properties.",
               "abbreviation": "RR",
               "calculationFormula": "sum(rentalRates)/totalProperties"
            }
         ],
         "reports": [
            {
               "key": "rental_health_summary",
               "name": "Rental Health Summary",
               "description": "A summary of the company’s rental health based on key metrics.",
               "outputType": "TextReport"
            },
            {
               "key": "rental_health_trend",
               "name": "Rental Health Trend",
               "description": "A trend analysis of the company’s rental health over time.",
               "outputType": "BarGraph"
            }
         ]
      }
   ]
}
```

Other option is we can pass
```json
{
   "ticker": "AMT",
   "criteriaFileUrl": "<s3-base-url>/public-equities/US/gics/real-estate/equity-reits/custom-criteria.json"
}
```
Here langflow can download the file and then use the criteria from the file to generate the report.

So langflow should be able to 
1. parse the criteria file/data
2. Loop through each criterion
3. Match the criteria key - There is already if-else component in langflow, so we have to use 5-6 if-else components 
4. Then for each criteria, we will have logic to generate the report. This is already there for `debt`

### Task
- Work on 1, 2, 3, 4.
- For now you can pass hardcoded criteria info from postman(or other REST tool) to the webhook url.  


### Conditional Logic in Langflow
- SWITCH CASE - Better, but we dont have this in langflow. 
- IF-ELSE - We have this in langflow. So we can use this for now.

So the if-else component will have the following logic:
```typescript
// First Component
if(criterial.key == "rentalHealth") {
    // Generate the report for rental_health
} else 
  // Second Component
  if(criterial.key == "debtAndLeverage") {
    // Generate the report for debt
  } else 
    // Third Component
    if(criterial.key == "stockDistribution") {
        // Generate the report for founderAndTeam
        } else 
        // Fourth Component
        if(criterial.key == "costOfOperations") {
            // Generate the report for traction
        } else 
            // Fifth Component
            if(criterial.key == "team") {
            // Generate the report for marketOpportunity
            } else 
               // Sixth Component
               if(criterial.key == "ffoAndAffo") {
                   // Generate the report for executionSpeed
               }
```



# Langflow Tools
We will have these tools in Langflow
1. SEC Edgar Extractor - This will extract the information from the latest 10Q - Already Done
2. Test Data Tool - This tool can allow for pulling test data from some url/github etc. This is just for testing purposes.
   - This will decouple the logic of extraction of data from the logic of generating the report. 
   - The person generating the report can just assume the test data tool to get the right data.
   - Also we dont need to invoke LLM every time to get the data as we work on optimizing the prompts for report generation.
   - For example we need to have data for criterion `debt` when evaluating REITs. Now either we invoke the SEC Edgar Extractor again and again, or just use the test data tool.
   - The tool can have two dropdowns - 1. Ticker 2. Criterion. And then it can return the data for that criterion for that ticker.
