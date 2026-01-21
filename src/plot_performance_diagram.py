"""
Performance Diagram comparing AQM, Persistence, and CLYFAR ozone exceedance prediction.
Displays POD vs Success Ratio with CSI contours and frequency bias lines.
Focused on winter 2022-23 overlap period for direct comparison.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from verification_metrics import THRESHOLD, VerificationMetrics, calculate_contingency_counts

DATA_PATH = Path(__file__).parent.parent / 'data' / 'all_matched_obs_aqm.parquet'
AQM_FXX24_PATH = Path(__file__).parent.parent / 'data' / 'winter2022-23_aqm_fxx24.parquet'
CLYFAR_PATH = Path(__file__).parent.parent / 'data' / 'clyfar_hindcast_stats.csv'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'

# Probability threshold for CLYFAR poss_elevated
POSS_THRESHOLD = 0.3

# CSI contour values
CSI_VALUES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

# Frequency bias values
BIAS_VALUES = [0.25, 0.5, 1.0, 2.0, 4.0]

# Model styles - clean for poster
MODEL_STYLES = {
    'AQM (Day 1)': {'color': '#d62728', 'marker': 's', 'size': 200},  # Red square
    'Persistence': {'color': '#aaa', 'marker': 'D', 'size': 150},  # Gray diamond (not main focus)
    'CLYFAR p50': {'color': '#aaa', 'marker': 'o', 'size': 120},  # Gray - conservative
    'CLYFAR p90': {'color': '#2ca02c', 'marker': '*', 'size': 500, 'edgewidth': 2},  # BEST: Green star
    'CLYFAR poss≥0.3': {'color': '#aaa', 'marker': '^', 'size': 120},  # Gray
    'CLYFAR extreme≥0.1': {'color': '#aaa', 'marker': 'd', 'size': 100},  # Gray
    'CLYFAR moderate≥0.3': {'color': '#aaa', 'marker': 'o', 'size': 120},  # Gray
}


def load_merged_data() -> pl.DataFrame:
    """Load AQM fxx=24 and CLYFAR data, merge, and filter to overlap period.

    Uses AQM Day 1 forecasts (fxx=24) for fair comparison with CLYFAR's ~24h lead time.
    """
    # Load AQM fxx=24 Day 1 forecasts
    aqm_fxx24 = pl.read_parquet(AQM_FXX24_PATH)
    # Shift date by +1 day to get valid date (fxx=24 forecast made on day D is valid for day D+1)
    aqm_fxx24 = aqm_fxx24.with_columns([
        (pl.col('date') + pl.duration(days=1)).alias('date')
    ])

    # Load observations from matched data (date, stid, obs_mda8, winter)
    obs = pl.read_parquet(DATA_PATH).select(['date', 'stid', 'obs_mda8', 'winter'])

    # Join AQM fxx=24 with observations
    df = obs.join(aqm_fxx24, on=['date', 'stid'], how='inner')

    # Load CLYFAR data
    clyfar = pl.read_csv(CLYFAR_PATH)
    clyfar = clyfar.with_columns([
        pl.col('valid_date').str.to_date().alias('date')
    ])

    # Merge on date (inner join to get overlap period)
    df = df.join(
        clyfar.select(['date', 'forecast_p50', 'forecast_p90', 'poss_elevated', 'poss_extreme', 'poss_moderate']),
        on='date',
        how='inner'
    )

    # Filter to winter 2022-23
    df = df.filter(pl.col('winter') == '2022-23')

    return df


def calculate_metrics(df: pl.DataFrame, label: str, fcst_col: str = 'aqm_max',
                      threshold: float = THRESHOLD) -> VerificationMetrics:
    """Calculate contingency table metrics for a given dataframe and forecast column."""
    hits, misses, false_alarms, correct_negatives = calculate_contingency_counts(
        df, 'obs_mda8', fcst_col, threshold
    )

    return VerificationMetrics(
        name=label,
        hits=hits,
        misses=misses,
        false_alarms=false_alarms,
        correct_negatives=correct_negatives,
        n_total=len(df)
    )


def calculate_probability_metrics(df: pl.DataFrame, label: str, prob_col: str,
                                   prob_threshold: float) -> VerificationMetrics:
    """Calculate metrics for probability-based forecasts with separate thresholds.

    Uses obs_mda8 >= 70 ppb for observed exceedance, prob_col >= prob_threshold for forecast.
    """
    hits = len(df.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col(prob_col) >= prob_threshold)
    ))
    misses = len(df.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col(prob_col) < prob_threshold)
    ))
    false_alarms = len(df.filter(
        (pl.col('obs_mda8') < THRESHOLD) & (pl.col(prob_col) >= prob_threshold)
    ))
    correct_negatives = len(df.filter(
        (pl.col('obs_mda8') < THRESHOLD) & (pl.col(prob_col) < prob_threshold)
    ))

    return VerificationMetrics(
        name=label,
        hits=hits,
        misses=misses,
        false_alarms=false_alarms,
        correct_negatives=correct_negatives,
        n_total=len(df)
    )


def draw_csi_contours(ax: plt.Axes) -> None:
    """Draw curved CSI contour lines - minimal labels."""
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
            linewidth = 1.2 if csi in [0.3, 0.5, 0.7] else 0.6
            ax.plot(sr_valid, pod_values,
                    color='#cccccc', linestyle='-', linewidth=linewidth, alpha=0.6)

            # Only label key CSI values
            if csi in [0.3, 0.5, 0.7]:
                mid_idx = len(sr_valid) // 3
                if mid_idx < len(sr_valid):
                    ax.text(sr_valid[mid_idx], pod_values[mid_idx], f'{csi}',
                            fontsize=9, color='#888', ha='center', va='center')


def draw_bias_lines(ax: plt.Axes) -> None:
    """Draw only the bias=1 line (no labels)."""
    sr_range = np.linspace(0, 1.05, 100)

    # Only draw bias=1 line
    ax.plot(sr_range, sr_range, color='#aaa', linestyle='-', linewidth=1, alpha=0.5)


def plot_data_points(ax: plt.Axes, metrics_list: list[VerificationMetrics]) -> None:
    """Plot model comparison data points with labels for key systems."""

    for metrics in metrics_list:
        style = MODEL_STYLES.get(metrics.name, {'color': 'gray', 'marker': 'o', 'size': 100})
        edgewidth = style.get('edgewidth', 1.5)

        ax.scatter(metrics.sr, metrics.pod,
                   c=style['color'], marker=style['marker'], s=style['size'],
                   edgecolors='white', linewidths=edgewidth,
                   zorder=5)

        # Labels for key systems only
        if metrics.name == 'AQM (Day 1)':
            ax.annotate(f'AQM\nCSI={metrics.csi:.2f}',
                        xy=(metrics.sr, metrics.pod), xytext=(8, -20),
                        textcoords='offset points', fontsize=10, ha='left',
                        color='#d62728', fontweight='bold')
        elif metrics.name == 'CLYFAR p90':
            ax.annotate(f'CLYFAR p90\nCSI={metrics.csi:.2f}',
                        xy=(metrics.sr, metrics.pod), xytext=(-10, -25),
                        textcoords='offset points', fontsize=11, ha='right',
                        color='#2ca02c', fontweight='bold')

    # Gold star at perfect forecast (1, 1)
    ax.scatter(1.0, 1.0,
               c='gold', marker='*', s=800,
               edgecolors='black', linewidths=1.5,
               zorder=8)
    ax.annotate('Perfect', xy=(1.0, 1.0), xytext=(-8, -15),
                textcoords='offset points', fontsize=10, ha='right', color='#666')


def add_metrics_legend(fig: plt.Figure, metrics_list: list[VerificationMetrics]) -> None:
    """Add a simplified metrics summary box below the plot."""

    # Only show key systems
    key_systems = ['AQM (Day 1)', 'CLYFAR p90']
    key_metrics = [m for m in metrics_list if m.name in key_systems]

    lines = ['System                POD    FAR    CSI   Bias']
    lines.append('-' * 52)
    for m in key_metrics:
        lines.append(f'{m.name:<20} {m.pod:.3f}  {m.far:.3f}  {m.csi:.3f}  {m.frequency_bias:.2f}')

    metrics_text = '\n'.join(lines)

    fig.text(0.5, 0.01, metrics_text, ha='center', va='bottom',
             fontsize=10, fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                       edgecolor='black', alpha=0.95, linewidth=1.5))


def create_legend(ax: plt.Axes) -> None:
    """Create compact legend."""
    legend_elements = [
        Line2D([0], [0], marker='s', color='w', markerfacecolor='#d62728', markersize=10,
               markeredgecolor='w', label='AQM (operational)'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='#2ca02c', markersize=14,
               markeredgecolor='w', label='CLYFAR p90'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#aaa', markersize=8,
               markeredgecolor='w', label='CLYFAR (other thresholds)'),
    ]

    ax.legend(handles=legend_elements, loc='lower right', fontsize=10,
              framealpha=0.9, edgecolor='#ccc')


def main():
    """Generate the performance diagram comparing AQM, Persistence, and CLYFAR."""
    # Load merged data (winter 2022-23 overlap)
    df = load_merged_data()
    print(f'Loaded {len(df)} station-day pairs for winter 2022-23')

    # Calculate metrics for each model/threshold combination
    metrics_list = []

    # AQM Day 1: forecast >= 70 ppb (fxx=24, ~24h lead time)
    aqm_metrics = calculate_metrics(df, 'AQM (Day 1)', 'aqm_max', THRESHOLD)
    metrics_list.append(aqm_metrics)

    # Persistence: yesterday's obs as today's forecast
    df_with_lag = df.sort(['stid', 'date']).with_columns([
        pl.col('obs_mda8').shift(1).over('stid').alias('persistence_fcst')
    ])
    df_with_lag = df_with_lag.filter(pl.col('persistence_fcst').is_not_null())
    persistence_metrics = calculate_metrics(df_with_lag, 'Persistence', 'persistence_fcst', THRESHOLD)
    metrics_list.append(persistence_metrics)

    # CLYFAR p50 >= 70 ppb
    clyfar_p50 = calculate_metrics(df, 'CLYFAR p50', 'forecast_p50', THRESHOLD)
    metrics_list.append(clyfar_p50)

    # CLYFAR p90 >= 70 ppb
    clyfar_p90 = calculate_metrics(df, 'CLYFAR p90', 'forecast_p90', THRESHOLD)
    metrics_list.append(clyfar_p90)

    # CLYFAR poss_elevated >= 0.3 (probability threshold)
    # Use separate thresholds: obs >= 70 ppb, poss_elevated >= 0.3
    clyfar_poss = calculate_probability_metrics(df, 'CLYFAR poss≥0.3', 'poss_elevated', POSS_THRESHOLD)
    metrics_list.append(clyfar_poss)

    # CLYFAR poss_extreme >= 0.1 (probability of extreme ozone)
    # Use separate thresholds: obs >= 70 ppb, poss_extreme >= 0.1
    clyfar_extreme = calculate_probability_metrics(df, 'CLYFAR extreme≥0.1', 'poss_extreme', 0.1)
    metrics_list.append(clyfar_extreme)

    # CLYFAR poss_moderate >= 0.3 (probability of moderate ozone)
    # Use separate thresholds: obs >= 70 ppb, poss_moderate >= 0.3
    clyfar_moderate = calculate_probability_metrics(df, 'CLYFAR moderate≥0.3', 'poss_moderate', 0.3)
    metrics_list.append(clyfar_moderate)

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
    plot_data_points(ax, metrics_list)

    # Labels
    ax.set_xlabel('Success Ratio (1 - FAR)', fontsize=14)
    ax.set_ylabel('Probability of Detection (POD)', fontsize=14)

    # Title
    ax.set_title('Performance Diagram: Winter 2022-23 (24h lead)', fontsize=16, fontweight='bold', pad=10)

    # Minimal grid
    ax.grid(True, alpha=0.15, zorder=0)

    # Legend
    create_legend(ax)

    # Simple metrics table - just AQM vs CLYFAR p90
    key_systems = ['AQM (Day 1)', 'CLYFAR p90']
    key_metrics = [m for m in metrics_list if m.name in key_systems]

    table_text = '             POD    FAR    CSI\n'
    for m in key_metrics:
        name = m.name.replace(' (Day 1)', '')
        table_text += f'{name:<12} {m.pod:.2f}   {m.far:.2f}   {m.csi:.2f}\n'

    ax.text(0.02, 0.02, table_text.strip(), transform=ax.transAxes,
            fontsize=10, fontfamily='monospace', va='bottom',
            bbox=dict(facecolor='white', edgecolor='#ccc', alpha=0.9, pad=5))

    plt.tight_layout()

    # Save figure
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / 'performance_diagram.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    # Print summary
    print(f'\nPerformance Metrics Summary (Winter 2022-23):')
    print(f'{"Model":<22} {"POD":>8} {"FAR":>8} {"CSI":>8} {"Bias":>8}')
    print('-' * 56)
    for m in metrics_list:
        print(f'{m.name:<22} {m.pod:>8.3f} {m.far:>8.3f} {m.csi:>8.3f} {m.frequency_bias:>8.2f}')


if __name__ == '__main__':
    main()
