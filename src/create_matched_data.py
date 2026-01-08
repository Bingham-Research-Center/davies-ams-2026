"""
Create matched observations and AQM forecast dataset.
Combines UDAQ (QRS, QV4) and BRC (UBHSP, UB7ST, UBCSP) stations.
"""

import polars as pl
from pathlib import Path

from stations import OZONE_STATIONS

DATA_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_PATH = DATA_DIR / 'all_matched_obs_aqm.parquet'

# Winters to process
WINTERS = ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']

# Station network mapping
UDAQ_STATIONS = ['QRS', 'QV4']
BRC_STATIONS = ['UBHSP', 'UB7ST', 'UBCSP']
TARGET_STATIONS = UDAQ_STATIONS + BRC_STATIONS


def get_winter_from_date(date: pl.Expr) -> pl.Expr:
    """Determine winter season from date (Dec-Mar spans two years)."""
    year = date.dt.year()
    month = date.dt.month()
    # Dec belongs to winter starting that year, Jan-Mar belongs to winter starting prev year
    start_year = pl.when(month >= 12).then(year).otherwise(year - 1)
    end_year = start_year + 1
    return start_year.cast(pl.Utf8) + '-' + (end_year % 100).cast(pl.Utf8).str.zfill(2)


def compute_mda8(df: pl.DataFrame) -> pl.DataFrame:
    """
    Compute Maximum Daily 8-hour Average (MDA8) ozone for each station.

    Args:
        df: Hourly ozone data with date_time, stid, value columns

    Returns:
        DataFrame with date, stid, obs_mda8 columns
    """
    # Filter for ozone concentration and target stations
    ozone = df.filter(
        (pl.col('variable') == 'ozone_concentration') &
        (pl.col('stid').is_in(TARGET_STATIONS))
    )

    if len(ozone) == 0:
        return pl.DataFrame(schema={'date': pl.Date, 'stid': pl.Utf8, 'obs_mda8': pl.Float64})

    # Sort by station and time for rolling calculation
    ozone = ozone.sort(['stid', 'date_time'])

    # Compute rolling 8-hour mean per station
    ozone = ozone.with_columns([
        pl.col('value')
        .rolling_mean(window_size=8, min_periods=6)
        .over('stid')
        .alias('rolling_8hr')
    ])

    # Extract date and compute daily max of rolling 8-hour mean
    ozone = ozone.with_columns([
        pl.col('date_time').dt.date().alias('date')
    ])

    mda8 = ozone.group_by(['date', 'stid']).agg([
        pl.col('rolling_8hr').max().alias('obs_mda8')
    ])

    return mda8


def load_ozone_data() -> pl.DataFrame:
    """Load and process all winter ozone data files."""
    all_mda8 = []

    for winter in WINTERS:
        ozone_path = DATA_DIR / f'winter{winter}_ozone.parquet'
        if not ozone_path.exists():
            print(f"  Warning: {ozone_path.name} not found, skipping")
            continue

        print(f"  Processing {ozone_path.name}...")
        df = pl.read_parquet(ozone_path)
        mda8 = compute_mda8(df)

        if len(mda8) > 0:
            all_mda8.append(mda8)
            print(f"    Found {len(mda8)} daily MDA8 values")

    if not all_mda8:
        raise ValueError("No ozone data found")

    return pl.concat(all_mda8)


def load_aqm_data() -> pl.DataFrame:
    """Load all winter AQM forecast data files."""
    all_aqm = []

    for winter in WINTERS:
        aqm_path = DATA_DIR / f'winter{winter}_aqm.parquet'
        if not aqm_path.exists():
            print(f"  Warning: {aqm_path.name} not found, skipping")
            continue

        print(f"  Processing {aqm_path.name}...")
        df = pl.read_parquet(aqm_path)

        # Filter for target stations
        df = df.filter(pl.col('stid').is_in(TARGET_STATIONS))

        if len(df) > 0:
            all_aqm.append(df)
            print(f"    Found {len(df)} AQM forecasts")

    if not all_aqm:
        raise ValueError("No AQM data found")

    return pl.concat(all_aqm)


def main():
    print("Creating matched observations and AQM data...")
    print(f"Target stations: {TARGET_STATIONS}")
    print()

    # Load observations
    print("[1/3] Loading and computing MDA8 from ozone observations...")
    obs_df = load_ozone_data()
    print(f"  Total MDA8 observations: {len(obs_df)}")
    print()

    # Load AQM forecasts
    print("[2/3] Loading AQM forecasts...")
    aqm_df = load_aqm_data()
    print(f"  Total AQM forecasts: {len(aqm_df)}")
    print()

    # Join observations with AQM
    print("[3/3] Matching observations with AQM forecasts...")
    matched = obs_df.join(aqm_df, on=['date', 'stid'], how='inner')

    # Add winter season column
    matched = matched.with_columns([
        get_winter_from_date(pl.col('date')).alias('winter')
    ])

    # Add source column based on station network
    matched = matched.with_columns([
        pl.when(pl.col('stid').is_in(UDAQ_STATIONS))
        .then(pl.lit('UDAQ'))
        .otherwise(pl.lit('BRC'))
        .alias('source')
    ])

    # Reorder columns to match expected schema
    matched = matched.select(['date', 'stid', 'obs_mda8', 'winter', 'source', 'aqm_max'])
    matched = matched.sort(['date', 'stid'])

    # Save
    matched.write_parquet(OUTPUT_PATH)
    print(f"\nSaved to {OUTPUT_PATH}")

    # Summary
    print(f"\nSummary:")
    print(f"  Total matched records: {len(matched)}")
    print(f"\n  By source:")
    print(matched.group_by('source').len().sort('source'))
    print(f"\n  By station:")
    print(matched.group_by('stid').len().sort('stid'))
    print(f"\n  By winter:")
    print(matched.group_by('winter').len().sort('winter'))


if __name__ == '__main__':
    main()
