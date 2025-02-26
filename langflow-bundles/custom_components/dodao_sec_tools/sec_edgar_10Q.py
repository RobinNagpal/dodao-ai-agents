from langflow.custom import Component
from langflow.inputs import StrInput, DropdownInput
from langflow.template import Output
from langflow.schema.message import Message

class SecEdgarMergedComponent(Component):
    display_name = "SEC 10-Q Financial Data Extractor"
    description = "A custom component for retrieving financial statements, specific reports, or criteria information from SEC 10-Q filings."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "custom_components"
    name = "Sec10QDataExtractor"
    
    inputs = [
        StrInput(
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
        StrInput(
            name="report_type",
            display_name="Report Type (Used if mode='specific_report')",
            value="",
            info="E.g.: 'balance_sheet', 'income_statement', 'operation_statement', or 'cash_flow'.",
            tool_mode=True,
        ),
        StrInput(
            name="criteria_key",
            display_name="Criteria Key (Used if mode='criteria_related_info')",
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
        criteria_key = self.criteria_key

        if mode == "all_financials":
            placeholder_text = (
                f"Mode: all_financials\n"
                f"Fetching all 10Q Financials for ticker: {ticker}\n\n"
                f"Report Type: {report_type}\n\n"
                f"Criteria Key: {criteria_key}\n\n"
                f"(In Part 2, replace this placeholder with actual requests.post(...))"
            )
            return Message(text=placeholder_text)

        elif mode == "specific_report":
            placeholder_text = (
                f"Mode: specific_report\n"
                f"Ticker: {ticker}\n"
                f"Report Type: {report_type}\n\n"
                f"Criteria Key: {criteria_key}\n\n"
                f"(In Part 2, replace this placeholder with actual requests.post(...))"
            )
            return Message(text=placeholder_text)
        
        elif mode == "criteria_related_info":
            placeholder_text = (
                f"Mode: criteria_related_info\n"
                f"Ticker: {ticker}\n"
                f"Report Type: {report_type}\n\n"
                f"Criteria Key: {criteria_key}\n\n"
                f"(Placeholder: In Part 2, call your /criteria endpoint to retrieve or store data on '{criteria_key}'.)"
            )
            return Message(text=placeholder_text)

        else:
            return Message(
                text=(
                    f"You selected mode '{mode}', which isn't implemented yet.\n"
                    "In the future, we can add new routes or logic here."
                )
            )
