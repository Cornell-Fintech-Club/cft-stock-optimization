import numpy as np
from app.models import StockIndicator
from optimizers.optimize_rebalance import rebalance_portfolio
from analytics.portfolio import compute_portfolio_metrics
from analytics.data import fetch_multiple_series, align_price_series
from survey_to_ranges import get_target_ranges

def get_stock_deficiencies(metrics, target_ranges):
    """Return dict of {metric: 'increase' or 'decrease'} for out-of-bound metrics."""
    out_of_range = {}
    for key, (lo, hi) in target_ranges.items():
        val = metrics.get(key)
        if val is None:
            continue
        if lo is not None and val < lo:
            out_of_range[key] = "increase"
        elif hi is not None and val > hi:
            out_of_range[key] = "decrease"
    return out_of_range

def query_stock_to_fix(metric, direction, sectors, exclude):
    """Return one stock from sector that helps move a specific metric in a desired direction."""
    query = StockIndicator.query.filter(StockIndicator.sector.in_(sectors))
    if exclude:
        query = query.filter(~StockIndicator.ticker.in_(exclude))
    all_candidates = query.all()

    candidates = []
    for stock in all_candidates:
        val = getattr(stock, metric, None)
        if val is None:
            continue
        candidates.append((val, stock))

    if direction == "increase":
        candidates.sort(key=lambda x: -x[0])  # highest first
    elif direction == "decrease":
        candidates.sort(key=lambda x: x[0])   # lowest first

    return candidates[0][1] if candidates else None

def optimize_with_greedy_addition(survey, symbols, weights, max_additions=3):
    """Greedily add stocks to fix metrics one at a time."""
    target_ranges = get_target_ranges(survey)
    selected_sectors = survey.get("selectedSectors", [])

    price_dict = fetch_multiple_series(symbols)
    price_df = align_price_series(price_dict)
    metrics = compute_portfolio_metrics(price_df, np.array(weights))

    out_of_range = get_stock_deficiencies(metrics, target_ranges)

    added = []
    for metric, direction in out_of_range.items():
        if len(added) >= max_additions:
            break
        candidate = query_stock_to_fix(metric, direction, selected_sectors, symbols)
        if not candidate:
            continue

        print(f"Adding {candidate.ticker} to improve {metric} ({direction})")

        symbols.append(candidate.ticker)
        weights.append(0.05)
        weights = [w / sum(weights) for w in weights]  # re-normalize
        added.append(candidate.ticker)

        # Re-evaluate metrics
        price_dict = fetch_multiple_series(symbols)
        price_df = align_price_series(price_dict)
        metrics = compute_portfolio_metrics(price_df, np.array(weights))
        out_of_range = get_stock_deficiencies(metrics, target_ranges)

        if not out_of_range:
            break

    # Final rebalance
    result = rebalance_portfolio(survey, symbols, weights)
    result["added_stocks"] = added
    return result

if __name__ == "__main__":
    from app import create_app
    from pprint import pprint

    app = create_app()
    with app.app_context():
        survey = {
            "age_range": "18-35",
            "volatility_tolerance": "high",
            "time_horizon": "long",
            "investment_goal": "growth",
            "selectedSectors": ["technology", "health"]
        }
        symbols = ["AAPL", "MSFT", "JNJ", "PFE"]
        weights = [0.25, 0.25, 0.25, 0.25]

        result = optimize_with_greedy_addition(survey, symbols, weights)
        
        print("Desired Ranges:")
        pprint(get_target_ranges(survey))
        print("-"*30)
        pprint(result)
