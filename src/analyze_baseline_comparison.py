"""
Compare AQM forecasts against naive baselines.

Tests whether AQM provides value over:
- Persistence: "Tomorrow's ozone = today's ozone"
- Climatology: "Tomorrow's ozone = monthly average"

Key insight: Stratify by event phase (onset vs continuation) since
persistence has an unfair advantage during multi-day events.
"""
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from verification_metrics import (
    THRESHOLD,
    VerificationMetrics,
    calculate_contingency_counts,
    bootstrap_pod_difference,
)
from report_writer import create_report

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'
AQM_DATA_PATH = DATA_DIR / 'all_matched_obs_aqm.parquet'


@dataclass
class StratifiedPOD:
    """Container for POD stratified by event phase."""
    name: str
    onset_hits: int
    onset_total: int
    continuation_hits: int
    continuation_total: int

    @property
    def onset_pod(self) -> float:
        return self.onset_hits / self.onset_total if self.onset_total > 0 else 0.0

    @property
    def continuation_pod(self) -> float:
        return self.continuation_hits / self.continuation_total if self.continuation_total > 0 else 0.0


def create_baseline_forecasts(df: pl.DataFrame) -> pl.DataFrame:
    """Create persistence and climatology baseline forecasts."""
    # Sort by station and date for proper shifting
    df = df.sort(['stid', 'date'])

    # Persistence: previous day's observation
    df = df.with_columns([
        pl.col('obs_mda8').shift(1).over('stid').alias('persistence')
    ])

    # Extract month and year for climatology
    df = df.with_columns([
        pl.col('date').dt.month().alias('month'),
        pl.col('date').dt.year().alias('year')
    ])

    # Leave-one-year-out climatology: use mean from OTHER years only
    climatology_dfs = []
    for year in df['year'].unique().sort().to_list():
        other_years = df.filter(pl.col('year') != year)
        clim = other_years.group_by(['stid', 'month']).agg([
            pl.col('obs_mda8').mean().alias('climatology')
        ])
        clim = clim.with_columns(pl.lit(year).alias('year'))
        climatology_dfs.append(clim)

    climatology_df = pl.concat(climatology_dfs)
    df = df.join(climatology_df, on=['stid', 'month', 'year'], how='left')
    df = df.drop('year')

    return df


def flag_event_phases(df: pl.DataFrame) -> pl.DataFrame:
    """Flag onset and continuation days for exceedance events."""
    # Onset: first day of exceedance (obs >= 70 AND prev < 70)
    # Continuation: subsequent days (obs >= 70 AND prev >= 70)
    df = df.with_columns([
        (
            (pl.col('obs_mda8') >= THRESHOLD) &
            ((pl.col('persistence') < THRESHOLD) | pl.col('persistence').is_null())
        ).alias('is_onset'),
        (
            (pl.col('obs_mda8') >= THRESHOLD) &
            (pl.col('persistence') >= THRESHOLD)
        ).alias('is_continuation'),
    ])

    return df


def calculate_metrics(df: pl.DataFrame, fcst_col: str, name: str) -> VerificationMetrics:
    """Calculate verification metrics for a forecast column."""
    # Filter to rows with valid forecast values
    valid = df.filter(pl.col(fcst_col).is_not_null())

    # Categorical counts using shared function
    hits, misses, false_alarms, correct_negatives = calculate_contingency_counts(
        valid, 'obs_mda8', fcst_col, THRESHOLD
    )

    # Continuous metrics
    errors = valid.with_columns([
        (pl.col(fcst_col) - pl.col('obs_mda8')).alias('error')
    ])

    mean_bias = errors['error'].mean()
    rmse = np.sqrt((errors['error'] ** 2).mean())

    return VerificationMetrics(
        name=name,
        hits=hits,
        misses=misses,
        false_alarms=false_alarms,
        correct_negatives=correct_negatives,
        mean_bias=mean_bias,
        rmse=rmse,
        n_total=valid.height
    )


def calculate_stratified_pod(df: pl.DataFrame, fcst_col: str, name: str) -> StratifiedPOD:
    """Calculate POD stratified by event phase."""
    # Filter to valid forecasts
    valid = df.filter(pl.col(fcst_col).is_not_null())

    # Onset days
    onset_days = valid.filter(pl.col('is_onset'))
    onset_hits = onset_days.filter(pl.col(fcst_col) >= THRESHOLD).height
    onset_total = onset_days.height

    # Continuation days
    continuation_days = valid.filter(pl.col('is_continuation'))
    continuation_hits = continuation_days.filter(pl.col(fcst_col) >= THRESHOLD).height
    continuation_total = continuation_days.height

    return StratifiedPOD(
        name=name,
        onset_hits=onset_hits,
        onset_total=onset_total,
        continuation_hits=continuation_hits,
        continuation_total=continuation_total
    )


