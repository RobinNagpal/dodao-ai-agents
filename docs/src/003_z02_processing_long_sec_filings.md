# Extracting Information from Long SEC Filings

In the below section(Extracting Information from Long Text) we discuss the reasoning and the process of extracting 
information from long SEC filings.

When processing long filings/text, we need to know which criterion on which we need to process the text.

See the [Evaluation Criteria](./002_z05_z01_evaluation_criteria.md) for more information on the criterion.

![Extracting Information from SEC Filings](./images/04_tech/process_long_sec_filings/long_sec_filings.png)

# Extracting Information from Long Text

This can be a product in itself.

Some background:

### Data Accuracy
- If we build a RAG it works well for text data, but doesn't work well for financial data which is context based,
  and for specific time, and specific sections.
- Using a RAG will lead to incorrect results
- Also its better is Data is provided in some other format to LLM, like as HTML, JSON or XBRL(see [SEC](https://www.sec.gov/data-research/inline-xbrl) for more information)
  LLM will perform better as it will exactly understand where the data belongs

If you have built a RAG you will probably agree right away.

### Generic Data Formats
- As mentioned above numeric data in PDFs might not be in a format that is easily readable by LLMs. So we
  should try to see if there are other input formats that are more readable by LLMs

In cases of SEC filings, the data is available in XBRL format, which is a format that can be more easily read by LLMs

### Providing Context
- With LLMs we are always trying to find a sweep spot between providing all the necessary information and not providing
  too much information
- This means we need to have all the information for a specific "section", or "category" of information
- One of the ways is if we extract the information before hand, and then provide it to the LLM and ask for a more formatted
  and specific information from the LLM

### Extracting Information
- One way to extract information is to use a PDF parser, and then extract the information from text page(or a few pages)
  at a time and extracting information corresponding to each "category" of information.
- This will make sure that no information is overlooked
- For example we can read the text and say
    - Extract rental related information for 2025 from these pages. Then combine all the information.
    - Extract revenue related information for 2024 from these pages. Then combine all the information.
    - This way we have extracted out all the rent related information, and also by year
    - Something like this is not possible with a RAG, as it will not understand the context of the information

# Extracting Information Design
In our design we need to be aware of the topics and the time/data/quarter for which the information may be needed. 
We then loop through the doc, and attachment by attachment we find which information matches the criteria.

This result is then saved in S3, and later fetched by the LLM tools.
