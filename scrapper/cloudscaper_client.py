import cloudscraper

scraper = cloudscraper.create_scraper(
    interpreter="nodejs",
    browser={
        "browser": "chrome",
        "platform": "ios",
        "desktop": False,
    }
)