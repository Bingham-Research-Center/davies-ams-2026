"""
Analyze the relationship between snow depth and AQM bias.

Creates scatter plots and binned analysis showing how AQM bias
varies with basin-averaged snow depth.
"""
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy import stats

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'
AQM_DATA_PATH = DATA_DIR / 'all_matched_obs_aqm.parquet'

# All winters
WINTERS = ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']


def aggregate_daily_snow(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate sub-hourly/hourly snow to daily values per station.

    Uses median to be robust against sensor outliers.
    Value is already in cm (Synoptic API returns cm for snow_depth).
    """
    df = df.with_columns([
        pl.col('date_time').dt.date().alias('date')
    ])

    # Use median for robustness against sensor outliers
    daily = df.group_by(['stid', 'date']).agg([
        pl.col('value').median().alias('snow_depth_cm')
    ])

    # Filter out unreasonable values (> 200 cm is implausible)
    daily = daily.filter(
        (pl.col('snow_depth_cm') <= 200) &
        (pl.col('snow_depth_cm') >= 0)
    )

    return daily


def compute_basin_average(daily_df: pl.DataFrame) -> pl.DataFrame:
    """Compute basin-average snow depth from station data."""
    basin_avg = daily_df.group_by('date').agg([
        pl.col('snow_depth_cm').mean().round(2).alias('basin_avg_snow_cm'),
        pl.col('stid').n_unique().alias('n_stations')
    ])

    return basin_avg.sort('date')


def load_snow_data() -> pl.DataFrame:
    """Load and process all winter snow data files."""
    all_daily = []

    for winter in WINTERS:
        path = DATA_DIR / f'winter{winter}_snow.parquet'
        if not path.exists():
            print(f"  Warning: {path.name} not found, skipping")
            continue

        print(f"  Processing {path.name}...")
        df = pl.read_parquet(path)

        # Filter for snow_depth variable only
        snow = df.filter(pl.col('variable') == 'snow_depth')

        if len(snow) == 0:
            print(f"    No snow_depth observations in {winter}")
            continue

        # Aggregate to daily values
        daily = aggregate_daily_snow(snow)
        all_daily.append(daily)
        print(f"    Found {len(daily)} station-days")

    if not all_daily:
        raise ValueError("No snow data found")

    # Concatenate all winters
    all_daily_df = pl.concat(all_daily)

    # Compute basin average
    basin_avg = compute_basin_average(all_daily_df)

    return basin_avg


def merge_snow_with_aqm(snow_df: pl.DataFrame, aqm_df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Merge snow with AQM data and calculate bias. Returns (all_days, exceedance_only)."""
    # Calculate bias
    aqm_df = aqm_df.with_columns([
        (pl.col('aqm_max') - pl.col('obs_mda8')).alias('bias')
    ])

    # Filter out rows with null obs_mda8 (can't calculate meaningful bias)
    aqm_df = aqm_df.filter(pl.col('obs_mda8').is_not_null())

    # Join on date
    all_days = aqm_df.join(snow_df, on='date', how='inner')

    # Filter to exceedance days only (obs >= 70 ppb)
    exceedance_only = all_days.filter(pl.col('obs_mda8') >= 70)

    return all_days, exceedance_only


def create_scatter_plot(all_days: pl.DataFrame, exceedance: pl.DataFrame) -> None:
    """Create side-by-side scatter plots comparing all days vs exceedance days."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    datasets = [
        (all_days, 'All Days', axes[0]),
        (exceedance, 'Exceedance Days (Obs >= 70 ppb)', axes[1])
    ]

    for df, title, ax in datasets:
        # Extract data
        snow = df['basin_avg_snow_cm'].to_numpy()
        bias = df['bias'].to_numpy()

        # Remove NaN values
        mask = ~np.isnan(snow) & ~np.isnan(bias)
        snow = snow[mask]
        bias = bias[mask]

        # Calculate regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(snow, bias)

        # Scatter plot
        ax.scatter(snow, bias, alpha=0.4, s=30, c='steelblue', edgecolors='none')

        # Regression line
        x_line = np.linspace(snow.min(), snow.max(), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'r={r_value:.3f}')

        # Zero bias reference line
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1.5, alpha=0.7)

        # Labels
        ax.set_xlabel('Basin-Average Snow Depth (cm)', fontsize=11)
        ax.set_ylabel('Bias (ppb): AQM - Observed', fontsize=11)
        ax.set_title(f'{title}\nn={len(snow):,}, r={r_value:.3f}, mean bias={bias.mean():.1f} ppb', fontsize=11)

        # Grid and legend
        ax.grid(True, alpha=0.3)
        ax.legend(loc='lower left')

    fig.suptitle('Snow Depth vs. AQM Bias', fontsize=14, fontweight='bold')
    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / 'snow_bias_scatter.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def create_binned_plot(all_days: pl.DataFrame, exceedance: pl.DataFrame) -> None:
    """Create side-by-side bar charts comparing all days vs exceedance days."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))

    bin_order = {'0-2': 0, '2-5': 1, '5-10': 2, '10-20': 3, '20+': 4}

    datasets = [
        (all_days, 'All Days', axes[0]),
        (exceedance, 'Exceedance Days (Obs >= 70 ppb)', axes[1])
    ]

    for df, title, ax in datasets:
        # Define bins
        df = df.with_columns([
            pl.when(pl.col('basin_avg_snow_cm') < 2).then(pl.lit('0-2'))
            .when(pl.col('basin_avg_snow_cm') < 5).then(pl.lit('2-5'))
            .when(pl.col('basin_avg_snow_cm') < 10).then(pl.lit('5-10'))
            .when(pl.col('basin_avg_snow_cm') < 20).then(pl.lit('10-20'))
            .otherwise(pl.lit('20+'))
            .alias('snow_bin')
        ])

        # Calculate statistics per bin
        bin_stats = df.group_by('snow_bin').agg([
            pl.col('bias').mean().alias('mean_bias'),
            pl.col('bias').std().alias('std_bias'),
            pl.col('bias').count().alias('n')
        ])

        bin_stats = bin_stats.with_columns([
            pl.col('snow_bin').replace_strict(bin_order).alias('bin_order')
        ]).sort('bin_order')

        # Extract data
        bins = bin_stats['snow_bin'].to_list()
        means = bin_stats['mean_bias'].to_numpy()
        stds = bin_stats['std_bias'].to_numpy()
        counts = bin_stats['n'].to_list()

        x = np.arange(len(bins))
        colors = ['coral' if m >= 0 else 'steelblue' for m in means]

        # Plot bars
        ax.bar(x, means, color=colors, edgecolor='black', linewidth=1.0, zorder=3)

        # Error bars
        ax.errorbar(x, means, yerr=stds, fmt='none', color='black', capsize=5,
                    capthick=1.5, linewidth=1.5, zorder=4)

        # Zero line
        ax.axhline(y=0, color='black', linewidth=1.5, zorder=2)

        # Annotations
        for i, (mean, std, n) in enumerate(zip(means, stds, counts)):
            y_pos = mean + std + 2 if mean >= 0 else mean - std - 2
            va = 'bottom' if mean >= 0 else 'top'
            mean_str = f'{mean:+.1f}' if mean != 0 else '0.0'
            label = f'n={n}\n{mean_str}'
            ax.text(i, y_pos, label, ha='center', va=va, fontsize=9)

        # Labels
        ax.set_xticks(x)
        ax.set_xticklabels([f'{b}' for b in bins], fontsize=10)
        ax.set_xlabel('Snow Depth (cm)', fontsize=11)
        ax.set_ylabel('Mean Bias (ppb)', fontsize=11)
        ax.set_title(title, fontsize=11)

        # Grid
        ax.grid(True, axis='y', alpha=0.3, zorder=0)
        ax.set_axisbelow(True)

        # Adjust y-axis limits
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(y_min - 10, y_max + 8)

    fig.suptitle('AQM Bias by Snow Depth', fontsize=14, fontweight='bold')

    # Legend
    overpred = mpatches.Patch(color='coral', label='Overprediction')
    underpred = mpatches.Patch(color='steelblue', label='Underprediction')
    fig.legend(handles=[overpred, underpred], loc='lower center',
               ncol=2, fontsize=10, framealpha=0.9, bbox_to_anchor=(0.5, 0.02))

    plt.tight_layout(rect=[0, 0.06, 1, 0.94])

    # Save
    output_path = OUTPUT_DIR / 'snow_bias_binned.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def print_summary_statistics(df: pl.DataFrame) -> None:
    """Print summary statistics to console."""
    print('\n' + '='*60)
    print('SUMMARY STATISTICS')
    print('='*60)

    # Overall stats
    n_total = len(df)
    n_days = df['date'].n_unique()

    print(f'\nDataset size:')
    print(f'  Total records: {n_total:,}')
    print(f'  Unique days: {n_days}')

    # Snow depth stats
    snow = df['basin_avg_snow_cm']
    print(f'\nSnow depth (cm):')
    print(f'  Mean: {snow.mean():.2f}')
    print(f'  Median: {snow.median():.2f}')
    print(f'  Std: {snow.std():.2f}')
    print(f'  Min: {snow.min():.2f}')
    print(f'  Max: {snow.max():.2f}')

    # Bias stats
    bias = df['bias']
    print(f'\nBias (ppb):')
    print(f'  Mean: {bias.mean():.2f}')
    print(f'  Median: {bias.median():.2f}')
    print(f'  Std: {bias.std():.2f}')
    print(f'  Min: {bias.min():.2f}')
    print(f'  Max: {bias.max():.2f}')


def main():
    """Main function."""
    print('='*60)
    print('SNOW DEPTH vs AQM BIAS ANALYSIS')
    print('='*60)

    # Load AQM data
    print('\n[1/4] Loading AQM verification data...')
    aqm_df = pl.read_parquet(AQM_DATA_PATH)
    print(f'  Loaded {len(aqm_df)} matched obs/AQM records')

    # Load and process snow data
    print('\n[2/4] Loading and processing snow data...')
    snow_df = load_snow_data()
    print(f'  Basin-average snow depth for {len(snow_df)} days')

    # Merge datasets
    print('\n[3/4] Merging snow with AQM data...')
    all_days, exceedance = merge_snow_with_aqm(snow_df, aqm_df)
    print(f'  All days: {len(all_days)} records')
    print(f'  Exceedance days: {len(exceedance)} records')

    # Print summary for both
    print('\n--- ALL DAYS ---')
    print_summary_statistics(all_days)
    print('\n--- EXCEEDANCE DAYS ONLY ---')
    print_summary_statistics(exceedance)

    # Create visualizations
    print('\n[4/4] Creating visualizations...')
    create_scatter_plot(all_days, exceedance)
    create_binned_plot(all_days, exceedance)

    print('\nDone!')


if __name__ == '__main__':
    main()
