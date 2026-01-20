"""
Conditional Bias Bar Chart

Bar chart showing mean model bias binned by observed ozone concentration.
Compares AQM and CLYFAR p50 side-by-side for the overlapping period (winter 2022-23).
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy import stats

from verification_metrics import THRESHOLD

# Paths
DATA_PATH = Path(__file__).parent.parent / 'data' / 'all_matched_obs_aqm.parquet'
AQM_FXX24_PATH = Path(__file__).parent.parent / 'data' / 'winter2022-23_aqm_fxx24.parquet'
CLYFAR_PATH = Path(__file__).parent.parent / 'data' / 'clyfar_hindcast_stats.csv'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'


def load_and_process_data() -> pl.DataFrame:
    """Load AQM fxx=24 and CLYFAR data, merge on date, filter to overlap period.

    Uses AQM Day 1 forecasts (fxx=24) for fair comparison with CLYFAR's ~24h lead time.
    Returns merged DataFrame with both AQM and CLYFAR biases calculated.
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

    # Merge on date (CLYFAR is basin-wide, replicates across stations)
    df = df.join(clyfar.select(['date', 'forecast_p50']), on='date', how='inner')

    # Filter to winter 2022-23 (overlap period)
    df = df.filter(pl.col('winter') == '2022-23')

    # Calculate biases: model - observed
    df = df.with_columns([
        (pl.col('aqm_max') - pl.col('obs_mda8')).alias('aqm_bias'),
        (pl.col('forecast_p50') - pl.col('obs_mda8')).alias('clyfar_bias')
    ])

    return df


def bin_data(df: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, dict[str, np.ndarray]]]:
    """Bin data by observed ozone concentration and calculate statistics for both models.

    Returns:
        Tuple of (stats DataFrame, dict mapping bin label to {'aqm': array, 'clyfar': array})
    """
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

    # Collect raw bias values for each bin (for significance testing)
    bin_labels = ['20-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90+']
    raw_bias_by_bin = {}
    for label in bin_labels:
        bin_df = df.filter(pl.col('obs_bin') == label)
        raw_bias_by_bin[label] = {
            'aqm': bin_df['aqm_bias'].to_numpy(),
            'clyfar': bin_df['clyfar_bias'].to_numpy()
        }

    # Group by bin and calculate statistics for both models
    bin_stats = df.group_by('obs_bin').agg([
        pl.col('aqm_bias').mean().alias('aqm_mean'),
        pl.col('aqm_bias').std().alias('aqm_std'),
        pl.col('clyfar_bias').mean().alias('clyfar_mean'),
        pl.col('clyfar_bias').std().alias('clyfar_std'),
        pl.col('aqm_bias').count().alias('n')
    ])

    # Add bin order for sorting
    bin_order = {label: i for i, label in enumerate(bin_labels)}
    bin_stats = bin_stats.with_columns([
        pl.col('obs_bin').replace_strict(bin_order).alias('bin_order')
    ])
    bin_stats = bin_stats.sort('bin_order')

    return bin_stats, raw_bias_by_bin


