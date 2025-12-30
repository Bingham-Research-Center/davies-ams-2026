#!/usr/bin/env python3
"""
Create poster figures for AQM vs observations analysis.

Generates:
- Scatter plot of AQM vs Observations with quadrant analysis
- Time series for Roosevelt station showing systematic bias
- Basin vs Windward regional comparison

Usage:
    python plot_results.py --obs data/winter2023_ozone.parquet --aqm data/winter2023_aqm.parquet --output figures/

Requires:
    pip install polars matplotlib pandas numpy
"""

import argparse
import os
import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# NAAQS threshold
NAAQS_THRESHOLD = 70  # ppb


def load_comparison_data(obs_path: str, aqm_path: str) -> pl.DataFrame:
    """Load and join observation and AQM data."""
    obs = pl.read_parquet(obs_path)
    aqm = pl.read_parquet(aqm_path)

    # Get daily max observations
    ozone = obs.filter(obs['variable'] == 'ozone_concentration')
    obs_daily = ozone.group_by([
        pl.col('date_time').dt.date().alias('date'),
        'stid'
    ]).agg(pl.col('value').max().alias('obs_max'))

    # Join with AQM
    comparison = obs_daily.join(aqm, on=['date', 'stid'], how='inner')

    return comparison


def plot_scatter(comparison: pl.DataFrame, output_dir: str):
    """Create scatter plot of AQM vs Observations."""
    fig, ax = plt.subplots(figsize=(8, 8))

    obs_vals = comparison['obs_max'].to_numpy()
    aqm_vals = comparison['aqm_max'].to_numpy()

    # Color by exceedance
    colors = ['red' if o >= NAAQS_THRESHOLD else 'blue' for o in obs_vals]
    ax.scatter(obs_vals, aqm_vals, c=colors, alpha=0.5, s=30)

    # 1:1 line
    ax.plot([0, 130], [0, 130], 'k--', linewidth=1, label='1:1 line')

    # NAAQS threshold lines
    ax.axhline(NAAQS_THRESHOLD, color='orange', linestyle=':', linewidth=1.5)
    ax.axvline(NAAQS_THRESHOLD, color='orange', linestyle=':', linewidth=1.5)

    # Quadrant labels
    exceed_mask = obs_vals >= NAAQS_THRESHOLD
    caught = np.sum((obs_vals >= NAAQS_THRESHOLD) & (aqm_vals >= NAAQS_THRESHOLD))
    missed = np.sum((obs_vals >= NAAQS_THRESHOLD) & (aqm_vals < NAAQS_THRESHOLD))
    total_exceed = np.sum(obs_vals >= NAAQS_THRESHOLD)

    ax.text(95, 55, f'AQM MISSED\n({100*missed/total_exceed:.0f}%)',
            fontsize=10, ha='center', color='darkred', fontweight='bold')
    ax.text(95, 95, f'AQM Caught\n({100*caught/total_exceed:.0f}%)',
            fontsize=10, ha='center', color='darkgreen', fontweight='bold')

    ax.set_xlabel('Observed Max O₃ (ppb)', fontsize=12)
    ax.set_ylabel('AQM Forecast Max O₃ (ppb)', fontsize=12)
    ax.set_title(f'AQM vs Observations\n(n={len(comparison)} station-days)', fontsize=14)
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 130)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    # Bias annotation
    bias = aqm_vals - obs_vals
    ax.text(0.98, 0.02, f'Mean Bias: {bias.mean():.1f} ppb\nExceedance Bias: {bias[exceed_mask].mean():.1f} ppb',
            transform=ax.transAxes, fontsize=10, ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'aqm_scatter.png'), dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/aqm_scatter.png")
    plt.close()


def plot_timeseries(comparison: pl.DataFrame, output_dir: str, station: str = 'QRS'):
    """Create time series plot for a single station."""
    station_data = comparison.filter(pl.col('stid') == station).sort('date')

    fig, ax = plt.subplots(figsize=(12, 5))

    dates = pd.to_datetime(station_data['date'].to_list())
    obs = station_data['obs_max'].to_numpy()
    aqm = station_data['aqm_max'].to_numpy()

    ax.plot(dates, obs, 'b-', linewidth=1.5, marker='o', markersize=3, label='Observations')
    ax.plot(dates, aqm, 'r-', linewidth=1.5, marker='s', markersize=3, label='AQM Forecast')
    ax.axhline(NAAQS_THRESHOLD, color='orange', linestyle='--', linewidth=2, label=f'NAAQS ({NAAQS_THRESHOLD} ppb)')

    # Shade underestimates
    ax.fill_between(dates, obs, aqm, where=obs > aqm,
                    color='red', alpha=0.2, label='AQM underestimate')

    # Count exceedances
    n_exceed = np.sum(obs >= NAAQS_THRESHOLD)
    n_caught = np.sum((obs >= NAAQS_THRESHOLD) & (aqm >= NAAQS_THRESHOLD))

    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Daily Max O₃ (ppb)', fontsize=12)
    ax.set_title(f'{station} Station: {n_exceed} exceedance days, AQM caught {n_caught} ({100*n_caught/n_exceed:.0f}%)',
                 fontsize=14)
    ax.legend(loc='upper left')
    ax.set_ylim(0, 130)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'timeseries_{station}.png'), dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/timeseries_{station}.png")
    plt.close()


