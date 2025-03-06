# Saving of Reports

We will have the initial structure of the ticker already populated. At this step of the process we will now be
saving the results from each criterion evaluations.

For each criterion evaluation, we will have the following information:
1. Important Metrics Results
2. Reports
3. Performance Checklist

So the s3 updater tool can have a two dropdowns to select the field we are updating. The dropdown will have the following 
options:
1. ImportantMetricsResults
2. Reports
3. PerformanceChecklist

Other dropdown will have the status with the options
1. Completed
2. InProgress
3. Failed

We still need to see when failed status will be used.

# Save Report Status
When completed, The body passed to the tool will be look like this:
```json
{
  "ticker": "AMT",
  "criterion": "rental_health",
  "reportKey": "rental_health",
  "data": "This data is string in case of text report and an object in case of bar chart or pie chart ."
}
```

Here `data` will be the data that will be saved in the report structure. It can be a string in case of text report and 
an object in case of bar chart or pie chart.


For Important Metrics Results, the data will be an array of objects. Each object will have the following structure:

```json
{
   "ticker": "AMT",
   "criterion": "rental_health",
   "data": [
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
   ]
}
```

or in case of `PerformanceChecklist` the data will be an array of objects. Each object will have the following structure:

```json
{
   "ticker": "AMT",
   "criterion": "rental_health",
   "data": [
        {
             "checklistItem": "The item to be checked. Explain in 7-10 words.",
             "oneLinerExplanation": "A brief explanation of how the item was evaluated.",
             "informationUsed": "The information used to evaluate the item.",
             "detailedExplanation": "A detailed explanation of how the item was evaluated.",
             "evaluationLogic": "The logic used to evaluate the item.",
             "score": 1
        },
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
```
