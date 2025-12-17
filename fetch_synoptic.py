#!/usr/bin/env python3
"""
Fetch observation data from Synoptic API and save to Polars DataFrame.

Requires:
    pip install SynopticPy

Usage:
    export SYNOPTIC_TOKEN="your_token_here"
    python fetch_synoptic.py
"""

# ============== CONFIGURATION ==============
# Modify these to fetch different data

STATIONS = ['QV4', 'QRS', 'A3822', 'A1386']  # Station IDs

VARIABLES = [
    'ozone_concentration',
    'air_temp',
    # 'wind_speed',
    # 'relative_humidity',
    # 'pm_2_5_concentration',
]

START_DATE = '2023-02-21T00:00'
END_DATE = '2023-02-28T23:59'

OUTPUT_FILE = 'synoptic_data.parquet'  # or .csv

# ============================================

from synoptic import TimeSeries


def fetch_data():
    """Fetch data from Synoptic API and save to file."""
    df = TimeSeries(
        stid=STATIONS,
        start=START_DATE,
        end=END_DATE,
        vars=VARIABLES,
    ).df()

    # Save to file
    if OUTPUT_FILE.endswith('.parquet'):
        df.write_parquet(OUTPUT_FILE)
    else:
        df.write_csv(OUTPUT_FILE)

    print(f"Saved {len(df)} rows to {OUTPUT_FILE}")
    return df


if __name__ == '__main__':
    fetch_data()
