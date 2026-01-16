"""
Severity-stratified POD and near-miss analysis for AQM ozone prediction.

Produces two analyses:
1. POD broken down by observed ozone severity tier (70-80, 80-90, 90+ ppb)
2. Near-miss cross-tabulation showing how badly AQM missed on miss days
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from verification_metrics import THRESHOLD, bootstrap_pod_ci
from report_writer import create_report

DATA_PATH = Path(__file__).parent.parent / 'data' / 'all_matched_obs_aqm.parquet'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'


def load_data() -> pl.DataFrame:
    """Load matched obs/AQM data."""
    return pl.read_parquet(DATA_PATH)


def stratified_pod(df: pl.DataFrame, include_ci: bool = True) -> list[dict]:
    """Calculate POD by observed severity tier with optional bootstrap CIs.

    Args:
        df: DataFrame with obs_mda8 and aqm_max columns
        include_ci: Whether to compute 95% bootstrap confidence intervals

    Returns:
        List of dicts with tier info, n, hits, POD, and optionally CI bounds.
    """
    tiers = [
        (70, 80, '70-80'),
        (80, 90, '80-90'),
        (90, float('inf'), '90+'),  # No upper limit for extreme events
    ]

    results = []
    for low, high, label in tiers:
        # Filter to days where obs falls in this tier
        tier_df = df.filter(
            (pl.col('obs_mda8') >= low) & (pl.col('obs_mda8') < high)
        )
        n_obs = len(tier_df)

        # Count hits (where AQM also >= threshold)
        n_hits = len(tier_df.filter(pl.col('aqm_max') >= THRESHOLD))

        pod = n_hits / n_obs if n_obs > 0 else 0

        result = {
            'tier': label,
            'low': low,
            'high': high,
            'n': n_obs,
            'hits': n_hits,
            'misses': n_obs - n_hits,
            'pod': pod,
        }

        # Add bootstrap CI if requested and enough data
        if include_ci and n_obs >= 10:
            # For tier-specific POD, we just need to bootstrap the hit rate
            pod_est, ci_lower, ci_upper = bootstrap_tier_pod(tier_df, n_iterations=1000)
            result['ci_lower'] = ci_lower
            result['ci_upper'] = ci_upper
        elif include_ci:
            result['ci_lower'] = None
            result['ci_upper'] = None

        results.append(result)

    return results


def bootstrap_tier_pod(
    tier_df: pl.DataFrame,
    n_iterations: int = 1000,
    seed: int = 42
) -> tuple[float, float, float]:
    """Bootstrap POD for a specific severity tier.

    Args:
        tier_df: DataFrame filtered to a specific tier (all rows are exceedances)
        n_iterations: Number of bootstrap samples
        seed: Random seed for reproducibility

    Returns:
        Tuple of (pod, ci_lower, ci_upper)
    """
    rng = np.random.default_rng(seed)
    n = len(tier_df)

    if n == 0:
        return (0.0, 0.0, 0.0)

    fcst = tier_df['aqm_max'].to_numpy()
    hits = (fcst >= THRESHOLD).sum()
    pod_observed = hits / n

    # Bootstrap
    pods = np.zeros(n_iterations)
    for i in range(n_iterations):
        idx = rng.integers(0, n, size=n)
        hits_boot = (fcst[idx] >= THRESHOLD).sum()
        pods[i] = hits_boot / n

    ci_lower = np.percentile(pods, 2.5)
    ci_upper = np.percentile(pods, 97.5)

    return (pod_observed, ci_lower, ci_upper)


def plot_stratified_pod(pod_data: list[dict]) -> None:
    """Create horizontal bar chart of POD by severity tier with CIs."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    tiers = [d['tier'] for d in pod_data]
    pods = [d['pod'] for d in pod_data]
    ns = [d['n'] for d in pod_data]
    hits = [d['hits'] for d in pod_data]

    # Extract CI bounds if present
    ci_lowers = [d.get('ci_lower') for d in pod_data]
    ci_uppers = [d.get('ci_upper') for d in pod_data]
    has_ci = any(cl is not None for cl in ci_lowers)

    fig, ax = plt.subplots(figsize=(9, 5))

    y_pos = np.arange(len(tiers))
    colors = ['#2ecc71', '#f39c12', '#e74c3c']  # Green to red gradient

    bars = ax.barh(y_pos, pods, color=colors, edgecolor='black', linewidth=1.2, height=0.6)

    # Add error bars for CI if available
    if has_ci:
        for i, (pod, cl, cu) in enumerate(zip(pods, ci_lowers, ci_uppers)):
            if cl is not None and cu is not None:
                ax.errorbar(pod, i, xerr=[[pod - cl], [cu - pod]],
                           fmt='none', color='black', capsize=4, capthick=1.5, linewidth=1.5)

    # Add labels on bars
    for i, (bar, n, h, pod, cl, cu) in enumerate(zip(bars, ns, hits, pods, ci_lowers, ci_uppers)):
        # POD value inside bar
        ax.text(pod - 0.03, i, f'{pod:.0%}', va='center', ha='right',
                fontsize=14, fontweight='bold', color='white')
        # n, hits, and CI outside bar
        if cl is not None and cu is not None:
            label = f'n={n}, hits={h}\n95% CI: [{cl:.0%}, {cu:.0%}]'
        else:
            label = f'n={n}, hits={h}'
        ax.text(pod + 0.02, i, label, va='center', ha='left',
                fontsize=10, color='black')

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f'{t} ppb' for t in tiers], fontsize=12)
    ax.set_xlabel('Probability of Detection (POD)', fontsize=12)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.5, len(tiers) - 0.5)

    # Add vertical line at overall POD for reference
    overall_hits = sum(d['hits'] for d in pod_data)
    overall_n = sum(d['n'] for d in pod_data)
    overall_pod = overall_hits / overall_n if overall_n > 0 else 0
    ax.axvline(overall_pod, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.text(overall_pod + 0.01, len(tiers) - 0.3, f'Overall: {overall_pod:.0%}',
            fontsize=10, color='gray', va='bottom')

    # Grid
    ax.grid(True, axis='x', alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # Title
    fig.suptitle('POD by Observed Ozone Severity', fontsize=14, fontweight='bold')
    ax.set_title('Borderline events (70-80 ppb) hardest to detect', fontsize=11, style='italic')

    plt.tight_layout()

    output_path = OUTPUT_DIR / 'stratified_pod.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def print_pod_table(pod_data: list[dict]) -> None:
    """Print severity-stratified POD table to console."""
    has_ci = any(d.get('ci_lower') is not None for d in pod_data)

    print('\nSeverity-Stratified POD:')
    if has_ci:
        print('-' * 65)
        print(f'{"Tier":<12} {"n":>6} {"Hits":>6} {"Misses":>8} {"POD":>8} {"95% CI":>18}')
        print('-' * 65)
    else:
        print('-' * 45)
        print(f'{"Tier":<12} {"n":>6} {"Hits":>6} {"Misses":>8} {"POD":>8}')
        print('-' * 45)

    total_n = 0
    total_hits = 0
    for d in pod_data:
        ci_str = ''
        if has_ci and d.get('ci_lower') is not None:
            ci_str = f'[{d["ci_lower"]:.2f}, {d["ci_upper"]:.2f}]'
        if has_ci:
            print(f'{d["tier"] + " ppb":<12} {d["n"]:>6} {d["hits"]:>6} {d["misses"]:>8} {d["pod"]:>8.2f} {ci_str:>18}')
        else:
            print(f'{d["tier"] + " ppb":<12} {d["n"]:>6} {d["hits"]:>6} {d["misses"]:>8} {d["pod"]:>8.2f}')
        total_n += d['n']
        total_hits += d['hits']

    if has_ci:
        print('-' * 65)
    else:
        print('-' * 45)
    overall_pod = total_hits / total_n if total_n > 0 else 0
    print(f'{"Overall":<12} {total_n:>6} {total_hits:>6} {total_n - total_hits:>8} {overall_pod:>8.2f}')


def order_crosstab_bins(
    crosstab: pl.DataFrame,
    row_col: str,
    row_order: list[str],
    col_order: list[str]
) -> pl.DataFrame:
    """Reorder crosstab rows and columns to specified bin order.

    Args:
        crosstab: Pivoted DataFrame with row labels in row_col
        row_col: Name of the row label column
        row_order: Desired order of row labels
        col_order: Desired order of column labels (excluding row_col)

    Returns:
        Reordered DataFrame with columns in specified order and rows sorted
    """
    # Add missing columns with zeros
    for col in col_order:
        if col not in crosstab.columns:
            crosstab = crosstab.with_columns(pl.lit(0).alias(col))

    # Reorder columns
    crosstab = crosstab.select([row_col] + col_order)

    # Sort rows by specified order
    order_map = {label: i for i, label in enumerate(row_order)}
    crosstab = crosstab.with_columns([
        pl.col(row_col).replace_strict(order_map).alias('_order')
    ]).sort('_order').drop('_order')

    return crosstab


def near_miss_analysis(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Cross-tabulate misses by AQM forecast and observed bins.

    Returns:
        crosstab: DataFrame with obs_bin rows, aqm_bin columns, count values
        mean_aqm: DataFrame with mean AQM forecast per observed tier
    """
    # Filter to miss days only (obs >= 70, aqm < 70)
    misses = df.filter(
        (pl.col('obs_mda8') >= THRESHOLD) & (pl.col('aqm_max') < THRESHOLD)
    )

    # Bin by AQM forecast value
    misses = misses.with_columns([
        pl.when(pl.col('aqm_max') < 30).then(pl.lit('0-30'))
        .when(pl.col('aqm_max') < 50).then(pl.lit('30-50'))
        .when(pl.col('aqm_max') < 60).then(pl.lit('50-60'))
        .otherwise(pl.lit('60-69'))
        .alias('aqm_bin')
    ])

    # Bin by observed severity
    misses = misses.with_columns([
        pl.when(pl.col('obs_mda8') < 80).then(pl.lit('70-80'))
        .when(pl.col('obs_mda8') < 90).then(pl.lit('80-90'))
        .otherwise(pl.lit('90+'))
        .alias('obs_bin')
    ])

    # Cross-tabulate
    crosstab = misses.group_by(['obs_bin', 'aqm_bin']).agg([
        pl.len().alias('count')
    ])

    # Pivot to wide format
    crosstab = crosstab.pivot(
        index='obs_bin',
        on='aqm_bin',
        values='count'
    ).fill_null(0)

    # Define bin orders
    aqm_bin_order = ['0-30', '30-50', '50-60', '60-69']
    obs_bin_order = ['70-80', '80-90', '90+']

    # Use helper to reorder rows and columns
    crosstab = order_crosstab_bins(crosstab, 'obs_bin', obs_bin_order, aqm_bin_order)

    # Calculate mean AQM forecast by observed tier
    obs_order_map = {label: i for i, label in enumerate(obs_bin_order)}
    mean_aqm = misses.group_by('obs_bin').agg([
        pl.col('aqm_max').mean().alias('mean_aqm'),
        pl.col('aqm_max').std().alias('std_aqm'),
        pl.len().alias('n')
    ])
    mean_aqm = mean_aqm.with_columns([
        pl.col('obs_bin').replace_strict(obs_order_map).alias('_order')
    ]).sort('_order').drop('_order')

    return crosstab, mean_aqm


def plot_near_miss_heatmap(crosstab: pl.DataFrame, mean_aqm: pl.DataFrame) -> None:
    """Create heatmap of near-miss cross-tabulation."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    obs_bins = crosstab['obs_bin'].to_list()
    aqm_bins = ['0-30', '30-50', '50-60', '60-69']

    # Extract data as numpy array
    data = crosstab.select(aqm_bins).to_numpy()

    fig, ax = plt.subplots(figsize=(9, 6))

    # Create heatmap
    im = ax.imshow(data, cmap='YlOrRd', aspect='auto')

    # Add colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Number of Miss Days', fontsize=11)

    # Set ticks
    ax.set_xticks(np.arange(len(aqm_bins)))
    ax.set_yticks(np.arange(len(obs_bins)))
    ax.set_xticklabels([f'{b} ppb' for b in aqm_bins], fontsize=11)
    ax.set_yticklabels([f'{b} ppb' for b in obs_bins], fontsize=11)

    # Annotate cells with counts
    for i in range(len(obs_bins)):
        for j in range(len(aqm_bins)):
            val = data[i, j]
            text_color = 'white' if val > data.max() * 0.6 else 'black'
            ax.text(j, i, str(int(val)), ha='center', va='center',
                    fontsize=14, fontweight='bold', color=text_color)

    # Labels
    ax.set_xlabel('AQM Forecast (ppb)', fontsize=12)
    ax.set_ylabel('Observed Ozone (ppb)', fontsize=12)

    # Title
    total_misses = data.sum()
    fig.suptitle('Near-Miss Analysis: How Badly Did AQM Miss?',
                 fontsize=14, fontweight='bold')
    ax.set_title(f'{int(total_misses)} miss days cross-tabulated by forecast vs observed severity',
                 fontsize=11, style='italic')

    # Add mean AQM annotation box
    mean_text = 'Mean AQM on miss days:\n'
    for row in mean_aqm.iter_rows(named=True):
        mean_text += f'  {row["obs_bin"]} ppb obs: {row["mean_aqm"]:.1f} ppb\n'

    props = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='gray', alpha=0.9)
    ax.text(1.02, -0.25, mean_text.strip(), transform=ax.transAxes, fontsize=10,
            va='top', ha='left', bbox=props, fontfamily='monospace')

    plt.tight_layout()
    plt.subplots_adjust(right=0.75)

    output_path = OUTPUT_DIR / 'near_miss_heatmap.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')
    plt.close(fig)


def print_near_miss_summary(crosstab: pl.DataFrame, mean_aqm: pl.DataFrame) -> None:
    """Print near-miss cross-tabulation to console."""
    obs_bins = crosstab['obs_bin'].to_list()
    aqm_bins = ['0-30', '30-50', '50-60', '60-69']

    total_misses = sum(crosstab.select(aqm_bins).sum_horizontal().to_list())

    print(f'\nNear-Miss Analysis ({total_misses} misses):')
    print('-' * 55)
    print('Cross-tabulation (rows: observed, cols: AQM forecast):')
    print()

    # Header
    header = f'{"Obs \\ AQM":>12}'
    for ab in aqm_bins:
        header += f'{ab:>10}'
    header += f'{"Total":>10}'
    print(header)
    print('-' * 55)

    # Rows
    for row in crosstab.iter_rows(named=True):
        line = f'{row["obs_bin"] + " ppb":>12}'
        row_total = 0
        for ab in aqm_bins:
            val = row[ab]
            line += f'{val:>10}'
            row_total += val
        line += f'{row_total:>10}'
        print(line)

    print('-' * 55)

    # Column totals
    totals_line = f'{"Total":>12}'
    for ab in aqm_bins:
        col_total = crosstab[ab].sum()
        totals_line += f'{col_total:>10}'
    totals_line += f'{total_misses:>10}'
    print(totals_line)

    # Mean AQM by tier
    print('\nMean AQM forecast on miss days by observed tier:')
    for row in mean_aqm.iter_rows(named=True):
        std_str = f' (std: {row["std_aqm"]:.1f})' if row["std_aqm"] else ''
        print(f'  {row["obs_bin"]} ppb: {row["mean_aqm"]:.1f} ppb{std_str}, n={row["n"]}')


def write_report(
    pod_data: list[dict],
    crosstab: pl.DataFrame,
    mean_aqm: pl.DataFrame
) -> None:
    """Write stratified analysis to markdown report."""
    report = create_report('stratified_analysis.md')
    report.add_title('Stratified Analysis')

    # Severity-Stratified POD table
    report.add_section('Severity-Stratified POD')
    has_ci = any(d.get('ci_lower') is not None for d in pod_data)

    if has_ci:
        headers = ['Tier', 'n', 'Hits', 'Misses', 'POD', '95% CI']
    else:
        headers = ['Tier', 'n', 'Hits', 'Misses', 'POD']

    rows = []
    total_n = 0
    total_hits = 0
    for d in pod_data:
        if has_ci and d.get('ci_lower') is not None:
            ci_str = f'[{d["ci_lower"]:.2f}, {d["ci_upper"]:.2f}]'
            rows.append([
                f'{d["tier"]} ppb',
                str(d['n']),
                str(d['hits']),
                str(d['misses']),
                f'{d["pod"]:.2f}',
                ci_str
            ])
        else:
            rows.append([
                f'{d["tier"]} ppb',
                str(d['n']),
                str(d['hits']),
                str(d['misses']),
                f'{d["pod"]:.2f}'
            ])
        total_n += d['n']
        total_hits += d['hits']

    report.add_table(headers, rows)

    overall_pod = total_hits / total_n if total_n > 0 else 0
    report.add_key_value('Overall', f'n={total_n}, hits={total_hits}, POD={overall_pod:.2f}')
    report.add_text('')

    # Near-Miss Cross-tabulation
    report.add_section('Near-Miss Analysis')

    obs_bins = crosstab['obs_bin'].to_list()
    aqm_bins = ['0-30', '30-50', '50-60', '60-69']

    total_misses = sum(crosstab.select(aqm_bins).sum_horizontal().to_list())
    report.add_text(f'Cross-tabulation of {total_misses} misses (rows: observed, cols: AQM forecast)')
    report.add_text('')

    headers = ['Obs \\ AQM'] + [f'{ab} ppb' for ab in aqm_bins] + ['Total']
    rows = []
    for row in crosstab.iter_rows(named=True):
        row_total = sum(row[ab] for ab in aqm_bins)
        rows.append([
            f'{row["obs_bin"]} ppb',
            *[str(row[ab]) for ab in aqm_bins],
            str(row_total)
        ])

    # Add column totals row
    col_totals = ['Total']
    for ab in aqm_bins:
        col_totals.append(str(crosstab[ab].sum()))
    col_totals.append(str(total_misses))
    rows.append(col_totals)

    report.add_table(headers, rows)

    # Mean AQM by tier
    report.add_section('Mean AQM Forecast on Miss Days', level=3)
    for row in mean_aqm.iter_rows(named=True):
        std_str = f' (std: {row["std_aqm"]:.1f})' if row["std_aqm"] else ''
        report.add_key_value(
            f'{row["obs_bin"]} ppb',
            f'{row["mean_aqm"]:.1f} ppb{std_str}, n={row["n"]}'
        )

    report.save()


def main():
    """Main function."""
    print('Loading data...')
    df = load_data()
    print(f'Loaded {len(df)} matched obs/AQM records')

    # Part 1: Severity-stratified POD
    print('\n' + '=' * 55)
    print('PART 1: SEVERITY-STRATIFIED POD')
    print('=' * 55)

    pod_data = stratified_pod(df)
    print_pod_table(pod_data)
    plot_stratified_pod(pod_data)

    # Part 2: Near-miss analysis
    print('\n' + '=' * 55)
    print('PART 2: NEAR-MISS ANALYSIS')
    print('=' * 55)

    crosstab, mean_aqm = near_miss_analysis(df)
    print_near_miss_summary(crosstab, mean_aqm)
    plot_near_miss_heatmap(crosstab, mean_aqm)

    # Write markdown report
    write_report(pod_data, crosstab, mean_aqm)

    print('\nDone!')


if __name__ == '__main__':
    main()