def create_plot(bin_stats: pl.DataFrame, raw_bias_by_bin: dict[str, dict[str, np.ndarray]]) -> None:
    """Create grouped conditional bias bar chart comparing AQM and CLYFAR p50.

    Args:
        bin_stats: DataFrame with bias stats per bin for both models
        raw_bias_by_bin: Dict mapping bin labels to {'aqm': array, 'clyfar': array}
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Extract data
    bins = bin_stats['obs_bin'].to_list()
    aqm_means = bin_stats['aqm_mean'].to_numpy()
    aqm_stds = bin_stats['aqm_std'].to_numpy()
    clyfar_means = bin_stats['clyfar_mean'].to_numpy()
    clyfar_stds = bin_stats['clyfar_std'].to_numpy()
    counts = bin_stats['n'].to_list()

    # Bar positions and width
    x = np.arange(len(bins))
    bar_width = 0.35

    # Calculate significance for each bin (one-sample t-test: is bias != 0?)
    aqm_p_values = []
    clyfar_p_values = []
    for bin_label in bins:
        aqm_bias = raw_bias_by_bin.get(bin_label, {}).get('aqm', np.array([]))
        clyfar_bias = raw_bias_by_bin.get(bin_label, {}).get('clyfar', np.array([]))

        if len(aqm_bias) > 2:
            _, p_val = stats.ttest_1samp(aqm_bias, 0)
            aqm_p_values.append(p_val)
        else:
            aqm_p_values.append(1.0)

        if len(clyfar_bias) > 2:
            _, p_val = stats.ttest_1samp(clyfar_bias, 0)
            clyfar_p_values.append(p_val)
        else:
            clyfar_p_values.append(1.0)

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot AQM bars (red tones)
    aqm_colors = ['indianred' if m >= 0 else 'lightcoral' for m in aqm_means]
    ax.bar(x - bar_width/2, aqm_means, bar_width, color=aqm_colors,
           edgecolor='darkred', linewidth=1.0, label='AQM (Day 1)', zorder=3)
    ax.errorbar(x - bar_width/2, aqm_means, yerr=aqm_stds, fmt='none',
                color='darkred', capsize=4, capthick=1.2, linewidth=1.2, zorder=4)

    # Plot CLYFAR bars (blue tones)
    clyfar_colors = ['steelblue' if m >= 0 else 'lightsteelblue' for m in clyfar_means]
    ax.bar(x + bar_width/2, clyfar_means, bar_width, color=clyfar_colors,
           edgecolor='darkblue', linewidth=1.0, label='CLYFAR p50', zorder=3)
    ax.errorbar(x + bar_width/2, clyfar_means, yerr=clyfar_stds, fmt='none',
                color='darkblue', capsize=4, capthick=1.2, linewidth=1.2, zorder=4)

    # Horizontal line at zero
    ax.axhline(y=0, color='black', linewidth=1.5, zorder=2)

    # Vertical dashed line at threshold boundary (between 60-70 and 70-80)
    threshold_idx = bins.index('60-70') if '60-70' in bins else 3
    ax.axvline(x=threshold_idx + 0.5, color='gray', linestyle='--', linewidth=2, zorder=2)
    ax.text(threshold_idx + 0.55, ax.get_ylim()[1] * 0.9, '70 ppb\nthreshold',
            fontsize=9, va='top', ha='left', color='gray')

    # Add count labels and significance markers
    def sig_marker(p_val):
        if p_val < 0.001:
            return '***'
        elif p_val < 0.01:
            return '**'
        elif p_val < 0.05:
            return '*'
        return ''

    for i, (n, aqm_m, aqm_s, aqm_p, clf_m, clf_s, clf_p) in enumerate(
            zip(counts, aqm_means, aqm_stds, aqm_p_values, clyfar_means, clyfar_stds, clyfar_p_values)):
        # AQM label
        aqm_y = aqm_m + aqm_s + 1 if aqm_m >= 0 else aqm_m - aqm_s - 1
        aqm_va = 'bottom' if aqm_m >= 0 else 'top'
        ax.text(i - bar_width/2, aqm_y, f'{aqm_m:+.1f}{sig_marker(aqm_p)}',
                ha='center', va=aqm_va, fontsize=7, color='darkred')

        # CLYFAR label
        clf_y = clf_m + clf_s + 1 if clf_m >= 0 else clf_m - clf_s - 1
        clf_va = 'bottom' if clf_m >= 0 else 'top'
        ax.text(i + bar_width/2, clf_y, f'{clf_m:+.1f}{sig_marker(clf_p)}',
                ha='center', va=clf_va, fontsize=7, color='darkblue')

        # Count label below
        ax.text(i, ax.get_ylim()[0] + 2, f'n={n}', ha='center', va='bottom', fontsize=8)

    # Labels and title
    ax.set_xticks(x)
    ax.set_xticklabels(bins, fontsize=11)
    ax.set_xlabel('Observed MDA8 Ozone (ppb)', fontsize=12)
    ax.set_ylabel('Mean Bias (ppb)', fontsize=12)

    # Title and subtitle
    fig.suptitle('Conditional Bias: AQM vs CLYFAR p50 (24h Lead)', fontsize=14, fontweight='bold', y=0.96)
    ax.set_title('Winter 2022-23 Comparison (* p<0.05, ** p<0.01, *** p<0.001)',
                 fontsize=11, style='italic', pad=10)

    # Grid
    ax.grid(True, axis='y', alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # Dynamic y-axis adjustment
    all_stds = np.concatenate([aqm_stds, clyfar_stds])
    max_err = max(all_stds) if len(all_stds) > 0 else 0
    padding = max(max_err * 1.8, 12)
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(y_min - padding, y_max + padding)

    # Legend
    aqm_patch = mpatches.Patch(facecolor='indianred', edgecolor='darkred', label='AQM (Day 1)')
    clyfar_patch = mpatches.Patch(facecolor='steelblue', edgecolor='darkblue', label='CLYFAR p50')
    ax.legend(handles=[aqm_patch, clyfar_patch], loc='upper right', fontsize=10, framealpha=0.9)

    # Tight layout
    plt.tight_layout(rect=[0, 0.02, 1, 0.94])

    # Save figure
    output_path = OUTPUT_DIR / 'conditional_bias.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    plt.close(fig)


def main():
    """Main function."""
    print('Loading and processing data...')
    df = load_and_process_data()
    print(f'Loaded {len(df)} station-day pairs for winter 2022-23')

    print('Binning data by observed concentration...')
    bin_stats, raw_bias_by_bin = bin_data(df)

    print('Bin statistics:')
    print(bin_stats)

    print('Creating plot...')
    create_plot(bin_stats, raw_bias_by_bin)


if __name__ == '__main__':
    main()
