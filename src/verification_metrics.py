"""
Shared verification metrics for ozone forecast evaluation.

Provides standardized calculation of categorical forecast verification
metrics (POD, FAR, CSI, bias) and bootstrap confidence intervals.
"""
from dataclasses import dataclass

import numpy as np
import polars as pl

# Constants
THRESHOLD = 70  # NAAQS ozone exceedance threshold (ppb)


@dataclass
class VerificationMetrics:
    """Container for categorical forecast verification metrics."""
    name: str
    hits: int
    misses: int
    false_alarms: int
    correct_negatives: int
    mean_bias: float = 0.0
    rmse: float = 0.0
    n_total: int = 0

    @property
    def pod(self) -> float:
        """Probability of Detection = hits / (hits + misses)."""
        denom = self.hits + self.misses
        return self.hits / denom if denom > 0 else 0.0

    @property
    def far(self) -> float:
        """False Alarm Ratio = false_alarms / (hits + false_alarms)."""
        denom = self.hits + self.false_alarms
        return self.false_alarms / denom if denom > 0 else 0.0

    @property
    def sr(self) -> float:
        """Success Ratio = 1 - FAR."""
        return 1.0 - self.far

    @property
    def csi(self) -> float:
        """Critical Success Index = hits / (hits + misses + false_alarms)."""
        denom = self.hits + self.misses + self.false_alarms
        return self.hits / denom if denom > 0 else 0.0

    @property
    def frequency_bias(self) -> float:
        """Frequency Bias = (hits + false_alarms) / (hits + misses)."""
        denom = self.hits + self.misses
        return (self.hits + self.false_alarms) / denom if denom > 0 else 0.0

    def skill_score(self, reference: 'VerificationMetrics', metric: str = 'csi') -> float:
        """
        Skill score relative to reference: (score - ref) / (1 - ref).

        Positive = better than reference, 0 = equal, 1 = perfect.
        """
        if metric == 'csi':
            score, ref_score = self.csi, reference.csi
        elif metric == 'pod':
            score, ref_score = self.pod, reference.pod
        else:
            raise ValueError(f"Unknown metric: {metric}")

        if ref_score >= 1.0:
            return 0.0
        return (score - ref_score) / (1.0 - ref_score)


def calculate_contingency_counts(
    df: pl.DataFrame,
    obs_col: str,
    fcst_col: str,
    threshold: float = THRESHOLD
) -> tuple[int, int, int, int]:
    """
    Calculate contingency table counts from forecast and observation columns.

    Returns:
        Tuple of (hits, misses, false_alarms, correct_negatives)
    """
    hits = len(df.filter(
        (pl.col(obs_col) >= threshold) & (pl.col(fcst_col) >= threshold)
    ))
    misses = len(df.filter(
        (pl.col(obs_col) >= threshold) & (pl.col(fcst_col) < threshold)
    ))
    false_alarms = len(df.filter(
        (pl.col(obs_col) < threshold) & (pl.col(fcst_col) >= threshold)
    ))
    correct_negatives = len(df.filter(
        (pl.col(obs_col) < threshold) & (pl.col(fcst_col) < threshold)
    ))

    return hits, misses, false_alarms, correct_negatives


def calculate_metrics_from_df(
    df: pl.DataFrame,
    obs_col: str,
    fcst_col: str,
    name: str,
    threshold: float = THRESHOLD
) -> VerificationMetrics:
    """
    Calculate full verification metrics from a DataFrame.

    Args:
        df: DataFrame with observation and forecast columns
        obs_col: Name of observation column
        fcst_col: Name of forecast column
        name: Label for the metrics
        threshold: Exceedance threshold (default: 70 ppb)

    Returns:
        VerificationMetrics dataclass with all verification scores
    """
    # Filter to valid values
    valid = df.filter(
        pl.col(obs_col).is_not_null() & pl.col(fcst_col).is_not_null()
    )

    hits, misses, false_alarms, correct_negatives = calculate_contingency_counts(
        valid, obs_col, fcst_col, threshold
    )

    # Continuous metrics
    errors = valid.with_columns([
        (pl.col(fcst_col) - pl.col(obs_col)).alias('_error')
    ])

    mean_bias = errors['_error'].mean() if len(errors) > 0 else 0.0
    rmse = np.sqrt((errors['_error'] ** 2).mean()) if len(errors) > 0 else 0.0

    return VerificationMetrics(
        name=name,
        hits=hits,
        misses=misses,
        false_alarms=false_alarms,
        correct_negatives=correct_negatives,
        mean_bias=mean_bias,
        rmse=rmse,
        n_total=len(valid)
    )


def calculate_forecast_bias(df: pl.DataFrame, fcst_col: str, obs_col: str) -> float:
    """Mean forecast error (forecast - observed)."""
    valid = df.filter(
        pl.col(obs_col).is_not_null() & pl.col(fcst_col).is_not_null()
    )
    if len(valid) == 0:
        return 0.0
    return (valid[fcst_col] - valid[obs_col]).mean()


def calculate_rmse(df: pl.DataFrame, fcst_col: str, obs_col: str) -> float:
    """Root mean square error."""
    valid = df.filter(
        pl.col(obs_col).is_not_null() & pl.col(fcst_col).is_not_null()
    )
    if len(valid) == 0:
        return 0.0
    errors = valid[fcst_col] - valid[obs_col]
    return np.sqrt((errors ** 2).mean())


