import json
import os
from scrapingant_client import ScrapingAntClient
from bs4 import BeautifulSoup  # To extract text from HTML

def lambda_handler(event, context):
    """
    AWS Lambda function to scrape web content using ScrapingAntClient.

    Expected Input:
    {
        "url": "https://example.com"
    }

    Returns:
    {
        "url": "https://example.com",
        "content": "Extracted text content from the website"
    }
    """
    try:
        # Extract URL from event
        url = event.get("url")
        if not url:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'url' parameter"})
            }

        # Retrieve API key from environment variable
        api_key = os.environ.get("SCRAPINGANT_API_KEY")
        if not api_key:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Missing ScrapingAnt API Key"})
            }

        # ScrapingAnt request
        client = ScrapingAntClient(token=api_key)
        result = client.general_request(url)

        # Convert HTML to text using BeautifulSoup
        soup = BeautifulSoup(result.content, "html.parser")
        text_content = soup.get_text(separator="\n", strip=True)  # Extract readable text

        return {
            "statusCode": 200,
            "body": json.dumps({
                "url": url,
                "content": text_content[:5000]  # Limit response size for Lambda
            }),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
