# Latest 10Q Financial Info
In 10Q filing we have quite some information. Some of the standard information includes:
- Balance Sheet
- Income Statement or Statement of Operations
- Cash Flow Statement

This information is very useful for analyzing basic financial health of the company.

# Code
Code of this tool can be found at [agent-tools/sec-edgar/src/lambda_function.py](./../../agent-tools/sec-edgar/src/lambda_function.py)

# Open Items
- Validation of the extracted information
- See if we can optimize for the model being used
- Right now we call the model for each of the information. Can we call the model once and get all the information in one go?
