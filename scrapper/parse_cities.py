import os

from requests.models import PreparedRequest
from dotenv import load_dotenv

from cloudscaper_client import scraper

load_dotenv()

def fetch_cities(country, input, maxSize):
    FETCH_URL = os.getenv("BASE_URL") + os.getenv("CITY_SEARCH_URL")

    params = {
        "country": country,
        "input" : input,
        "maxMatches" : str(maxSize) # max 5152, more doesn't count by bbb.org server
    }
    req = PreparedRequest()
    req.prepare_url(FETCH_URL, params)

    response = scraper.get(FETCH_URL, params= params)

    if response.status_code // 100 != 2:
        print(f"""Status code: {response.status_code}. Error: {response.text}
              User URL: {req.url}
              """)
        return None
    else:
        data = response.json()
        cities = set([item["displayText"] for item in data])
        return cities


