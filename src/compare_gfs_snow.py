#!/usr/bin/env python3
"""
Compare GFS snow depth estimates vs. observed snow depth from Synoptic stations.

Creates:
1. Scatter plot with 1:1 line and statistics (gfs_snow_scatter.png)
2. Error histogram showing GFS bias distribution (gfs_snow_error_histogram.png)
3. Summary statistics table to console

Usage:
    python src/compare_gfs_snow.py [--force-refetch]
"""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy import stats

# === CONFIGURATION ===
DATA_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'
CACHE_DIR = DATA_DIR / 'gfs_cache'

# Basin center coordinates for GFS extraction
BASIN_LAT = 40.0
BASIN_LON = 360 - 109.5  # 250.5 in 0-360 notation for GFS

# Winter definition
WINTERS = ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']


# === UTILITY FUNCTIONS ===

def parse_winter(winter: str) -> tuple[date, date]:
    """Convert winter string (e.g., '2022-23') to start and end dates."""
    start_year, end_suffix = winter.split('-')
    start_year = int(start_year)
    end_year = int(f'20{end_suffix}')
    return date(start_year, 12, 1), date(end_year, 3, 31)


def get_winter_dates() -> list[date]:
    """Generate all dates across all winters (Dec 1 - Mar 31)."""
    all_dates = []
    for winter in WINTERS:
        start, end = parse_winter(winter)
        current = start
        while current <= end:
            all_dates.append(current)
            current += timedelta(days=1)
    return all_dates


# === CACHING ===

def load_gfs_cache() -> dict[str, float | None]:
    """Load cached GFS snow values from JSON file."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / 'gfs_snow.json'
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print('  Warning: Cache corrupted, starting fresh')
        return {}


def save_gfs_cache(cache: dict[str, float | None]) -> None:
    """Save GFS snow values to JSON cache file (atomic write)."""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / 'gfs_snow.json'
    temp_path = cache_path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(cache, f, indent=2)
    temp_path.rename(cache_path)


# === GFS DATA ===

def get_gfs_snow_single(d: date) -> float | None:
    """Fetch GFS snow depth for a single date via Herbie.

    Returns snow depth in cm, or None on failure.
    """
    try:
        from herbie import Herbie
        H = Herbie(f'{d} 12:00', model='gfs', product='pgrb2.0p25', fxx=0, verbose=False)
        ds = H.xarray(':SNOD:surface')
        val_m = float(ds['sde'].sel(latitude=BASIN_LAT, longitude=BASIN_LON, method='nearest').values)
        return val_m * 100  # Convert m to cm
    except Exception:
        return None


def fetch_all_gfs_snow(dates: list[date], cache: dict, force: bool = False) -> dict[str, float | None]:
    """Fetch GFS data for all dates with progress tracking and caching."""
    success_count = 0
    fail_count = 0
    cached_count = 0

    for i, d in enumerate(dates):
        date_str = str(d)

        # Check cache (skip if already fetched, unless forcing)
        if date_str in cache and not force:
            cached_count += 1
            continue

        val = get_gfs_snow_single(d)
        cache[date_str] = val

        if val is not None:
            success_count += 1
        else:
            fail_count += 1

        # Progress update every 50 dates
        if (i + 1) % 50 == 0:
            print(f'  Progress: {i + 1}/{len(dates)} '
                  f'({success_count} fetched, {fail_count} failed, {cached_count} cached)')

        # Save cache every 100 dates
        if (i + 1) % 100 == 0:
            save_gfs_cache(cache)

    # Final save
    save_gfs_cache(cache)

    total_fetched = success_count + fail_count
    if total_fetched > 0:
        print(f'  Fetched {success_count} new dates, {fail_count} failed, {cached_count} from cache')
    else:
        print(f'  All {cached_count} dates loaded from cache')

    return cache


# === OBSERVED DATA ===

def aggregate_daily_snow(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate sub-hourly/hourly snow to daily values per station.

    Uses median to be robust against sensor outliers.
    Synoptic API returns mm for snow_depth, converted to cm here.
    """
    df = df.with_columns([
        pl.col('date_time').dt.date().alias('date')
    ])

    # Use median for robustness against sensor outliers
    daily = df.group_by(['stid', 'date']).agg([
        pl.col('value').median().alias('snow_depth_mm')
    ])

    # Convert mm to cm
    daily = daily.with_columns([
        (pl.col('snow_depth_mm') / 10.0).alias('snow_depth_cm')
    ])

    # Filter out unreasonable values (> 200 cm is implausible for Basin)
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

        # Filter for snow_depth variable only
        snow = df.filter(pl.col('variable') == 'snow_depth')

        if len(snow) == 0:
            continue

        # Aggregate to daily values
        daily = aggregate_daily_snow(snow)
        all_daily.append(daily)

    if not all_daily:
        raise ValueError('No snow data found')

    # Concatenate all winters
    all_daily_df = pl.concat(all_daily)

    # Compute basin average
    basin_avg = compute_basin_average(all_daily_df)

    return basin_avg


