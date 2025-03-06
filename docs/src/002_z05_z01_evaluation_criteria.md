# Saving Criteria Information

## Introduction
- We have four levels of information - Sector(11), Industry Group(25), Industry(74), and Sub-Industry(163).
- It wont be possible to have specific criteria for all 163 sub-industries, or even all 74 industries.
- If we are working on a specific criteria, it might be good to target them at "Industry Group" level, as if they are at Sector level, they might be too broad, and if they are at 
Industry level, they might be difficult to create based on the number of industries.
- So this can be our assumption for now.

## List of Industry Groups with Specific Criteria
- We can create a file in `public-equities/US/gics/<sector>/<industry-group>/custom-criterias.json` which will have the list of Industry Groups with specific criteria.
- We can upsert criteria for Industry Groups in this file.

The file can look something like

```json
{
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
When generating a report for a specific ticker, we can check if the criteria is available in the `public-equities/US/gics/<sector>/<industry-group>/custom-criterias.json` 
file, and if it is, we can use the criteria from the file.

If not we can use the criteria from the `public-equities/US/gics/real-estate/equity-reits/ai-criteria.json` file. If this
file doesn't exist, we throw error.

The reason we have two separate files is that we can know if the criteria is created by AI or by a human. From the
file name itself, we can know if the criteria is created by AI or by a human.

### Criteria Table
We can show a list of Industry Groups, and show the ai-criteria.json and custom-criteria.json files for each Industry Group if it exists, else those columns will be empty.

We can have a button(link) to create a new criteria for the Industry Group. This button can be in both the columns, if they are important. 

For ai column, we can also have a re-generate button, which will re-generate the criteria for the Industry Group.

Here we can use either Icon buttons or Links as normal buttons will look ugly. For creating or re-generating ai criteria, we can show a confirmation dialog, and then create the criteria.

See "ConfirmationModal" in shared components. 

### Create/Edit Criteria(Human Criteria)

A Criteria can have the following fields
```json
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
```

### Upsert Custom Criteria

Criteria can be displayed as a table with each criterion representing a two. There will be an add button at the top 
and edit button at the end of each row. 

Try using our existing Table component for this.

When we add or edit a criterion, we can show a modal with the text area, where the user can edit or paste the criteria.

In the popup we can use https://github.com/microlinkhq/react-json-view to allow adding and editing a particular criterion.

The json editing library should provide support for json schema validation also. Let Robin know if it doesn't

The criteria table can have the following columns
- Key
- Name
- Short Description
- Edit Icon Button (only pencil icon. No text needed)

Or table component allows us to add a button at the top which can be an add icon button.

For now assume any schema for criterion. We want to validate the schema as well. We can have this schema as the
starting point. 

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RentalHealth",
  "type": "object",
  "properties": {
    "key": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "shortDescription": {
      "type": "string"
    },
    "importantMetrics": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "key": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "description": {
            "type": "string"
          },
          "abbreviation": {
            "type": "string"
          },
          "calculationFormula": {
            "type": "string"
          }
        },
        "required": [
          "key",
          "name",
          "description",
          "abbreviation",
          "calculationFormula"
        ]
      }
    },
    "reports": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "key": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "description": {
            "type": "string"
          },
          "outputType": {
            "type": "string"
          }
        },
        "required": [
          "key",
          "name",
          "description",
          "outputType"
        ]
      }
    }
  },
  "required": [
    "key",
    "name",
    "shortDescription",
    "importantMetrics",
    "reports"
  ]
}

```

### Other

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
        id: "rental_health",
        name: "Rental Health",
        shortDescription: "Rental Health is a measure of the health of the rental market. It includes metrics like occupancy rates, lease expirations, and rental rates.",
        importantMetrics: [
          {
            id: "occupancy_rates",
            name: "Occupancy Rates",
            description: "The percentage of occupied units in a property or portfolio."
          },
          {
            id: "lease_expirations",
            name: "Lease Expirations",
            description: "The percentage of leases expiring in the next 12 months."
          },
          {
            id: "rental_rates",
            name: "Rental Rates",
            description: "The average rental rates for the company’s properties."
          }
        ],
        reports: [
          {
            id: "rental_health_summary",
            name: "Rental Health Summary",
            description: "A summary of the company’s rental health based on key metrics.",
            prompt: "Give me a summary of the rental health ..........." ,
            outputType: "TextReport"
          },
          {
            id: "rental_health_trend",
            name: "Rental Health Trend",
            description: "A trend analysis of the company’s rental health over time.",
            prompt: "Give me a trend analysis of the rental trend ...........",
            outputType: "BarGraph"
          }
        ]
      }
    ]
  }
}
```
