from dotenv import load_dotenv
from edgar import Company, use_local_storage, set_identity
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.criteria_matching import get_ticker_report, save_latest10Q_financial_statements
from src.specific_10Q_report import specific_report_text
import pandas as pd

load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")


class ColumnsToInclude(BaseModel):
    columns_to_include: list[str] = Field(
        description="List of columns to include in the DataFrame after filtering."
    )


def get_statement_of_equity(ticker: str, period_of_report: str) -> str:
    """
    Fetches the statement of equity for a given ticker.
    """
    try:
        raw_text = specific_report_text(
            ticker, "equity_statement", fetch_raw_content=True
        )

        llm = ChatOpenAI(temperature=1, model="o4-mini")
        user_prompt = f"""
        The following is the raw text from an SEC 10-Q financial statement table:
        Extract the columns that represent the latest financial quarter and exclude the older ones.
        
        The period of report is {period_of_report}. You should see one of the columns for a quarter ending on {period_of_report}.
        
        You should pick that column and exclude the rest.
        
        Return the filtered contents of the statement
        
        Also normalize the values in the table to be in USD, so multiply the values by 1000 if they are in thousands or by 1000000 if they are in millions.
    
        Also add negative sign to the values that are negative in the table or have parenthesis as that generally means negative.
    
        **Return the information in markdown format which the values in the table and the column names as well.**
        
        # Raw text to analyze
        {raw_text}
        """

        response = llm.invoke([HumanMessage(content=user_prompt)])
        content = response.content
        return f"### Statement of Equity\n {content}"

    except Exception as e:
        print(f"Error fetching statement of equity: {str(e)}")
        return None


def filter_older_columns(df: pd.DataFrame, period_of_report: str):
    """
    Uses LLM to identify and remove older columns in financial statement tables,
    keeping only the latest quarter's data.
    """
    print(f"Filtering older columns from DataFrame with shape {df.shape}...")
    if df is None or df.empty:
        return df  # Return as-is if DataFrame is empty

    columns_text = "\n".join(df.columns)  # Convert column names to text

    llm = ChatOpenAI(temperature=1, model="o4-mini")

    user_prompt = f"""
        The following are column names from an SEC 10-Q financial statement table:

        Identify the column that represent the latest financial quarter and exclude the older ones.
        
        Return only the names of the column that should be included as Python list without any code fences or quotes.
        
        You should see one of the columns for a quarter ending on {period_of_report}. You should pick that column and exclude the rest.

        # Columns to analyze 
        
        {columns_text}
        """

    print(user_prompt)

    structured_llm = llm.with_structured_output(ColumnsToInclude)
    columns_to_include: ColumnsToInclude = structured_llm.invoke(
        [HumanMessage(content=user_prompt)]
    )

    print(f"Columns to include: {columns_to_include}")

    # Check if columns_to_include is not empty and columns exist in DataFrame
    if not columns_to_include.columns_to_include:
        return None
    valid_cols = [col for col in columns_to_include.columns_to_include if col in df.columns]
    if not valid_cols:
        return None
    
    # Drop only existing columns to prevent KeyErrors
    to_include = columns_to_include.columns_to_include
    to_include.append("label")
    to_include.append("level")
    columns_to_exclude = [col for col in df.columns if col not in to_include]

    cleaned_df = df.drop(columns=columns_to_exclude, errors="ignore")

    print(f"Cleaned DataFrame:\n{cleaned_df.head()}")
    return cleaned_df  # Use errors="ignore" to prevent KeyErrors


def fetch_from_raw_html(ticker: str, report_type: str, period_of_report: str) -> str:
    """
    Fetches raw text from the latest 10-Q filing attachments based on report type.
    """
    print(f"Fetching raw HTML content for {ticker} and report type {report_type}...")

    raw_content = specific_report_text(ticker, report_type, fetch_raw_content=True)
    if not raw_content:
        raise ValueError(
            f"No raw content found for ticker '{ticker}' and report type '{report_type}'."
        )

    print(f"Raw content fetched successfully. {raw_content}")
    user_prompt = f""" 
    The following is the raw text from an SEC 10-Q financial statement table:
    
    I want to to focus on the latest quarter and exclude the columns that are older or is not specific to the latest 
    quarter i.e. three months. If the data is for nine months or year, exclude that.
    
    Return the consolidated version of the financial statement that is correct and make sure to include the latest quarter.
    
    The period of report is {period_of_report}. You should see one of the columns for a quarter ending on {period_of_report}.
    
    **Return the information in markdown format which the values in the table and the column names as well.**
    
    Also normalize the values in the table to be in USD, so multiply the values by 1000 if they are in thousands or by 1000000 if they are in millions.
    
    Also add negative sign to the values that are negative in the table or have parenthesis as that generally means negative.
    
    **Read the contents carefully to make the decision on normalization and negative sign.**
    
    # Raw text to analyze
    {raw_content}
    """
    llm = ChatOpenAI(temperature=1, model="o4-mini")
    response = llm.invoke([HumanMessage(content=user_prompt)])

    content = response.content
    return content


