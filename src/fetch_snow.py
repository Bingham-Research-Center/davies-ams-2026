import argparse
import polars as pl
from synoptic import TimeSeries

from stations import ALL_STATIONS, get_available_snow_stations

SNOW_VARS = ['snow_depth', 'snow_accum_24_hour']


def fetch_snow_data(start: str, end: str, stations: list[str] | None = None) -> pl.DataFrame:
    if stations is None:
        stations = get_available_snow_stations(start)

    if not stations:
        print(f"No stations with snow data available for {start}")
        return pl.DataFrame()

    print(f"Fetching snow data...")
    print(f"  Period: {start} to {end}")
    print(f"  Stations: {len(stations)}")
    print(f"  Variables: {', '.join(SNOW_VARS)}")

    df = TimeSeries(stid=stations, start=start, end=end, vars=SNOW_VARS).df()

    network_map = {stid: s.network for stid, s in ALL_STATIONS.items()}
    df = df.with_columns([pl.col('stid').replace_strict(network_map, default='Unknown').alias('network')])

    print(f"  Retrieved {len(df)} observations")
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--stations', nargs='*')
    args = parser.parse_args()

    available = get_available_snow_stations(args.start)
    print(f"Stations with snow data for {args.start}:")
    for stid in available:
        name = ALL_STATIONS[stid].name if stid in ALL_STATIONS else stid
        network = ALL_STATIONS[stid].network if stid in ALL_STATIONS else 'Unknown'
        print(f"  {stid}: {name} ({network})")
    print()

    stations = args.stations if args.stations else None
    df = fetch_snow_data(args.start, args.end, stations)

    if len(df) == 0:
        print("No data retrieved")
        return

    df.write_parquet(args.output)
    print(f"Saved to {args.output}")

    print("\nSummary by station:")
    snow_depth = df.filter(pl.col('variable') == 'snow_depth')
    if len(snow_depth) > 0:
        summary = snow_depth.group_by(['stid', 'network']).agg([
            pl.col('value').mean().round(2).alias('mean_cm'),
            pl.col('value').max().round(2).alias('max_cm'),
            pl.col('value').count().alias('n_obs'),
        ]).sort(['network', 'stid'])
        print("\nSnow Depth (cm):")
        print(summary)


if __name__ == '__main__':
    main()
