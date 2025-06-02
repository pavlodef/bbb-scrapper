import re
import os

from requests.models import PreparedRequest
from bs4 import BeautifulSoup
from models import Company
from dotenv import load_dotenv

from cloudscaper_client import scraper
from database_utils import use_db, save_company_to_db
from parse_cities import fetch_cities

load_dotenv()


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

def remove_dublicates(results):
    seen_urls = set()
    unique_results = []

    for item in results:
        url = item.get("reportUrl")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(item)

    return unique_results

def fetch_initial_info(param_text, page_number, city):

    params = {
    "find_text": param_text,
    "page": str(page_number),
    "find_loc": city
    }

    FETCH_URL = os.getenv("BASE_URL") + os.getenv("COMPANY_SEARCH_URL")
    req = PreparedRequest()
    req.prepare_url(FETCH_URL, params)
    response = scraper.get(FETCH_URL, headers=headers_initial, params=params)

    if response.status_code // 100 == 2 :
        data = response.json()
        
        results = remove_dublicates(data["results"])


        for item in results:
            company = Company(
                company_id=(item.get("id") or "").strip(),
                category=(item.get("tobText") or "").strip(),
                name=re.sub(r"</?em>", "", (item.get("businessName") or "")).strip(),
                phone=item.get("phone") or [],
                address=(item.get("address") or "").strip(),
                city=(item.get("city") or "").strip(),
                state=(item.get("state") or "").strip(),
                postalCode=(item.get("postalcode") or "").strip(),
                websiteUrl=None,
                years=None,
                description=None,
                reportUrl=(item.get("reportUrl") or "").strip(),
                owners=None
            )


            fetch_extra_info(company)

            use_db(
                dsn=os.getenv('DATABASE_URL'),
                callback=lambda cursor, conn: save_company_to_db(cursor, company)
            )

    else:
        
        print(f"""Problem with response:{response.status_code},
              Response text: {response.text},
              Full URL: {req.url}
              """)


def fetch_extra_info(company : Company):

    if not company.reportUrl:
        return
    
    
    FETCH_URL = os.getenv("BASE_URL") + company.reportUrl


    response = scraper.get(FETCH_URL, headers=headers_extra)


    if response.status_code // 100 != 2:
        print(f"""Failed to fetch extra info for {company.name},
              Using this URL for extra info:{FETCH_URL}
              """)
        return

    soup = BeautifulSoup(response.text, "html.parser")

    website_link_tag = soup.select_one("a:-soup-contains('Visit Website')")
    website_url = website_link_tag["href"] if website_link_tag else None

    years_tag = soup.select_one("p:-soup-contains('Years in Business')")
    years = years_tag.text.split(":")[-1].strip() if years_tag else None

    description_heading = soup.find("h2", id="about")
    description_body_div = description_heading.find_next_sibling("div", class_="bds-body") if description_heading else None
    description = description_body_div.text.strip() if description_body_div else None


    possible_names = ["Owner", "Manager", "Director", "President"]

    owners_tag = set()

    # slow 
    for dd in soup.select("dd"):
        if any(name in dd.get_text() for name in possible_names):
            owners_tag.add(dd)

    owners = {}
    for item in owners_tag:
        text = item.text
        try:
            owner, role = text.split(",", 1)
            owners[owner.strip()] = role.strip()
        except ValueError:
            print(f"""Skipping malformed owner entry: '{text}'
                  Using this URL for extra info:{FETCH_URL}
                  """)
            continue

    company.description = description
    company.years = years
    company.websiteUrl = website_url
    company.owners = owners

    
cities = fetch_cities("USA","a",500)

for city in cities:
    for i in range(15):
        fetch_initial_info("Restaurants", i+1, city)