def cross_check_income_statement(
    ticker, df_based_report: str, raw_html_based_report: str, period_of_report: str
) -> str:
    """
    Cross-checks the income statement with the balance sheet and cash flow statement.
    """

    print(f"Cross-checking income statement for {ticker}...")

    text_content = specific_report_text(ticker, "income_statement")

    user_prompt = f"""
    I have extracted the following financial statement from an SEC 10-Q filing using two different methods.
    I will share with you three different versions of the same financial statement. Make sure to cross-check the 
    values between the data frame based version and the raw HTML based version and make sure they match. I 
    will also share with you the text version of the financial statement. You can also refer to that to see 
    which one is correct. 
    
    I want to to focus on the latest quarter and exclude the columns that are older or is not specific to the latest 
    quarter i.e. three months. If the data is for nine months or year, exclude that.
    
    Return the consolidated version of the financial statement that is correct and make sure to include the latest quarter.
    
    The period of report is {period_of_report}. You should see one of the columns for a quarter ending on {period_of_report}.
    
    **Return the information in markdown format which the values in the table and the column names as well.**
    
    Also normalize the values in the table to be in USD, so multiply the values by 1000 if they are in thousands or by 1000000 if they are in millions.
    
    Also add negative sign to the values that are negative in the table or have parenthesis as that generally means negative.
    
    **Read the contents carefully to make the decision on normalization and negative sign.**
    
    
    # Data frame based report
    {df_based_report}
    
    # Raw HTML based report
    {raw_html_based_report}
    
    # Text version of the financial statement
    {text_content}
    """

    llm = ChatOpenAI(temperature=1, model="o4-mini")
    response = llm.invoke([HumanMessage(content=user_prompt)])

    content = response.content
    return content


def get_xbrl_financials(ticker: str, force_refresh: bool = False) -> str:
    latest10Q_financial_statements = ""
    try:
        ticker_report = get_ticker_report(ticker)
        latest10Q_financial_statements = ticker_report.latest10QFinancialStatements
    except Exception as e:
        print(f"Error getting ticker report: {str(e)}")
    if latest10Q_financial_statements and not force_refresh:
        return latest10Q_financial_statements

    print(f"Fetching Financial Statements from scratch...")

    company = Company(ticker)
    tenq = company.latest_tenq
    period_of_report = company.latest_tenq.period_of_report

    # Extract financial statements
    statements = {
        "Balance Sheet": tenq.balance_sheet.to_dataframe(),
        "Income Statement": tenq.income_statement.to_dataframe(),
        "Cash Flow Statement": tenq.cash_flow_statement.to_dataframe(),
        "Equity Statement": tenq.financials.statement_of_equity().to_dataframe(),
    }

    filtered_statements = []
    for statement_name, df in statements.items():
        if df is not None and not df.empty:
            print(f"Processing {statement_name} for {ticker}...")
            print(df)
            cleaned_df = filter_older_columns(df, period_of_report)

            if cleaned_df is None:
                print(f"No relevant columns found in {statement_name} for {ticker}.")
                try:
                    cleaned_report = fetch_from_raw_html(ticker, statement_name.lower().replace(" ", "_"), period_of_report)
                    print("Cleaned report from raw HTML:\n", cleaned_report)
                    markdown_output = f"### {statement_name}\n" + cleaned_report
                    filtered_statements.append(markdown_output)
                except Exception as e:
                    print(f"Error fetching raw HTML for {statement_name}: {str(e)}")
                    continue
            else:
                markdown_output = f"### {statement_name}\n" + cleaned_df.to_markdown(
                    floatfmt=""
                )
                filtered_statements.append(markdown_output)


    if not filtered_statements:
        return (
            f"No relevant financial statements found in the latest 10-Q for '{ticker}'."
        )
    latest10Q_financial_statements = "\n\n\n\n".join(filtered_statements)

    try:
        save_latest10Q_financial_statements(ticker, latest10Q_financial_statements)
    except Exception as e:
        print(f"Error saving latest10q financial statements: {str(e)}")
    return latest10Q_financial_statements
