#!/usr/bin/env python3
"""
Compare AQM forecasts vs observations.

Joins AQM and observation data, calculates bias and hit/miss statistics
for NAAQS exceedance events (>= 70 ppb).

Usage:
    python compare_aqm_obs.py --obs data/winter2023_ozone.parquet --aqm data/winter2023_aqm.parquet

Requires:
    pip install polars numpy
"""

import argparse
import numpy as np
import polars as pl


# NAAQS 8-hour ozone standard
NAAQS_THRESHOLD = 70  # ppb


def load_and_prepare_obs(obs_path: str) -> pl.DataFrame:
    """
    Load observation data and compute daily max ozone by station.

    Args:
        obs_path: Path to observation parquet file

    Returns:
        DataFrame with columns: date, stid, obs_max
    """
    obs = pl.read_parquet(obs_path)

    # Filter for ozone only
    ozone = obs.filter(obs['variable'] == 'ozone_concentration')

    # Compute daily max by station
    daily_max = ozone.group_by([
        pl.col('date_time').dt.date().alias('date'),
        'stid'
    ]).agg(pl.col('value').max().alias('obs_max'))

    return daily_max


def compare_aqm_obs(obs_path: str, aqm_path: str) -> pl.DataFrame:
    """
    Compare AQM forecasts with observations.

    Args:
        obs_path: Path to observation parquet file
        aqm_path: Path to AQM parquet file

    Returns:
        DataFrame with comparison results
    """
    # Load data
    obs_daily = load_and_prepare_obs(obs_path)
    aqm = pl.read_parquet(aqm_path)

    # Join on date and station
    comparison = obs_daily.join(aqm, on=['date', 'stid'], how='inner')

    # Calculate metrics
    comparison = comparison.with_columns([
        (pl.col('aqm_max') - pl.col('obs_max')).alias('bias'),
        (pl.col('obs_max') >= NAAQS_THRESHOLD).alias('obs_exceedance'),
        (pl.col('aqm_max') >= NAAQS_THRESHOLD).alias('aqm_exceedance'),
    ])

    return comparison


def print_summary(comparison: pl.DataFrame):
    """Print summary statistics for AQM performance."""

    print("=" * 60)
    print("AQM Performance Summary")
    print("=" * 60)

    # Overall statistics
    bias = comparison['bias'].to_numpy()
    print(f"\nOverall (all days, all stations):")
    print(f"  Total comparisons: {len(comparison)}")
    print(f"  Mean Bias: {bias.mean():.1f} ppb")
    print(f"  RMSE: {np.sqrt((bias**2).mean()):.1f} ppb")

    # Exceedance statistics
    exceed = comparison.filter(pl.col('obs_exceedance'))
    if len(exceed) > 0:
        caught = exceed.filter(pl.col('aqm_exceedance'))
        missed = exceed.filter(~pl.col('aqm_exceedance'))

        print(f"\nExceedance days (obs >= {NAAQS_THRESHOLD} ppb):")
        print(f"  Total: {len(exceed)}")
        print(f"  Mean Obs: {exceed['obs_max'].mean():.1f} ppb")
        print(f"  Mean AQM: {exceed['aqm_max'].mean():.1f} ppb")
        print(f"  Mean Bias: {exceed['bias'].mean():.1f} ppb")

        print(f"\n  AQM caught (predicted >= {NAAQS_THRESHOLD}): {len(caught)} ({100*len(caught)/len(exceed):.0f}%)")
        print(f"  AQM missed (predicted < {NAAQS_THRESHOLD}): {len(missed)} ({100*len(missed)/len(exceed):.0f}%)")

    # By station
    print("\n\nBy Station:")
    for stid in comparison['stid'].unique().sort().to_list():
        station = comparison.filter(pl.col('stid') == stid)
        exceed_st = station.filter(pl.col('obs_exceedance'))

        if len(exceed_st) > 0:
            caught_st = exceed_st.filter(pl.col('aqm_exceedance'))
            print(f"\n  {stid}:")
            print(f"    Exceedance days: {len(exceed_st)}")
            print(f"    AQM caught: {len(caught_st)} ({100*len(caught_st)/len(exceed_st):.0f}%)")
            print(f"    Mean bias: {exceed_st['bias'].mean():.1f} ppb")
        else:
            print(f"\n  {stid}: No exceedance days")


def main():
    parser = argparse.ArgumentParser(description='Compare AQM forecasts vs observations')
    parser.add_argument('--obs', required=True, help='Path to observation parquet file')
    parser.add_argument('--aqm', required=True, help='Path to AQM parquet file')
    parser.add_argument('--output', help='Optional: save comparison to parquet')

    args = parser.parse_args()

    comparison = compare_aqm_obs(args.obs, args.aqm)
    print_summary(comparison)

    if args.output:
        comparison.write_parquet(args.output)
        print(f"\nSaved comparison to {args.output}")


if __name__ == '__main__':
    main()
