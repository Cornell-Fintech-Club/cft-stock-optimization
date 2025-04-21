import re
import cloudscraper           # drop‑in requests replacement
from bs4 import BeautifulSoup


def get_top_tech_ticker():
    url = "https://finviz.com/screener.ashx"
    params = {
        "v": 111,
        "f": "sec_technology",
        "o": "-marketcap",
        "r": 1,               # start at row 1
    }

    scraper = cloudscraper.create_scraper(  # Cloudflare‑aware session
        browser={"browser": "chrome", "platform": "darwin", "desktop": True}
    )
    html = scraper.get(url, params=params, timeout=15).text

    # If Cloudflare still served a captcha, html will be tiny – guard for that:
    if "screener-link-primary" not in html:
        raise RuntimeError(
            "Blocked by Cloudflare (no ticker tags in response). "
            "Try a slower rate or a residential VPN."
        )

    soup = BeautifulSoup(html, "lxml")

    # ---------- Robust locator #1: grab the FIRST ticker anchor ----------
    ticker_tag = soup.select_one("a.screener-link-primary")
    if not ticker_tag:                # should never happen if html passed the check
        raise RuntimeError("Ticker anchor not found – FinViz markup changed again.")

    ticker = ticker_tag.text.strip()

    # Company name is the sibling <a> without the “‑primary” class
    row = ticker_tag.find_parent("tr")
    company_tag = row.select_one("a.screener-link:not(.screener-link-primary)")
    company = company_tag.text.strip() if company_tag else "N/A"

    return ticker, company


if __name__ == "__main__":
    tkr, name = get_top_tech_ticker()
    print(f"Top Technology stock on FinViz: {tkr} — {name}")
