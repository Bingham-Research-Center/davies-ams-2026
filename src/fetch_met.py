import argparse
import polars as pl
from synoptic import TimeSeries

from stations import ALL_STATIONS, get_stations_by_network

MET_VARS = ['air_temp', 'relative_humidity', 'wind_speed', 'wind_direction', 'solar_radiation']

MET_STATION_IDS = (
    [s.stid for s in get_stations_by_network('UDAQ')] +
    [s.stid for s in get_stations_by_network('UDOT')] +
    [s.stid for s in get_stations_by_network('BRC')]
)


def fetch_met_data(start: str, end: str, stations: list[str] | None = None) -> pl.DataFrame:
    if stations is None:
        stations = MET_STATION_IDS

    print(f"Fetching meteorology data...")
    print(f"  Period: {start} to {end}")
    print(f"  Stations: {len(stations)}")
    print(f"  Variables: {', '.join(MET_VARS)}")

    df = TimeSeries(stid=stations, start=start, end=end, vars=MET_VARS).df()

    network_map = {stid: s.network for stid, s in ALL_STATIONS.items()}
    df = df.with_columns([pl.col('stid').replace_strict(network_map, default='Other').alias('network')])

    print(f"  Retrieved {len(df)} observations")
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--stations', nargs='*')
    args = parser.parse_args()

    stations = args.stations if args.stations else None
    df = fetch_met_data(args.start, args.end, stations)

    df.write_parquet(args.output)
    print(f"Saved to {args.output}")

    print("\nSummary by variable:")
    for var in MET_VARS:
        var_df = df.filter(pl.col('variable') == var)
        if len(var_df) > 0:
            print(f"\n  {var}:")
            summary = var_df.group_by(['stid', 'network']).agg([
                pl.col('value').mean().round(2).alias('mean'),
                pl.col('value').min().round(2).alias('min'),
                pl.col('value').max().round(2).alias('max'),
                pl.col('value').count().alias('n_obs'),
            ]).sort(['network', 'stid'])
            print(summary)


if __name__ == '__main__':
    main()
