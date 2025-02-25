from edgar import *
from tabulate import tabulate

set_identity("dawoodmehmood52222@gmail.com")
company = Company('FVR')
filings = company.get_filings(form="10-Q")

latest_10q = filings.latest()
# print(f'LAtest q: {latest_10q}')
# tenk = latest_10q.obj()
# print(f'filing: {tenk}')
attachments = latest_10q.attachments
print(f"Total Attachments Found: {len(attachments)}")

# print(f'Attachments: {attachments}')
for i, attach in enumerate(attachments):
    try:
        print(f"{i+1}. {attach.document} - Purpose: {attach.purpose}")
    except Exception as e:
        print(f"Error fetching attachment {i+1}: {str(e)}")

# print(f'Lines of Credit and Term Loan : {attachments[29].view()}')
# print(f'Attachments: {attachments[14].view()}')
# print(f'Attachments: {attachments[15].view()}')
# print(f'Lease text: {attachments[36].text()}')
# print(f'Lease view: {attachments[36].view()}')
# attachments[36].download('./file.html')
# financials = tenk.financials
# print(f'balance sheet: {financials.get_balance_sheet()}')
# df = financials.get_balance_sheet().get_dataframe()
# print(f"Balance Sheet:\n{tabulate(df, headers='keys', tablefmt='fancy_grid')}")