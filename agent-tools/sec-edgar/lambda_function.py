from edgar import Company

def lambda_handler(event, context):
    """
    This Lambda takes a ticker and returns the latest 10-Q filing.
    Example usage:
      event = {"ticker": "AAPL"}
    """
    ticker = event.get('ticker', 'AAPL')
    company = Company(ticker)

    # Example from your library usage:
    company.get_filings(form="10-Q")

    if company.filings:
        return company.filings[0].to_dict()
    else:
        return {"message": f"No 10-Q found for ticker '{ticker}'."}
