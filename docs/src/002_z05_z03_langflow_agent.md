# Invoking Langflow Agent
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
   "criteriaFileUrl": "<s3-base-url>/public-equities/US/gics/<sector>/<industry-group>/custom-criteria.json"
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

