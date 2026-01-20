"""
Time series plot for February 4-8, 2023 ozone event case study.

Shows multi-day evolution of observed vs forecast ozone concentrations,
illustrating CLYFAR and AQM performance during a high ozone episode.
"""

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from pathlib import Path
from datetime import date

from verification_metrics import THRESHOLD

DATA_DIR = Path(__file__).parent.parent / 'data'
CLYFAR_PATH = DATA_DIR / 'clyfar_hindcast_stats.csv'
AQM_FXX24_PATH = DATA_DIR / 'winter2022-23_aqm_fxx24.parquet'
OBS_PATH = DATA_DIR / 'all_matched_obs_aqm.parquet'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'

# Case study period
CASE_START = date(2023, 2, 4)
CASE_END = date(2023, 2, 8)

# Key stations for the case study
CASE_STATIONS = ['UBHSP', 'UB7ST', 'UBCSP', 'QRS']

# Station display names
STATION_NAMES = {
    'UBHSP': 'Horsepool',
    'UB7ST': 'Seven Sisters',
    'UBCSP': 'Castle Peak',
    'QRS': 'Roosevelt',
}


def load_case_study_data() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Load and filter data for case study period.

    Returns:
        obs: Observations for case period with station breakdown
        clyfar: CLYFAR forecasts for case period
        aqm: AQM Day 1 forecasts for case period
    """
    # Load observations
    obs_all = pl.read_parquet(OBS_PATH)
    obs = obs_all.filter(
        (pl.col('date') >= CASE_START) &
        (pl.col('date') <= CASE_END) &
        pl.col('stid').is_in(CASE_STATIONS)
    ).select(['date', 'stid', 'obs_mda8']).sort(['date', 'stid'])

    # Load CLYFAR data
    clyfar = pl.read_csv(CLYFAR_PATH)
    clyfar = clyfar.with_columns([
        pl.col('valid_date').str.to_date().alias('date')
    ]).filter(
        (pl.col('date') >= CASE_START) &
        (pl.col('date') <= CASE_END)
    ).select(['date', 'forecast_p50', 'forecast_p10', 'forecast_p90', 'poss_elevated']).sort('date')

    # Load AQM fxx=24 (Day 1) forecasts
    aqm = pl.read_parquet(AQM_FXX24_PATH)
    # Shift date by +1 day to get valid date
    aqm = aqm.with_columns([
        (pl.col('date') + pl.duration(days=1)).alias('date')
    ]).filter(
        (pl.col('date') >= CASE_START) &
        (pl.col('date') <= CASE_END) &
        pl.col('stid').is_in(CASE_STATIONS)
    ).select(['date', 'stid', 'aqm_max']).sort(['date', 'stid'])

    return obs, clyfar, aqm


def plot_timeseries() -> None:
    """Create time series plot for case study period."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    obs, clyfar, aqm = load_case_study_data()

    # Get unique dates
    dates = clyfar['date'].to_list()

    # Prepare figure
    fig, ax = plt.subplots(figsize=(12, 7))

    # Station colors
    station_colors = {
        'UBHSP': '#e74c3c',  # Red
        'UB7ST': '#3498db',  # Blue
        'UBCSP': '#2ecc71',  # Green
        'QRS': '#9b59b6',    # Purple
    }

    # Plot observed values by station
    for stid in CASE_STATIONS:
        station_obs = obs.filter(pl.col('stid') == stid)
        if len(station_obs) > 0:
            st_dates = station_obs['date'].to_list()
            st_vals = station_obs['obs_mda8'].to_list()
            ax.plot(st_dates, st_vals, 'o-', color=station_colors[stid],
                    linewidth=2, markersize=8, label=f'Obs: {STATION_NAMES[stid]}',
                    zorder=5)

    # Get CLYFAR values
    clf_dates = clyfar['date'].to_list()
    clf_p50 = clyfar['forecast_p50'].to_list()
    clf_p10 = clyfar['forecast_p10'].to_list()
    clf_p90 = clyfar['forecast_p90'].to_list()
    clf_poss = clyfar['poss_elevated'].to_list()

    # Plot CLYFAR ensemble spread as shading
    ax.fill_between(clf_dates, clf_p10, clf_p90, alpha=0.25, color='#f39c12',
                    label='CLYFAR p10-p90 spread', zorder=2)

    # Plot CLYFAR p50 and p90
    ax.plot(clf_dates, clf_p50, 's--', color='#f39c12', linewidth=2.5, markersize=9,
            label='CLYFAR p50', zorder=4, markeredgecolor='black', markeredgewidth=1)
    ax.plot(clf_dates, clf_p90, 'd--', color='#d35400', linewidth=2.5, markersize=9,
            label='CLYFAR p90', zorder=4, markeredgecolor='black', markeredgewidth=1)

    # Calculate and plot daily mean AQM
    aqm_daily = aqm.group_by('date').agg(pl.col('aqm_max').mean().alias('aqm_mean')).sort('date')
    aqm_dates = aqm_daily['date'].to_list()
    aqm_vals = aqm_daily['aqm_mean'].to_list()
    ax.plot(aqm_dates, aqm_vals, '^--', color='#34495e', linewidth=2.5, markersize=10,
            label='AQM Day 1 (mean)', zorder=4, markeredgecolor='black', markeredgewidth=1)

    # Add 70 ppb threshold line
    ax.axhline(THRESHOLD, color='red', linestyle=':', linewidth=2, alpha=0.7,
               label=f'{THRESHOLD} ppb threshold', zorder=1)

    # Add poss_elevated annotations
    for i, (d, poss) in enumerate(zip(clf_dates, clf_poss)):
        y_pos = clf_p90[i] + 3
        ax.annotate(f'p={poss:.2f}', xy=(d, y_pos), fontsize=9,
                    ha='center', va='bottom', color='#8e44ad', fontweight='bold')

    # Highlight Feb 5 (worst miss) and Feb 7 (CLYFAR success)
    ax.axvspan(date(2023, 2, 5), date(2023, 2, 5), alpha=0.15, color='red', zorder=0)
    ax.axvspan(date(2023, 2, 7), date(2023, 2, 7), alpha=0.15, color='green', zorder=0)

    # Add annotations for key dates
    ax.annotate('MISS\n(poss=0.25)', xy=(date(2023, 2, 5), 128), fontsize=10,
                ha='center', va='bottom', color='red', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', alpha=0.9))
    ax.annotate('HIT\n(poss=0.62)', xy=(date(2023, 2, 7), 115), fontsize=10,
                ha='center', va='bottom', color='green', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='green', alpha=0.9))

    # Formatting
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('MDA8 Ozone (ppb)', fontsize=12)
    ax.set_ylim(30, 140)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    plt.xticks(rotation=0, fontsize=11)

    # Grid
    ax.grid(True, alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # Legend
    ax.legend(loc='upper left', fontsize=9, ncol=2, framealpha=0.95)

    # Title
    fig.suptitle('Early February 2023 Ozone Event', fontsize=14, fontweight='bold')
    ax.set_title('Multi-day episode: Feb 5 (miss) vs Feb 7 (CLYFAR p90 success)', fontsize=11, style='italic')

    plt.tight_layout()

    # Save figure
    output_path = OUTPUT_DIR / 'case_study_feb2023_timeseries.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def print_case_summary() -> None:
    """Print case study data summary."""
    obs, clyfar, aqm = load_case_study_data()

    print('\n' + '=' * 80)
    print('CASE STUDY: EARLY FEBRUARY 2023 OZONE EVENT')
    print('=' * 80)

    print(f'\nPeriod: {CASE_START} to {CASE_END}')
    print(f'Stations: {", ".join(CASE_STATIONS)}')

    # Daily summary
    print(f'\n{"Date":<12} {"Peak Obs":>10} {"CLYFAR p50":>12} {"CLYFAR p90":>12} {"poss_elev":>10} {"AQM mean":>10} {"Result":<10}')
    print('-' * 80)

    for row in clyfar.iter_rows(named=True):
        d = row['date']

        # Get peak observed for the day
        day_obs = obs.filter(pl.col('date') == d)
        peak_obs = day_obs['obs_mda8'].max() if len(day_obs) > 0 else None

        # Get mean AQM for the day
        day_aqm = aqm.filter(pl.col('date') == d)
        mean_aqm = day_aqm['aqm_max'].mean() if len(day_aqm) > 0 else None

        # Determine result
        if peak_obs is not None and peak_obs >= THRESHOLD:
            if row['forecast_p90'] >= THRESHOLD:
                result = 'HIT (p90)'
            elif row['forecast_p50'] >= THRESHOLD:
                result = 'HIT (p50)'
            else:
                result = 'MISS'
        else:
            result = 'N/A'

        print(f'{str(d):<12} {peak_obs:>10.1f} {row["forecast_p50"]:>12.1f} {row["forecast_p90"]:>12.1f} '
              f'{row["poss_elevated"]:>10.2f} {mean_aqm:>10.1f} {result:<10}')


def main():
    """Main function."""
    print('Loading case study data...')

    # Print summary
    print_case_summary()

    # Create plot
    print('\nCreating time series plot...')
    plot_timeseries()

    print('\nDone!')


if __name__ == '__main__':
    main()
