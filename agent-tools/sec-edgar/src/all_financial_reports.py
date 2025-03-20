from dotenv import load_dotenv
from edgar import Company, use_local_storage, set_identity
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from src.criteria_matching import get_ticker_report, save_latest10Q_financial_statements
load_dotenv()

# Initialize edgar settings
use_local_storage()
set_identity("your_email@example.com")


def filter_older_columns(df):
    """
    Uses LLM to identify and remove older columns in financial statement tables,
    keeping only the latest quarter's data.
    """
    if df is None or df.empty:
        return df  # Return as-is if DataFrame is empty

    columns_text = "\n".join(df.columns)  # Convert column names to text

    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

    system_prompt = "You are an expert in financial statement analysis."

    user_prompt = f"""
        The following are column names from an SEC 10-Q financial statement table:
        {columns_text}

        Identify the column that represent the latest financial quarter and exclude the older ones. Dont exclude the 'concept' column.
        Return only the names of the excluded columns as a Python list without any code fences or quotes.
        """

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    # Ensure the response is a valid Python list
    try:
        excluded_columns = eval(response.content)
        print(f"Excluded Columns: {excluded_columns}")
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        excluded_columns = []

    # Drop only existing columns to prevent KeyErrors
    existing_excluded_columns = [col for col in excluded_columns if col in df.columns]

    return df.drop(
        columns=existing_excluded_columns, errors="ignore"
    )  # Use errors="ignore" to prevent KeyErrors


def get_xbrl_financials(ticker: str) -> str:
    latest10Q_financial_statements = ''
    try:
        ticker_report = get_ticker_report(ticker)
        latest10Q_financial_statements = ticker_report.latest10QFinancialStatements
    except Exception as e:
        print(f"Error getting ticker report: {str(e)}")
    if latest10Q_financial_statements:
        return latest10Q_financial_statements

    company = Company(ticker)
    tenq = company.latest_tenq

    # Extract financial statements
    statements = {
        "Balance Sheet": tenq.balance_sheet.get_dataframe(),
        "Income Statement": tenq.income_statement.get_dataframe(),
        "Cash Flow Statement": tenq.cash_flow_statement.get_dataframe(),
    }

    filtered_statements = []
    for statement_name, df in statements.items():
        if df is not None and not df.empty:
            print(f"Processing {statement_name} for {ticker}...")
            cleaned_df = filter_older_columns(df)
            markdown_output = f"### {statement_name}\n" + cleaned_df.to_markdown(
                floatfmt=""
            )
            filtered_statements.append(markdown_output)

    if not filtered_statements:
        return (
            f"No relevant financial statements found in the latest 10-Q for '{ticker}'."
        )
    
    latest10Q_financial_statements =  "\n\n\n\n".join(filtered_statements)
    try:
        save_latest10Q_financial_statements(ticker, latest10Q_financial_statements)
    except Exception as e:
        print(f"Error saving latest10q financial statements: {str(e)}")
    return latest10Q_financial_statements