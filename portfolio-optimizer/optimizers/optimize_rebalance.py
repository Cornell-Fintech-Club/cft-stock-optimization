import numpy as np
from scipy.optimize import minimize
from app.models import StockIndicator
from analytics.portfolio import compute_portfolio_metrics
from analytics.data import fetch_multiple_series, align_price_series
from survey_to_ranges import get_target_ranges

def rebalance_portfolio(survey: dict, symbols: list, weights: list):
    """
    Adjust portfolio weights to fit within indicator target ranges.
    Prevents weights from dropping below 0.2 for any stock.
    """
    target_ranges = get_target_ranges(survey)

    # Step 1: Pull price data for the given symbols
    price_dict = fetch_multiple_series(symbols)
    price_df = align_price_series(price_dict)
    n = len(symbols)

    # Step 2: Define loss function based on how far current metrics are from target
    def loss(w):
        if np.any(np.array(w) < 0) or not np.isclose(np.sum(w), 1):
            return np.inf

        metrics = compute_portfolio_metrics(price_df, np.array(w))
        penalty = 0

        # Priority weights (higher means more important)
        priority_weights = {
            "expected_return": 5.0,
            "alpha": 4.0,
            "sharpe_ratio": 3.0,
            "beta": 2.0,
            "volatility": 2.0,
            "max_drawdown": 1.5,
            "value_at_risk": 1.0,
            "diversification_score": 0.5,
        }

        for key, (lo, hi) in target_ranges.items():
            val = metrics.get(key)
            if val is None:
                continue
            weight = priority_weights.get(key, 1.0)
            if lo is not None and val < lo:
                penalty += weight * (lo - val) ** 2
            if hi is not None and val > hi:
                penalty += weight * (val - hi) ** 2

        return penalty

    # Step 3: Constraints and bounds
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    min_weight = 0.02  # Minimum weight per stock (not 0)
    bounds = [(min_weight, 1.0) for _ in range(n)]

    result = minimize(loss, weights, method='SLSQP', bounds=bounds, constraints=constraints)

    if result.success:
        optimized_weights = result.x
        optimized_metrics = compute_portfolio_metrics(price_df, optimized_weights)
        return {
            "success": True,
            "optimized_weights": list(optimized_weights),
            "optimized_metrics": optimized_metrics,
        }
    else:
        return {
            "success": False,
            "message": result.message
        }

# Example usage
if __name__ == "__main__":
    survey = {
        "age_range": "18-35",
        "volatility_tolerance": "high",
        "time_horizon": "long",
        "investment_goal": "growth"
    }
    symbols = ["AAPL", "MSFT", "JNJ", "PFE", "JPM", "GS", "XOM", "CVX", "WMT", "PG"]
    weights = [0.15, 0.10, 0.10, 0.05, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10]
    from pprint import pprint
    print("Metric Ranges:")
    pprint(get_target_ranges(survey=survey))
    print("\n")
    result = rebalance_portfolio(survey, symbols, weights)
    pprint(result)
