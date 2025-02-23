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
