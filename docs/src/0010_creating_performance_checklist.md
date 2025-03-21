# How to Generate the performance checklist for your desired company

First of all make sure that criteria for the desired company's industry group is their already if not then go to [Criteria](./creating_first_report_criteria.md)

## Generating the Checklist

- Build the flow

  ![Copy Criteria](./images/criteira_and_report/flow-for-checklist.png)

- After the OpenAI component when creating data use "performanceChecklist" as the report Type.
- Carefully fill the fileds whcih are in yellow rectangle in image
- The Api Request should be sent to https://kolagains.com/api/langflow/save-performance-checklist

## Prompts for checklists:

- When you are creating the checklist for the first time you will use the prompt. Below exapmle is for criterion stock types you will have to make changes for your criterion accordinginly

```
Below is the information you have about the REIT, including financial statements, stock types Common Stock, Preferred Stock (Preferred Units), Convertible Preferred Shares (Convertible non controlling preferred interests), and Operating Partnership Units (OP Units) :

{data}

Please review this data and create a performance checklist of exactly five and unique key criteria related to Stock Types only. Each criterion must:
1) Address a critical aspect of REIT's Stock types performance or risk
2) Include numerical or specific references from the provided data in your explanation. never use par value as  reference .
3) Assign a score of 0 or 1 with clear logic on why it passes or fails.

Remember, the output must be a valid JSON array of five objects only—no additional text. Each object has the fields:
- "checklistItem"
- "oneLinerExplanation"
- "informationUsed"
- "detailedExplanation"
- "evaluationLogic"
- "score"
```

- Then the output of this prompt will be passed to the Open AI component where the prompt will be set as

```
You are a highly knowledgeable REIT performance analyst. Your role is to evaluate the provided financial statements and stock types data to create five key performance criteria for assessing this REIT’s health and risk. Each checklist item must be scored 0 or 1 based on whether the REIT meets the criterion, with clear reasoning. Return the results only as a JSON list of 5 objects.

Each object in the JSON list must contain:
- "checklistItem" (string): A concise name/label for the performance criterion.
- "oneLinerExplanation" (string): A brief 1-line summary of why it matters.
- "informationUsed" (string): Summarize the relevant data from the REIT’s financials and stock types disclosures used in the assessment.
- "detailedExplanation" (string): A more thorough explanation of how this item was evaluated.
- "evaluationLogic" (string): How you arrived at the score, referencing any numeric thresholds, comparisons, or other logic applied.
- "score" (integer): 1 if the criterion is met, 0 if not met.

Do not include any additional commentary or text outside the JSON list. Output only the JSON array of 5 objects.

```

The abpve prompts are specific to REITS and criterion stock types so make changes accordingly