def plot_combined(comparison: pl.DataFrame, output_dir: str):
    """Create combined scatter + time series figure."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Scatter plot
    ax1 = axes[0]
    obs_vals = comparison['obs_max'].to_numpy()
    aqm_vals = comparison['aqm_max'].to_numpy()
    colors = ['red' if o >= NAAQS_THRESHOLD else 'blue' for o in obs_vals]

    ax1.scatter(obs_vals, aqm_vals, c=colors, alpha=0.5, s=30)
    ax1.plot([0, 130], [0, 130], 'k--', linewidth=1)
    ax1.axhline(NAAQS_THRESHOLD, color='orange', linestyle=':', linewidth=1.5)
    ax1.axvline(NAAQS_THRESHOLD, color='orange', linestyle=':', linewidth=1.5)

    exceed_mask = obs_vals >= NAAQS_THRESHOLD
    caught = np.sum((obs_vals >= NAAQS_THRESHOLD) & (aqm_vals >= NAAQS_THRESHOLD))
    missed = np.sum((obs_vals >= NAAQS_THRESHOLD) & (aqm_vals < NAAQS_THRESHOLD))
    total_exceed = np.sum(exceed_mask)

    ax1.text(95, 55, f'MISSED\n({100*missed/total_exceed:.0f}%)',
             fontsize=10, ha='center', color='darkred', fontweight='bold')
    ax1.text(95, 95, f'Caught\n({100*caught/total_exceed:.0f}%)',
             fontsize=10, ha='center', color='darkgreen', fontweight='bold')

    ax1.set_xlabel('Observed Max O₃ (ppb)')
    ax1.set_ylabel('AQM Forecast Max O₃ (ppb)')
    ax1.set_title(f'AQM vs Observations (n={len(comparison)})')
    ax1.set_xlim(0, 130)
    ax1.set_ylim(0, 130)
    ax1.grid(True, alpha=0.3)

    bias = aqm_vals - obs_vals
    ax1.text(0.98, 0.02, f'Bias: {bias.mean():.1f} ppb',
             transform=ax1.transAxes, fontsize=10, ha='right', va='bottom',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Time series for Roosevelt
    ax2 = axes[1]
    roosevelt = comparison.filter(pl.col('stid') == 'QRS').sort('date')
    dates = pd.to_datetime(roosevelt['date'].to_list())
    obs_rs = roosevelt['obs_max'].to_numpy()
    aqm_rs = roosevelt['aqm_max'].to_numpy()

    ax2.plot(dates, obs_rs, 'b-', linewidth=1.5, marker='o', markersize=3, label='Observations')
    ax2.plot(dates, aqm_rs, 'r-', linewidth=1.5, marker='s', markersize=3, label='AQM')
    ax2.axhline(NAAQS_THRESHOLD, color='orange', linestyle='--', linewidth=2)
    ax2.fill_between(dates, obs_rs, aqm_rs, where=obs_rs > aqm_rs, color='red', alpha=0.2)

    ax2.set_xlabel('Date')
    ax2.set_ylabel('Daily Max O₃ (ppb)')
    ax2.set_title('Roosevelt Station Time Series')
    ax2.legend(loc='upper left')
    ax2.set_ylim(0, 130)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'aqm_performance.png'), dpi=150, bbox_inches='tight')
    print(f"Saved: {output_dir}/aqm_performance.png")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Create AQM analysis figures')
    parser.add_argument('--obs', required=True, help='Path to observation parquet file')
    parser.add_argument('--aqm', required=True, help='Path to AQM parquet file')
    parser.add_argument('--output', default='figures/', help='Output directory for figures')

    args = parser.parse_args()

    # Create output directory if needed
    os.makedirs(args.output, exist_ok=True)

    # Load data
    comparison = load_comparison_data(args.obs, args.aqm)
    print(f"Loaded {len(comparison)} station-day comparisons")

    # Create figures
    plot_scatter(comparison, args.output)
    plot_timeseries(comparison, args.output, station='QRS')
    plot_combined(comparison, args.output)

    print("\nAll figures created!")


if __name__ == '__main__':
    main()
