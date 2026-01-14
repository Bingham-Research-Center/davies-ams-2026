import argparse
import os

from stations import OZONE_STATIONS
from fetch_observations import fetch_ozone_data
from fetch_aqm import fetch_aqm_data


def parse_winter_span(winter: str) -> tuple[int, int, str, str]:
    start_year, end_suffix = winter.split('-')
    start_year = int(start_year)
    end_year = int(f"20{end_suffix}")
    start = f"{start_year}-12-01"
    end = f"{end_year}-03-31"
    return start_year, end_year, start, end


def fetch_winter(winter: str, data_dir: str = 'data', stations: list[str] | None = None) -> tuple[str, str]:
    start_year, end_year, start, end = parse_winter_span(winter)

    obs_path = os.path.join(data_dir, f"winter{winter}_ozone.parquet")
    aqm_path = os.path.join(data_dir, f"winter{winter}_aqm.parquet")

    print(f"\n{'='*60}")
    print(f"Fetching Winter {winter} ({start} to {end})")
    print('='*60)

    print(f"\n[1/2] Fetching observations...")
    obs_df = fetch_ozone_data(start, end, stations=stations)
    obs_df.write_parquet(obs_path)
    print(f"  Saved: {obs_path}")

    print(f"\n[2/2] Fetching AQM forecasts...")
    aqm_df = fetch_aqm_data(start, end)
    aqm_df.write_parquet(aqm_path)
    print(f"  Saved: {aqm_path}")

    return obs_path, aqm_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--winters', nargs='+', type=str, required=True)
    parser.add_argument('--data-dir', default='data')
    args = parser.parse_args()

    os.makedirs(args.data_dir, exist_ok=True)

    stations = list(OZONE_STATIONS.keys())
    print(f"Fetching Uinta Basin stations: {stations}")
    print(f"Fetching {len(args.winters)} winter seasons: {args.winters}")

    for winter in sorted(args.winters):
        fetch_winter(winter, args.data_dir, stations=stations)

    print(f"\n{'='*60}")
    print("FETCH COMPLETE")
    print('='*60)
    for winter in sorted(args.winters):
        print(f"  {winter}: Obs OK  AQM OK")


if __name__ == '__main__':
    main()
