import os

from cloudscaper_client import scraper 
def fetch_cities(country, input, maxSize):

    FETCH_URL = os.getenv("BASE_URL") + os.getenv("CITY_SEARCH_URL")

    params = {
        "country": {country},
        "input" : {input},
        "maxMatches" : {str(maxSize)}
    }

    response = scraper.get(FETCH_URL, params= params)

    print(response.status_code)


fetch_cities("USA","na", 1000)

