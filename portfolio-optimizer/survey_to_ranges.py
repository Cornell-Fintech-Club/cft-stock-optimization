def get_target_ranges(survey):
    """
    Given survey responses, return the target financial indicator ranges.
    survey: dict with keys like 'age_range', 'volatility_tolerance', etc.
    """
    age_map = {
        "18-35": {
            "expected_return": (0.08, 0.12),
            # "volatility": (0, 0.18),
            # "sharpe_ratio": (0.6, float("inf")),
            "beta": (1.0, 1.4),
            # "alpha": (0.02, float("inf")),
            # "max_drawdown": (None, 0.25),
            # "var": (-0.12, None),
            "diversification_score": (0.7, float("inf")),
        },
        "36-55": {
            "expected_return": (0.06, 0.09),
            # "volatility": (0, 0.12),
            # "sharpe_ratio": (0.8, float("inf")),
            "beta": (0.8, 1.2),
            # "alpha": (0.01, float("inf")),
            # "max_drawdown": (None, 0.20),
            # "var": (-0.08, None),
            "diversification_score": (0.8, float("inf")),
        },
        "56+": {
            "expected_return": (0.04, 0.06),
            # "volatility": (0, 0.08),
            # "sharpe_ratio": (1.0, float("inf")),
            "beta": (0, 0.8),
            # "alpha": (0.0, 0.01),
            # "max_drawdown": (None, 0.10),
            # "var": (-0.05, None),
            "diversification_score": (0.9, float("inf")),
        }
    }

    vol_map = {
        "low": {
            "expected_return": (0.04, 0.06),
            # "volatility": (0, 0.08),
            # "sharpe_ratio": (1.0, float("inf")),
            "beta": (0, 0.8),
            # "alpha": (0.0, 0.01),
            # "max_drawdown": (None, 0.10),
            # "var": (-0.05, None),
            "diversification_score": (0.9, float("inf")),
        },
        "moderate": {
            "expected_return": (0.06, 0.09),
            # "volatility": (0, 0.12),
            # "sharpe_ratio": (0.8, float("inf")),
            "beta": (0.8, 1.2),
            # "alpha": (0.01, float("inf")),
            # "max_drawdown": (None, 0.15),
            # "var": (-0.08, None),
            "diversification_score": (0.8, float("inf")),
        },
        "high": {
            "expected_return": (0.09, 0.14),
            # "volatility": (0, 0.20),
            # "sharpe_ratio": (0.5, float("inf")),
            "beta": (1.2, 1.5),
            # "alpha": (0.02, float("inf")),
            # "max_drawdown": (None, 0.30),
            # "var": (-0.15, None),
            "diversification_score": (0.7, float("inf")),
        }
    }

    horizon_map = {
        "short": {
            "expected_return": (0.04, 0.06),
            # "volatility": (0, 0.08),
            # "sharpe_ratio": (1.0, float("inf")),
            "beta": (0, 0.8),
            # "alpha": (0.0, 0.01),
            # "max_drawdown": (None, 0.10),
            # "var": (-0.05, None),
            "diversification_score": (0.9, float("inf")),
        },
        "medium": {
            "expected_return": (0.06, 0.09),
            # "volatility": (0, 0.12),
            # "sharpe_ratio": (0.8, float("inf")),
            "beta": (0.8, 1.2),
            # "alpha": (0.01, float("inf")),
            # "max_drawdown": (None, 0.20),
            # "var": (-0.10, None),
            "diversification_score": (0.8, float("inf")),
        },
        "long": {
            "expected_return": (0.09, 0.12),
            # "volatility": (0, 0.18),
            # "sharpe_ratio": (0.6, float("inf")),
            "beta": (1.0, 1.4),
            # "alpha": (0.02, float("inf")),
            # "max_drawdown": (None, 0.30),
            # "var": (-0.15, None),
            "diversification_score": (0.7, float("inf")),
        }
    }

    goal_map = {
        "income": {
            "expected_return": (0.04, 0.06),
            # "volatility": (0, 0.10),
            # "sharpe_ratio": (1.0, float("inf")),
            "beta": (0, 0.8),
            # "alpha": (0.0, 0.01),
            # "max_drawdown": (None, 0.12),
            # "var": (-0.06, None),
            "diversification_score": (0.9, float("inf")),
        },
        "growth": {
            "expected_return": (0.09, 0.14),
            # "volatility": (0, 0.20),
            # "sharpe_ratio": (0.6, float("inf")),
            "beta": (1.2, 1.5),
            # "alpha": (0.02, float("inf")),
            # "max_drawdown": (None, 0.30),
            # "var": (-0.15, None),
            "diversification_score": (0.7, float("inf")),
        },
        "capital preservation": {
            "expected_return": (0.03, 0.05),
            # "volatility": (0, 0.08),
            # "sharpe_ratio": (1.2, float("inf")),
            "beta": (0, 0.7),
            # "alpha": (0.0, 0.01),
            # "max_drawdown": (None, 0.08),
            # "var": (-0.04, None),
            "diversification_score": (0.95, float("inf")),
        }
    }

    indicators = ["expected_return", "beta", "diversification_score"]
    agg = {k: [None, None] for k in indicators}

    for key, mapping in [
        ("age_range", age_map),
        ("volatility_tolerance", vol_map),
        ("time_horizon", horizon_map),
        ("investment_goal", goal_map)
    ]:
        prefs = mapping.get(survey.get(key), {})
        for k in indicators:
            lo, hi = prefs.get(k, (None, None))
            if lo is not None:
                if agg[k][0] is None:
                    agg[k][0] = lo
                else:
                    agg[k][0] = max(agg[k][0], lo)
            if hi is not None:
                if agg[k][1] is None:
                    agg[k][1] = hi
                else:
                    agg[k][1] = min(agg[k][1], hi)

    # Fallback for invalid (non-overlapping) ranges
    for k, (lo, hi) in agg.items():
        if lo is not None and hi is not None and lo > hi:
            agg[k] = (min(lo, hi), max(lo, hi))

    return {k: tuple(v) for k, v in agg.items() if v != [None, None]}


if __name__ == "__main__":
    survey = {
        "age_range": "18-35",
        "volatility_tolerance": "high",
        "time_horizon": "long",
        "investment_goal": "growth",
        "selectedSectors": ["technology","health"]
    }
    from pprint import pprint
    pprint(get_target_ranges(survey))
