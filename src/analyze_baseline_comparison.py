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

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'
AQM_DATA_PATH = DATA_DIR / 'all_matched_obs_aqm.parquet'

# Threshold
THRESHOLD = 70  # NAAQS ozone exceedance (ppb)


@dataclass
class VerificationMetrics:
    """Container for forecast verification metrics."""
    name: str
    hits: int
    misses: int
    false_alarms: int
    correct_negatives: int
    bias: float
    rmse: float
    n_total: int

    @property
    def pod(self) -> float:
        """Probability of Detection."""
        denom = self.hits + self.misses
        return self.hits / denom if denom > 0 else 0.0

    @property
    def far(self) -> float:
        """False Alarm Ratio."""
        denom = self.hits + self.false_alarms
        return self.false_alarms / denom if denom > 0 else 0.0

    @property
    def csi(self) -> float:
        """Critical Success Index."""
        denom = self.hits + self.misses + self.false_alarms
        return self.hits / denom if denom > 0 else 0.0


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

    # Extract month for climatology
    df = df.with_columns([
        pl.col('date').dt.month().alias('month')
    ])

    # Climatology: mean observation by month and station
    climatology = df.group_by(['stid', 'month']).agg([
        pl.col('obs_mda8').mean().alias('climatology')
    ])

    # Join climatology back
    df = df.join(climatology, on=['stid', 'month'], how='left')

    return df


def flag_event_phases(df: pl.DataFrame) -> pl.DataFrame:
    """Flag onset and continuation days for exceedance events."""
    # Previous day observation (already computed as persistence)
    df = df.with_columns([
        pl.col('persistence').alias('prev_obs')
    ])

    # Onset: first day of exceedance (obs >= 70 AND prev < 70)
    # Continuation: subsequent days (obs >= 70 AND prev >= 70)
    df = df.with_columns([
        (
            (pl.col('obs_mda8') >= THRESHOLD) &
            ((pl.col('prev_obs') < THRESHOLD) | pl.col('prev_obs').is_null())
        ).alias('is_onset'),
        (
            (pl.col('obs_mda8') >= THRESHOLD) &
            (pl.col('prev_obs') >= THRESHOLD)
        ).alias('is_continuation'),
    ])

    return df


def calculate_metrics(df: pl.DataFrame, fcst_col: str, name: str) -> VerificationMetrics:
    """Calculate verification metrics for a forecast column."""
    # Filter to rows with valid forecast values
    valid = df.filter(pl.col(fcst_col).is_not_null())

    # Categorical counts
    hits = valid.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col(fcst_col) >= THRESHOLD)
    ).height

    misses = valid.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col(fcst_col) < THRESHOLD)
    ).height

    false_alarms = valid.filter(
        (pl.col('obs_mda8') < THRESHOLD) & (pl.col(fcst_col) >= THRESHOLD)
    ).height

    correct_negatives = valid.filter(
        (pl.col('obs_mda8') < THRESHOLD) & (pl.col(fcst_col) < THRESHOLD)
    ).height

    # Continuous metrics
    errors = valid.with_columns([
        (pl.col(fcst_col) - pl.col('obs_mda8')).alias('error')
    ])

    bias = errors['error'].mean()
    rmse = np.sqrt((errors['error'] ** 2).mean())

    return VerificationMetrics(
        name=name,
        hits=hits,
        misses=misses,
        false_alarms=false_alarms,
        correct_negatives=correct_negatives,
        bias=bias,
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


def print_overall_table(metrics_list: list[VerificationMetrics]) -> None:
    """Print overall comparison table."""
    print('\n' + '='*80)
    print('TABLE 1: OVERALL MODEL COMPARISON')
    print('='*80)

    print(f'\n{"Model":<15} {"POD":>8} {"FAR":>8} {"CSI":>8} {"Bias":>10} {"RMSE":>10} {"n":>8}')
    print('-'*80)

    for m in metrics_list:
        print(f'{m.name:<15} {m.pod:>8.1%} {m.far:>8.1%} {m.csi:>8.1%} {m.bias:>+10.2f} {m.rmse:>10.2f} {m.n_total:>8}')

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

    # Print tables
    print_overall_table(metrics_list)
    print_stratified_table(strat_list)
    print_interpretation(metrics_list, strat_list)

    # Create visualization
    print('\n[5/5] Creating comparison figure...')
    plot_comparison(metrics_list, strat_list)

    print('\nDone!')


if __name__ == '__main__':
    main()
