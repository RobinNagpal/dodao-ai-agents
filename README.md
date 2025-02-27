# Docs
- See functional/business docs at https://docs.koalainsights.com
- Docs are created using `mdBook`


# Development
This repo has four main parts
1. The backend server which is present in `crowd-fund-analysis` folder
2. The deployment of langflow which is present in `langflow` folder
3. Custom agent(langflow) tools and flows which are present in `langflow-bundles` folder. These components are 
wrappers and call the lambda functions. This is done to keep things decoupled and to make it easier to test. 
4. Lambda functions which are present in `agent-tools` folder. 

Each of these components have their own READMEs which explain how to run them.

Important Readmes:
- [Backend Readme](crowd-fund-analysis/README.md)
- [Langflow Readme](langflow/README.md)
- [Langflow Bundles Readme](langflow-bundles/README.md)
- [Agent Tools Readme](agent-tools/README.md)

# Checklist to see if you understand the important concepts

## Backend
- [ ] How API is called
- [ ] How agent-status.json is created and updated
- [ ] How reports are created

## Langflow
- [ ] Why we do a custom setup?


## Langflow Bundles


## Agent Tools
