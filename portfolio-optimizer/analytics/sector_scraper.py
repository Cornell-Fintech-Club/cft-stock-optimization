# sector_scraper.py

import requests
from bs4 import BeautifulSoup
import time

SECTOR_FILTERS = {
    "technology": "sec_technology",
    "healthcare": "sec_healthcare",
    "energy": "sec_energy",
    "consumer_staples": "sec_consumercyclical",
    "communication": "sec_communicationservices"
}

def scrape_top_100_tickers(sector: str) -> list[str]:
    if sector not in SECTOR_FILTERS:
        raise ValueError(f"Invalid sector '{sector}'. Valid options are: {list(SECTOR_FILTERS.keys())}")

    base_url = "https://finviz.com/screener.ashx"
    tickers = []
    page = 1

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
    }

    while len(tickers) < 100:
        r_param = (page - 1) * 20 + 1
        params = {
            "v": 111,
            "f": SECTOR_FILTERS[sector],
            "o": "-marketcap",
            "r": r_param
        }

        try:
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            ticker_links = soup.select("#screener-table a.tab-link")

            if not ticker_links:
                break  # No more tickers

            new_tickers = [link.text.strip() for link in ticker_links]
            tickers.extend(new_tickers)

            if len(new_tickers) < 20:
                break  # Reached end of available results

            page += 1
            time.sleep(1)  # polite delay

        except requests.RequestException as e:
            print(f"Request failed on page {page}: {e}")
            break

    return tickers[:100]