def calculate_metrics_by_lead_time(
    df: pl.DataFrame,
    fcst_col: str,
    name: str,
    lead_time_bins: list[tuple[int, int]] = [(0, 24), (24, 48), (48, 72)]
) -> list[VerificationMetrics]:
    """
    Calculate metrics stratified by lead time.

    NOTE: Requires 'lead_time' column from upstream data pipeline changes.
    Current data uses fxx=0 only. To enable:
    - Modify fetch_aqm.py to fetch multiple fxx values (0, 24, 48)
    - Add lead_time column to matched data
    """
    if 'lead_time' not in df.columns:
        print('  Note: Lead-time stratification requires upstream data changes.')
        return []

    metrics_by_lead = []
    for start_hr, end_hr in lead_time_bins:
        subset = df.filter(
            (pl.col('lead_time') >= start_hr) &
            (pl.col('lead_time') < end_hr)
        )
        if len(subset) > 0:
            metrics = calculate_metrics(subset, fcst_col, f'{name} ({start_hr}-{end_hr}h)')
            metrics_by_lead.append(metrics)

    return metrics_by_lead


def print_overall_table(metrics_list: list[VerificationMetrics]) -> None:
    """Print overall comparison table."""
    print('\n' + '='*80)
    print('TABLE 1: OVERALL MODEL COMPARISON')
    print('='*80)

    print(f'\n{"Model":<15} {"POD":>8} {"FAR":>8} {"CSI":>8} {"Bias":>10} {"RMSE":>10} {"n":>8}')
    print('-'*80)

    for m in metrics_list:
        print(f'{m.name:<15} {m.pod:>8.1%} {m.far:>8.1%} {m.csi:>8.1%} {m.mean_bias:>+10.2f} {m.rmse:>10.2f} {m.n_total:>8}')

    print('-'*80)


def print_stratified_table(strat_list: list[StratifiedPOD]) -> None:
    """Print stratified POD table."""
    print('\n' + '='*80)
    print('TABLE 2: POD STRATIFIED BY EVENT PHASE')
    print('='*80)

    print(f'\n{"Model":<15} {"Onset POD":>12} {"Cont. POD":>12} {"n Onset":>10} {"n Cont.":>10}')
    print('-'*80)

    for s in strat_list:
        print(f'{s.name:<15} {s.onset_pod:>12.1%} {s.continuation_pod:>12.1%} {s.onset_total:>10} {s.continuation_total:>10}')

    print('-'*80)


def print_interpretation(metrics_list: list[VerificationMetrics],
                         strat_list: list[StratifiedPOD]) -> None:
    """Print interpretation of results."""
    print('\n' + '='*80)
    print('INTERPRETATION')
    print('='*80)

    # Find metrics by name
    aqm = next(m for m in metrics_list if m.name == 'AQM')
    persistence = next(m for m in metrics_list if m.name == 'Persistence')

    aqm_strat = next(s for s in strat_list if s.name == 'AQM')
    pers_strat = next(s for s in strat_list if s.name == 'Persistence')

    print('\n1. ONSET DETECTION (where AQM should add value):')
    print(f'   - AQM onset POD: {aqm_strat.onset_pod:.1%}')
    print(f'   - Persistence onset POD: {pers_strat.onset_pod:.1%} (expected ~0% by definition)')

    if aqm_strat.onset_pod < 0.10:
        print('   -> AQM provides essentially NO advance warning of onset')
    elif aqm_strat.onset_pod < 0.30:
        print('   -> AQM provides MARGINAL advance warning')
    else:
        print('   -> AQM provides MEANINGFUL advance warning')

    print('\n2. OVERALL PERFORMANCE:')
    print(f'   - AQM overall POD: {aqm.pod:.1%}')
    print(f'   - Persistence overall POD: {persistence.pod:.1%}')

    if aqm.pod <= persistence.pod:
        print('   -> AQM adds NO VALUE over simple persistence')
    else:
        improvement = aqm.pod - persistence.pod
        print(f'   -> AQM improves over persistence by {improvement:.1%} points')

    print('\n3. CONTINUATION DETECTION:')
    print(f'   - AQM continuation POD: {aqm_strat.continuation_pod:.1%}')
    print(f'   - Persistence continuation POD: {pers_strat.continuation_pod:.1%}')
    print('   (High continuation POD is less impressive - yesterday predicts today)')

    print('\n4. SKILL SCORES (vs persistence):')
    csi_skill = aqm.skill_score(persistence, 'csi')
    pod_skill = aqm.skill_score(persistence, 'pod')
    print(f'   - CSI skill: {csi_skill:.3f}')
    print(f'   - POD skill: {pod_skill:.3f}')


