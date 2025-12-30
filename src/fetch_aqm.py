#!/usr/bin/env python3
"""
Fetch AQM (NOAA Air Quality Model) forecast data using Herbie.

Downloads max_8hr_o3 forecasts and extracts values at Basin station locations.

Usage:
    python fetch_aqm.py --start 2023-01-01 --end 2023-02-28 --output data/winter2023_aqm.parquet

Requires:
    pip install herbie-data xarray pandas polars numpy
    Also requires the custom AQM template in ~/.config/herbie/custom_template.py
"""

import argparse
import numpy as np
import pandas as pd
import polars as pl
import xarray as xr
from herbie import Herbie


# Basin station coordinates (lat, lon)
# Note: Longitude is in -180 to 180 format; AQM uses 0-360
BASIN_STATIONS = {
    'QRS': (40.2943, -110.009),      # Roosevelt
    'QV4': (40.46472, -109.56083),   # Vernal
    'A1386': (40.4838, -109.9062),   # Whiterocks
    'A3822': (40.4372, -109.3047),   # Dinosaur NM
}


def extract_at_stations(ds: xr.Dataset, stations: dict) -> dict:
    """
    Extract AQM values at station locations.

    Args:
        ds: xarray Dataset from AQM GRIB file
        stations: Dict of station_id -> (lat, lon) tuples

    Returns:
        Dict of station_id -> ozone value (ppb)
    """
    lats = ds['latitude'].values
    lons = ds['longitude'].values
    data = ds['unknown']  # AQM ozone variable

    results = {}
    for stid, (slat, slon) in stations.items():
        # Convert longitude from -180/180 to 0/360 format
        slon_360 = 360 + slon if slon < 0 else slon

        # Find nearest grid point
        dist = np.sqrt((lats - slat)**2 + (lons - slon_360)**2)
        min_idx = np.unravel_index(dist.argmin(), dist.shape)
        y_idx, x_idx = min_idx

        # Get value (step=0 is the analysis/first forecast)
        val = float(data.isel(step=0, y=y_idx, x=x_idx))
        results[stid] = val

    return results


def fetch_aqm_data(start: str, end: str) -> pl.DataFrame:
    """
    Fetch AQM max_8hr_o3 forecasts for a date range.

    Args:
        start: Start date string (YYYY-MM-DD)
        end: End date string (YYYY-MM-DD)

    Returns:
        Polars DataFrame with columns: date, stid, aqm_max
    """
    dates = pd.date_range(start, end, freq='D')
    aqm_data = []

    print(f"Fetching AQM data for {len(dates)} days...")

    for i, date in enumerate(dates):
        try:
            # Get 12Z cycle for max_8hr_o3
            H = Herbie(
                date.strftime('%Y-%m-%d 12:00'),
                model='aqm',
                product='max_8hr_o3',
                fxx=0
            )
            local_file = H.download()
            ds = xr.open_dataset(local_file, engine='cfgrib', decode_times=False)

            station_vals = extract_at_stations(ds, BASIN_STATIONS)

            for stid, val in station_vals.items():
                aqm_data.append({
                    'date': date.date(),
                    'stid': stid,
                    'aqm_max': val
                })

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(dates)} days...")

        except Exception as e:
            print(f"  {date.date()}: Error - {e}")

    return pl.DataFrame(aqm_data)


def main():
    parser = argparse.ArgumentParser(description='Fetch AQM forecasts via Herbie')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', required=True, help='Output parquet file path')

    args = parser.parse_args()

    df = fetch_aqm_data(args.start, args.end)

    # Save to parquet
    df.write_parquet(args.output)
    print(f"\nSaved {len(df)} rows to {args.output}")

    # Print summary
    print("\nAQM summary by station:")
    summary = df.group_by('stid').agg([
        pl.col('aqm_max').mean().round(1).alias('mean_ppb'),
        pl.col('aqm_max').max().round(1).alias('max_ppb'),
        pl.col('aqm_max').count().alias('n_days'),
    ])
    print(summary.sort('stid'))


if __name__ == '__main__':
    main()
