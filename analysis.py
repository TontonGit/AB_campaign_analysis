import pandas as pd
import numpy as np
from scipy.stats import norm
from typing import Dict, Literal


def _validate_inputs(x_a: int, x_b: int, n_a: int, n_b: int) -> None:
    if n_a <= 0 or n_b <= 0:
        raise ValueError("n_a and n_b must be positive.")
    if x_a < 0 or x_b < 0:
        raise ValueError("x_a and x_b must be non-negative.")
    if x_a > n_a or x_b > n_b:
        raise ValueError("x_a and x_b cannot exceed sample sizes.")


def sample_proportions(x_a: int, x_b: int, n_a: int, n_b: int) -> Dict[str, float]:
    _validate_inputs(x_a, x_b, n_a, n_b)
    return {"p_a": x_a / n_a, "p_b": x_b / n_b}


def pooled_proportion(x_a: int, x_b: int, n_a: int, n_b: int) -> float:
    _validate_inputs(x_a, x_b, n_a, n_b)
    return (x_a + x_b) / (n_a + n_b)


def unpooled_standard_error(p_a: float, p_b: float, n_a: int, n_b: int) -> float:
    if n_a <= 0 or n_b <= 0:
        raise ValueError("n_a and n_b must be positive.")
    return np.sqrt((p_a * (1 - p_a) / n_a) + (p_b * (1 - p_b) / n_b))


def pooled_standard_error(p_pool: float, n_a: int, n_b: int) -> float:
    if n_a <= 0 or n_b <= 0:
        raise ValueError("n_a and n_b must be positive.")
    return np.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))


def z_score(p_a: float, p_b: float, se: float) -> float:
    if se <= 0:
        raise ValueError("Standard error must be positive.")
    return (p_b - p_a) / se


def p_value(z: float, alternative: Literal["larger", "smaller", "two-sided"] = "larger") -> float:
    if alternative == "larger":
        return 1 - norm.cdf(z)
    if alternative == "smaller":
        return norm.cdf(z)
    if alternative == "two-sided":
        return 2 * (1 - norm.cdf(abs(z)))
    raise ValueError("alternative must be 'larger', 'smaller', or 'two-sided'")


def z_critical(ci: float) -> float:
    if not (0 < ci < 1):
        raise ValueError("ci must be between 0 and 1.")
    alpha = 1 - ci
    return norm.ppf(1 - alpha / 2)


def conf_interval(diff: float, z_crit: float, se: float) -> Dict[str, float]:
    return {
        "lower": diff - z_crit * se,
        "upper": diff + z_crit * se,
    }


def calculate_conversion(df: pd.DataFrame) -> pd.Series:
    required = {"ad_group", "converted"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df.groupby("ad_group")["converted"].mean()


def two_proportion_test(
    x_a: int,
    x_b: int,
    n_a: int,
    n_b: int,
    alternative: Literal["larger", "smaller", "two-sided"] = "larger",
) -> Dict[str, float]:
    _validate_inputs(x_a, x_b, n_a, n_b)

    props = sample_proportions(x_a, x_b, n_a, n_b)
    p_a, p_b = props["p_a"], props["p_b"]

    p_pool = pooled_proportion(x_a, x_b, n_a, n_b)
    se = pooled_standard_error(p_pool, n_a, n_b)
    z = z_score(p_a, p_b, se)
    p_val = p_value(z, alternative=alternative)

    return {
        "p_a": p_a,
        "p_b": p_b,
        "difference": p_b - p_a,
        "z_score": z,
        "p_value": p_val,
    }


def confidence_interval_two_proportions(
    p_a: float,
    p_b: float,
    n_a: int,
    n_b: int,
    ci: float = 0.95,
) -> Dict[str, float]:
    diff = p_b - p_a
    se = unpooled_standard_error(p_a, p_b, n_a, n_b)
    z_crit = z_critical(ci)
    return conf_interval(diff, z_crit, se)