# === ANALYSIS ===

def merge_gfs_obs(gfs_data: dict[str, float | None], obs_df: pl.DataFrame) -> pl.DataFrame:
    """Merge GFS and observed data, calculate error metrics."""
    # Convert GFS dict to DataFrame (exclude None values)
    gfs_records = [
        {'date': date.fromisoformat(k), 'gfs_snow_cm': v}
        for k, v in gfs_data.items()
        if v is not None
    ]

    if not gfs_records:
        raise ValueError('No valid GFS data found')

    gfs_df = pl.DataFrame(gfs_records)

    # Inner join on date
    merged = gfs_df.join(obs_df, on='date', how='inner')

    # Calculate error metrics
    merged = merged.with_columns([
        (pl.col('gfs_snow_cm') - pl.col('obs_snow_cm')).alias('error_cm'),
    ])

    # Filter to days with observed snow > 0 (meaningful comparison)
    merged = merged.filter(pl.col('obs_snow_cm') > 0)

    return merged.sort('date')


# === VISUALIZATION ===

def create_scatter_plot(df: pl.DataFrame) -> None:
    """Create scatter plot of GFS vs observed snow depth."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Extract data
    obs = df['obs_snow_cm'].to_numpy()
    gfs = df['gfs_snow_cm'].to_numpy()

    # Calculate regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(obs, gfs)

    # Calculate RMSE and mean bias
    error = gfs - obs
    rmse = np.sqrt(np.mean(error ** 2))
    mean_bias = np.mean(error)
    pct_under = np.sum(error < 0) / len(error) * 100

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))

    # Scatter plot
    ax.scatter(obs, gfs, alpha=0.4, s=30, c='steelblue', edgecolors='none')

    # 1:1 reference line
    max_val = max(obs.max(), gfs.max()) * 1.1
    ax.plot([0, max_val], [0, max_val], 'k--', linewidth=1.5, label='1:1 line')

    # Regression line
    x_line = np.linspace(0, obs.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Fit (r={r_value:.3f})')

    # Labels
    ax.set_xlabel('Observed Snow Depth (cm)', fontsize=12)
    ax.set_ylabel('GFS Snow Depth (cm)', fontsize=12)

    # Title
    fig.suptitle('GFS Systematically Underestimates Basin Snow', fontsize=14, fontweight='bold')
    ax.set_title(f'n={len(obs):,}, Mean Bias={mean_bias:.1f} cm, RMSE={rmse:.1f} cm', fontsize=11)

    # Grid
    ax.grid(True, alpha=0.3)

    # Stats text box
    stats_text = (f'r = {r_value:.3f}\n'
                  f'Bias = {mean_bias:.1f} cm\n'
                  f'RMSE = {rmse:.1f} cm\n'
                  f'Underest. = {pct_under:.0f}%')
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Legend
    ax.legend(loc='upper right', fontsize=10)

    # Axis limits
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)

    # Save
    output_path = OUTPUT_DIR / 'gfs_snow_scatter.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'  Saved: {output_path}')
    plt.close(fig)


def create_error_histogram(df: pl.DataFrame) -> None:
    """Create histogram of GFS errors."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    error = df['error_cm'].to_numpy()

    # Statistics
    mean_err = np.mean(error)
    median_err = np.median(error)
    pct_under = np.sum(error < 0) / len(error) * 100

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Histogram
    ax.hist(error, bins=30, color='steelblue', edgecolor='black', linewidth=0.8, alpha=0.7)

    # Zero line
    ax.axvline(x=0, color='black', linestyle='--', linewidth=2, label='Zero error')

    # Mean line
    ax.axvline(x=mean_err, color='red', linestyle='-', linewidth=2,
               label=f'Mean = {mean_err:.1f} cm')

    # Labels
    ax.set_xlabel('GFS Error (GFS - Observed, cm)', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)

    # Title
    fig.suptitle('GFS Snow Depth Bias', fontsize=14, fontweight='bold')
    ax.set_title(f'Mean={mean_err:.1f} cm, Median={median_err:.1f} cm, '
                 f'{pct_under:.0f}% Underestimated', fontsize=11)

    # Grid
    ax.grid(True, axis='y', alpha=0.3)

    # Legend
    ax.legend(loc='upper right', fontsize=10)

    # Save
    output_path = OUTPUT_DIR / 'gfs_snow_error_histogram.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'  Saved: {output_path}')
    plt.close(fig)


