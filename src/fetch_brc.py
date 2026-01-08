import argparse
import os
import pandas as pd
import polars as pl

from stations import BASIN_STATIONS, RESEARCH_STATIONS, BRC_NAME_TO_STID, STID_TO_NAME

BRC_FILES = {
    '2010-11': '1-UBwinter2010-11ozonedata.xlsx',
    '2011-12': '2-UBwinter2011-12ozonedata.xlsx',
    '2012-13': '3-ALLSITESNov2012-Mar2013ozonedata_.xlsx',
    '2013-14': '4-ALLSITESNov2013-Mar2014ozonedata.xlsx',
    '2014-15': '5-ALLSITESNov2014-Mar2015ozonedata.xlsx',
    '2015-16': '6-ALLSITESNov2015-Mar2016ozonedata.xlsx',
    '2016-17': '7-ALLSITESNov2016-Mar2017ozonedata.xlsx',
    '2017-18': '8-ALLSITESNov2017-Mar2018ozonedata.xlsx',
    '2018-19': '9-ALLSITESNov2018-Mar2019ozonedata.xlsx',
    '2019-20': '10-ALLSITESNov2019-Mar2020ozonedata.xlsx',
    '2020-21': '11-ALLSITESDec2020-Mar2021ozonedata_.xlsx',
    '2021-22': '12-ALLSITESDec2021-Mar2022ozonedata.xlsx',
    '2022-23': '13-ALLSITESDec2022-Mar2023ozonedata.xlsx',
    '2023-24': '14-ALLSITESDec2023-Mar2024ozonedata.xlsx',
    '2024-25': '15-ALLSITESDec2024-Mar2025ozonedata.xlsx',
}


def get_region(stid: str) -> str:
    if stid in BASIN_STATIONS:
        return 'Basin'
    elif stid in RESEARCH_STATIONS:
        return 'Research'
    else:
        return 'BRC'


def parse_brc_file(file_path: str) -> pl.DataFrame:
    print(f"Parsing: {file_path}")

    df = pd.read_excel(file_path, sheet_name='Hourly Data', header=None)
    site_row = df.iloc[1].tolist()

    site_names = []
    site_cols = []
    for i, name in enumerate(site_row[1:], start=1):
        name_str = str(name).strip()
        if name_str and name_str != 'nan' and name_str != 'Hour':
            site_names.append(name_str)
            site_cols.append(i)

    data = df.iloc[3:].copy()
    cols_to_use = [0] + site_cols
    data = data.iloc[:, cols_to_use]
    data.columns = ['date_time'] + site_names

    data['date_time'] = pd.to_datetime(data['date_time'], errors='coerce')
    data = data.dropna(subset=['date_time'])

    long_df = data.melt(id_vars=['date_time'], var_name='site', value_name='value')
    long_df['stid'] = long_df['site'].map(BRC_NAME_TO_STID)

    unmapped = long_df[long_df['stid'].isna()]['site'].unique()
    if len(unmapped) > 0:
        print(f"  Warning: Unmapped sites: {list(unmapped)}")

    long_df = long_df.dropna(subset=['stid', 'value'])
    long_df['value'] = pd.to_numeric(long_df['value'], errors='coerce')
    long_df = long_df.dropna(subset=['value'])

    long_df['name'] = long_df['stid'].map(STID_TO_NAME)
    long_df['variable'] = 'ozone_concentration'
    long_df['region'] = long_df['stid'].apply(get_region)

    result = long_df[['date_time', 'stid', 'name', 'variable', 'value', 'region']]
    pl_df = pl.from_pandas(result)

    print(f"  Retrieved {len(pl_df)} observations from {len(site_names)} sites")
    return pl_df


def fetch_brc_data(winter: str, brc_dir: str = 'brc_data') -> pl.DataFrame:
    if winter not in BRC_FILES:
        raise ValueError(f"No BRC file for winter {winter}. Available: {sorted(BRC_FILES.keys())}")

    file_name = BRC_FILES[winter]
    file_path = os.path.join(brc_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"BRC file not found: {file_path}")

    return parse_brc_file(file_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--winter', type=str, required=True)
    parser.add_argument('--brc-dir', default='brc_data')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    df = fetch_brc_data(args.winter, args.brc_dir)

    df.write_parquet(args.output)
    print(f"\nSaved to {args.output}")

    print("\nSummary by station:")
    summary = df.group_by(['stid', 'name', 'region']).agg([
        pl.col('value').mean().round(1).alias('mean_ppb'),
        pl.col('value').max().round(0).alias('max_ppb'),
        pl.col('value').count().alias('n_obs'),
    ])
    print(summary.sort(['region', 'stid']))


if __name__ == '__main__':
    main()
