import requests

secedgar_url = "lambda_url_here"

payload = {
    "ticker": "AMT",
    "report_type": "balance_sheet",
}

response = requests.post(secedgar_url, json=payload)
print("HTTP status code:", response.status_code)
print("Lambda response JSON:", response.json())

