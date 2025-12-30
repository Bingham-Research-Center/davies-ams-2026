#!/usr/bin/env python3
"""
Fetch ozone observation data from Synoptic API.

Fetches hourly ozone concentration data for Basin and Wasatch Front stations
and saves to parquet format.

Usage:
    python fetch_observations.py --start 2023-01-01 --end 2023-02-28 --output data/winter2023_ozone.parquet

Requires:
    pip install SynopticPy polars
    export SYNOPTIC_TOKEN="your_token"  # or configure in ~/.config/SynopticPy/config.toml
"""

import argparse
from synoptic import TimeSeries
import polars as pl


# Station definitions
BASIN_STATIONS = {
    'QRS': 'Roosevelt',
    'QV4': 'Vernal',
    'A1386': 'Whiterocks',
    'A3822': 'Dinosaur NM',
}

WINDWARD_STATIONS = {
    'QCV': 'Copperview',
    'QLN': 'Lindon',
    'QRP': 'Rose Park',
}


def fetch_ozone_data(start: str, end: str, stations: list[str] = None) -> pl.DataFrame:
    """
    Fetch ozone concentration data from Synoptic API.

    Args:
        start: Start datetime string (e.g., '2023-01-01' or '2023-01-01T06:00')
        end: End datetime string
        stations: List of station IDs. If None, uses all Basin + Windward stations.

    Returns:
        Polars DataFrame with ozone observations
    """
    if stations is None:
        stations = list(BASIN_STATIONS.keys()) + list(WINDWARD_STATIONS.keys())

    print(f"Fetching ozone data for {len(stations)} stations...")
    print(f"  Period: {start} to {end}")

    df = TimeSeries(
        stid=stations,
        start=start,
        end=end,
        vars=['ozone_concentration'],
    ).df()

    # Add region label
    basin_ids = list(BASIN_STATIONS.keys())
    df = df.with_columns([
        pl.when(pl.col('stid').is_in(basin_ids))
        .then(pl.lit('Basin'))
        .otherwise(pl.lit('Windward'))
        .alias('region')
    ])

    print(f"  Retrieved {len(df)} observations")
    return df


def main():
    parser = argparse.ArgumentParser(description='Fetch ozone data from Synoptic API')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', required=True, help='Output parquet file path')
    parser.add_argument('--basin-only', action='store_true', help='Only fetch Basin stations')

    args = parser.parse_args()

    stations = list(BASIN_STATIONS.keys()) if args.basin_only else None

    df = fetch_ozone_data(args.start, args.end, stations)

    # Save to parquet
    df.write_parquet(args.output)
    print(f"Saved to {args.output}")

    # Print summary
    ozone = df.filter(df['variable'] == 'ozone_concentration')
    print("\nSummary by station:")
    summary = ozone.group_by(['stid', 'name', 'region']).agg([
        pl.col('value').mean().round(1).alias('mean_ppb'),
        pl.col('value').max().alias('max_ppb'),
        pl.col('value').count().alias('n_obs'),
    ])
    print(summary.sort(['region', 'stid']))


if __name__ == '__main__':
    main()
