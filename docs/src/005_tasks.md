# Tasks

This page has list of all the tasks

---
## Push/Pull agent-status.json to s3 using tool - `Hussain` - `Parked`

Note - `May be this can be called SubmitReport?`


### Open Items
- Right now we dont know how the generic agent status file will look like.

See [005_z01_push_pull_agent_status_fom_s3.md](./005_z01_push_pull_agent_status_fom_s3.md)

---
## Extracting Information from Latest 10Q - `Dawood` - `In Progress`
We want this for analyzing REITs. 

See 
- [005_z05_extracting_info_from_latest_10q.md](./005_z05_extracting_info_from_latest_10q.md)
- [005_z06_processing_long_sec_filings.md](./005_z06_processing_long_sec_filings.md)
- [005_z07_collecting_info_from_pdf.md](./005_z07_collecting_info_from_pdf.md)

---

## Structured LLM Prompt Editor

This can be a Typescript app which allows for adding a `StructuredLLMCall`.
- Input type and schema
- Output type and schema
- Prompt
- Default Model

Then it gives a slug based url which can be called with the input, and the model type.

We can also save all the invocations, making it easier to debug.

See [005_z02_structured_llm_prompt_editor.md](./005_z02_structured_llm_prompt_editor.md)

---

## Spider Charts Criterion for all the tickers
- For spider charts we need to evaluate an equity based on 6 or 8 criterion. 
- We need to have a way to get the criterion for all the tickers.
- Which means we can get criterion for sectors and sub-sectors and then we can get criterion applicable to 
an equity based on the sector and sub-sector.

See [005_z03_generic_spider_chart_criterion.md](./005_z03_generic_spider_chart_criterion.md)


---

## Pull SEC EDGAR Filings Information
Analyze all the python libraries for extracting information from SEC. There are many libraries that can be used to
extract information from SEC.

See [005_z04_compare_sec_filing_libs.md](./005_z04_compare_sec_filing_libs.md)

---

## V1 - Timeline and Summarized SEC EDGAR Filings

---
