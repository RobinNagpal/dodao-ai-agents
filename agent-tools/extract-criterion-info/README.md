# 10-Q Report Data Extraction Lambda
## Purpose
This AWS Lambda function extracts topic-specific data from SEC 10-Q reports. It identifies key financial topics such as rent, lease, debt, and stock distribution from report attachments.

## Process Overview
1. Retrieve Latest 10-Q Report
   - Fetches the most recent 10-Q filing from the SEC for a given stock ticker.
   - Extracts all attachments except financial statements (e.g., balance sheets, income statements).
  
2. Analyze Attachments for Relevant Topics
   - Uses GPT-4o-mini to determine whether each attachment contains highly relevant information for up to two topics.
   - Outputs a JSON result with match confidence scores for each topic.

3. Store Extracted Data in S3

   - Saves matched content in S3, organized by ticker and topic:
    <Ticker>/Latest10QReport/<Topic>.txt  
    Example: FVR/Latest10QReport/rent.txt
    
4. Status Tracking & Retrieval
   - Updates a status file in S3 (status.json) to indicate if processing is complete.
   - A separate tool can read the stored files for further analysis.

- [] Lambda Function Handler 
- [] Parsing and Validating Input (ticker, keywords)
- [] Fetching Latest 10-Q Filings from SEC
- [] Excluding Attachments (which are already covered in another tool)
- [] Limiting Topics to Two
- [] See whether other attachments has very large content or not, if yes then divide it partially and then give it to LLM
- [] Calling LLM with correct prompt
- [] Checking for Matched Topics and Confidence Score
- [] Adding Content to S3 files
- [] Maintaining a Status file in S3
- [] Lambda Response type
- [] Testing Required


## changes

### cleanups
- rename `get_raw_10q_text` to `get_criterion_matched_attachments_list`
- store attachment url instead of content
- add url key in MatchedAttachment model:
  ```python
  class MatchedAttachment(BaseModel):
    name: str = Field(description="The name of the attachment")
    url: str = Field(description="The url of the attachment")
    matched_amount: float = Field(description="The percentage of the content that matched the criterion")
  ```
- store and use open api key from env variable

### s3 changes
- store and use bucket name from env variable
- store the json file `<bucket-name>/US/<ticker>/latest-10q-criterial-info.json` in the following format:
  ```json 
   {
      "ticker": "AMT",
      "sector": {id: 6, name: "Real Estate"},
      "industryGroup": {id: 60, name: "Equity REITs"},
      "industry": {id: 6010, name: "Specialized REITs"},
      "subIndustry": {id: 601010, name: "Specialized REITs"},
      "latest10QSecURL": "https://www.sec.gov/Archives/edgar/data/1053507/000105350721000013/0001053507-21-000013-index.htm",
      "criteriaExtractedInfo": [
         {
            criterionId: 'rental_health',
            criterionName: 'Rental Health',
            relevantAttachments: [
            {
               attachmentName: 'Exhibit 99.1',
               attachmentURL: 'https://www.sec.gov/Archives/edgar/data/1053507/000105350721000013/amt-ex991_6.htm',
               mathcingAmount: 80 // Percentage of matching information
            }
            ]
         }
      ]
   }
  ```