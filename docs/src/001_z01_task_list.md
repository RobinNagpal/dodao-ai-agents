- [ ] Add the docs about getting started

- [ ] Explain the architecture of the project

# Architecture of the project (just current scope)

- We enable creating of reports for a particular sector and industry group.
  - Explain what a Sector and Industry group is. Explain about GICS.
  - Why we chose to use GICS
- Now when we are analyzing a particular sector, and industry group, we need to know how that sector and industry group is different
  - That means we need to know about the criteria on which we should evaluate the companies in that sector and industry group
  - For this we use criteria which is a list of criterion
  - Each criterion represents part of the Radar/Spider chart
  - So each criteria also includes information about how to calculate the value of that criteria
- Then we generate reports under each criterion, so we declare what each type of report is.
- The Implementation of the report is done via an AI agent. We can use any AI agent we want.
- The platform will call that AI agent and ask it to generate the report. So when we create the ciiteria, we also need to specify which AI agent to use for that criteria. (We tell the URL of the AI agent)
- Langflow is one such AI agent platform which helps in creating AI agents. So we can use Langflow to create AI agents for generating reports.
- The platform will call the AI agent and ask it to generate the report. The AI agent will generate the report and return it to the platform.
- Then the report is displayed in the platform.

# About the AI agent

- The AI Agent is called with a URL and also the payload is passed to it. The payload includes:
  - ticker
  - reportKey
  - criterion
    - key
    - name
    - shortDescription
    - importantMetrics
    - reports
- All the required information is extracted form the payload in the processable input form
- Now based on the reportKey either we can run all the reports for the criterion or the specific one
  - The specific reportKey can be performanceChecklist ,importantMetrics or any specific report
- First of all the Data is obtained from SEC 10Q report for that ticker using the Dodao SEC tool
  - The tool is use dot obtain all the financial statements
  - The tool is used to obtain the criterion related specific data
- Then the output of these tools is combined
- Then based on the reportKey next steps are as follows
  - If reportKey is `all` then the whole flow will run including performance checklist, important metrics and all specific reports
  - If reportKEy is `performanceCheckist` the flow for performance checklist will run only
  - If reportKEy is `importantMetrics` the flow for important metrics will run only
  - If reportKEy is a specific report e.g `debt_information` the flow for the debt information report will run only
- When this flow runs it generates a report which is either a text report or a visualiztion like pioe chart etc and it is saved to s3
  - The report type is also specified in the report information
  - based on this report type the corresponding report will be generated and saved to s3
