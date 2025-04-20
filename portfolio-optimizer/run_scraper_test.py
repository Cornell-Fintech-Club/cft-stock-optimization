from analytics.sector_scraper import scrape_top_100_tickers

if __name__ == "__main__":
    sectors = ["technology", "healthcare", "energy", "consumer_staples", "communication"]

    for sector in sectors:
        tickers = scrape_top_100_tickers(sector)
        print(f"{sector.title()} Sector ({len(tickers)} tickers):")
        print(tickers[:10], "...\n")
