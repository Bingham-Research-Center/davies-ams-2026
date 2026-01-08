"""
Visual 2x2 contingency table for AQM ozone exceedance prediction.
Shows Hits, False Alarms, Misses, and Correct Negatives with performance metrics.
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
    total = len(df)

    # Calculate contingency table categories (all days, not just exceedance events)
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

    # Calculate performance metrics
    pod = hits / (hits + misses) if (hits + misses) > 0 else 0
    far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else 0
    csi = hits / (hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else 0
    accuracy = (hits + correct_negatives) / total if total > 0 else 0

    # Create figure with extra space on right for metrics
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(-0.1, 2.1)
    ax.set_ylim(-0.1, 2.1)
    ax.set_aspect('equal')
    ax.axis('off')

    # Cell definitions: (x, y, color, label, count)
    cells = [
        (0, 1, 'green', 'Hits', hits),           # Top-left
        (1, 1, 'orange', 'False Alarms', false_alarms),  # Top-right
        (0, 0, 'red', 'Misses', misses),         # Bottom-left
        (1, 0, 'royalblue', 'Correct Negatives', correct_negatives),  # Bottom-right
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
                fontsize=14, fontweight='bold', color='black',
                ha='center', va='center')
        # Count below label
        ax.text(x + 0.5, y + 0.35, f'n = {count}',
                fontsize=12, color='black',
                ha='center', va='center')

    # X-axis labels (below grid)
    ax.text(0.5, -0.15, 'Observed\nExceedance', fontsize=11, fontweight='bold',
            ha='center', va='top')
    ax.text(1.5, -0.15, 'Observed\nNo Exceedance', fontsize=11, fontweight='bold',
            ha='center', va='top')

    # Y-axis labels (left of grid)
    ax.text(-0.15, 1.5, 'AQM\nExceedance', fontsize=11, fontweight='bold',
            ha='right', va='center', rotation=0)
    ax.text(-0.15, 0.5, 'AQM\nNo Exceedance', fontsize=11, fontweight='bold',
            ha='right', va='center', rotation=0)

    # Metrics text box (right side)
    metrics_text = (
        f'POD:      {pod:.2f}\n'
        f'FAR:      {far:.2f}\n'
        f'CSI:      {csi:.2f}\n'
        f'Accuracy: {accuracy:.2f}'
    )
    props = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', alpha=0.9)
    ax.text(2.4, 1.0, metrics_text, fontsize=12, fontfamily='monospace',
            ha='left', va='center', bbox=props)

    # Title and subtitle
    fig.suptitle('Contingency Table: Exceedance Prediction (>70 ppb)',
                 fontsize=14, fontweight='bold')
    ax.set_title(f'5 Winter Seasons, n={total} days', fontsize=11, pad=15)

    # Adjust layout to prevent clipping
    plt.subplots_adjust(left=0.15, right=0.85, top=0.82, bottom=0.1)

    # Save figure
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / 'contingency_table.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    # Print summary
    print(f'\nContingency Table Summary:')
    print(f'  Hits:              {hits}')
    print(f'  False Alarms:      {false_alarms}')
    print(f'  Misses:            {misses}')
    print(f'  Correct Negatives: {correct_negatives}')
    print(f'  Total:             {total}')
    print(f'\nPerformance Metrics:')
    print(f'  POD:      {pod:.3f}')
    print(f'  FAR:      {far:.3f}')
    print(f'  CSI:      {csi:.3f}')
    print(f'  Accuracy: {accuracy:.3f}')


if __name__ == '__main__':
    main()
