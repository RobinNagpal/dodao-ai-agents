# Sample Criteria JSON
Important Fields in Criterion JSON:
- key: The key of the criterion. This will be used to identify the criterion.
- "name": The "name" of the criterion.
- "shortDescription": A short "description" of the criterion.


```json
{
  "tickers": ["AMT"],
  "selectedIndustryGroup": {
    "id": 60,
    "name": "Equity REITs"
  },
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
          "formula": "occupied_units / total_units"
        },
        {
          "key": "lease_expirations",
          "name": "Lease Expirations",
          "description": "The percentage of leases expiring in the next 12 months.",
          "formula": "leases_expiring / total_leases"
        },
        {
          "key": "rental_rates",
          "name": "Rental Rates",
          "description": "The average rental rates for the company’s properties.",
          "formula": "total_rent / total_units"
        }
      ],
      "reports": [
        {
          "key": "rental_health_summary",
          "name": "Rental Health Summary",
          "description": "A summary of the company’s rental health based on key metrics.",
          "prompt": "Give me a summary of the rental health ..........." ,
          "outputType": "TextReport"
        },
        {
          "key": "rental_health_trend",
          "name": "Rental Health Trend",
          "description": "A trend analysis of the company’s rental health over time.",
          "prompt": "Give me a trend analysis of the rental trend ...........",
          "outputType": "BarGraph"
        }
      ]
    }
  ]
}
```


