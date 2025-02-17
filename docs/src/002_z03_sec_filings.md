# V1 - Timeline and Summarized SEC EDGAR Filings
This can be a product in itself. Here we consider all type of SEC filings and summarize them.

This feature has two main parts
- Summarized SEC EDGAR Filings
- SEC Fillings Timeline i.e. storing the summaries and events with proper information so that it can be
  shown in a timeline.


### 1. Summarized SEC EDGAR Filings

For creating great information on REITs we need to make sure the SEC fillings information is nicely extracted. Nicely
means
- Extracting the most important information
- Grouping the information by some criteria(like by Debt, by Rent, by Growth, etc)
- Keeping both quantitative and qualitative information
- Capturing the timeline of events and storing them in a proper way

When evaluating equity Real Estate Investment Trusts (REITs), it's essential to consider various SEC filings that
provide comprehensive insights into their operations, financial health, and strategic plans. Below is a ranked list of
the ten most important SEC forms for equity REITs, along with their average page counts:

| Rank | SEC Form                           | Description                                                                                                                                   | Average Page Count                  |
|------|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| 1    | **Form 10-K**                      | Annual report providing a comprehensive overview of the REIT's business and financial condition, including audited financial statements.      | Approximately 200-300 pages         |
| 2    | **Form 10-Q**                      | Quarterly report detailing the REIT's financial position and operations for the quarter, including unaudited financial statements.            | Approximately 50-100 pages          |
| 3    | **Form 8-K**                       | Current report used to announce major events that shareholders should know about, such as acquisitions, disposals, or changes in management.  | Varies widely; typically 2-10 pages |
| 4    | **Form S-11**                      | Registration statement for securities offerings by REITs, providing details on the use of proceeds, business plans, and risk factors.         | Approximately 100-200 pages         |
| 5    | **Schedule 14A (Proxy Statement)** | Document providing information on matters to be discussed at shareholder meetings, including executive compensation and corporate governance. | Approximately 50-150 pages          |
| 6    | **Form 3**                         | Initial statement of beneficial ownership filed when an individual becomes a company insider.                                                 | Typically 2-3 pages                 |
| 7    | **Form 4**                         | Statement of changes in beneficial ownership, filed to report transactions in the company's securities by insiders.                           | Typically 2-3 pages                 |
| 8    | **Form 5**                         | Annual statement of changes in beneficial ownership, covering transactions not reported on Form 4.                                            | Typically 2-3 pages                 |
| 9    | **Form S-3**                       | Simplified registration form for secondary offerings, allowing companies to register securities more quickly.                                 | Approximately 50-100 pages          |
| 10   | **Form 144**                       | Notice of proposed sale of securities by affiliates in reliance on Rule 144.                                                                  | Typically 2-5 pages                 |

**Long Forms**

If we just try to summarize form 10K, 10Q or other larger forms
- We can miss some important information
- The context can be lost by LLMs
- The information will not be grouped by some criteria, as we want to then later do some analysis each of the groups
  for example  do deeper analysis by Debt, by Rent, by Growth, etc

See more information on collecting information from PDFs in the [Collecting Infor for Large Text](./004_z01_collecting_info_from_pdf) section.

**Short Forms**
These can be easily summarized by LLMs, but they don't contain much information.


### 2. SEC Fillings Timeline
