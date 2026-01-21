#!/usr/bin/env python3
"""
Figure 4: GFS Systematic Snow Depth Underestimation
Shows the physical root cause of AQM failure - GFS snow depth bias.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import polars as pl
from scipy import stats

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'
CACHE_DIR = DATA_DIR / 'gfs_cache'

WINTERS = ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']


def aggregate_daily_snow(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate sub-hourly/hourly snow to daily values per station."""
    df = df.with_columns([
        pl.col('date_time').dt.date().alias('date')
    ])
    daily = df.group_by(['stid', 'date']).agg([
        pl.col('value').median().alias('snow_depth_mm')
    ])
    daily = daily.with_columns([
        (pl.col('snow_depth_mm') / 10.0).alias('snow_depth_cm')
    ])
    daily = daily.filter(
        (pl.col('snow_depth_cm') <= 200) &
        (pl.col('snow_depth_cm') >= 0)
    )
    return daily


def compute_basin_average(daily_df: pl.DataFrame) -> pl.DataFrame:
    """Compute basin-average snow depth from station data."""
    basin_avg = daily_df.group_by('date').agg([
        pl.col('snow_depth_cm').mean().round(2).alias('obs_snow_cm'),
        pl.col('stid').n_unique().alias('n_stations')
    ])
    return basin_avg.sort('date')


def load_observed_snow() -> pl.DataFrame:
    """Load and process all winter snow data files."""
    all_daily = []
    for winter in WINTERS:
        path = DATA_DIR / f'winter{winter}_snow.parquet'
        if not path.exists():
            print(f'  Warning: {path.name} not found, skipping')
            continue
        df = pl.read_parquet(path)
        snow = df.filter(pl.col('variable') == 'snow_depth')
        if len(snow) == 0:
            continue
        daily = aggregate_daily_snow(snow)
        all_daily.append(daily)

    if not all_daily:
        raise ValueError('No snow data found')

    all_daily_df = pl.concat(all_daily)
    basin_avg = compute_basin_average(all_daily_df)
    return basin_avg


def load_gfs_cache() -> dict:
    """Load cached GFS snow values."""
    import json
    cache_path = CACHE_DIR / 'gfs_snow.json'
    if not cache_path.exists():
        raise FileNotFoundError(f'GFS cache not found at {cache_path}. Run compare_gfs_snow.py first.')
    with open(cache_path) as f:
        return json.load(f)


def merge_data(gfs_data: dict, obs_df: pl.DataFrame) -> pl.DataFrame:
    """Merge GFS and observed data."""
    from datetime import date
    gfs_records = [
        {'date': date.fromisoformat(k), 'gfs_snow_cm': v}
        for k, v in gfs_data.items()
        if v is not None
    ]
    gfs_df = pl.DataFrame(gfs_records)
    merged = gfs_df.join(obs_df, on='date', how='inner')
    merged = merged.with_columns([
        (pl.col('gfs_snow_cm') - pl.col('obs_snow_cm')).alias('error_cm'),
    ])
    # Filter to days with observed snow > 0
    merged = merged.filter(pl.col('obs_snow_cm') > 0)
    return merged.sort('date')


def create_poster_figure(df: pl.DataFrame) -> None:
    """Create poster-quality scatter plot of GFS vs observed snow depth."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Extract data - Observed on X, GFS on Y (intuitive: below line = underestimate)
    obs = df['obs_snow_cm'].to_numpy()
    gfs = df['gfs_snow_cm'].to_numpy()
    error = df['error_cm'].to_numpy()

    # Calculate statistics
    slope, intercept, r_value, p_value, std_err = stats.linregress(obs, gfs)
    pct_under = np.sum(error < 0) / len(error) * 100

    # Deep snow statistics (observed > 20 cm)
    deep_mask = obs > 20
    deep_mean_error = np.mean(error[deep_mask]) if deep_mask.sum() > 0 else 0

    # Create square figure (9" x 9")
    fig, ax = plt.subplots(figsize=(9, 9))

    # Determine axis limits
    max_val = 45

    # Shaded underestimation zone (below 1:1 line)
    ax.fill_between([0, max_val], [0, 0], [0, max_val],
                    color='#ffe0e0', alpha=0.4, zorder=1)

    # Scatter plot
    ax.scatter(obs, gfs, alpha=0.5, s=60, c='#2171b5', edgecolors='none', zorder=3)

    # 1:1 reference line
    ax.plot([0, max_val], [0, max_val], 'k--', linewidth=2, zorder=4)

    # Regression line
    x_line = np.linspace(0, 40, 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, '#d62728', linewidth=3, zorder=4)

    # Key annotation - single prominent callout (top left, out of the way)
    ax.text(0.04, 0.96, f'{pct_under:.0f}% Underestimation',
            transform=ax.transAxes, fontsize=20, fontweight='bold',
            color='#c00000', ha='left', va='top')

    # Secondary info below
    ax.text(0.04, 0.88, f'Deep snow (>20cm): {deep_mean_error:.0f} cm bias',
            transform=ax.transAxes, fontsize=12, color='#444',
            ha='left', va='top')

    # Sample size and correlation
    ax.text(0.04, 0.81, f'n = {len(obs):,}  |  r = {r_value:.2f}',
            transform=ax.transAxes, fontsize=11, color='#666',
            ha='left', va='top')

    # Line label - just 1:1
    ax.text(40, 42, '1:1', fontsize=11, color='#555', rotation=45, va='bottom')

    # Axis labels
    ax.set_xlabel('Observed Snow Depth (cm)', fontsize=15, fontweight='bold')
    ax.set_ylabel('GFS Snow Depth (cm)', fontsize=15, fontweight='bold')

    # Title
    ax.set_title('GFS Systematic Snow Underestimation',
                 fontsize=18, fontweight='bold', pad=15)

    # Axis formatting
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.set_aspect('equal', adjustable='box')
    ax.tick_params(axis='both', labelsize=12)

    # Minimal grid
    ax.grid(True, alpha=0.2, linestyle='-', zorder=0)

    # Clean spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / 'figure4_gfs_snow_bias_poster.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f'Saved: {output_path}')
    plt.close(fig)


def main():
    print('=' * 60)
    print('Figure 4: GFS Snow Depth Underestimation')
    print('=' * 60)

    print('\n[1/3] Loading observed snow data...')
    obs_df = load_observed_snow()
    print(f'  Loaded {len(obs_df)} days of basin-average snow')

    print('\n[2/3] Loading GFS cache...')
    gfs_data = load_gfs_cache()
    print(f'  Loaded {len(gfs_data)} days from cache')

    print('\n[3/3] Creating poster figure...')
    merged = merge_data(gfs_data, obs_df)
    print(f'  {len(merged)} matched days with observed snow > 0')
    create_poster_figure(merged)

    # Print key statistics for reference
    gfs = merged['gfs_snow_cm'].to_numpy()
    obs = merged['obs_snow_cm'].to_numpy()
    error = merged['error_cm'].to_numpy()
    pct_under = np.sum(error < 0) / len(error) * 100

    print(f'\nKey statistics:')
    print(f'  Underestimation rate: {pct_under:.0f}%')
    print(f'  Mean bias: {np.mean(error):.1f} cm')
    print(f'  RMSE: {np.sqrt(np.mean(error**2)):.1f} cm')

    # Deep snow
    deep_mask = obs > 20
    if deep_mask.sum() > 0:
        print(f'  Deep snow (>20cm) error: {np.mean(error[deep_mask]):.1f} cm (n={deep_mask.sum()})')

    print('\nDone!')


if __name__ == '__main__':
    main()
