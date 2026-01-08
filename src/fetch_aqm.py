import argparse
import numpy as np
import pandas as pd
import polars as pl
import xarray as xr
from herbie import Herbie

from stations import OZONE_STATIONS, get_station_coords


def extract_at_stations(ds: xr.Dataset, stations: dict[str, tuple[float, float]]) -> dict[str, float]:
    lats = ds['latitude'].values
    lons = ds['longitude'].values
    data = ds['unknown']

    results = {}
    for stid, (slat, slon) in stations.items():
        slon_360 = 360 + slon if slon < 0 else slon
        dist = np.sqrt((lats - slat)**2 + (lons - slon_360)**2)
        min_idx = np.unravel_index(dist.argmin(), dist.shape)
        y_idx, x_idx = min_idx
        val = float(data.isel(step=0, y=y_idx, x=x_idx))
        results[stid] = val

    return results


def fetch_aqm_data(start: str, end: str) -> pl.DataFrame:
    dates = pd.date_range(start, end, freq='D')
    aqm_data = []
    station_coords = get_station_coords(list(OZONE_STATIONS.keys()))

    print(f"Fetching AQM data...")
    print(f"  Period: {start} to {end}")
    print(f"  Stations: {len(station_coords)}")

    for i, date in enumerate(dates):
        H = Herbie(date.strftime('%Y-%m-%d 12:00'), model='aqm', product='max_8hr_o3', fxx=0)
        local_file = H.download()
        ds = xr.open_dataset(local_file, engine='cfgrib', decode_times=False)
        station_vals = extract_at_stations(ds, station_coords)

        for stid, val in station_vals.items():
            aqm_data.append({'date': date.date(), 'stid': stid, 'aqm_max': val})

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(dates)} days...")

    print(f"  Retrieved {len(aqm_data)} records")
    return pl.DataFrame(aqm_data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    df = fetch_aqm_data(args.start, args.end)
    df.write_parquet(args.output)
    print(f"\nSaved {len(df)} rows to {args.output}")

    print("\nAQM summary by station:")
    summary = df.group_by('stid').agg([
        pl.col('aqm_max').mean().round(1).alias('mean_ppb'),
        pl.col('aqm_max').max().round(1).alias('max_ppb'),
        pl.col('aqm_max').count().alias('n_days'),
    ])
    print(summary.sort('stid'))


if __name__ == '__main__':
    main()
