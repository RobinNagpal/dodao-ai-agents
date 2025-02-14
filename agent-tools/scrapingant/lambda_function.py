from scrapingant_client import ScrapingAntClient

def lambda_handler(event, context):
    """
    This Lambda takes a 'url' from the event and returns the HTML content.
    Example usage:
      event = {"url": "https://example.com"}
    """
    # In production, do NOT hardcode the API key; use Secrets Manager or env vars.
    api_key = "API_KEY"
    client = ScrapingAntClient(api_key=api_key)

    url = event.get("url", "https://example.com")
    response = client.get(url)
    return {
        "url": url,
        "html": response
    }
