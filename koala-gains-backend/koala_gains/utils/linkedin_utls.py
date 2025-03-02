import hashlib
import json
import traceback
from typing import List, Dict, Any
from urllib.parse import urlparse

import requests
from linkedin_scraper import Person, actions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing_extensions import TypedDict

from koala_gains.utils.env_variables import LINKEDIN_EMAIL, LINKEDIN_PASSWORD, PROXYCURL_API_KEY
from koala_gains.utils.s3_utils import s3_client, BUCKET_NAME, upload_to_s3


class TeamMemberLinkedinUrl(TypedDict):
    id: str
    name: str
    url: str


class RawLinkedinProfile(TypedDict):
    id: str
    name: str
    profile: Dict[str, Any]

class ProxyCurlLinkedinProfile(TypedDict):
    public_identifier: str
    profile_pic_url: str
    first_name: str
    last_name: str
    full_name: str
    headline: str
    occupation: str
    summary: str
    experiences: List[Dict[str, Any]]
    educations: List[Dict[str, Any]]
    certifications: List[Dict[str, Any]]


def scrape_single_linkedin_profiles_with_proxycurl(linkedin_url: str) -> ProxyCurlLinkedinProfile or None:
    headers = {'Authorization': f'Bearer {PROXYCURL_API_KEY}'}

    # API endpoint for retrieving a LinkedIn person profile
    api_endpoint = 'https://nubela.co/proxycurl/api/v2/linkedin'

    # Set up the parameters. Note that you should include only one of:
    # 'linkedin_profile_url', 'twitter_profile_url', or 'facebook_profile_url'
    params = {
        'linkedin_profile_url': linkedin_url,
        'use_cache': 'if-present',
        'fallback_to_cache': 'on-error',
    }

    # Make the GET request to the API
    response = requests.get(api_endpoint, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        profile = response.json()

        relevant_profile = {
            "public_identifier": profile.get('public_identifier'),
            "profile_pic_url": profile.get('profile_pic_url'),
            "first_name": profile.get('first_name'),
            "last_name": profile.get('last_name'),
            "full_name": profile.get('full_name'),
            "headline": profile.get('headline'),
            "occupation": profile.get('occupation'),
            "summary": profile.get('summary'),
            "experiences": profile.get('experiences'),
            "educations": profile.get('educations'),
            "certifications": profile.get('certifications'),

        }

        return relevant_profile
    else:
        print(f"Failed to retrieve LinkedIn profile for {linkedin_url}. Status code: {response.status_code}")
        print(response.json())
        return None

def get_identifier_from_linkedin_url(linkedin_url: str) -> str:
    """
    Extracts a human-readable identifier from the LinkedIn URL.
    If the URL follows the '/in/<identifier>' or '/pub/<identifier>' format,
    returns the identifier; otherwise, falls back to an MD5 hash.
    """
    parsed = urlparse(linkedin_url)
    parts = parsed.path.strip("/").split("/")
    if parts and parts[0] in {"in", "pub"} and len(parts) >= 2:
        return parts[1]
    return hashlib.md5(linkedin_url.encode("utf-8")).hexdigest()

def get_s3_profile_key(linkedin_url: str) -> str:
    """
    Creates a readable S3 key for storing the LinkedIn profile JSON.
    """
    identifier = get_identifier_from_linkedin_url(linkedin_url)
    return f"linkedin-profiles/{identifier}.json"

def get_s3_pic_key(linkedin_url: str) -> str:
    """
    Creates a readable S3 key for storing the LinkedIn profile picture.
    """
    identifier = get_identifier_from_linkedin_url(linkedin_url)
    return f"linkedin-pics/{identifier}.jpg"

def cache_profile_pic(linkedin_url: str, profile_pic_url: str) -> str:
    """
    Downloads the profile picture from the provided URL and uploads it to S3.
    Returns the public S3 URL of the uploaded image.
    """
    s3_pic_key = get_s3_pic_key(linkedin_url)

    try:
        # Check if the profile picture is already cached in S3
        s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_pic_key)
        print(f"Profile picture already cached: {s3_pic_key}")
    except s3_client.exceptions.ClientError:
        print(f"Downloading profile picture from {profile_pic_url}")
        response = requests.get(profile_pic_url)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "image/jpeg")
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_pic_key,
                Body=response.content,
                ContentType=content_type,
                ACL="public-read",
            )
            print(f"Profile picture cached in S3: {s3_pic_key}")
        else:
            print(f"Failed to download profile picture from {profile_pic_url} - Status code: {response.status_code}")

    # Construct the public S3 URL (assuming the bucket is public-read)
    s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_pic_key}"
    return s3_url