def write_report(
    metrics_list: list[VerificationMetrics],
    strat_list: list[StratifiedPOD],
    boot_results: dict
) -> None:
    """Write analysis results to markdown report."""
    report = create_report('baseline_comparison.md')
    report.add_title('Baseline Comparison Analysis')

    # Overall Model Comparison table
    report.add_section('Overall Model Comparison')
    headers = ['Model', 'POD', 'FAR', 'CSI', 'Bias', 'RMSE', 'n']
    rows = []
    for m in metrics_list:
        rows.append([
            m.name,
            f'{m.pod:.1%}',
            f'{m.far:.1%}',
            f'{m.csi:.1%}',
            f'{m.mean_bias:+.2f}',
            f'{m.rmse:.2f}',
            str(m.n_total)
        ])
    report.add_table(headers, rows)

    # POD by Event Phase table
    report.add_section('POD by Event Phase')
    headers = ['Model', 'Onset POD', 'Continuation POD', 'n Onset', 'n Cont.']
    rows = []
    for s in strat_list:
        rows.append([
            s.name,
            f'{s.onset_pod:.1%}',
            f'{s.continuation_pod:.1%}',
            str(s.onset_total),
            str(s.continuation_total)
        ])
    report.add_table(headers, rows)

    # Bootstrap Confidence Interval
    report.add_section('Bootstrap Confidence Interval')
    report.add_key_value('AQM vs Persistence POD Difference', f'{boot_results["pod_diff"]:.1%}')
    report.add_key_value('95% CI', f'[{boot_results["ci_lower"]:.1%}, {boot_results["ci_upper"]:.1%}]')
    report.add_key_value('P-value', f'{boot_results["p_value"]:.3f}')
    report.add_text('')

    # Interpretation
    report.add_section('Interpretation')

    # Find metrics by name
    aqm = next(m for m in metrics_list if m.name == 'AQM')
    persistence = next(m for m in metrics_list if m.name == 'Persistence')
    aqm_strat = next(s for s in strat_list if s.name == 'AQM')
    pers_strat = next(s for s in strat_list if s.name == 'Persistence')

    # Onset Detection
    report.add_section('Onset Detection', level=3)
    report.add_key_value('AQM onset POD', f'{aqm_strat.onset_pod:.1%}')
    report.add_key_value('Persistence onset POD', f'{pers_strat.onset_pod:.1%}')
    if aqm_strat.onset_pod < 0.10:
        assessment = 'AQM provides essentially NO advance warning of onset'
    elif aqm_strat.onset_pod < 0.30:
        assessment = 'AQM provides MARGINAL advance warning'
    else:
        assessment = 'AQM provides MEANINGFUL advance warning'
    report.add_key_value('Assessment', assessment)
    report.add_text('')

    # Overall Performance
    report.add_section('Overall Performance', level=3)
    report.add_key_value('AQM overall POD', f'{aqm.pod:.1%}')
    report.add_key_value('Persistence overall POD', f'{persistence.pod:.1%}')
    if aqm.pod <= persistence.pod:
        assessment = 'AQM adds NO VALUE over simple persistence'
    else:
        improvement = aqm.pod - persistence.pod
        assessment = f'AQM improves over persistence by {improvement:.1%} points'
    report.add_key_value('Assessment', assessment)
    report.add_text('')

    # Skill Scores
    report.add_section('Skill Scores (vs Persistence)', level=3)
    csi_skill = aqm.skill_score(persistence, 'csi')
    pod_skill = aqm.skill_score(persistence, 'pod')
    report.add_key_value('CSI skill', f'{csi_skill:.3f}')
    report.add_key_value('POD skill', f'{pod_skill:.3f}')

    report.save()


