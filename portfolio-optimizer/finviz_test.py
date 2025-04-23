import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def get_finviz_tickers(sector='technology', max_tickers=100):
    base_url = "https://finviz.com/screener.ashx"
    tickers = []
    page = 1
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    while len(tickers) < max_tickers:
        r_param = (page - 1) * 20 + 1
        
        params = {
            'v': 111,  # View type
            'f': f"sec_{sector}",
            'o': "-marketcap",
            'r': r_param
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            ticker_links = soup.select('#screener-table a.tab-link')
            
            if not ticker_links:
                break  
                
     
            new_tickers = [link.text for link in ticker_links]
            tickers.extend(new_tickers)
            
            print(f"Page {page}: Found {len(new_tickers)} tickers")
            
            # Stop if we've reached our target or if we're not getting new tickers
            if len(new_tickers) < 20 or len(tickers) >= max_tickers:
                break
                
            page += 1
            time.sleep(1)  
            
        except requests.exceptions.RequestException as e:
            print(f"Error on page {page}: {e}")
            break
    
    return tickers[:max_tickers] 

if __name__ == "__main__":
    tech_tickers = get_finviz_tickers(sector='technology', max_tickers=100)
    print(f"\nFound {len(tech_tickers)} technology tickers:")
    print(tech_tickers)
