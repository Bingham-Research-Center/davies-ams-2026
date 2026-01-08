"""
Conditional Bias Bar Chart

Bar chart showing mean model bias (AQM minus observed) binned by observed
ozone concentration. Highlights underprediction at high ozone levels.
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

# Paths
DATA_PATH = Path(__file__).parent.parent / 'data' / 'all_matched_obs_aqm.parquet'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'


def load_and_process_data() -> pl.DataFrame:
    """Load matched data and calculate bias."""
    df = pl.read_parquet(DATA_PATH)

    # Calculate bias: AQM - observed
    df = df.with_columns([
        (pl.col('aqm_max') - pl.col('obs_mda8')).alias('bias')
    ])

    return df


def bin_data(df: pl.DataFrame) -> pl.DataFrame:
    """Bin data by observed ozone concentration and calculate statistics."""
    # Filter out values below 20 ppb
    df = df.filter(pl.col('obs_mda8') >= 20)

    # Create bin column using when/then/otherwise
    df = df.with_columns([
        pl.when(pl.col('obs_mda8') < 40).then(pl.lit('20-40'))
        .when(pl.col('obs_mda8') < 50).then(pl.lit('40-50'))
        .when(pl.col('obs_mda8') < 60).then(pl.lit('50-60'))
        .when(pl.col('obs_mda8') < 70).then(pl.lit('60-70'))
        .when(pl.col('obs_mda8') < 80).then(pl.lit('70-80'))
        .when(pl.col('obs_mda8') < 90).then(pl.lit('80-90'))
        .otherwise(pl.lit('90+'))
        .alias('obs_bin')
    ])

    # Group by bin and calculate statistics
    stats = df.group_by('obs_bin').agg([
        pl.col('bias').mean().alias('mean_bias'),
        pl.col('bias').std().alias('std_bias'),
        pl.col('bias').count().alias('n')
    ])

    # Add bin order for sorting
    bin_labels = ['20-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90+']
    bin_order = {label: i for i, label in enumerate(bin_labels)}
    stats = stats.with_columns([
        pl.col('obs_bin').replace_strict(bin_order).alias('bin_order')
    ])
    stats = stats.sort('bin_order')

    return stats


def create_plot(stats: pl.DataFrame) -> None:
    """Create the conditional bias bar chart."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Extract data
    bins = stats['obs_bin'].to_list()
    means = stats['mean_bias'].to_numpy()
    stds = stats['std_bias'].to_numpy()
    counts = stats['n'].to_list()

    # Bar positions
    x = np.arange(len(bins))

    # Determine bar colors based on bias sign
    colors = ['coral' if m >= 0 else 'steelblue' for m in means]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))

    # Plot bars
    bars = ax.bar(x, means, color=colors, edgecolor='black', linewidth=1.0, zorder=3)

    # Add error bars
    ax.errorbar(x, means, yerr=stds, fmt='none', color='black', capsize=5,
                capthick=1.5, linewidth=1.5, zorder=4)

    # Horizontal line at zero
    ax.axhline(y=0, color='black', linewidth=1.5, zorder=2)

    # Vertical dashed red line between 60-70 and 70-80 bins (index 3 and 4)
    # Position it at x = 3.5 (between index 3 and 4)
    ax.axvline(x=3.5, color='red', linestyle='--', linewidth=2, zorder=2)

    # Add stats labels above error bars (n, mean, std)
    for i, (mean, std, n) in enumerate(zip(means, stds, counts)):
        # Position label above the error bar
        y_pos = mean + std + 2 if mean >= 0 else mean - std - 2
        va = 'bottom' if mean >= 0 else 'top'
        # Format: n=X, bias: mean, std: ±value
        mean_str = f'{mean:+.1f}' if mean != 0 else '0.0'
        label = f'n={n}\nbias: {mean_str}\nstd: ±{std:.1f}'
        ax.text(i, y_pos, label, ha='center', va=va, fontsize=8)

    # Labels and title
    ax.set_xticks(x)
    ax.set_xticklabels(bins, fontsize=11)
    ax.set_xlabel('Observed MDA8 Ozone (ppb)', fontsize=12)
    ax.set_ylabel('Mean Bias (ppb)', fontsize=12)

    # Title and subtitle
    fig.suptitle('Conditional Bias by Observed Concentration', fontsize=14, fontweight='bold', y=0.96)
    ax.set_title(r'AQM Underpredicts High O$_3$ Events', fontsize=11, style='italic', pad=10)

    # Grid
    ax.grid(True, axis='y', alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # Adjust y-axis limits to accommodate stat labels
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(y_min - 15, y_max + 10)

    # Add legend at bottom
    overpred_patch = mpatches.Patch(color='coral', label='Overprediction (AQM > Obs)')
    underpred_patch = mpatches.Patch(color='steelblue', label='Underprediction (AQM < Obs)')
    fig.legend(handles=[overpred_patch, underpred_patch], loc='lower center',
               ncol=2, fontsize=10, framealpha=0.9, bbox_to_anchor=(0.5, 0.02))

    # Tight layout with space for legend
    plt.tight_layout(rect=[0, 0.08, 1, 0.94])

    # Save figure
    output_path = OUTPUT_DIR / 'conditional_bias.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    plt.close(fig)


def main():
    """Main function."""
    print('Loading and processing data...')
    df = load_and_process_data()

    print('Binning data by observed concentration...')
    stats = bin_data(df)

    print('Bin statistics:')
    print(stats)

    print('Creating plot...')
    create_plot(stats)


if __name__ == '__main__':
    main()
