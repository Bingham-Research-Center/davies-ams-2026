"""
Fetch snow data for all winters missing from the dataset.
"""
import argparse
from pathlib import Path

import polars as pl

from fetch_snow import fetch_snow_data
from stations import get_available_snow_stations

DATA_DIR = Path(__file__).parent.parent / 'data'

ALL_WINTERS = ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']


def parse_winter_span(winter: str) -> tuple[str, str]:
    """Parse winter string to start/end dates."""
    start_year, end_suffix = winter.split('-')
    start_year = int(start_year)
    end_year = int(f"20{end_suffix}")
    start = f"{start_year}-12-01"
    end = f"{end_year}-03-31"
    return start, end


def get_missing_winters() -> list[str]:
    """Return list of winters without snow data files."""
    missing = []
    for winter in ALL_WINTERS:
        path = DATA_DIR / f'winter{winter}_snow.parquet'
        if not path.exists():
            missing.append(winter)
    return missing


def fetch_winter_snow(winter: str) -> pl.DataFrame:
    """Fetch snow data for a single winter season."""
    start, end = parse_winter_span(winter)
    stations = get_available_snow_stations(start)

    print(f"  Available stations: {stations}")
    df = fetch_snow_data(start, end, stations)
    return df


def main():
    parser = argparse.ArgumentParser(description='Fetch snow data for all winters')
    parser.add_argument('--winters', nargs='*',
                        help='Specific winters to fetch (default: all missing)')
    parser.add_argument('--force', action='store_true',
                        help='Re-fetch even if file exists')
    args = parser.parse_args()

    if args.winters:
        winters = args.winters
    else:
        winters = get_missing_winters() if not args.force else ALL_WINTERS

    if not winters:
        print("All snow data files present. Use --force to re-fetch.")
        return

    print(f"Fetching snow data for {len(winters)} winters: {winters}")

    for winter in sorted(winters):
        print(f"\n{'='*50}")
        print(f"Winter {winter}")
        print('='*50)

        df = fetch_winter_snow(winter)

        if len(df) == 0:
            print(f"  Warning: No data retrieved for {winter}")
            continue

        output_path = DATA_DIR / f'winter{winter}_snow.parquet'
        df.write_parquet(output_path)
        print(f"  Saved: {output_path} ({len(df)} rows)")

    print("\nDone!")


if __name__ == '__main__':
    main()
