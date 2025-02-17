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
