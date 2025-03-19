# Architecture

Koalagains is a platform which allows the creation of the comprehensive and detailed reports for particular sector and industry group

## Sector and Industry Group

There are lots of public equities which can be divided into different categories and sub categories. In our case at Koalagains we have used the GICS as standard for dividing the equities

### What is GICS?

GICS (Global Industry Classification Standard) is an industry taxonomy which divides which consists of 11 sectors,25 industry groups 74 industries and 163 sub industries

![GICS](./images/gics.svg)

### Why GICS?

- We at koalagains chose GICS as it is one of the best classification standard that exists for the industries developed by developed by MSCI in collaboration with S&P Dow Jones Indices.
- Also the classification by GICS is not to large and is understandable easily
- It is commmonly used around the world in different indices like S&P 500.

## Criteria

Now when we have to analyze a sector and industry group we must finalize some cirteira based on which any company that falls in these can be evaluated.The criteria must be according to the industry group as their are 25 of them.

### Why Criteria is at industry group level?

The criteria is finalized at industry group level because the at sector level it would have beeen to generalized while at the industry level it would have been overwhelming and would take long

### What is Criteria?

- The criteria is a collection of criterions which are specific to the industry group .
- Each of the criterion is provided with the SEC 10 Q data and matching instruction for that criterion based on which factual information is extracted
- Also all the criterions are provided with matching instruction which helps in calculating criteria
- Spider Chart is also shown which consits of all the criterions

- For Example for REITS Industry Group

![CUstom-Crietria](./images/criteira_and_report/custom-criteria.png)

## Reports

Now after the criteria is finalized than we generate the reports for the criterions

- One criterion can have multiple reports
- each report will have information about what it will generate
- each report will have a type either text or chart
- each criterion will have a performace checklist
- each criterion will have important metrics
- The spider chart is based on the cheklist of all the criterions

### How report is generated?

- To generate the reports for the criterion the criterion info along with ticker is passed to an AI agent
- We at koalagains have used langflow to create the AI Agents
- The AI Agent can be created using langflow or any other tool and than this AI Agent can be used using its URL and passing the the information in payload which contains:
  - ticker
  - reportKey
  - criterion
    - key
    - name
    - shortDescription
    - importantMetrics
    - reports
- Now this information is passed to the AI Agent and as a return the Agent generates a report and returns back to the platform.
- This report is than shown on the platform

## How Do AI Agent Works Here?

The AI Agents that we have made using langflow till now can be called using their URLs and giving them the payload which includes:

- ticker
- reportKey
- criterion
  - key
  - name
  - shortDescription
  - importantMetrics
  - reports

### Extraction

- The above data is in Json format so firstly it is converted to message form which is processable by different components in langflow
- Now the reportKey which comes in payload decides that what part of flow will run.

### SEC 10Q Data

- Also the in a while the SEC 10 Q data tool is being used to get
  - All financial statements
  - Criteria related information based on criterion key in the payload
- Output of the above two is combined in a single place

### Report Key

Now based on the reportKey one of the following occurs:

- If reportKey is `all` then the whole flow will run including performance checklist, important metrics and all specific reports
- If reportKEy is `performanceCheckist` the flow for performance checklist will run only
- If reportKEy is `importantMetrics` the flow for important metrics will run only
- If reportKEy is a specific report e.g `debt_information` the flow for the debt information report will run only

### Generation of Reports

- When this flow runs it generates a report which is either a text report or a visualization like pie chart etc
  - The above report type also comes from the payload where the criterion has reports which have specific reportType there

### Saving of the Reports

- After the generation of the reports these reports are saved into s3

## Showing of the Reports

- Now after the saving of the reports these reports will be visible on the platform

  ![Report](./images/criteira_and_report/report-example.png)

### Processing Long SEC Filings

See [003_z02_processing_long_sec_filings.md](./003_z02_processing_long_sec_filings.md)
