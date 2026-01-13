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

DATA_PATH = Path(__file__).parent.parent / 'data' / 'all_matched_obs_aqm.parquet'
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'
THRESHOLD = 70


def load_data() -> pl.DataFrame:
    """Load matched obs/AQM data."""
    return pl.read_parquet(DATA_PATH)


def stratified_pod(df: pl.DataFrame) -> list[dict]:
    """Calculate POD by observed severity tier.

    Returns list of dicts with tier info, n, hits, and POD.
    """
    tiers = [
        (70, 80, '70-80'),
        (80, 90, '80-90'),
        (90, 200, '90+'),  # Upper bound high enough to capture all extreme events
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

        results.append({
            'tier': label,
            'low': low,
            'high': high,
            'n': n_obs,
            'hits': n_hits,
            'misses': n_obs - n_hits,
            'pod': pod,
        })

    return results


def plot_stratified_pod(pod_data: list[dict]) -> None:
    """Create horizontal bar chart of POD by severity tier."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    tiers = [d['tier'] for d in pod_data]
    pods = [d['pod'] for d in pod_data]
    ns = [d['n'] for d in pod_data]
    hits = [d['hits'] for d in pod_data]

    fig, ax = plt.subplots(figsize=(9, 5))

    y_pos = np.arange(len(tiers))
    colors = ['#2ecc71', '#f39c12', '#e74c3c']  # Green to red gradient

    bars = ax.barh(y_pos, pods, color=colors, edgecolor='black', linewidth=1.2, height=0.6)

    # Add labels on bars
    for i, (bar, n, h, pod) in enumerate(zip(bars, ns, hits, pods)):
        # POD value inside bar
        ax.text(pod - 0.03, i, f'{pod:.0%}', va='center', ha='right',
                fontsize=14, fontweight='bold', color='white')
        # n and hits outside bar
        ax.text(pod + 0.02, i, f'n={n}, hits={h}', va='center', ha='left',
                fontsize=11, color='black')

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
    print('\nSeverity-Stratified POD:')
    print('-' * 45)
    print(f'{"Tier":<12} {"n":>6} {"Hits":>6} {"Misses":>8} {"POD":>8}')
    print('-' * 45)

    total_n = 0
    total_hits = 0
    for d in pod_data:
        print(f'{d["tier"] + " ppb":<12} {d["n"]:>6} {d["hits"]:>6} {d["misses"]:>8} {d["pod"]:>8.2f}')
        total_n += d['n']
        total_hits += d['hits']

    print('-' * 45)
    overall_pod = total_hits / total_n if total_n > 0 else 0
    print(f'{"Overall":<12} {total_n:>6} {total_hits:>6} {total_n - total_hits:>8} {overall_pod:>8.2f}')


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

    # Ensure correct column order
    aqm_bin_order = ['0-30', '30-50', '50-60', '60-69']
    obs_bin_order = ['70-80', '80-90', '90+']

    # Add missing columns if needed
    for col in aqm_bin_order:
        if col not in crosstab.columns:
            crosstab = crosstab.with_columns(pl.lit(0).alias(col))

    # Reorder columns
    crosstab = crosstab.select(['obs_bin'] + aqm_bin_order)

    # Sort rows by obs_bin order
    obs_order_map = {label: i for i, label in enumerate(obs_bin_order)}
    crosstab = crosstab.with_columns([
        pl.col('obs_bin').replace_strict(obs_order_map).alias('_order')
    ]).sort('_order').drop('_order')

    # Calculate mean AQM forecast by observed tier
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

    print('\nDone!')


if __name__ == '__main__':
    main()
