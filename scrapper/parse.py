import cloudscraper
import requests
from bs4 import BeautifulSoup
from models import Company
from database_utils import use_db, save_company_to_db
import re
BASE_URL = "https://www.bbb.org"

#find_country = ["US", "CAN"]

headers_initial = {
    "Accept": "application/json, text/plain, */*", 
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "DNT": "1",
    "Host": "www.bbb.org",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Referer": "https://www.bbb.org/search",
    "Origin": "https://www.bbb.org",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

BASE_URL = "https://www.bbb.org"

headers_extra = {
    "Host": "www.bbb.org",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, zstd",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i"
}

scraper = cloudscraper.create_scraper(
    interpreter="nodejs",
    browser={
        "browser": "chrome",
        "platform": "ios",
        "desktop": False,
    }
)



test_url = "https://www.bbb.org/us/ny/new-york/profile/restaurants/taam-tov-restaurant-inc-0121-170777"


def fetch_initial_info(param_text, page_number):

    params = {
    "find_text": {param_text},
    "find_country": "USA",
    "page": {str(page_number)},
    }

    FETCH_URL = BASE_URL + "/api/search"
    #testing
    req = requests.Request("GET", FETCH_URL, params=params, headers=headers_initial)
    prepared = req.prepare()
    print("Full link:", prepared.url) 

    response = scraper.get(FETCH_URL, headers=headers_initial, params=params)
    if response.status_code // 100 == 2 :
        data = response.json()
        
        results = data["results"]

        for item in results:
            company = Company(
                company_id=item["id"],
                category=item["tobText"],
                name = re.sub(r"</?em>", "",item["businessName"]),
                phone=item["phone"],
                address=item["address"],
                city=item["city"],
                state=item["state"],
                postalCode=item["postalcode"],
                websiteUrl=None,
                years=None,
                description=None,
                reportUrl=item["ReportUrl"],
                owners = None
            )
            fetch_extra_info(company)

            use_db(
                dbname="bbb",
                user="postgres",
                password="postgres",
                callback=lambda cursor, conn: save_company_to_db(cursor, company)
            )

    else:
        print("Problem with response:", response.status_code)
        print(response.text)


def fetch_extra_info(company : Company):

    if not company.reportUrl:
        return
    
    FETCH_URL = BASE_URL + company.reportUrl

    response = scraper.get(FETCH_URL, headers=headers_extra)


    if response.status_code // 100 != 2:
        print(f"Failed to fetch extra info for {company.name}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    website_link_tag = soup.select_one("a:-soup-contains('Visit Website')")
    website_url = website_link_tag["href"] if website_link_tag else None
    print(website_url)

    years_tag = soup.select_one("p:-soup-contains('Years in Business')")
    years = years_tag.text.split(":")[-1].strip() if years_tag else None
    print(years)

    description_heading = soup.find("h2", id="about")
    description_body_div = description_heading.find_next_sibling("div", class_="bds-body") if description_heading else None
    description = description_body_div.text.strip() if description_body_div else None

    print(description)

    possible_names = ["Owner", "Manager", "Director", "President"]

    owners_tag = set()
    # slow 
    for dd in soup.select("dd"):
        if any(name in dd.get_text() for name in possible_names):
            owners_tag.add(dd)

    owners = {}
    for item in owners_tag:
        owner, role = item.text.split(",")
        owners[owner.strip()] = role.strip()

    company.description = description
    company.years = years
    company.websiteUrl = website_url
    company.owners = owners

    



fetch_initial_info("Restaurants",15)