# Industry group criteria information

## Populate Custom Criteria

- If AI Criteria is not present create it from koalgains UI (https://koalagains.com/public-equities/industry-group-criteria)
- copy custom criteria from ai if already not present
- start Editing custom Criteria as per requirement

## Populate specific criterion information

- If required criterion doesn't exist already add it in custom criteria

### Understand criterion using ChatGPT

- Use ChatGPT to understand the criterion

### Create Criterion Structure using ChatGPT

- create criterion structure using chatGPT which includes:
  - key
  - name
  - shortDescription
  - importantMetrics(3to5)
  - reports(theoretical + visuals)
- it should be like this {
  key:string,
  name:string,
  shortDescription:string,
  importantMetrics:[]
  reports:[]
  }

### Refine Custom Criteria

- refine the AI generated criterion based on your understanding and data provided in SEC-10Q report

### Save the custom Criteria on Koalagains

- Save the refined criterion within that specific industry group custom criteria

  https://koalagains.com/public-equities/industry-group-criteria

# Create First Report in Langflow

- Create a very basic report in langflow to test the accuracy of the extracted information from SEC10-Q attachements for the new criterion

## Populate Matching Criterion

- if new criterion was added we need to retrigger the populating of matching attachments (press the regnerate button for it on debug page)
  https://koalagains.com/public-equities/debug/ticker-reports/FVR

  - Instead of FVR use the The Ticker you are working with

## List Matching Sections from latest 10Q

- Go through the latest 10Q report and see which are the sections that match
- The macthed sections are the ones which we expect to be listed on the debug page

## Test Matching Criterion

- After retriggering of mathching attachments, review the content present in the accordion of the specific criterion
- if not satisfied than need to update the short description of the criterion

## Create report using chat Input/Output + SEC Edgar Tool

- Create a simple Flow by using the SEC edgar tool:
  - select `criteria_related_info` from the Mode dropdown
  - enter your specific criterion key in the Criterion Key field

## Test Report Relevance

- Use the information from tool output to generate a simple report
- Test the relevance of report if not satisfied try tweaking the prompt

# Integrate first report with Koalagains

# Integrate Metrices with Koalagains

# Integrate PerformanceChecklist with Koalagains

# Integraate other custom reports with Koalagains

## Creating Visualizations

# Tasks

- [ ] first part will be to add stock types to custom criteria with one reoprt ype for now
- [ ] call the populate endpoint sec-edgar tool lambda with a Ticker right now e are using FVR
- [ ] use the tool with criterion Key
- [ ] we get data based on that data we can ask gpt what kind of reports we can generate or visualization
- [ ] than we decide on the type of report and start making branches
