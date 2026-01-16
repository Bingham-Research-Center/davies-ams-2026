"""
Analyze AQM performance by station.

Calculates verification metrics for each station to identify
spatial patterns in model skill across the Uinta Basin.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from stations import ALL_STATIONS
from verification_metrics import THRESHOLD, bootstrap_pod_ci
from report_writer import create_report

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'
AQM_DATA_PATH = DATA_DIR / 'all_matched_obs_aqm.parquet'

# Longitude dividing western (UBCSP, QRS) from eastern (UBHSP, QV4, UB7ST) basin
# Based on geographic midpoint of monitoring network
BASIN_SPLIT_LON = -109.8

# Station order from west to east for visualization
STATION_ORDER = ['UBCSP', 'QRS', 'UBHSP', 'QV4', 'UB7ST']


def calculate_station_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """Calculate verification metrics by station."""
    # Filter out null observations
    df = df.filter(pl.col('obs_mda8').is_not_null())

    # Calculate bias for each record
    df = df.with_columns([
        (pl.col('aqm_max') - pl.col('obs_mda8')).alias('bias'),
        (pl.col('obs_mda8') >= THRESHOLD).alias('is_exceedance'),
        ((pl.col('obs_mda8') >= THRESHOLD) & (pl.col('aqm_max') >= THRESHOLD)).alias('is_hit'),
    ])

    # Group by station and calculate metrics
    metrics = df.group_by('stid').agg([
        pl.len().alias('n'),
        pl.col('obs_mda8').mean().alias('mean_obs'),
        pl.col('aqm_max').mean().alias('mean_aqm'),
        pl.col('bias').mean().alias('mean_bias'),
        (pl.col('bias') ** 2).mean().sqrt().alias('rmse'),
        pl.col('is_exceedance').sum().alias('n_exceedance'),
        pl.col('is_hit').sum().alias('hits'),
    ])

    # Calculate POD and miss rate with safe division (0 when no exceedances)
    metrics = metrics.with_columns([
        (pl.when(pl.col('n_exceedance') > 0)
           .then(pl.col('hits') / pl.col('n_exceedance'))
           .otherwise(0.0)).alias('pod'),
        (pl.when(pl.col('n_exceedance') > 0)
           .then(1 - pl.col('hits') / pl.col('n_exceedance'))
           .otherwise(0.0)).alias('miss_rate'),
    ])

    return metrics


def add_station_metadata(metrics: pl.DataFrame) -> pl.DataFrame:
    """Add lat/lon and name from station configuration."""
    # Create lookup dataframes
    station_data = []
    for stid, station in ALL_STATIONS.items():
        station_data.append({
            'stid': stid,
            'name': station.name,
            'lat': station.lat,
            'lon': station.lon,
        })

    station_df = pl.DataFrame(station_data)

    # Join with metrics
    metrics = metrics.join(station_df, on='stid', how='left')

    return metrics


def print_station_table(metrics: pl.DataFrame) -> None:
    """Print formatted station metrics table."""
    print('\n' + '='*90)
    print('STATION VERIFICATION METRICS')
    print('='*90)

    # Header
    print(f'\n{"Station":<12} {"Name":<15} {"n":>6} {"Bias":>8} {"RMSE":>8} {"Exceed":>8} {"Hits":>6} {"POD":>8} {"Miss":>8}')
    print('-'*90)

    # Sort by longitude (west to east)
    sorted_metrics = metrics.sort('lon', descending=True)

    for row in sorted_metrics.iter_rows(named=True):
        stid = row['stid']
        name = row['name'] if row['name'] else stid
        n = row['n']
        bias = row['mean_bias']
        rmse = row['rmse']
        n_exc = row['n_exceedance']
        hits = row['hits']
        pod = row['pod'] if row['pod'] is not None else 0
        miss = row['miss_rate'] if row['miss_rate'] is not None else 1

        print(f'{stid:<12} {name:<15} {n:>6} {bias:>+8.2f} {rmse:>8.2f} {n_exc:>8} {hits:>6} {pod:>8.1%} {miss:>8.1%}')

    print('-'*90)


def bootstrap_spatial_pod_difference(
    df: pl.DataFrame,
    western_stids: list[str],
    eastern_stids: list[str],
    n_iterations: int = 1000,
    seed: int = 42
) -> dict:
    """Bootstrap test for POD difference between basin regions.

    Args:
        df: Full DataFrame with all station data
        western_stids: List of station IDs in western region
        eastern_stids: List of station IDs in eastern region
        n_iterations: Number of bootstrap iterations
        seed: Random seed for reproducibility

    Returns:
        Dict with west_pod, east_pod, difference, ci_lower, ci_upper, p_value
    """
    rng = np.random.default_rng(seed)

    # Filter to exceedance days only
    exc_df = df.filter(
        (pl.col('obs_mda8') >= THRESHOLD) &
        pl.col('aqm_max').is_not_null()
    )

    west_data = exc_df.filter(pl.col('stid').is_in(western_stids))
    east_data = exc_df.filter(pl.col('stid').is_in(eastern_stids))

    n_west = len(west_data)
    n_east = len(east_data)

    if n_west == 0 or n_east == 0:
        return {'west_pod': 0.0, 'east_pod': 0.0, 'difference': 0.0,
                'ci_lower': 0.0, 'ci_upper': 0.0, 'p_value': 1.0}

    west_fcst = west_data['aqm_max'].to_numpy()
    east_fcst = east_data['aqm_max'].to_numpy()

    # Observed POD
    west_pod = (west_fcst >= THRESHOLD).sum() / n_west
    east_pod = (east_fcst >= THRESHOLD).sum() / n_east
    observed_diff = west_pod - east_pod

    # Bootstrap
    diffs = np.zeros(n_iterations)
    for i in range(n_iterations):
        west_idx = rng.integers(0, n_west, size=n_west)
        east_idx = rng.integers(0, n_east, size=n_east)
        west_pod_boot = (west_fcst[west_idx] >= THRESHOLD).sum() / n_west
        east_pod_boot = (east_fcst[east_idx] >= THRESHOLD).sum() / n_east
        diffs[i] = west_pod_boot - east_pod_boot

    ci_lower = np.percentile(diffs, 2.5)
    ci_upper = np.percentile(diffs, 97.5)

    # Two-sided p-value: probability that difference could be zero or opposite sign
    if observed_diff >= 0:
        p_value = np.mean(diffs <= 0) * 2
    else:
        p_value = np.mean(diffs >= 0) * 2
    p_value = min(p_value, 1.0)

    return {
        'west_pod': west_pod,
        'east_pod': east_pod,
        'difference': observed_diff,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'p_value': p_value,
        'n_west': n_west,
        'n_east': n_east
    }


def print_spatial_summary(metrics: pl.DataFrame, df: pl.DataFrame = None) -> None:
    """Print summary of spatial patterns.

    Args:
        metrics: Station-level aggregated metrics
        df: Optional full DataFrame for bootstrap test
    """
    print('\n' + '='*60)
    print('SPATIAL PATTERN ANALYSIS')
    print('='*60)

    # Sort by longitude
    sorted_metrics = metrics.sort('lon', descending=True)

    # Western stations (lon < BASIN_SPLIT_LON)
    western = metrics.filter(pl.col('lon') < BASIN_SPLIT_LON)
    eastern = metrics.filter(pl.col('lon') >= BASIN_SPLIT_LON)

    if len(western) > 0 and len(eastern) > 0:
        west_pod = western['pod'].mean()
        east_pod = eastern['pod'].mean()
        west_bias = western['mean_bias'].mean()
        east_bias = eastern['mean_bias'].mean()

        west_stids = western['stid'].to_list()
        east_stids = eastern['stid'].to_list()

        print('\nWestern Basin (UBCSP, QRS):')
        print(f'  Mean POD: {west_pod:.1%}')
        print(f'  Mean Bias: {west_bias:+.2f} ppb')

        print('\nEastern/Central Basin (UBHSP, QV4, UB7ST):')
        print(f'  Mean POD: {east_pod:.1%}')
        print(f'  Mean Bias: {east_bias:+.2f} ppb')

        # Bootstrap test for significance if df provided
        if df is not None:
            boot_result = bootstrap_spatial_pod_difference(df, west_stids, east_stids)
            print('\nStatistical Test (Bootstrap, n=1000):')
            print(f'  POD Difference (West - East): {boot_result["difference"]:.1%}')
            print(f'  95% CI: [{boot_result["ci_lower"]:.1%}, {boot_result["ci_upper"]:.1%}]')
            print(f'  p-value: {boot_result["p_value"]:.3f}')
            if boot_result['p_value'] < 0.05:
                print('  -> Difference is statistically significant (p < 0.05)')
            else:
                print('  -> Difference is NOT statistically significant')

        print('\nPattern Assessment:')
        if east_pod < west_pod - 0.05:
            print('  -> Eastern stations show WORSE POD (potential snow shadow effect)')
        elif west_pod < east_pod - 0.05:
            print('  -> Western stations show WORSE POD')
        else:
            print('  -> POD relatively uniform across basin')


def plot_station_map(metrics: pl.DataFrame) -> None:
    """Create map showing POD by station location."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8))

    # Extract data
    lons = metrics['lon'].to_numpy()
    lats = metrics['lat'].to_numpy()
    pods = metrics['pod'].to_numpy()
    names = metrics['name'].to_list()
    stids = metrics['stid'].to_list()
    n_exc = metrics['n_exceedance'].to_list()

    # Handle NaN POD values (stations with no exceedances)
    pods = np.nan_to_num(pods, nan=0.0)

    # Create scatter plot
    scatter = ax.scatter(
        lons, lats,
        c=pods,
        cmap='RdYlGn',
        s=300,
        edgecolors='black',
        linewidths=1.5,
        vmin=0,
        vmax=1,
        zorder=3
    )

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, label='Probability of Detection (POD)', shrink=0.8)
    cbar.ax.tick_params(labelsize=10)

    # Annotate stations
    for i, (lon, lat, name, stid, pod, n) in enumerate(zip(lons, lats, names, stids, pods, n_exc)):
        # Position label above marker
        ax.annotate(
            f'{name}\n({stid})\nn={n}, POD={pod:.0%}',
            (lon, lat),
            textcoords='offset points',
            xytext=(0, 20),
            ha='center',
            va='bottom',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.9)
        )

    # Labels and title
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title('AQM Detection Rate (POD) by Station\nUinta Basin Ozone Monitoring Network',
                 fontsize=14, fontweight='bold')

    # Grid
    ax.grid(True, alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # Adjust axis limits for better visualization
    lon_margin = 0.15
    lat_margin = 0.1
    ax.set_xlim(lons.min() - lon_margin, lons.max() + lon_margin)
    ax.set_ylim(lats.min() - lat_margin, lats.max() + lat_margin)

    # Add basin orientation labels
    ax.text(0.02, 0.98, 'West', transform=ax.transAxes, fontsize=10,
            ha='left', va='top', style='italic', color='gray')
    ax.text(0.98, 0.98, 'East', transform=ax.transAxes, fontsize=10,
            ha='right', va='top', style='italic', color='gray')

    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / 'station_performance_map.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def plot_pod_comparison(metrics: pl.DataFrame) -> None:
    """Create horizontal bar chart comparing POD by station."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Sort by longitude (west to east, so reverse for horizontal bars)
    sorted_metrics = metrics.sort('lon')

    names = sorted_metrics['name'].to_list()
    stids = sorted_metrics['stid'].to_list()
    pods = sorted_metrics['pod'].to_numpy()
    n_exc = sorted_metrics['n_exceedance'].to_list()

    # Handle NaN values
    pods = np.nan_to_num(pods, nan=0.0)

    # Create labels
    labels = [f'{name} ({stid})' for name, stid in zip(names, stids)]

    y_pos = np.arange(len(labels))

    # Color by POD value
    colors = plt.cm.RdYlGn(pods)

    # Create horizontal bars
    bars = ax.barh(y_pos, pods, color=colors, edgecolor='black', linewidth=1.0, zorder=3)

    # Add value labels
    for i, (pod, n) in enumerate(zip(pods, n_exc)):
        ax.text(pod + 0.02, i, f'{pod:.0%} (n={n})', va='center', fontsize=10)

    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel('Probability of Detection (POD)', fontsize=12)
    ax.set_title('AQM Exceedance Detection Rate by Station\n(Sorted East to West)',
                 fontsize=14, fontweight='bold')

    # Reference line at overall POD
    overall_pod = metrics['hits'].sum() / metrics['n_exceedance'].sum()
    ax.axvline(x=overall_pod, color='red', linestyle='--', linewidth=2,
               label=f'Overall POD: {overall_pod:.0%}', zorder=2)

    ax.legend(loc='lower right', fontsize=10)

    # Grid
    ax.grid(True, axis='x', alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # Set x-axis limits
    ax.set_xlim(0, 1.15)

    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / 'station_pod_comparison.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def write_report(metrics: pl.DataFrame, df: pl.DataFrame) -> None:
    """Write station breakdown analysis to markdown report."""
    report = create_report('station_breakdown.md')
    report.add_title('Station Breakdown Analysis')

    # Station Verification Metrics table
    report.add_section('Station Verification Metrics')
    headers = ['Station', 'Name', 'n', 'Bias', 'RMSE', 'Exceedances', 'Hits', 'POD', 'Miss Rate']
    rows = []
    sorted_metrics = metrics.sort('lon', descending=True)
    for row in sorted_metrics.iter_rows(named=True):
        stid = row['stid']
        name = row['name'] if row['name'] else stid
        n = row['n']
        bias = row['mean_bias']
        rmse = row['rmse']
        n_exc = row['n_exceedance']
        hits = row['hits']
        pod = row['pod'] if row['pod'] is not None else 0
        miss = row['miss_rate'] if row['miss_rate'] is not None else 1
        rows.append([
            stid,
            name,
            str(n),
            f'{bias:+.2f}',
            f'{rmse:.2f}',
            str(n_exc),
            str(hits),
            f'{pod:.1%}',
            f'{miss:.1%}'
        ])
    report.add_table(headers, rows)

    # Spatial Pattern Analysis
    report.add_section('Spatial Pattern Analysis')

    western = metrics.filter(pl.col('lon') < BASIN_SPLIT_LON)
    eastern = metrics.filter(pl.col('lon') >= BASIN_SPLIT_LON)

    if len(western) > 0 and len(eastern) > 0:
        west_pod = western['pod'].mean()
        east_pod = eastern['pod'].mean()
        west_bias = western['mean_bias'].mean()
        east_bias = eastern['mean_bias'].mean()
        west_stids = western['stid'].to_list()
        east_stids = eastern['stid'].to_list()

        report.add_section('Western Basin (UBCSP, QRS)', level=3)
        report.add_key_value('Mean POD', f'{west_pod:.1%}')
        report.add_key_value('Mean Bias', f'{west_bias:+.2f} ppb')
        report.add_text('')

        report.add_section('Eastern/Central Basin (UBHSP, QV4, UB7ST)', level=3)
        report.add_key_value('Mean POD', f'{east_pod:.1%}')
        report.add_key_value('Mean Bias', f'{east_bias:+.2f} ppb')
        report.add_text('')

        # Bootstrap test
        boot_result = bootstrap_spatial_pod_difference(df, west_stids, east_stids)
        report.add_section('Bootstrap Significance Test', level=3)
        report.add_key_value('POD Difference (West - East)', f'{boot_result["difference"]:.1%}')
        report.add_key_value('95% CI', f'[{boot_result["ci_lower"]:.1%}, {boot_result["ci_upper"]:.1%}]')
        report.add_key_value('P-value', f'{boot_result["p_value"]:.3f}')
        if boot_result['p_value'] < 0.05:
            report.add_key_value('Significance', 'Difference is statistically significant (p < 0.05)')
        else:
            report.add_key_value('Significance', 'Difference is NOT statistically significant')
        report.add_text('')

        # Pattern Assessment
        report.add_section('Pattern Assessment', level=3)
        if east_pod < west_pod - 0.05:
            assessment = 'Eastern stations show WORSE POD (potential snow shadow effect)'
        elif west_pod < east_pod - 0.05:
            assessment = 'Western stations show WORSE POD'
        else:
            assessment = 'POD relatively uniform across basin'
        report.add_text(assessment)

    report.save()


def main():
    """Main function."""
    print('='*60)
    print('STATION BREAKDOWN ANALYSIS')
    print('='*60)

    # Load data
    print('\n[1/4] Loading verification data...')
    df = pl.read_parquet(AQM_DATA_PATH)
    print(f'  Loaded {len(df)} matched obs/AQM records')
    print(f'  Stations: {df["stid"].unique().to_list()}')
    print(f'  Winters: {df["winter"].unique().sort().to_list()}')

    # Calculate metrics
    print('\n[2/4] Calculating station metrics...')
    metrics = calculate_station_metrics(df)
    metrics = add_station_metadata(metrics)
    print(f'  Computed metrics for {len(metrics)} stations')

    # Print results
    print_station_table(metrics)
    print_spatial_summary(metrics, df)

    # Create visualizations
    print('\n[3/4] Creating station map...')
    plot_station_map(metrics)

    print('\n[4/4] Creating POD comparison chart...')
    plot_pod_comparison(metrics)

    # Write markdown report
    write_report(metrics, df)

    print('\nDone!')


if __name__ == '__main__':
    main()
