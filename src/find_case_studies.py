"""
Identify case study dates for AMS poster.

Finds:
1. Worst miss - largest underprediction on an exceedance day
2. Worst false alarm - highest AQM forecast that didn't verify
3. Best hit - smallest absolute bias on correctly predicted exceedance

Also provides meteorological context and GFS snow comparison.
"""

import polars as pl
from pathlib import Path
from datetime import date, timedelta

DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_PATH = DATA_DIR / 'all_matched_obs_aqm.parquet'
THRESHOLD = 70  # ppb NAAQS threshold

# Basin center for GFS extraction
BASIN_LAT = 40.0
BASIN_LON = 360 - 109.5  # Convert to 0-360 for GFS


def load_data() -> pl.DataFrame:
    """Load matched obs/AQM data with bias computed."""
    df = pl.read_parquet(DATA_PATH)
    df = df.with_columns((pl.col('aqm_max') - pl.col('obs_mda8')).alias('bias'))
    return df


def find_worst_miss(df: pl.DataFrame) -> pl.DataFrame:
    """Find exceedance day with largest underprediction using strict validation.

    Only considers dates where ALL reporting stations exceeded threshold.
    This ensures it was a real basin-wide event, not an isolated sensor issue.
    """
    # Find dates where ALL reporting stations exceeded threshold
    by_date = df.filter(pl.col('obs_mda8').is_not_null()).group_by('date').agg([
        pl.len().alias('n_reporting'),
        (pl.col('obs_mda8') >= THRESHOLD).sum().alias('n_exceeded'),
    ])

    validated_dates = by_date.filter(
        (pl.col('n_exceeded') == pl.col('n_reporting')) &
        (pl.col('n_reporting') >= 3)  # At least 3 stations reporting
    ).select('date')

    # Filter to exceedance days on validated dates only
    exceedance_days = df.filter(
        (pl.col('obs_mda8') >= THRESHOLD) &
        pl.col('date').is_in(validated_dates['date'])
    )

    return exceedance_days.sort('bias').head(1)


def find_worst_false_alarm(df: pl.DataFrame) -> pl.DataFrame:
    """Find false alarm with highest AQM forecast using multi-station validation.

    Only considers dates where NO station exceeded threshold to ensure
    a clean false alarm (not spatial variability).
    """
    # Find dates where no station exceeded threshold
    clean_dates = (
        df.group_by('date')
        .agg(pl.col('obs_mda8').max().alias('max_obs'))
        .filter(pl.col('max_obs') < THRESHOLD)
        .select('date')
    )

    # Filter to false alarms on clean dates only
    false_alarms = df.filter(
        (pl.col('aqm_max') >= THRESHOLD) &
        (pl.col('obs_mda8') < THRESHOLD) &
        pl.col('date').is_in(clean_dates['date'])
    )

    return false_alarms.sort('aqm_max', descending=True).head(1)


def find_best_hit(df: pl.DataFrame) -> pl.DataFrame:
    """Find hit with smallest absolute bias using strict validation.

    Only considers dates where ALL reporting stations exceeded threshold.
    This ensures the hit occurred during a real basin-wide event.
    """
    # Find dates where ALL reporting stations exceeded threshold
    by_date = df.filter(pl.col('obs_mda8').is_not_null()).group_by('date').agg([
        pl.len().alias('n_reporting'),
        (pl.col('obs_mda8') >= THRESHOLD).sum().alias('n_exceeded'),
    ])

    validated_dates = by_date.filter(
        (pl.col('n_exceeded') == pl.col('n_reporting')) &
        (pl.col('n_reporting') >= 3)  # At least 3 stations reporting
    ).select('date')

    # Filter to hits on validated dates only
    hits = df.filter(
        (pl.col('aqm_max') >= THRESHOLD) &
        (pl.col('obs_mda8') >= THRESHOLD) &
        pl.col('date').is_in(validated_dates['date'])
    )

    return hits.with_columns(
        pl.col('bias').abs().alias('abs_bias')
    ).sort('abs_bias').head(1).drop('abs_bias')


def print_case_study(label: str, row: pl.DataFrame) -> None:
    """Print a single case study row."""
    r = row.row(0, named=True)
    print(f'\n{label}:')
    print(f'  Date:    {r["date"]}')
    print(f'  Station: {r["stid"]}')
    print(f'  Obs:     {r["obs_mda8"]:.1f} ppb')
    print(f'  AQM:     {r["aqm_max"]:.1f} ppb')
    print(f'  Bias:    {r["bias"]:+.1f} ppb')
    print(f'  Winter:  {r["winter"]}')


