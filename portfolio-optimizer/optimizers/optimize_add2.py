from __future__ import annotations
import numpy as np
from typing import List, Dict, Tuple

from app import create_app, db
from app.models import StockIndicator
from analytics.portfolio import compute_portfolio_metrics
from analytics.data import fetch_multiple_series, align_price_series
from survey_to_ranges import get_target_ranges

def current_metrics(symbols: List[str], weights: List[float]) -> Dict[str, float]:
    price_df = align_price_series(fetch_multiple_series(symbols))
    return compute_portfolio_metrics(price_df, np.array(weights))

def metric_gap(metric_val: float, lo: float | None, hi: float | None) -> float:
    if lo is not None and metric_val < lo:
        return lo - metric_val
    if hi is not None and metric_val > hi:
        return hi - metric_val
    return 0.0

def best_candidate(metric: str, direction: str, sectors: List[str], exclude: List[str]) -> StockIndicator | None:
    q = StockIndicator.query.filter(
        StockIndicator.sector.in_(sectors),
        ~StockIndicator.ticker.in_(exclude),
        getattr(StockIndicator, metric).isnot(None)
    )
    ordering = getattr(StockIndicator, metric).desc() if direction == "increase" else getattr(StockIndicator, metric).asc()
    return q.order_by(ordering).first()

def ranked_portfolio(metric: str, direction: str, symbols: List[str]) -> List[Tuple[int, str, float]]:
    rows = db.session.query(StockIndicator).filter(StockIndicator.ticker.in_(symbols)).all()
    ranked = [(i, r.ticker, getattr(r, metric)) for i, r in enumerate(rows) if getattr(r, metric) is not None]
    return sorted(ranked, key=lambda x: x[2], reverse=(direction == "decrease"))

def optimize_with_swaps(survey: Dict, symbols: List[str], weights: List[float], max_add: int = 10, eps: float = 1e-4) -> Dict:
    tgt = get_target_ranges(survey)
    sectors = survey.get("selectedSectors", [])
    symbols = symbols.copy()
    weights = weights.copy()

    preserve_core = {"AAPL", "MSFT", "JNJ", "PFE"}  # ← protect these
    preserve_min = 0.10

    added = []
    iters = 0

    while iters < 25:
        iters += 1
        mets = current_metrics(symbols, weights)

        gap_info = None
        for m, (lo, hi) in tgt.items():
            g = metric_gap(mets.get(m), lo, hi)
            if abs(g) > eps:
                gap_info = (m, "increase" if g > 0 else "decrease", g)
                break

        if gap_info is None:
            return {
                "success": True,
                "symbols": symbols,
                "weights": weights,
                "metrics": mets,
                "added": added
            }

        metric, direction, gap_val = gap_info

        print(f"\nAttempting to fix '{metric}' ({direction}) — current: {mets.get(metric):.4f}, target: {tgt[metric]}")

        cand = best_candidate(metric, direction, sectors, symbols)
        if cand is None:
            print(f"No candidate found in sectors {sectors} to fix '{metric}'.")
            break

        ranked = ranked_portfolio(metric, direction, symbols)
        best_val = getattr(cand, metric)
        if best_val is None:
            print("  ⚠️ Best candidate has no value for metric")
            break

        remaining_gap = abs(gap_val)
        for i_worst, worst_sym, worst_val in ranked:
            if worst_val is None or best_val == worst_val:
                continue

            max_transferable = weights[i_worst]
            if worst_sym in preserve_core:
                max_transferable = max(0.0, weights[i_worst] - preserve_min)

            if max_transferable < eps:
                continue

            delta_w = min(remaining_gap / abs(best_val - worst_val), max_transferable, 0.20)

            print(f"  → Swapping from {worst_sym}={worst_val:.4f} to {cand.ticker}={best_val:.4f}, Δw={delta_w:.4f}")

            if delta_w < eps:
                continue

            weights[i_worst] -= delta_w

            if cand.ticker in symbols:
                i_cand = symbols.index(cand.ticker)
                weights[i_cand] += delta_w
            else:
                symbols.append(cand.ticker)
                weights.append(delta_w)
                added.append(cand.ticker)

            weights = [w / sum(weights) for w in weights]

            remaining_gap -= delta_w * abs(best_val - worst_val)

            if remaining_gap < eps:
                break

        if len(added) >= max_add:
            break

    return {
        "success": False,
        "message": "Could not satisfy ranges with greedy swaps.",
        "symbols": symbols,
        "weights": weights,
        "metrics": current_metrics(symbols, weights),
        "added": added
    }


if __name__ == "__main__":
    from pprint import pprint

    app = create_app()
    with app.app_context():
        survey = {
            "age_range": "18-35",
            "volatility_tolerance": "high",
            "time_horizon": "short",
            "investment_goal": "growth",
            "selectedSectors": ["technology", "health", "energy"]
        }
        symbols0 = ["AAPL", "MSFT", "JNJ", "PFE"]
        weights0 = [0.25, 0.25, 0.25, 0.25]

        print("Survey Computed Metrics:")
        pprint(get_target_ranges(survey))
        print("\n")

        res = optimize_with_swaps(survey, symbols0, weights0)
        pprint(res)
