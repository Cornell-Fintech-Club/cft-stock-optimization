from analytics.sector_scraper import scrape_top_100_tickers
import finviz_test

if __name__ == "__main__":
    sectors = ["technology", "healthcare", "energy", "consumercyclical", "communicationservices"]

    for sector in sectors:
        tech_tickers = finviz_test.get_finviz_tickers(sector=sector, max_tickers=10)
        print(f"\nFound {len(tech_tickers)} {sector} tickers:")
        print(tech_tickers)
