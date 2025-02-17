# Tasks

- [ ] Fix triggering of all the reports
- [ ] Add startup summary(`startupSummary: str`) to the `ProcessedProjectInfoSchema` and save it in agent-status.json

## Add startup summary

- In controller.py we call `ensure_processed_project_info(project_id)` to make sure that the `ProcessedProjectInfoSchema`
  is populated for all the information.
- In `ensure_processed_project_info(project_id)` there are checks for each field, similarly we need to check for
  startup summary.
- We can call `structured_llm_response` and try to get 3-4 sentences of summary of the startup. We
  can provide the startup crowd funding page and website home page both.
- Make sure to add a line/paragraph of 1-2 lines on the amount of money they are raising and the valuation. This
  will be saved as part of summary only.
- The prompt can be: "Provide a summary of the startup in 3-4 sentenctes and in next paragraph provide the amount of money that
  they are raising in the current crowdfunding round and the valuation."

## Pull/Push agent-status.json to s3 using tool

- Explain what we are trying to do here
  - Here we are trying to update the agent_status.json file whenever the a report is generated so that we can update the status to (in_progress, failed or complete )
  - So for that we will be creating a tool in langlfow which takes the report_type as input and fetch agent_status.json using the its public link based on project_id.
  - Then we update for the report type the status of it and than use the lambda we created to upload the updated agent_status.json file
- Explain how this tool will be used in langflow
  - In langflow this tool will work in a way that it will be a custom component which takes the report type and project id as inputs.
  - Then based on this input we fetch from the public link the agent status file for project and than update it accordingly
  - output it will return the updated json file agent_status
- Explain how the full flow will work
  - the full flow works in a way that when the processing of a report starts than this component is given the project id and report type and it updates the status of report to in_progress
  - Than when either the report is generated successfully or fails than based on that result the component is again called to update the status to failed or complete.
- Explain the list of things you are changing or adding in the code
  - Firstly we will add the logic for just getting the agent_status.json file
  - Than update logic based on report name
  - than just pass the stuff to the s3-uploader component which uploads the file
  - Also we may have to pass the status as input also we can set the default as in_progress
