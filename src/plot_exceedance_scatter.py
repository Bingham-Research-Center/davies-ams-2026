"""
Scatter plot showing AQM performance on ozone exceedance events.
Categorizes days as Hits, Misses, or False Alarms based on 70 ppb threshold.
"""

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

THRESHOLD = 70  # ppb NAAQS threshold
DATA_PATH = Path(__file__).parent.parent / 'data' / 'all_matched_obs_aqm.parquet'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'


def main():
    # Load data
    df = pl.read_parquet(DATA_PATH)

    # Filter to exceedance events only (either obs or AQM >= threshold)
    df_exc = df.filter(
        (pl.col('obs_mda8') >= THRESHOLD) | (pl.col('aqm_max') >= THRESHOLD)
    )

    # Categorize events
    hits = df_exc.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col('aqm_max') >= THRESHOLD)
    )
    misses = df_exc.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col('aqm_max') < THRESHOLD)
    )
    false_alarms = df_exc.filter(
        (pl.col('obs_mda8') < THRESHOLD) & (pl.col('aqm_max') >= THRESHOLD)
    )

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 8))

    # Axis limits
    x_min, x_max = 35, 130
    y_min, y_max = 35, 105
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # Quadrant shading (draw first, behind everything else)
    # Upper-right: Hits region (green)
    ax.fill_between([THRESHOLD, x_max], THRESHOLD, y_max,
                    color='green', alpha=0.1, zorder=0)
    # Upper-left: False Alarms region (orange)
    ax.fill_between([x_min, THRESHOLD], THRESHOLD, y_max,
                    color='orange', alpha=0.1, zorder=0)
    # Lower-right: Misses region (red)
    ax.fill_between([THRESHOLD, x_max], y_min, THRESHOLD,
                    color='red', alpha=0.1, zorder=0)

    # Reference lines
    # Threshold lines at 70 ppb
    ax.axhline(y=THRESHOLD, color='gray', linestyle='--', linewidth=1.5, zorder=1)
    ax.axvline(x=THRESHOLD, color='gray', linestyle='--', linewidth=1.5, zorder=1)
    # 1:1 reference line
    ax.plot([x_min, min(x_max, y_max)], [x_min, min(x_max, y_max)],
            color='black', linestyle=':', linewidth=1.5, zorder=1, label='1:1 line')

    # Scatter points
    # Hits: green circles
    ax.scatter(hits['obs_mda8'].to_numpy(), hits['aqm_max'].to_numpy(),
               c='green', marker='o', s=60, edgecolors='black', linewidths=0.8,
               label=f'Hits (n={len(hits)})', zorder=3)
    # Misses: red X markers
    ax.scatter(misses['obs_mda8'].to_numpy(), misses['aqm_max'].to_numpy(),
               c='red', marker='X', s=70, edgecolors='black', linewidths=0.8,
               label=f'Misses (n={len(misses)})', zorder=3)
    # False Alarms: orange squares
    ax.scatter(false_alarms['obs_mda8'].to_numpy(), false_alarms['aqm_max'].to_numpy(),
               c='orange', marker='s', s=60, edgecolors='black', linewidths=0.8,
               label=f'False Alarms (n={len(false_alarms)})', zorder=3)

    # Quadrant labels
    ax.text(100, 88, 'Hits', fontsize=12, fontweight='bold', color='darkgreen',
            ha='center', va='center', zorder=2)
    ax.text(52, 88, 'False\nAlarms', fontsize=12, fontweight='bold', color='darkorange',
            ha='center', va='center', zorder=2)
    ax.text(100, 52, 'Misses', fontsize=12, fontweight='bold', color='darkred',
            ha='center', va='center', zorder=2)

    # Labels and title
    ax.set_xlabel('Observed 8-hour Max Ozone (ppb)', fontsize=12)
    ax.set_ylabel('AQM Predicted 8-hour Max Ozone (ppb)', fontsize=12)
    fig.suptitle('Individual Exceedance Events', fontsize=14, fontweight='bold', y=0.98)
    ax.set_title('AQM vs Observed (70 ppb threshold)', fontsize=11, pad=10)

    # Legend
    ax.legend(loc='lower right', fontsize=10, framealpha=0.9)

    # Grid
    ax.grid(True, alpha=0.3, zorder=0)

    # Save figure
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / 'exceedance_scatter.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    # Print summary
    print(f'\nExceedance Event Summary:')
    print(f'  Hits: {len(hits)}')
    print(f'  Misses: {len(misses)}')
    print(f'  False Alarms: {len(false_alarms)}')
    print(f'  Total events: {len(df_exc)}')


if __name__ == '__main__':
    main()