def plot_comparison(metrics_list: list[VerificationMetrics],
                    strat_list: list[StratifiedPOD]) -> None:
    """Create bar chart comparing models."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Colors for each model
    colors = {'AQM': '#2ecc71', 'Persistence': '#3498db', 'Climatology': '#e74c3c'}

    # --- Left panel: Overall metrics ---
    ax1 = axes[0]
    models = [m.name for m in metrics_list]
    x = np.arange(len(models))
    width = 0.25

    pods = [m.pod for m in metrics_list]
    fars = [m.far for m in metrics_list]
    csis = [m.csi for m in metrics_list]

    bars1 = ax1.bar(x - width, pods, width, label='POD', color='#2ecc71', edgecolor='black')
    bars2 = ax1.bar(x, fars, width, label='FAR', color='#e74c3c', edgecolor='black')
    bars3 = ax1.bar(x + width, csis, width, label='CSI', color='#3498db', edgecolor='black')

    ax1.set_ylabel('Score', fontsize=12)
    ax1.set_title('Overall Verification Metrics', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models, fontsize=11)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.set_ylim(0, 1.0)
    ax1.grid(True, axis='y', alpha=0.3, zorder=0)
    ax1.set_axisbelow(True)

    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height:.0%}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),
                         textcoords='offset points',
                         ha='center', va='bottom', fontsize=9)

    # --- Right panel: Stratified POD ---
    ax2 = axes[1]

    onset_pods = [s.onset_pod for s in strat_list]
    cont_pods = [s.continuation_pod for s in strat_list]

    x2 = np.arange(len(strat_list))
    width2 = 0.35

    bars4 = ax2.bar(x2 - width2/2, onset_pods, width2, label='Onset Days',
                    color='#9b59b6', edgecolor='black')
    bars5 = ax2.bar(x2 + width2/2, cont_pods, width2, label='Continuation Days',
                    color='#f39c12', edgecolor='black')

    ax2.set_ylabel('POD', fontsize=12)
    ax2.set_title('POD by Event Phase\n(Onset = First Day, Continuation = Subsequent Days)',
                  fontsize=14, fontweight='bold')
    ax2.set_xticks(x2)
    ax2.set_xticklabels([s.name for s in strat_list], fontsize=11)
    ax2.legend(loc='upper right', fontsize=10)
    ax2.set_ylim(0, 1.0)
    ax2.grid(True, axis='y', alpha=0.3, zorder=0)
    ax2.set_axisbelow(True)

    # Add value labels
    for bars in [bars4, bars5]:
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{height:.0%}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),
                         textcoords='offset points',
                         ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / 'baseline_comparison.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def main():
    """Main function."""
    print('='*60)
    print('BASELINE COMPARISON ANALYSIS')
    print('='*60)

    # Load data
    print('\n[1/5] Loading verification data...')
    df = pl.read_parquet(AQM_DATA_PATH)
    print(f'  Loaded {len(df)} matched obs/AQM records')

    # Filter out null observations
    df = df.filter(pl.col('obs_mda8').is_not_null())
    print(f'  After filtering nulls: {len(df)} records')

    # Create baseline forecasts
    print('\n[2/5] Creating baseline forecasts...')
    df = create_baseline_forecasts(df)

    # Print climatology values
    clim_summary = df.group_by('month').agg([
        pl.col('climatology').mean().alias('mean_clim')
    ]).sort('month')
    print('  Monthly climatology values:')
    for row in clim_summary.iter_rows(named=True):
        month_name = {12: 'Dec', 1: 'Jan', 2: 'Feb', 3: 'Mar'}.get(row['month'], str(row['month']))
        print(f'    {month_name}: {row["mean_clim"]:.1f} ppb')

    # Flag event phases
    print('\n[3/5] Flagging event phases...')
    df = flag_event_phases(df)

    n_exceedance = df.filter(pl.col('obs_mda8') >= THRESHOLD).height
    n_onset = df.filter(pl.col('is_onset')).height
    n_continuation = df.filter(pl.col('is_continuation')).height
    print(f'  Total exceedance days: {n_exceedance}')
    print(f'  Onset days: {n_onset}')
    print(f'  Continuation days: {n_continuation}')

    # Calculate metrics for each model
    print('\n[4/5] Calculating verification metrics...')
    models = [
        ('aqm_max', 'AQM'),
        ('persistence', 'Persistence'),
        ('climatology', 'Climatology'),
    ]

    metrics_list = []
    strat_list = []

    for fcst_col, name in models:
        metrics = calculate_metrics(df, fcst_col, name)
        strat = calculate_stratified_pod(df, fcst_col, name)
        metrics_list.append(metrics)
        strat_list.append(strat)
        print(f'  {name}: POD={metrics.pod:.1%}, Onset POD={strat.onset_pod:.1%}')

    # Bootstrap confidence interval
    print('\n  Bootstrap CI for AQM vs Persistence POD:')
    boot = bootstrap_pod_difference(df, 'aqm_max', 'persistence')
    print(f'    Difference: {boot["pod_diff"]:.1%} [{boot["ci_lower"]:.1%}, {boot["ci_upper"]:.1%}]')
    print(f'    P-value: {boot["p_value"]:.3f}')

    # Print tables
    print_overall_table(metrics_list)
    print_stratified_table(strat_list)
    print_interpretation(metrics_list, strat_list)

    # Create visualization
    print('\n[5/5] Creating comparison figure...')
    plot_comparison(metrics_list, strat_list)

    # Write markdown report
    write_report(metrics_list, strat_list, boot)

    print('\nDone!')


if __name__ == '__main__':
    main()