# === REPORTING ===

def print_summary_statistics(df: pl.DataFrame) -> None:
    """Print comprehensive summary statistics."""
    obs = df['obs_snow_cm'].to_numpy()
    gfs = df['gfs_snow_cm'].to_numpy()
    error = df['error_cm'].to_numpy()

    # Overall stats
    r_value = np.corrcoef(obs, gfs)[0, 1]
    rmse = np.sqrt(np.mean(error ** 2))
    mean_bias = np.mean(error)
    pct_under = np.sum(error < 0) / len(error) * 100

    print('\n' + '=' * 60)
    print('GFS SNOW DEPTH COMPARISON SUMMARY')
    print('=' * 60)
    print(f'Total matched days (snow > 0): {len(df):,}')
    print(f'Mean GFS snow:      {np.mean(gfs):6.1f} cm')
    print(f'Mean Observed snow: {np.mean(obs):6.1f} cm')
    print(f'Mean Bias (GFS-Obs):{mean_bias:6.1f} cm')
    print(f'RMSE:               {rmse:6.1f} cm')
    print(f'Correlation (r):    {r_value:6.3f}')
    print(f'Days GFS underest.: {pct_under:6.1f}%')

    # Stratified by snow depth bins
    print('\nBy Observed Snow Depth Bin:')
    bins = [(0, 5), (5, 10), (10, 20), (20, float('inf'))]
    bin_labels = ['0-5 cm', '5-10 cm', '10-20 cm', '20+ cm']

    for (lo, hi), label in zip(bins, bin_labels):
        mask = (obs >= lo) & (obs < hi)
        if mask.sum() > 0:
            bin_error = error[mask]
            print(f'  {label:10s}: bias = {bin_error.mean():6.1f} cm (n={mask.sum():3d})')

    print('=' * 60)


# === MAIN ===

def main():
    parser = argparse.ArgumentParser(description='Compare GFS vs observed snow depth')
    parser.add_argument('--force-refetch', action='store_true',
                        help='Re-fetch GFS data even if cached')
    args = parser.parse_args()

    print('=' * 60)
    print('GFS vs OBSERVED SNOW DEPTH COMPARISON')
    print('Uintah Basin, Dec-Mar 2019-2025')
    print('=' * 60)

    # Step 1: Load observed snow data
    print('\n[1/5] Loading observed snow data...')
    obs_df = load_observed_snow()
    print(f'  Loaded basin-average snow for {len(obs_df)} days')

    # Step 2: Get all winter dates
    print('\n[2/5] Generating date list...')
    dates = get_winter_dates()
    print(f'  {len(dates)} dates to process (Dec-Mar, 6 winters)')

    # Step 3: Fetch GFS data (with caching)
    print('\n[3/5] Fetching GFS snow depth data...')
    cache = load_gfs_cache()
    print(f'  Cache contains {len(cache)} dates')
    gfs_data = fetch_all_gfs_snow(dates, cache, force=args.force_refetch)

    # Step 4: Merge and calculate metrics
    print('\n[4/5] Merging datasets...')
    merged = merge_gfs_obs(gfs_data, obs_df)
    print(f'  {len(merged)} matched days with observed snow > 0')

    # Step 5: Create outputs
    print('\n[5/5] Creating visualizations...')
    create_scatter_plot(merged)
    create_error_histogram(merged)

    # Print summary
    print_summary_statistics(merged)

    print('\nDone!')


if __name__ == '__main__':
    main()