def print_event_context(df: pl.DataFrame, target_date, days: int = 2) -> None:
    """Print all stations around a target date to show event context."""
    window = df.filter(
        (pl.col('date') >= target_date - timedelta(days=days)) &
        (pl.col('date') <= target_date + timedelta(days=days))
    ).sort(['date', 'stid'])

    print(f'\n  Event context ({days} days before/after):')
    print(f'  {"Date":<12} {"Station":<8} {"Obs":>6} {"AQM":>6} {"Bias":>7}')
    print('  ' + '-' * 43)

    for row in window.iter_rows(named=True):
        obs = row['obs_mda8']
        if obs is None:
            continue
        marker = '*' if obs >= THRESHOLD else ' '
        print(f'  {str(row["date"]):<12} {row["stid"]:<8} {obs:>6.1f} {row["aqm_max"]:>6.1f} {row["bias"]:>+7.1f}{marker}')


def get_winter_season(d: date) -> str:
    """Get winter season string (e.g., '2022-23') for a date."""
    if d.month >= 10:  # Oct-Dec
        return f'{d.year}-{str(d.year + 1)[2:]}'
    else:  # Jan-Mar
        return f'{d.year - 1}-{str(d.year)[2:]}'


def get_met_context(d: date) -> dict:
    """Get meteorological context for a date from parquet files."""
    winter = get_winter_season(d)
    result = {'snow_in': None, 'delta_t': None, 'wind': None, 'rh': None}

    # Snow data
    snow_path = DATA_DIR / f'winter{winter}_snow.parquet'
    if snow_path.exists():
        snow = pl.read_parquet(snow_path)
        day_snow = snow.filter(
            (pl.col('date_time').dt.date() == d) &
            (pl.col('variable') == 'snow_depth')
        )
        if len(day_snow) > 0:
            avg_mm = day_snow['value'].mean()
            result['snow_in'] = avg_mm / 25.4 if avg_mm else 0

    # Met data
    met_path = DATA_DIR / f'winter{winter}_met.parquet'
    if met_path.exists():
        met = pl.read_parquet(met_path)
        day_met = met.filter(pl.col('date_time').dt.date() == d)

        # Temperature range (inversion proxy)
        temps = day_met.filter(pl.col('variable') == 'air_temp')
        if len(temps) > 0:
            t_min = temps['value'].min()
            t_max = temps['value'].max()
            if t_min is not None and t_max is not None:
                result['delta_t'] = t_max - t_min

        # Wind speed
        winds = day_met.filter(pl.col('variable') == 'wind_speed')
        if len(winds) > 0:
            result['wind'] = winds['value'].mean()

        # Relative humidity
        rh = day_met.filter(pl.col('variable') == 'relative_humidity')
        if len(rh) > 0:
            result['rh'] = rh['value'].mean()

    return result


def get_gfs_snow(d: date) -> float | None:
    """Get GFS snow depth for a date via Herbie."""
    try:
        from herbie import Herbie
        H = Herbie(f'{d} 12:00', model='gfs', product='pgrb2.0p25', fxx=0)
        ds = H.xarray(':SNOD:surface')
        val_m = float(ds['sde'].sel(latitude=BASIN_LAT, longitude=BASIN_LON, method='nearest').values)
        return val_m * 39.37  # Convert m to inches
    except Exception:
        return None


def print_met_comparison(cases: list[tuple[str, date, float, float]]) -> None:
    """Print meteorological comparison table for case studies."""
    print('\n' + '=' * 75)
    print('METEOROLOGICAL CONTEXT')
    print('=' * 75)
    print(f'{"Date":<12} {"Case":<13} {"Snow":>7} {"ΔT(°C)":>8} {"Wind":>7} {"RH":>6} {"Obs":>6} {"AQM":>6}')
    print('-' * 75)

    for label, d, obs, aqm in cases:
        met = get_met_context(d)
        snow_str = f'{met["snow_in"]:.1f}"' if met['snow_in'] is not None else 'N/A'
        dt_str = f'{met["delta_t"]:.1f}' if met['delta_t'] is not None else 'N/A'
        wind_str = f'{met["wind"]:.1f}' if met['wind'] is not None else 'N/A'
        rh_str = f'{met["rh"]:.0f}%' if met['rh'] is not None else 'N/A'
        print(f'{str(d):<12} {label:<13} {snow_str:>7} {dt_str:>8} {wind_str:>7} {rh_str:>6} {obs:>6.0f} {aqm:>6.0f}')

    print()
    print('ΔT = diurnal temp range (smaller = stronger inversion)')