def get_cached_linkedin_profile(linkedin_url: str):
    """
    Retrieves a LinkedIn profile from cache (S3) if available;
    otherwise, fetches it from Proxycurl, caches it in S3, and returns the profile.
    """
    s3_profile_key = get_s3_profile_key(linkedin_url)

    try:
        # Attempt to check for the object in S3
        s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_profile_key)
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_profile_key)
        cached_data = response["Body"].read().decode("utf-8")
        profile = json.loads(cached_data)
        print(f"Cache hit: {s3_profile_key}")
        return profile
    except s3_client.exceptions.ClientError:
        # If the object does not exist, fetch it from Proxycurl and cache it
        print(f"Cache miss: {s3_profile_key}. Fetching from Proxycurl...")
        profile = scrape_single_linkedin_profiles_with_proxycurl(linkedin_url)
        if profile:
            json_data = json.dumps(profile, indent=4)
            print(f"Caching LinkedIn profile to S3: {s3_profile_key}")
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_profile_key,
                Body=json_data,
                ContentType="application/json",
                ACL="public-read",
            )
        print(f"LinkedIn profile fetched and cached: {s3_profile_key}")

        # If the profile contains a profile_pic_url, download and cache the image,
        # then update the profile to use the S3 URL of the picture.
        if profile and profile.get("profile_pic_url"):
            s3_pic_url = cache_profile_pic(linkedin_url, profile["profile_pic_url"])
            # Only update if the S3 URL is different from what is stored
            if profile["profile_pic_url"] != s3_pic_url:
                profile["profile_pic_url"] = s3_pic_url
                # Update the cached profile with the new profile_pic_url
                updated_json_data = json.dumps(profile, indent=4)
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=s3_profile_key,
                    Body=updated_json_data,
                    ContentType="application/json",
                    ACL="public-read",
                )
            print(f"Cached profile updated with new profile_pic_url: {s3_pic_url}")

        return profile

def scrape_linkedin_with_linkedin_scraper(linkedin_urls: list[TeamMemberLinkedinUrl]) -> list[RawLinkedinProfile]:
    """
    Uses linkedin_scraper to retrieve LinkedIn profile data based on the URLs

    If a team member has no LinkedIn URL (empty string), their profile will be empty.
    """

    # Setup Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU for better compatibility
    chrome_options.add_argument("--window-size=1920,1080")  # Optional: Set window size
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resources in containerized environments
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model (use with caution)

    driver = webdriver.Chrome(options=chrome_options)
    actions.login(driver, LINKEDIN_EMAIL, LINKEDIN_PASSWORD)

    def scrape_linkedin_profile(url: str) -> Dict[str, Any]:
        if not url:
            return {}
        try:
            # Scrape the LinkedIn profile using linkedin_scraper
            # Login to LinkedIn
            person = Person(url, driver=driver, scrape=False)
            person.scrape(close_on_complete=False)

            # Collect profile details
            return {
                "name": person.name,
                "experiences": person.experiences,
                "educations": person.educations,
            }
        except Exception as e:
            print(traceback.format_exc())
            return {}

    # Iterate through the LinkedIn URLs and scrape profiles
    raw_profiles: List[RawLinkedinProfile] = []
    for member in linkedin_urls:
        profile_data = scrape_linkedin_profile(member["url"])
        raw_profiles.append({
            "id": member.get('id'),
            "name": member.get('name'),
            "profile": profile_data
        })
    # Close the driver
    driver.quit()

    return raw_profiles
