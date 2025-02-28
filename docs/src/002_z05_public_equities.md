# Analyzing public equities
We definitely want to focus on REITs first but we want to write the code in a generic way so that we can use it for 
other public equities as well. This will allow us to create some basic reports for any public company.

# Spider Charts
At the core will be spider charts. Which means analyzing the company based on some criteria. 

We already have GICS sectors and industries. See - https://en.wikipedia.org/wiki/Global_Industry_Classification_Standard

Based on the type of company we can ask AI to give us 6-8 right criteria to evaluate the company.

# Terms Used
- Criteria - A set of criterion that can be used to evaluate a company.
    - Spider Charts: we plan to create spider charts for each company based on these criteria, with scores for each criterion. see example here - https://koalagains.com/crowd-funding/projects/nightware
- Criterion - A single parameter or topic or area that can be used to evaluate a company in a Industry Group. example `founderAndTeam`, `traction`, `marketOpportunity`, `executionSpeed` etc. See example of six criterion here - https://koalagains.com/crowd-funding/projects/nightware
    - For each criterion, need to calculate a score. We can use our current pattern for this
    - So corresponding to each criterion, we can have a `performanceChecklist: List[ChecklistItem]` of size 5
      ```python
      from pydantic import BaseModel, Field
      
      class ChecklistItem(BaseModel):
          """Checklist item with a score and comment."""
          checklist_item: str = Field(description="The item to be checked. Explain in 7-10 words.")
          one_line_explanation: str = Field(description="A brief explanation of how the item was evaluated.")
          information_used: str = Field(description="All the information used to evaluate the item.")
          detailed_explanation: str = Field(description="A very detailed explanation of how the item was evaluated. "
                                                        "Use numbers whenever possible like the numbers shared by startup or by industry standards. "
                                                        "Explain in at least 4-5 sentences.")
          evaluation_logic: str = Field(description="Explain in detail on how did you make an opinion. "
                                                    "What type of startup's data did you use, what industry standards did you take. "
                                                    "Explain by using the numbers shared by startup or by industry standards"
                                                    "Explain in at least 4-5 sentences.")
          score: Literal[0, 1] = Field(description="The score given for this item 0 or 1.")
      ```
- Metric - Under a criterion, a metric is a specific numerical value that will show how well a company is doing in that criterion.
  The reason to define these metrics is to have a common set of metrics when we compare different companies in a Industry Group. Will be implemented later.
- Report - For each criterion, we can have a report that can be generated.



# Step 1 - Evaluation Criteria for a Company

- We have four levels of information - Sector(11), Industry Group(25), Industry(74), and Sub-Industry(163).
- It wont be possible to have specific criteria for all 163 sub-industries, or even all 74 industries.
- If we are working on a specific criteria, it might be good to target them at "Industry Group" level

Here [002_z05_z01_evaluation_criteria.md](./002_z05_z01_evaluation_criteria.md) we have discussed how we can save the criteria information for each Industry Group


# Step 2 - Generating Reports for a Ticker
This involves three steps

### Extracting Information from Latest 10Q
Here we want to extract information related to each criterion from the latest 10Q. This has already been implemented 
in [004_z02_latest_10Q_criterion_info.md](./004_z02_latest_10Q_criterion_info.md).

### Create the Report
This is discussed in this section: [002_z05_z02_generating_reports_for_a_ticker.md](./002_z05_z02_generating_reports_for_a_ticker.md)

### Save the Report
See [002_z05_z03_save_report.md](./002_z05_z03_save_report.md)