def bootstrap_metric_ci(
    df: pl.DataFrame,
    metric_func: callable,
    n_iterations: int = 1000,
    confidence: float = 0.95,
    seed: int = 42
) -> tuple[float, float, float]:
    """
    Bootstrap confidence interval for any metric.

    Args:
        df: DataFrame to sample from
        metric_func: Function that takes a DataFrame and returns a float metric
        n_iterations: Number of bootstrap iterations
        confidence: Confidence level (default 0.95 for 95% CI)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (point_estimate, ci_lower, ci_upper)
    """
    rng = np.random.default_rng(seed)

    # Calculate point estimate
    point_estimate = metric_func(df)

    n = len(df)
    if n == 0:
        return (0.0, 0.0, 0.0)

    # Bootstrap sampling
    bootstrap_values = np.zeros(n_iterations)
    df_np_idx = np.arange(n)

    for i in range(n_iterations):
        idx = rng.choice(df_np_idx, size=n, replace=True)
        sample = df[idx.tolist()]
        bootstrap_values[i] = metric_func(sample)

    # Calculate confidence interval
    alpha = 1 - confidence
    ci_lower = np.percentile(bootstrap_values, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_values, 100 * (1 - alpha / 2))

    return (point_estimate, ci_lower, ci_upper)


def bootstrap_pod_difference(
    df: pl.DataFrame,
    fcst_col_a: str,
    fcst_col_b: str,
    obs_col: str = 'obs_mda8',
    threshold: float = THRESHOLD,
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42
) -> dict:
    """
    Bootstrap CI for POD difference between two forecasts.

    Args:
        df: DataFrame with observation and forecast columns
        fcst_col_a: Name of first forecast column
        fcst_col_b: Name of second forecast column
        obs_col: Name of observation column
        threshold: Exceedance threshold
        n_iterations: Number of bootstrap iterations
        confidence_level: Confidence level for CI
        seed: Random seed

    Returns:
        Dict with pod_diff, ci_lower, ci_upper, p_value, n_exceedance
    """
    rng = np.random.default_rng(seed)

    # Filter to exceedance days with valid forecasts
    exc_days = df.filter(
        (pl.col(obs_col) >= threshold) &
        pl.col(fcst_col_a).is_not_null() &
        pl.col(fcst_col_b).is_not_null()
    )

    n_total = len(exc_days)
    if n_total == 0:
        return {'pod_diff': 0.0, 'ci_lower': 0.0, 'ci_upper': 0.0, 'p_value': 1.0, 'n_exceedance': 0}

    fcst_a = exc_days[fcst_col_a].to_numpy()
    fcst_b = exc_days[fcst_col_b].to_numpy()

    # Original POD difference
    hit_a = (fcst_a >= threshold).sum()
    hit_b = (fcst_b >= threshold).sum()
    pod_diff_observed = (hit_a - hit_b) / n_total

    # Bootstrap
    pod_diffs = np.zeros(n_iterations)
    for i in range(n_iterations):
        idx = rng.integers(0, n_total, size=n_total)
        hit_a_boot = (fcst_a[idx] >= threshold).sum()
        hit_b_boot = (fcst_b[idx] >= threshold).sum()
        pod_diffs[i] = (hit_a_boot - hit_b_boot) / n_total

    # CI and p-value
    alpha = 1 - confidence_level
    ci_lower = np.percentile(pod_diffs, 100 * alpha / 2)
    ci_upper = np.percentile(pod_diffs, 100 * (1 - alpha / 2))
    p_value = np.mean(pod_diffs <= 0)

    return {
        'pod_diff': pod_diff_observed,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'p_value': p_value,
        'n_exceedance': n_total
    }


def bootstrap_pod_ci(
    df: pl.DataFrame,
    obs_col: str = 'obs_mda8',
    fcst_col: str = 'aqm_max',
    threshold: float = THRESHOLD,
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42
) -> tuple[float, float, float]:
    """
    Bootstrap CI for POD of a single forecast.

    Args:
        df: DataFrame with observation and forecast columns
        obs_col: Name of observation column
        fcst_col: Name of forecast column
        threshold: Exceedance threshold
        n_iterations: Number of bootstrap iterations
        confidence_level: Confidence level for CI
        seed: Random seed

    Returns:
        Tuple of (pod, ci_lower, ci_upper)
    """
    rng = np.random.default_rng(seed)

    # Filter to exceedance days with valid forecasts
    exc_days = df.filter(
        (pl.col(obs_col) >= threshold) &
        pl.col(fcst_col).is_not_null()
    )

    n_total = len(exc_days)
    if n_total == 0:
        return (0.0, 0.0, 0.0)

    fcst = exc_days[fcst_col].to_numpy()

    # Original POD
    hits = (fcst >= threshold).sum()
    pod_observed = hits / n_total

    # Bootstrap
    pods = np.zeros(n_iterations)
    for i in range(n_iterations):
        idx = rng.integers(0, n_total, size=n_total)
        hits_boot = (fcst[idx] >= threshold).sum()
        pods[i] = hits_boot / n_total

    # CI
    alpha = 1 - confidence_level
    ci_lower = np.percentile(pods, 100 * alpha / 2)
    ci_upper = np.percentile(pods, 100 * (1 - alpha / 2))

    return (pod_observed, ci_lower, ci_upper)