def print_gfs_comparison(cases: list[tuple[str, date]]) -> None:
    """Print GFS vs observed snow comparison."""
    print('\n' + '=' * 60)
    print('GFS SNOW DEPTH COMPARISON')
    print('=' * 60)
    print(f'{"Date":<12} {"Case":<13} {"GFS Snow":>10} {"Obs Snow":>10} {"Error":>8}')
    print('-' * 60)

    for label, d in cases:
        met = get_met_context(d)
        gfs_snow = get_gfs_snow(d)
        obs_snow = met['snow_in']

        if gfs_snow is not None and obs_snow is not None and obs_snow > 0:
            error = (gfs_snow - obs_snow) / obs_snow * 100
            print(f'{str(d):<12} {label:<13} {gfs_snow:>9.1f}" {obs_snow:>9.1f}" {error:>+7.0f}%')
        else:
            print(f'{str(d):<12} {label:<13} {"N/A":>10} {"N/A":>10} {"N/A":>8}')


def print_event_evolution(df: pl.DataFrame, start_date: date, end_date: date) -> None:
    """Print AQM error evolution over a multi-day event."""
    print('\n' + '=' * 65)
    print(f'AQM ERROR EVOLUTION ({start_date} to {end_date})')
    print('=' * 65)
    print(f'{"Date":<12} {"Mean Obs":>10} {"Mean AQM":>10} {"Mean Bias":>12} {"Phase":<12}')
    print('-' * 65)

    event = df.filter(
        (pl.col('date') >= start_date) & (pl.col('date') <= end_date)
    )

    by_date = event.group_by('date').agg([
        pl.col('obs_mda8').mean().alias('mean_obs'),
        pl.col('aqm_max').mean().alias('mean_aqm'),
        pl.col('bias').mean().alias('mean_bias'),
    ]).sort('date')

    phases = {
        date(2023, 2, 3): 'Onset',
        date(2023, 2, 4): 'Ramp-up',
        date(2023, 2, 5): 'Peak',
        date(2023, 2, 6): 'Peak',
        date(2023, 2, 7): 'Decay',
        date(2023, 2, 8): 'Decay',
    }

    for row in by_date.iter_rows(named=True):
        d = row['date']
        phase = phases.get(d, '')
        print(f'{str(d):<12} {row["mean_obs"]:>10.0f} {row["mean_aqm"]:>10.0f} {row["mean_bias"]:>+12.1f} {phase:<12}')

    print()
    print('Key finding: AQM struggles at event onset, improves as event matures')


def main():
    """Main function."""
    print('Loading data...')
    df = load_data()
    print(f'Loaded {len(df)} matched obs/AQM records')

    # Find case studies
    worst_miss = find_worst_miss(df)
    worst_fa = find_worst_false_alarm(df)
    best_hit = find_best_hit(df)

    # Extract key info
    wm = worst_miss.row(0, named=True)
    fa = worst_fa.row(0, named=True)
    bh = best_hit.row(0, named=True)

    # Print case study details
    print('\n' + '=' * 50)
    print('CASE STUDY DATES')
    print('=' * 50)

    print_case_study('WORST MISS (all stations exceeded)', worst_miss)
    print_event_context(df, wm['date'])

    print_case_study('FALSE ALARM (no station exceeded)', worst_fa)
    print_event_context(df, fa['date'])

    print_case_study('BEST HIT (all stations exceeded)', best_hit)
    print_event_context(df, bh['date'])

    # Summary table
    print('\n' + '-' * 50)
    print('Summary for poster annotation:')
    print('-' * 50)

    print(f'{"Case":<15} {"Date":<12} {"Station":<8} {"Obs":>6} {"AQM":>6} {"Bias":>7}')
    print('-' * 50)
    print(f'{"Worst Miss":<15} {str(wm["date"]):<12} {wm["stid"]:<8} {wm["obs_mda8"]:>6.1f} {wm["aqm_max"]:>6.1f} {wm["bias"]:>+7.1f}')
    print(f'{"False Alarm":<15} {str(fa["date"]):<12} {fa["stid"]:<8} {fa["obs_mda8"]:>6.1f} {fa["aqm_max"]:>6.1f} {fa["bias"]:>+7.1f}')
    print(f'{"Best Hit":<15} {str(bh["date"]):<12} {bh["stid"]:<8} {bh["obs_mda8"]:>6.1f} {bh["aqm_max"]:>6.1f} {bh["bias"]:>+7.1f}')

    # Meteorological context
    met_cases = [
        ('Worst Miss', wm['date'], wm['obs_mda8'], wm['aqm_max']),
        ('False Alarm', fa['date'], fa['obs_mda8'], fa['aqm_max']),
        ('Best Hit', bh['date'], bh['obs_mda8'], bh['aqm_max']),
    ]
    print_met_comparison(met_cases)

    # GFS snow comparison
    gfs_cases = [
        ('Worst Miss', wm['date']),
        ('False Alarm', fa['date']),
        ('Best Hit', bh['date']),
    ]
    print_gfs_comparison(gfs_cases)

    # Event evolution (Feb 2023 event)
    print_event_evolution(df, date(2023, 2, 3), date(2023, 2, 8))

    print('\nDone!')


if __name__ == '__main__':
    main()
