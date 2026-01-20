"""
Side-by-side contingency tables comparing AQM and CLYFAR p50 exceedance prediction.
Shows Hits, False Alarms, Misses, and Correct Negatives with performance metrics.
Focused on winter 2022-23 overlap period.
"""

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

from verification_metrics import THRESHOLD, calculate_contingency_counts

DATA_PATH = Path(__file__).parent.parent / 'data' / 'all_matched_obs_aqm.parquet'
AQM_FXX24_PATH = Path(__file__).parent.parent / 'data' / 'winter2022-23_aqm_fxx24.parquet'
CLYFAR_PATH = Path(__file__).parent.parent / 'data' / 'clyfar_hindcast_stats.csv'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'


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
        clyfar.select(['date', 'forecast_p50']),
        on='date',
        how='inner'
    )

    # Filter to winter 2022-23
    df = df.filter(pl.col('winter') == '2022-23')

    return df


def draw_contingency_table(ax: plt.Axes, hits: int, misses: int,
                           false_alarms: int, correct_negatives: int,
                           model_name: str, offset_x: float = 0) -> None:
    """Draw a single contingency table on the given axes.

    Args:
        ax: Matplotlib axes
        hits, misses, false_alarms, correct_negatives: Contingency counts
        model_name: Label for this model (e.g., 'AQM', 'CLYFAR p50')
        offset_x: X offset for positioning multiple tables
    """
    total = hits + misses + false_alarms + correct_negatives

    # Calculate metrics
    pod = hits / (hits + misses) if (hits + misses) > 0 else 0
    far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else 0
    csi = hits / (hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else 0

    # Cell definitions: (x, y, color, label, count)
    cells = [
        (offset_x + 0, 1, 'green', 'Hits', hits),
        (offset_x + 1, 1, 'orange', 'False Alarms', false_alarms),
        (offset_x + 0, 0, 'red', 'Misses', misses),
        (offset_x + 1, 0, 'royalblue', 'Correct Neg.', correct_negatives),
    ]

    # Draw cells
    for x, y, color, label, count in cells:
        rect = mpatches.FancyBboxPatch(
            (x, y), 1, 1,
            boxstyle='round,pad=0.02,rounding_size=0.05',
            facecolor=color,
            edgecolor='black',
            linewidth=2,
            alpha=0.5
        )
        ax.add_patch(rect)

        # Category label (bold)
        ax.text(x + 0.5, y + 0.6, label,
                fontsize=11, fontweight='bold', color='black',
                ha='center', va='center')
        # Count below label
        ax.text(x + 0.5, y + 0.35, f'n = {count}',
                fontsize=10, color='black',
                ha='center', va='center')

    # Model name above table
    ax.text(offset_x + 1.0, 2.2, model_name,
            fontsize=12, fontweight='bold', ha='center', va='bottom')

    # X-axis labels (below grid)
    ax.text(offset_x + 0.5, -0.12, 'Obs\nExceed', fontsize=9, fontweight='bold',
            ha='center', va='top')
    ax.text(offset_x + 1.5, -0.12, 'Obs\nNo Exceed', fontsize=9, fontweight='bold',
            ha='center', va='top')

    # Y-axis labels (left of grid) - only for leftmost table
    if offset_x < 0.5:
        ax.text(-0.12, 1.5, 'Model\nExceed', fontsize=9, fontweight='bold',
                ha='right', va='center')
        ax.text(-0.12, 0.5, 'Model\nNo Exceed', fontsize=9, fontweight='bold',
                ha='right', va='center')

    # Metrics text below table
    metrics_text = f'POD: {pod:.3f}  FAR: {far:.3f}  CSI: {csi:.3f}'
    ax.text(offset_x + 1.0, -0.5, metrics_text, fontsize=9, fontfamily='monospace',
            ha='center', va='top')


def main():
    # Load merged data (winter 2022-23 overlap)
    df = load_merged_data()
    total = len(df)
    print(f'Loaded {total} station-day pairs for winter 2022-23')

    # Calculate AQM contingency table
    aqm_hits, aqm_misses, aqm_fa, aqm_cn = calculate_contingency_counts(
        df, 'obs_mda8', 'aqm_max', THRESHOLD
    )

    # Calculate CLYFAR p50 contingency table
    clf_hits, clf_misses, clf_fa, clf_cn = calculate_contingency_counts(
        df, 'obs_mda8', 'forecast_p50', THRESHOLD
    )

    # Create figure for side-by-side tables
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(-0.3, 5.3)
    ax.set_ylim(-0.8, 2.5)
    ax.set_aspect('equal')
    ax.axis('off')

    # Draw AQM table on the left
    draw_contingency_table(ax, aqm_hits, aqm_misses, aqm_fa, aqm_cn,
                           'AQM (Day 1)', offset_x=0)

    # Draw CLYFAR table on the right (offset by 3 units)
    draw_contingency_table(ax, clf_hits, clf_misses, clf_fa, clf_cn,
                           'CLYFAR p50', offset_x=3)

    # Title
    fig.suptitle('Contingency Tables: AQM vs CLYFAR p50 (24h Lead, >70 ppb)',
                 fontsize=14, fontweight='bold', y=0.95)
    ax.text(2.5, 2.5, f'Winter 2022-23, n={total} station-days',
            fontsize=11, ha='center', va='bottom', style='italic')

    # Adjust layout
    plt.subplots_adjust(left=0.08, right=0.92, top=0.85, bottom=0.15)

    # Save figure
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / 'contingency_table.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    # Print summary
    print(f'\nAQM (Day 1) Contingency Table:')
    print(f'  Hits: {aqm_hits}, FA: {aqm_fa}, Misses: {aqm_misses}, CN: {aqm_cn}')
    aqm_pod = aqm_hits / (aqm_hits + aqm_misses) if (aqm_hits + aqm_misses) > 0 else 0
    aqm_far = aqm_fa / (aqm_hits + aqm_fa) if (aqm_hits + aqm_fa) > 0 else 0
    aqm_csi = aqm_hits / (aqm_hits + aqm_misses + aqm_fa) if (aqm_hits + aqm_misses + aqm_fa) > 0 else 0
    print(f'  POD: {aqm_pod:.3f}, FAR: {aqm_far:.3f}, CSI: {aqm_csi:.3f}')

    print(f'\nCLYFAR p50 Contingency Table:')
    print(f'  Hits: {clf_hits}, FA: {clf_fa}, Misses: {clf_misses}, CN: {clf_cn}')
    clf_pod = clf_hits / (clf_hits + clf_misses) if (clf_hits + clf_misses) > 0 else 0
    clf_far = clf_fa / (clf_hits + clf_fa) if (clf_hits + clf_fa) > 0 else 0
    clf_csi = clf_hits / (clf_hits + clf_misses + clf_fa) if (clf_hits + clf_misses + clf_fa) > 0 else 0
    print(f'  POD: {clf_pod:.3f}, FAR: {clf_far:.3f}, CSI: {clf_csi:.3f}')


if __name__ == '__main__':
    main()
