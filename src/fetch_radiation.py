import argparse
import polars as pl
from synoptic import TimeSeries

from stations import ALL_STATIONS, get_available_radiation_stations

RADIATION_VARS = ['solar_radiation', 'outgoing_radiation_sw', 'incoming_radiation_lw', 'outgoing_radiation_lw']


def fetch_radiation_data(start: str, end: str, stations: list[str] | None = None) -> pl.DataFrame:
    if stations is None:
        stations = get_available_radiation_stations(start)

    if not stations:
        print(f"No stations with full radiation data available for {start}")
        return pl.DataFrame()

    print(f"Fetching radiation data...")
    print(f"  Period: {start} to {end}")
    print(f"  Stations: {len(stations)}")
    print(f"  Variables: {', '.join(RADIATION_VARS)}")

    df = TimeSeries(stid=stations, start=start, end=end, vars=RADIATION_VARS).df()
    df = df.with_columns([pl.lit('BRC').alias('network')])

    print(f"  Retrieved {len(df)} observations")
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', required=True)
    parser.add_argument('--end', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--stations', nargs='*')
    args = parser.parse_args()

    available = get_available_radiation_stations(args.start)
    print(f"Stations with full radiation data for {args.start}:")
    for stid in available:
        name = ALL_STATIONS[stid].name if stid in ALL_STATIONS else stid
        print(f"  {stid}: {name}")
    print()

    stations = args.stations if args.stations else None
    df = fetch_radiation_data(args.start, args.end, stations)

    if len(df) == 0:
        print("No data retrieved")
        return

    df.write_parquet(args.output)
    print(f"Saved to {args.output}")

    print("\nSummary by variable:")
    for var in RADIATION_VARS:
        var_df = df.filter(pl.col('variable') == var)
        if len(var_df) > 0:
            summary = var_df.group_by('stid').agg([
                pl.col('value').mean().round(1).alias('mean_W/m2'),
                pl.col('value').max().round(1).alias('max_W/m2'),
                pl.col('value').count().alias('n_obs'),
            ]).sort('stid')
            print(f"\n  {var}:")
            print(summary)


if __name__ == '__main__':
    main()
