# Criterion Info from Latest 10Q
For each sector and sub-sector we will have a set of criterion based on which we can evaluate the company. For e.g.
for REITs, some of the criterion could be:
1. Debt & Leverage
2. Rental Health
3. Cost of Operations
4. Stock Structure & Dividends
5. Management - Team and Board
6. Value(for Money)

This tool extracts the relevant attachments from the latest 10Q filings that are specific to these criterion.

# Other Information
See
- [005_z05_extracting_info_from_latest_10q.md](./005_z05_extracting_info_from_latest_10q.md)
- [005_z06_processing_long_sec_filings.md](./005_z06_processing_long_sec_filings.md)
- [005_z07_collecting_info_from_pdf.md](./005_z07_collecting_info_from_pdf.md)


# Working
We can have two commands:
1. `start-criterion-info-extraction` - During this stage the tool will work on an async manner i.e. as soon as it gets the 
   request, it will return success and start the process of extracting the criterion information. Extracting information 
   about criterion is explained in detail in the next section.
2. `get-criterion-info` - Extraction of the information takes 1-2 mins, so this task will first trigger the extraction of 
   criterion information "if it doesn't exist" and then wait for the extraction to be completed. Once the extraction is completed, it will return 
   the extracted information.


# Extracting Criterion Information
- [005_z05_extracting_info_from_latest_10q.md](./005_z05_extracting_info_from_latest_10q.md)

# Code
The code for this tool can be found at [agent-tools/extract-criterion-info/lambda_handler.py](./../../agent-tools/extract-criterion-info/lambda_handler.py)
