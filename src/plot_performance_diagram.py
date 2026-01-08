"""
Performance Diagram for AQM ozone exceedance prediction.
Displays POD vs Success Ratio with CSI contours and frequency bias lines.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from dataclasses import dataclass

THRESHOLD = 70  # ppb NAAQS threshold
DATA_PATH = Path(__file__).parent.parent / 'data' / 'all_matched_obs_aqm.parquet'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'

# Season ordering for consistent display
WINTER_ORDER = ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

# Color scheme for 6 seasons (colorblind-friendly, distinct)
SEASON_COLORS = {
    '2019-20': '#1f77b4',  # blue
    '2020-21': '#ff7f0e',  # orange
    '2021-22': '#2ca02c',  # green
    '2022-23': '#9467bd',  # purple
    '2023-24': '#8c564b',  # brown
    '2024-25': '#e377c2',  # pink
}

# CSI contour values
CSI_VALUES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

# Frequency bias values
BIAS_VALUES = [0.25, 0.5, 1.0, 2.0, 4.0]


@dataclass
class PerformanceMetrics:
    """Container for forecast verification metrics."""
    label: str
    hits: int
    misses: int
    false_alarms: int
    correct_negatives: int

    @property
    def pod(self) -> float:
        """Probability of Detection = hits / (hits + misses)"""
        denom = self.hits + self.misses
        return self.hits / denom if denom > 0 else 0.0

    @property
    def far(self) -> float:
        """False Alarm Ratio = false_alarms / (hits + false_alarms)"""
        denom = self.hits + self.false_alarms
        return self.false_alarms / denom if denom > 0 else 0.0

    @property
    def sr(self) -> float:
        """Success Ratio = 1 - FAR"""
        return 1.0 - self.far

    @property
    def csi(self) -> float:
        """Critical Success Index = hits / (hits + misses + false_alarms)"""
        denom = self.hits + self.misses + self.false_alarms
        return self.hits / denom if denom > 0 else 0.0

    @property
    def bias(self) -> float:
        """Frequency Bias = (hits + false_alarms) / (hits + misses)"""
        denom = self.hits + self.misses
        return (self.hits + self.false_alarms) / denom if denom > 0 else 0.0


def calculate_metrics(df: pl.DataFrame, label: str) -> PerformanceMetrics:
    """
    Calculate contingency table metrics for a given dataframe.

    Args:
        df: DataFrame with obs_mda8 and aqm_max columns
        label: Label for the metrics (e.g., season name or 'All Seasons')

    Returns:
        PerformanceMetrics dataclass with all verification scores
    """
    hits = len(df.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col('aqm_max') >= THRESHOLD)
    ))
    false_alarms = len(df.filter(
        (pl.col('obs_mda8') < THRESHOLD) & (pl.col('aqm_max') >= THRESHOLD)
    ))
    misses = len(df.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col('aqm_max') < THRESHOLD)
    ))
    correct_negatives = len(df.filter(
        (pl.col('obs_mda8') < THRESHOLD) & (pl.col('aqm_max') < THRESHOLD)
    ))

    return PerformanceMetrics(
        label=label,
        hits=hits,
        misses=misses,
        false_alarms=false_alarms,
        correct_negatives=correct_negatives
    )


def draw_csi_contours(ax: plt.Axes) -> None:
    """
    Draw curved CSI contour lines on the performance diagram.

    CSI relationship: CSI = 1 / (1/POD + 1/SR - 1)
    Rearranged: POD = 1 / (1/CSI - 1/SR + 1)
    """
    sr_range = np.linspace(0.01, 1.0, 200)

    for csi in CSI_VALUES:
        pod_values = []
        sr_valid = []

        for sr in sr_range:
            denom = 1/csi - 1/sr + 1
            if denom > 0:
                pod = 1 / denom
                if 0 <= pod <= 1:
                    pod_values.append(pod)
                    sr_valid.append(sr)

        if sr_valid:
            ax.plot(sr_valid, pod_values,
                    color='gray', linestyle='--', linewidth=0.8, alpha=0.7)

            # Label the contour at 1/3 position
            mid_idx = len(sr_valid) // 3
            if mid_idx < len(sr_valid):
                ax.annotate(f'{csi}',
                            xy=(sr_valid[mid_idx], pod_values[mid_idx]),
                            fontsize=8, color='gray',
                            ha='center', va='center',
                            bbox=dict(boxstyle='round,pad=0.1',
                                      facecolor='white', edgecolor='none', alpha=0.7))


def draw_bias_lines(ax: plt.Axes) -> None:
    """
    Draw straight diagonal frequency bias lines.

    Bias = POD / SR, therefore POD = Bias * SR (lines through origin)
    """
    sr_range = np.linspace(0, 1.05, 100)

    for bias in BIAS_VALUES:
        pod_values = bias * sr_range
        mask = pod_values <= 1.05

        if bias == 1.0:
            ax.plot(sr_range[mask], pod_values[mask],
                    color='black', linestyle='-', linewidth=1.5)
        else:
            ax.plot(sr_range[mask], pod_values[mask],
                    color='blue', linestyle=':', linewidth=1.0, alpha=0.7)

        # Label positioning
        if bias <= 1.0:
            label_sr = 0.95
            label_pod = bias * label_sr
        else:
            label_pod = 0.98
            label_sr = label_pod / bias

        ax.annotate(f'Bias={bias}',
                    xy=(label_sr, label_pod),
                    fontsize=8, color='blue' if bias != 1.0 else 'black',
                    ha='right', va='bottom',
                    bbox=dict(boxstyle='round,pad=0.1',
                              facecolor='white', edgecolor='none', alpha=0.7))


def plot_data_points(ax: plt.Axes,
                     seasonal_metrics: list,
                     all_seasons_metrics: PerformanceMetrics) -> None:
    """
    Plot seasonal data points and all-seasons aggregate.
    """
    # Track points at similar positions for stacking labels
    origin_count = 0
    lower_right_count = 0

    # Plot individual seasons as colored circles with labels
    for metrics in seasonal_metrics:
        ax.scatter(metrics.sr, metrics.pod,
                   c=SEASON_COLORS.get(metrics.label, 'gray'),
                   marker='o', s=100, edgecolors='black', linewidths=1.0,
                   label=metrics.label, zorder=5)

        # Add text label with smart offset based on position
        if metrics.sr < 0.1 and metrics.pod < 0.1:  # Near origin
            offset = (10, 10 + origin_count * 14)
            origin_count += 1
            ha = 'left'
        elif metrics.sr > 0.9 and metrics.pod < 0.1:  # Lower right edge
            offset = (-10, 10 + lower_right_count * 14)
            lower_right_count += 1
            ha = 'right'
        else:  # Regular positioning
            offset = (8, 8)
            ha = 'left'

        ax.annotate(metrics.label, xy=(metrics.sr, metrics.pod),
                    xytext=offset, textcoords='offset points',
                    fontsize=8, ha=ha, va='bottom',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor='none', alpha=0.7))

    # Plot all-seasons aggregate as large red square
    ax.scatter(all_seasons_metrics.sr, all_seasons_metrics.pod,
               c='red', marker='s', s=200, edgecolors='black', linewidths=1.5,
               label='All Seasons', zorder=6)

    # Gold star at perfect forecast (1, 1)
    ax.scatter(1.0, 1.0,
               c='gold', marker='*', s=400, edgecolors='black', linewidths=1.0,
               label='Perfect', zorder=7)

    # Red arrow from all-seasons point toward (1, 1)
    dx = 1.0 - all_seasons_metrics.sr
    dy = 1.0 - all_seasons_metrics.pod
    if (dx**2 + dy**2) > 0.01:  # Only draw if distance is meaningful
        ax.annotate('',
                    xy=(1.0, 1.0),
                    xytext=(all_seasons_metrics.sr, all_seasons_metrics.pod),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    zorder=4)


def add_metrics_legend(fig: plt.Figure,
                       all_seasons_metrics: PerformanceMetrics) -> None:
    """
    Add a metrics box below the plot (outside data area).
    """
    metrics_text = (
        f'All Seasons:  POD: {all_seasons_metrics.pod:.3f}  |  '
        f'SR: {all_seasons_metrics.sr:.3f}  |  '
        f'CSI: {all_seasons_metrics.csi:.3f}  |  '
        f'Bias: {all_seasons_metrics.bias:.2f}'
    )

    fig.text(0.5, 0.02, metrics_text, ha='center', va='bottom',
             fontsize=10, fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                       edgecolor='black', alpha=0.9))


def main():
    """Generate the performance diagram."""
    # Load data
    df = pl.read_parquet(DATA_PATH)

    # Calculate metrics for each season
    seasonal_metrics = []
    for winter in WINTER_ORDER:
        df_season = df.filter(pl.col('winter') == winter)
        if len(df_season) > 0:
            metrics = calculate_metrics(df_season, winter)
            seasonal_metrics.append(metrics)

    # Calculate all-seasons aggregate
    all_seasons_metrics = calculate_metrics(df, 'All Seasons')

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 9))

    # Set axis limits
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_aspect('equal')

    # Draw reference elements (behind data points)
    draw_csi_contours(ax)
    draw_bias_lines(ax)

    # Plot data points
    plot_data_points(ax, seasonal_metrics, all_seasons_metrics)

    # Labels
    ax.set_xlabel('Success Ratio (1 - FAR)', fontsize=12)
    ax.set_ylabel('Probability of Detection (POD)', fontsize=12)

    # Title and subtitle
    fig.suptitle('Performance Diagram: NOAA AQM Exceedance Prediction',
                 fontsize=14, fontweight='bold', y=0.98)
    ax.set_title('Uinta Basin Winter O\u2083 > 70 ppb', fontsize=11, pad=10)

    # Grid
    ax.grid(True, alpha=0.3, zorder=0)

    # Season legend (upper left)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.9, ncol=2)

    # Adjust layout to make room for metrics box below
    plt.subplots_adjust(bottom=0.12)

    # Metrics legend box (below plot)
    add_metrics_legend(fig, all_seasons_metrics)

    # Save figure
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / 'performance_diagram.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    # Print summary
    print(f'\nPerformance Metrics Summary:')
    print(f'{"Season":<12} {"POD":>8} {"SR":>8} {"CSI":>8} {"Bias":>8}')
    print('-' * 48)
    for m in seasonal_metrics:
        print(f'{m.label:<12} {m.pod:>8.3f} {m.sr:>8.3f} {m.csi:>8.3f} {m.bias:>8.2f}')
    print('-' * 48)
    m = all_seasons_metrics
    print(f'{"All Seasons":<12} {m.pod:>8.3f} {m.sr:>8.3f} {m.csi:>8.3f} {m.bias:>8.2f}')


if __name__ == '__main__':
    main()
