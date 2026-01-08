import argparse
import polars as pl
from synoptic import TimeSeries

from stations import BASIN_STATIONS, RESEARCH_STATIONS, OZONE_STATIONS


def fetch_ozone_data(start: str, end: str, stations: list[str] | None = None) -> pl.DataFrame:
    if stations is None:
        stations = list(OZONE_STATIONS.keys())

    print(f"Fetching ozone data...")
    print(f"  Period: {start} to {end}")
    print(f"  Stations: {len(stations)}")

    df = TimeSeries(stid=stations, start=start, end=end, vars=['ozone_concentration']).df()

    basin_ids = list(BASIN_STATIONS.keys())
    research_ids = list(RESEARCH_STATIONS.keys())
    df = df.with_columns([
        pl.when(pl.col('stid').is_in(basin_ids))
        .then(pl.lit('Basin'))
        .when(pl.col('stid').is_in(research_ids))
        .then(pl.lit('Research'))
        .otherwise(pl.lit('Other'))
        .alias('region')
    ])

    print(f"  Retrieved {len(df)} observations")
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    df = fetch_ozone_data(args.start, args.end)
    df.write_parquet(args.output)
    print(f"Saved to {args.output}")

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
