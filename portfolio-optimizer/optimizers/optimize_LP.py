import numpy as np
from scipy.optimize import linprog
from app.models import StockIndicator
from survey_to_ranges import get_target_ranges


def optimize_portfolio_lp(survey: dict, symbols: list):
    """
    Linear programming approach to rebalance portfolio weights
    to satisfy linear metric constraints (expected_return, alpha, beta, volatility).
    Nonlinear constraints (sharpe_ratio, drawdown, etc.) are handled post-hoc.
    """
    target_ranges = get_target_ranges(survey)

    # Load indicators for given symbols
    indicators = {sym: StockIndicator.query.get(sym) for sym in symbols}

    # Linear metrics to optimize on
    linear_metrics = ["expected_return", "alpha", "beta", "volatility"]

    # Build A matrix where A[i][j] = indicator value of stock j for metric i
    A = []
    bounds_lo = []
    bounds_hi = []

    for metric in linear_metrics:
        row = []
        for sym in symbols:
            val = getattr(indicators[sym], metric, None)
            row.append(val if val is not None else 0.0)

        A.append(row)
        lo, hi = target_ranges.get(metric, (None, None))
        bounds_lo.append(lo if lo is not None else -np.inf)
        bounds_hi.append(hi if hi is not None else np.inf)

    A = np.array(A)

    # Objective: minimize distance from midpoint of target range
    c = np.zeros(len(symbols))  # objective can be modified as needed

    # Constraints: Ax >= bounds_lo and Ax <= bounds_hi
    A_ub = []
    b_ub = []
    for i in range(len(linear_metrics)):
        if bounds_hi[i] != np.inf:
            A_ub.append(A[i])
            b_ub.append(bounds_hi[i])
        if bounds_lo[i] != -np.inf:
            A_ub.append([-a for a in A[i]])
            b_ub.append(-bounds_lo[i])

    # Add equality constraint: sum(weights) == 1
    A_eq = [np.ones(len(symbols))]
    b_eq = [1.0]

    # Bounds: no shorting, min 2% allocation per stock
    x_bounds = [(0.02, 1.0) for _ in symbols]

    result = linprog(c,
                     A_ub=A_ub,
                     b_ub=b_ub,
                     A_eq=A_eq,
                     b_eq=b_eq,
                     bounds=x_bounds,
                     method="highs")

    if result.success:
        final_weights = result.x
        return {
            "success": True,
            "weights": dict(zip(symbols, final_weights)),
            "message": "LP solution found. Nonlinear metrics must be evaluated separately."
        }
    else:
        return {
            "success": False,
            "message": result.message
        }


if __name__ == "__main__":
    from app import create_app
    from pprint import pprint

    app = create_app()
    with app.app_context():
        survey = {
            "age_range": "18-35",
            "volatility_tolerance": "high",
            "time_horizon": "long",
            "investment_goal": "growth"
        }
        symbols = ["AAPL", "MSFT", "JNJ", "PFE", "JPM", "GS", "XOM", "CVX", "WMT", "PG"]

        result = optimize_portfolio_lp(survey, symbols)
        pprint(result)