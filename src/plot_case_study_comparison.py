"""
Side-by-side comparison of Feb 5, 2023 (miss) vs Feb 7, 2023 (hit).

Illustrates the contrast between CLYFAR's worst and best performance days
during the early February 2023 ozone event.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import date

from verification_metrics import THRESHOLD

DATA_DIR = Path(__file__).parent.parent / 'data'
CLYFAR_PATH = DATA_DIR / 'clyfar_hindcast_stats.csv'
AQM_FXX24_PATH = DATA_DIR / 'winter2022-23_aqm_fxx24.parquet'
OBS_PATH = DATA_DIR / 'all_matched_obs_aqm.parquet'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'

# Case study dates
FEB5 = date(2023, 2, 5)  # Worst miss
FEB7 = date(2023, 2, 7)  # CLYFAR success
FEB13 = date(2023, 2, 13)  # Complete miss (tertiary case)

# Key stations
CASE_STATIONS = ['UBHSP', 'UB7ST', 'UBCSP', 'QRS']

# Station display names
STATION_NAMES = {
    'UBHSP': 'Horsepool',
    'UB7ST': 'Seven Sisters',
    'UBCSP': 'Castle Peak',
    'QRS': 'Roosevelt',
}


def load_day_data(target_date: date) -> dict:
    """Load all data for a specific date.

    Returns:
        Dict with obs (by station), clyfar metrics, and aqm (by station)
    """
    # Load observations
    obs_all = pl.read_parquet(OBS_PATH)
    obs = obs_all.filter(
        (pl.col('date') == target_date) &
        pl.col('stid').is_in(CASE_STATIONS)
    ).select(['stid', 'obs_mda8']).sort('stid')

    # Load CLYFAR data
    clyfar = pl.read_csv(CLYFAR_PATH)
    clyfar = clyfar.with_columns([
        pl.col('valid_date').str.to_date().alias('date')
    ]).filter(pl.col('date') == target_date)

    clyfar_data = clyfar.row(0, named=True) if len(clyfar) > 0 else None

    # Load AQM fxx=24 (Day 1) forecasts
    aqm = pl.read_parquet(AQM_FXX24_PATH)
    aqm = aqm.with_columns([
        (pl.col('date') + pl.duration(days=1)).alias('date')
    ]).filter(
        (pl.col('date') == target_date) &
        pl.col('stid').is_in(CASE_STATIONS)
    ).select(['stid', 'aqm_max']).sort('stid')

    return {
        'obs': obs,
        'clyfar': clyfar_data,
        'aqm': aqm,
    }


def plot_comparison_feb5_vs_feb7() -> None:
    """Create side-by-side comparison of Feb 5 (miss) vs Feb 7 (hit)."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load data for both days
    feb5_data = load_day_data(FEB5)
    feb7_data = load_day_data(FEB7)

    fig, axes = plt.subplots(1, 2, figsize=(14, 7), sharey=True)

    # Station positions
    stations = CASE_STATIONS
    x = np.arange(len(stations))
    bar_width = 0.22

    for ax, day_data, day_label, result_color, result_text in [
        (axes[0], feb5_data, 'Feb 5, 2023', '#e74c3c', 'MISS'),
        (axes[1], feb7_data, 'Feb 7, 2023', '#27ae60', 'HIT'),
    ]:
        # Get observed values
        obs_vals = []
        for stid in stations:
            row = day_data['obs'].filter(pl.col('stid') == stid)
            obs_vals.append(row['obs_mda8'][0] if len(row) > 0 else 0)

        # Get AQM values
        aqm_vals = []
        for stid in stations:
            row = day_data['aqm'].filter(pl.col('stid') == stid)
            aqm_vals.append(row['aqm_max'][0] if len(row) > 0 else 0)

        # Get CLYFAR values (same for all stations)
        clf = day_data['clyfar']
        clf_p50 = clf['forecast_p50'] if clf else 0
        clf_p90 = clf['forecast_p90'] if clf else 0
        poss_elev = clf['poss_elevated'] if clf else 0

        # Plot bars
        bars_obs = ax.bar(x - bar_width * 1.5, obs_vals, bar_width, label='Observed',
                          color='#3498db', edgecolor='black', linewidth=1)
        bars_aqm = ax.bar(x - bar_width * 0.5, aqm_vals, bar_width, label='AQM Day 1',
                          color='#95a5a6', edgecolor='black', linewidth=1)
        bars_p50 = ax.bar(x + bar_width * 0.5, [clf_p50] * len(stations), bar_width,
                          label='CLYFAR p50', color='#f39c12', edgecolor='black', linewidth=1)
        bars_p90 = ax.bar(x + bar_width * 1.5, [clf_p90] * len(stations), bar_width,
                          label='CLYFAR p90', color='#d35400', edgecolor='black', linewidth=1)

        # Add value labels on bars
        for bar in bars_obs:
            height = bar.get_height()
            ax.annotate(f'{height:.0f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords='offset points', ha='center', va='bottom',
                        fontsize=9, fontweight='bold')

        for bar in bars_aqm:
            height = bar.get_height()
            ax.annotate(f'{height:.0f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords='offset points', ha='center', va='bottom',
                        fontsize=9)

        # Add CLYFAR value labels (once, in the middle)
        ax.annotate(f'{clf_p50:.0f}', xy=(1, clf_p50), xytext=(0, 3),
                    textcoords='offset points', ha='center', va='bottom', fontsize=9)
        ax.annotate(f'{clf_p90:.0f}', xy=(1.2, clf_p90), xytext=(0, 3),
                    textcoords='offset points', ha='center', va='bottom', fontsize=9)

        # Threshold line
        ax.axhline(THRESHOLD, color='red', linestyle='--', linewidth=2, alpha=0.7)

        # Station labels
        ax.set_xticks(x)
        ax.set_xticklabels([STATION_NAMES[s] for s in stations], fontsize=11)

        # Title and result box
        ax.set_title(day_label, fontsize=13, fontweight='bold')
        ax.text(0.5, 0.95, result_text, transform=ax.transAxes, fontsize=16,
                fontweight='bold', ha='center', va='top', color='white',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=result_color, edgecolor='black'))

        # poss_elevated annotation
        ax.text(0.5, 0.85, f'poss_elevated = {poss_elev:.2f}', transform=ax.transAxes,
                fontsize=11, ha='center', va='top', style='italic',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.9))

        # Calculate and show mean error
        mean_obs = np.mean(obs_vals)
        mean_error_p50 = clf_p50 - mean_obs
        mean_error_p90 = clf_p90 - mean_obs
        mean_error_aqm = np.mean(aqm_vals) - mean_obs

        error_text = (f'Mean errors:\n'
                      f'  CLYFAR p50: {mean_error_p50:+.1f} ppb\n'
                      f'  CLYFAR p90: {mean_error_p90:+.1f} ppb\n'
                      f'  AQM: {mean_error_aqm:+.1f} ppb')
        ax.text(0.02, 0.02, error_text, transform=ax.transAxes, fontsize=9,
                va='bottom', ha='left', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', edgecolor='gray', alpha=0.9))

        # Grid
        ax.grid(True, axis='y', alpha=0.3, zorder=0)
        ax.set_axisbelow(True)

    # Shared y-axis label
    axes[0].set_ylabel('MDA8 Ozone (ppb)', fontsize=12)

    # Legend (only on first subplot)
    axes[0].legend(loc='upper right', fontsize=9)

    # Shared title
    fig.suptitle('Case Study: Feb 5 (Extreme Underprediction) vs Feb 7 (CLYFAR Success)',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.subplots_adjust(top=0.90)

    # Save figure
    output_path = OUTPUT_DIR / 'case_study_feb5_vs_feb7.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def plot_three_day_comparison() -> None:
    """Create three-panel comparison including Feb 13 (complete miss)."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load data for all three days
    feb5_data = load_day_data(FEB5)
    feb7_data = load_day_data(FEB7)
    feb13_data = load_day_data(FEB13)

    fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=True)

    # Station positions
    stations = ['UBHSP', 'UB7ST']  # Focus on stations with data for all days
    x = np.arange(len(stations))
    bar_width = 0.2

    cases = [
        (axes[0], feb5_data, 'Feb 5: Extreme Underprediction', '#e74c3c', 'MISS'),
        (axes[1], feb7_data, 'Feb 7: CLYFAR Success', '#27ae60', 'HIT'),
        (axes[2], feb13_data, 'Feb 13: Complete Miss', '#8e44ad', 'MISS'),
    ]

    for ax, day_data, day_label, result_color, result_text in cases:
        # Get observed values
        obs_vals = []
        for stid in stations:
            row = day_data['obs'].filter(pl.col('stid') == stid)
            obs_vals.append(row['obs_mda8'][0] if len(row) > 0 else 0)

        # Get AQM values
        aqm_vals = []
        for stid in stations:
            row = day_data['aqm'].filter(pl.col('stid') == stid)
            aqm_vals.append(row['aqm_max'][0] if len(row) > 0 else 0)

        # Get CLYFAR values
        clf = day_data['clyfar']
        clf_p50 = clf['forecast_p50'] if clf else 0
        clf_p90 = clf['forecast_p90'] if clf else 0
        poss_elev = clf['poss_elevated'] if clf else 0

        # Plot bars
        ax.bar(x - bar_width * 1.5, obs_vals, bar_width, label='Observed',
               color='#3498db', edgecolor='black', linewidth=1)
        ax.bar(x - bar_width * 0.5, aqm_vals, bar_width, label='AQM',
               color='#95a5a6', edgecolor='black', linewidth=1)
        ax.bar(x + bar_width * 0.5, [clf_p50] * len(stations), bar_width,
               label='CLYFAR p50', color='#f39c12', edgecolor='black', linewidth=1)
        ax.bar(x + bar_width * 1.5, [clf_p90] * len(stations), bar_width,
               label='CLYFAR p90', color='#d35400', edgecolor='black', linewidth=1)

        # Threshold line
        ax.axhline(THRESHOLD, color='red', linestyle='--', linewidth=2, alpha=0.7)

        # Station labels
        ax.set_xticks(x)
        ax.set_xticklabels([STATION_NAMES[s] for s in stations], fontsize=10)

        # Title
        ax.set_title(day_label, fontsize=11, fontweight='bold')

        # Result box
        ax.text(0.5, 0.95, result_text, transform=ax.transAxes, fontsize=14,
                fontweight='bold', ha='center', va='top', color='white',
                bbox=dict(boxstyle='round,pad=0.4', facecolor=result_color, edgecolor='black'))

        # poss_elevated
        ax.text(0.5, 0.84, f'poss = {poss_elev:.2f}', transform=ax.transAxes,
                fontsize=10, ha='center', va='top', style='italic',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='gray', alpha=0.9))

        # Grid
        ax.grid(True, axis='y', alpha=0.3, zorder=0)
        ax.set_axisbelow(True)

    axes[0].set_ylabel('MDA8 Ozone (ppb)', fontsize=12)
    axes[0].legend(loc='upper right', fontsize=8)

    fig.suptitle('Three Case Studies: Forecast Skill Variability',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.subplots_adjust(top=0.88)

    output_path = OUTPUT_DIR / 'case_study_three_days.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def print_comparison_table() -> None:
    """Print detailed comparison table for all three case study dates."""
    print('\n' + '=' * 90)
    print('CASE STUDY COMPARISON')
    print('=' * 90)

    for target_date, label in [(FEB5, 'Feb 5 (MISS)'), (FEB7, 'Feb 7 (HIT)'), (FEB13, 'Feb 13 (MISS)')]:
        data = load_day_data(target_date)
        clf = data['clyfar']

        print(f'\n{label} - poss_elevated = {clf["poss_elevated"]:.2f}')
        print('-' * 70)
        print(f'{"Station":<12} {"Observed":>10} {"CLYFAR p50":>12} {"CLYFAR p90":>12} {"AQM":>10}')
        print('-' * 70)

        for stid in CASE_STATIONS:
            obs_row = data['obs'].filter(pl.col('stid') == stid)
            aqm_row = data['aqm'].filter(pl.col('stid') == stid)

            obs_val = obs_row['obs_mda8'][0] if len(obs_row) > 0 else None
            aqm_val = aqm_row['aqm_max'][0] if len(aqm_row) > 0 else None

            if obs_val is not None:
                print(f'{STATION_NAMES[stid]:<12} {obs_val:>10.1f} {clf["forecast_p50"]:>12.1f} '
                      f'{clf["forecast_p90"]:>12.1f} {aqm_val:>10.1f}')


def main():
    """Main function."""
    print('Creating case study comparison plots...')

    # Print comparison table
    print_comparison_table()

    # Create Feb 5 vs Feb 7 comparison
    print('\nCreating Feb 5 vs Feb 7 comparison...')
    plot_comparison_feb5_vs_feb7()

    # Create three-day comparison
    print('\nCreating three-day comparison...')
    plot_three_day_comparison()

    print('\nDone!')


if __name__ == '__main__':
    main()
