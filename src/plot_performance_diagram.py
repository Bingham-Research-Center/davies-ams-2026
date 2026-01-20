"""
Performance Diagram comparing AQM and CLYFAR ozone exceedance prediction.
Displays POD vs Success Ratio with CSI contours and frequency bias lines.
Focused on winter 2022-23 overlap period for direct comparison.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

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
    """
    Calculate contingency table metrics for a given dataframe and forecast column.

    Args:
        df: DataFrame with obs_mda8 and forecast columns
        label: Label for the metrics
        fcst_col: Name of the forecast column to evaluate
        threshold: Exceedance threshold for the forecast

    Returns:
        VerificationMetrics dataclass with all verification scores
    """
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


def plot_data_points(ax: plt.Axes, metrics_list: list[VerificationMetrics]) -> None:
    """
    Plot model comparison data points with color coding.

    Args:
        ax: Matplotlib axes
        metrics_list: List of VerificationMetrics for each model/threshold
    """
    # Color and marker scheme for different models
    model_styles = {
        'AQM (Day 1)': {'color': 'red', 'marker': 's', 'size': 200},
        'CLYFAR p50': {'color': 'blue', 'marker': 'o', 'size': 150},
        'CLYFAR p90': {'color': 'lightblue', 'marker': 'o', 'size': 150},
        'CLYFAR poss≥0.3': {'color': 'green', 'marker': '^', 'size': 150},
        'CLYFAR extreme≥0.1': {'color': 'purple', 'marker': 'd', 'size': 150},
        'CLYFAR moderate≥0.3': {'color': 'orange', 'marker': 'v', 'size': 150},
    }

    for metrics in metrics_list:
        style = model_styles.get(metrics.name, {'color': 'gray', 'marker': 'o', 'size': 100})
        ax.scatter(metrics.sr, metrics.pod,
                   c=style['color'], marker=style['marker'], s=style['size'],
                   edgecolors='black', linewidths=1.0,
                   label=metrics.name, zorder=5)

        # Add label
        offset_x = 10 if metrics.sr < 0.7 else -10
        ha = 'left' if metrics.sr < 0.7 else 'right'
        ax.annotate(f'{metrics.name}\nCSI={metrics.csi:.3f}',
                    xy=(metrics.sr, metrics.pod),
                    xytext=(offset_x, 8), textcoords='offset points',
                    fontsize=8, ha=ha, va='bottom',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                              edgecolor='none', alpha=0.8))

    # Gold star at perfect forecast (1, 1)
    ax.scatter(1.0, 1.0,
               c='gold', marker='*', s=400, edgecolors='black', linewidths=1.0,
               label='Perfect', zorder=7)


def add_metrics_legend(fig: plt.Figure, metrics_list: list[VerificationMetrics]) -> None:
    """
    Add a metrics summary box below the plot.
    """
    lines = ['Model          POD    FAR    CSI   Bias']
    for m in metrics_list:
        lines.append(f'{m.name:<14} {m.pod:.3f}  {m.far:.3f}  {m.csi:.3f}  {m.frequency_bias:.2f}')

    metrics_text = '\n'.join(lines)

    fig.text(0.5, 0.01, metrics_text, ha='center', va='bottom',
             fontsize=9, fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                       edgecolor='black', alpha=0.9))


def main():
    """Generate the performance diagram comparing AQM and CLYFAR."""
    # Load merged data (winter 2022-23 overlap)
    df = load_merged_data()
    print(f'Loaded {len(df)} station-day pairs for winter 2022-23')

    # Calculate metrics for each model/threshold combination
    metrics_list = []

    # AQM Day 1: forecast >= 70 ppb (fxx=24, ~24h lead time)
    aqm_metrics = calculate_metrics(df, 'AQM (Day 1)', 'aqm_max', THRESHOLD)
    metrics_list.append(aqm_metrics)

    # CLYFAR p50 >= 70 ppb
    clyfar_p50 = calculate_metrics(df, 'CLYFAR p50', 'forecast_p50', THRESHOLD)
    metrics_list.append(clyfar_p50)

    # CLYFAR p90 >= 70 ppb
    clyfar_p90 = calculate_metrics(df, 'CLYFAR p90', 'forecast_p90', THRESHOLD)
    metrics_list.append(clyfar_p90)

    # CLYFAR poss_elevated >= 0.3 (probability threshold)
    clyfar_poss = calculate_metrics(df, 'CLYFAR poss≥0.3', 'poss_elevated', POSS_THRESHOLD)
    metrics_list.append(clyfar_poss)

    # CLYFAR poss_extreme >= 0.1 (probability of extreme ozone)
    clyfar_extreme = calculate_metrics(df, 'CLYFAR extreme≥0.1', 'poss_extreme', 0.1)
    metrics_list.append(clyfar_extreme)

    # CLYFAR poss_moderate >= 0.3 (probability of moderate ozone)
    clyfar_moderate = calculate_metrics(df, 'CLYFAR moderate≥0.3', 'poss_moderate', 0.3)
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
    ax.set_xlabel('Success Ratio (1 - FAR)', fontsize=12)
    ax.set_ylabel('Probability of Detection (POD)', fontsize=12)

    # Title and subtitle
    fig.suptitle('Performance Diagram: AQM vs CLYFAR (24h Lead Time)',
                 fontsize=14, fontweight='bold', y=0.98)
    ax.set_title('Uinta Basin Winter 2022-23 Comparison (O\u2083 > 70 ppb)', fontsize=11, pad=10)

    # Grid
    ax.grid(True, alpha=0.3, zorder=0)

    # Corner labels
    corner_style = dict(fontsize=9, ha='center', va='center',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                  edgecolor='gray', alpha=0.9))
    ax.text(-0.08, 1.08, 'Overforecast\n(All False Alarms)',
            transform=ax.transData, **corner_style)
    ax.text(1.0, -0.08, 'Underforecast\n(All Misses)',
            transform=ax.transData, **corner_style)
    ax.text(-0.08, -0.08, 'No Skill',
            transform=ax.transData, **corner_style)

    # Legend
    ax.legend(loc='upper left', fontsize=9, framealpha=0.9)

    # Adjust layout for metrics box
    plt.subplots_adjust(bottom=0.18)

    # Metrics summary box
    add_metrics_legend(fig, metrics_list)

    # Save figure
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / 'performance_diagram.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    # Print summary
    print(f'\nPerformance Metrics Summary (Winter 2022-23):')
    print(f'{"Model":<16} {"POD":>8} {"FAR":>8} {"CSI":>8} {"Bias":>8}')
    print('-' * 52)
    for m in metrics_list:
        print(f'{m.name:<16} {m.pod:>8.3f} {m.far:>8.3f} {m.csi:>8.3f} {m.frequency_bias:>8.2f}')


if __name__ == '__main__':
    main()
