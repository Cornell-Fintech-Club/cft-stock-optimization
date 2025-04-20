import requests
import pandas as pd

SECTOR_FILTERS = {
    "technology": "sec_technology",
    "healthcare": "sec_healthcare",
    "energy": "sec_energy",
    "consumer_staples": "sec_consumerstaples",
    "communication": "sec_communicationservices"
}

def scrape_top_100_tickers(sector: str) -> list[str]:
    if sector not in SECTOR_FILTERS:
        raise ValueError(f"Unsupported sector '{sector}'. Choose from {list(SECTOR_FILTERS.keys())}")

    tickers = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for start in range(1, 101, 20):  # pages: 1, 21, 41, 61, 81
        url = f"https://finviz.com/screener.ashx?v=111&f={SECTOR_FILTERS[sector]}&o=-marketcap&r={start}"
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Request failed with status {resp.status_code}")
            continue

        try:
            tables = pd.read_html(resp.text)
            if len(tables) > 15:
                screener_table = tables[15]
            else:
                screener_table = tables[-1]

            tickers += screener_table["Ticker"].tolist()
        except Exception as e:
            print(f"Error parsing HTML: {e}")

    return tickers[:100]
