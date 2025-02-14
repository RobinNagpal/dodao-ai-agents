import os

# Tell edgartools to use local data and change the data directory to a writable path
os.environ['EDGAR_USE_LOCAL_DATA'] = '1'
os.environ['EDGARTOOLS_DATA_DIR'] = '/tmp/edgar_data'
os.environ['EDGAR_LOCAL_DATA_DIR'] = '/tmp/edgar_data'

# Optionally, if you want to print for debugging:
print("EDGARTOOLS_DATA_DIR:", os.environ.get("EDGARTOOLS_DATA_DIR"))
print("EDGAR_LOCAL_DATA_DIR:", os.environ.get("EDGAR_LOCAL_DATA_DIR"))
print("EDGAR_USE_LOCAL_DATA:", os.environ.get("EDGAR_USE_LOCAL_DATA"))


from edgar import *
import json
use_local_storage()

def lambda_handler(event, context):
    """
    This Lambda takes a ticker and returns the latest 10-Q filing.
    Example usage:
      event = {"ticker": "AAPL"}
    """
    try:
        set_identity('robinnagpal.tiet@gmail.com')
        ticker = event.get('ticker', 'AAPL')
        company = Company(ticker)

        # Example from your library usage:
        company.get_filings(form="10-Q")

        if company.filings:
            filing =  company.filings[0].to_dict()

            response = {
                'statusCode': 200,
                'body': json.dumps({ 'result': filing })
            }
            return response

        else:
            return {
                'statusCode': 404,
                'body': json.dumps({ 'error': 'No filings found for ticker: {}'.format(ticker) })
            }
    except Exception as e:
        print(e)

        return {
            'statusCode': 500,
            'body': json.dumps({ 'error': 'Internal server error ' + str(e) })
        }
