from langflow.custom import Component
from langflow.inputs import DropdownInput
from langflow.template import Output
from langflow.schema.message import Message
from langflow.io import MessageTextInput, Output

import requests
import json

"""
This module defines a single custom component (`SecEdgarMergedComponent`) that merges
three different "tools" or functionalities for retrieving SEC 10-Q filings data:

1) **All Financials (mode='all_financials')**  
   - Retrieves the full 10-Q XBRL-based financial statements for a given ticker.

2) **Specific 10-Q Report (mode='specific_report')**  
   - Retrieves a specific part of the 10-Q for a given ticker.  
   - e.g. 'balance_sheet', 'income_statement', etc.

3) **Criteria-Related Info (mode='criteria_related_info')**  
   - Retrieves data related to a given "criterion" (e.g., 'debt', 'rent') in the 10-Q.

-------------------------------------------------------------------------------
Example System Prompt (to guide the LLM on how to choose the 'mode' & inputs):

"You have a single custom SEC 10-Q data extractor tool that has 3 possible modes:
1) 'all_financials' for full 10-Q financial data,
2) 'specific_report' for a specific 10-Q section (balance_sheet, income_statement, etc.),
3) 'criteria_related_info' for retrieving specific criteria.

When a user asks for the full 10-Q financial statements, set mode='all_financials'.
When a user asks for a specific statement, set mode='specific_report' and fill 'report_type'.
When a user asks for a custom criterion, set mode='criteria_related_info' and fill 'criterion_key'.
Always set 'ticker' according to the user's request."

-------------------------------------------------------------------------------
Example User Prompts that will route to the correct mode:

1) "Give me the info of debt criteria of AMT in sec filing."
   "Find me info on lease obligations for AMT's latest 10-Q."
   -> mode='criteria_related_info', ticker='AMT', criterion_key='debt'

2) "Give me all financial details of AMT stock in sec filing."
   "Please fetch all 10-Q financial data for AMT."
   -> mode='all_financials', ticker='AMT'

3) "Give me balance sheet of AMT stock in sec filing."
   "Show me the balance sheet of AMT's latest 10-Q."
   -> mode='specific_report', ticker='AMT', report_type='balance_sheet'

-------------------------------------------------------------------------------
"""

class SecEdgarMergedComponent(Component):
    display_name = "SEC 10-Q Data"
    description = "A custom component for retrieving financial statements, specific reports, or criteria information from SEC 10-Q filings."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "custom_components"
    name = "Sec10QDataExtractor"

    FINANCIALS_ENDPOINT = "https://4mbhgkl77s4gubn7i2rdcllbru0wzyxl.lambda-url.us-east-1.on.aws/financials"
    SEARCH_ENDPOINT = "https://4mbhgkl77s4gubn7i2rdcllbru0wzyxl.lambda-url.us-east-1.on.aws/search"
    CRITERIA_ENDPOINT = "https://4mbhgkl77s4gubn7i2rdcllbru0wzyxl.lambda-url.us-east-1.on.aws/get-matching-criteria-attachments"
    
    inputs = [
        MessageTextInput(
            name="ticker",
            display_name="Ticker",
            value="AAPL",
            info="The stock ticker symbol (e.g. AAPL).",
            tool_mode=True,
        ),
        DropdownInput(
            name="mode",
            display_name="Mode",
            options=["all_financials", "specific_report", "criteria_related_info"],
            info=(
                "Select 'all_financials' to retrieve the full 10Q XBRL-based data.\n"
                "Select 'specific_report' to retrieve a specific part of the 10Q.\n"
                "Select 'criteria_related_info' to retrieve specific criterion data from the 10Q."
            ),
            tool_mode=True,
        ),
        MessageTextInput(
            name="report_type",
            display_name="Report Type (Used if mode='specific_report')",
            value="",
            info="E.g.: 'balance_sheet', 'income_statement', 'operation_statement', or 'cash_flow'.",
            tool_mode=True,
        ),
        MessageTextInput(
            name="criterion_key",
            display_name="Criterion Key (Used if mode='criteria_related_info')",
            value="",
            info="Provide the criterion key to retrieve e.g. 'debt', 'rent', etc.",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Merged SEC Output",
            name="merged_sec_output",
            method="call_merged_tool",
        )
    ]

    def call_merged_tool(self) -> Message:
        """
        Decide which underlying call to run based on 'mode'.
        For PART 1, we'll return placeholder text.
        Replace this with real Lambda calls in PART 2.
        """

        ticker = self.ticker
        mode = self.mode
        report_type = self.report_type
        criterion_key = self.criterion_key

        if mode == "all_financials":
            return self._call_all_financials(ticker)

        elif mode == "specific_report":
            return self._call_specific_report(ticker, report_type)
        
        elif mode == "criteria_related_info":
            return self._call_criteria_info(ticker, criterion_key)

        else:
            return Message(
                text=(
                    f"You selected mode '{mode}', which isn't implemented yet.\n"
                    "In the future, we can add new routes or logic here."
                )
            )

    def _call_all_financials(self, ticker: str) -> Message:
        try:
            payload = {"ticker": ticker}
            response = requests.post(self.FINANCIALS_ENDPOINT, json=payload)
            response_data = response.json()  

            if "message" in response_data:
                return Message(text=response_data["message"])
            elif "data" in response_data:
                return Message(text=response_data["data"])
            else:
                return Message(text=json.dumps(response_data, indent=2))

        except Exception as e:
            error_text = f"Error calling SEC Edgar Lambda (/financials): {e}"
            return Message(text=error_text)

    def _call_specific_report(self, ticker: str, report_type: str) -> Message:
        try:
            payload = {"ticker": ticker, "report_type": report_type}
            response = requests.post(self.SEARCH_ENDPOINT, json=payload)
            data = response.json()  

            message_text = data.get("data", "")
            return Message(text=message_text)

        except Exception as e:
            error_text = f"Error calling SEC Edgar Lambda (/search): {e}"
            return Message(text=error_text)

    def _call_criteria_info(self, ticker: str, criterion_key: str) -> Message:
        try:
            payload = {"ticker": ticker, "criterion_key": criterion_key}
            response = requests.post(self.CRITERIA_ENDPOINT, json=payload)
            response_data = response.json()  

            if "message" in response_data:
                return Message(text=response_data["message"])
            elif "data" in response_data:
                return Message(text=response_data["data"])
            else:
                return Message(text=json.dumps(response_data, indent=2))

        except Exception as e:
            error_text = f"Error calling SEC Edgar Lambda (/get-matching-criteria-attachments): {e}"
            return Message(text=error_text)
