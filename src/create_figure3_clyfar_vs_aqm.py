#!/usr/bin/env python3
"""
Figure 3: CLYFAR vs AQM Head-to-Head
Dual-panel grouped bar chart comparing statistical ensemble (CLYFAR)
against operational NWP (AQM) and persistence baseline.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Paths (following project conventions)
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'

# Data from performance diagram calculations (fixed threshold bug)
systems = ['AQM\n(Day 1)', 'CLYFAR\np90']
pod = [33.3, 74.8]   # Probability of Detection (%)
far = [30.5, 57.8]   # False Alarm Rate (%)
csi = [29.1, 36.9]   # Critical Success Index (%)
n_exceedances = 123  # Winter 2022-23 (hits + misses)

# Color scheme
colors = {
    'aqm': '#d62728',       # Red
    'clyfar': '#2ca02c'      # Green
}
system_colors = [colors['aqm'], colors['clyfar']]

# Create figure with two panels
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8))

# X positions
x = np.arange(len(systems))
width = 0.35

# ============ TOP PANEL: POD and FAR ============
# Grouped bars: POD on left, FAR on right for each system
bars_pod = ax1.bar(x - width/2 - 0.02, pod, width, label='POD',
                   color=system_colors, edgecolor='black', linewidth=1.5)
bars_far = ax1.bar(x + width/2 + 0.02, far, width, label='FAR',
                   color=system_colors, edgecolor='black', linewidth=1.5,
                   alpha=0.5, hatch='///')

# Value labels on POD bars
for bar, val in zip(bars_pod, pod):
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
             f'{val:.1f}%', ha='center', va='bottom',
             fontsize=14, fontweight='bold')

# Value labels on FAR bars
for bar, val in zip(bars_far, far):
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
             f'{val:.1f}%', ha='center', va='bottom',
             fontsize=14, fontweight='bold')

# 50% reference line
ax1.axhline(50, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
ax1.text(1.7, 51, '50%', fontsize=10, color='gray', va='bottom')

# Top panel formatting
ax1.set_ylabel('Percentage (%)', fontsize=14, fontweight='bold')
ax1.set_ylim(0, 90)
ax1.set_xlim(-0.6, 1.9)
ax1.set_xticks(x)
ax1.set_xticklabels(systems, fontsize=11)
ax1.grid(axis='y', alpha=0.3, linestyle=':')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Legend for POD/FAR
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='gray', edgecolor='black', label='POD (solid)'),
    Patch(facecolor='gray', edgecolor='black', alpha=0.5, hatch='///', label='FAR (hatched)')
]
ax1.legend(handles=legend_elements, loc='upper right', fontsize=11)

ax1.set_title('Detection Rate (POD) vs False Alarm Rate (FAR)', fontsize=14, fontweight='bold')

# ============ BOTTOM PANEL: CSI ============
bars_csi = ax2.bar(x, csi, width=0.6, color=system_colors,
                   edgecolor='black', linewidth=1.5)

# Value labels on CSI bars
for bar, val in zip(bars_csi, csi):
    if val > 20:
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height()/2.,
                 f'{val:.1f}%', ha='center', va='center',
                 fontsize=16, fontweight='bold', color='white')
    else:
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                 f'{val:.1f}%', ha='center', va='bottom',
                 fontsize=16, fontweight='bold')

# Callout box on CLYFAR bar
ax2.text(1, 55, '2.2x higher POD\n1.3x higher CSI', ha='center', va='center',
         fontsize=12, fontweight='bold', color='#2ca02c',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#e8f5e9',
                   edgecolor='#2ca02c', linewidth=2))

# Bottom panel formatting
ax2.set_ylabel('Critical Success Index (%)', fontsize=14, fontweight='bold')
ax2.set_ylim(0, 70)
ax2.set_xlim(-0.6, 1.9)
ax2.set_xticks(x)
ax2.set_xticklabels(systems, fontsize=11)
ax2.grid(axis='y', alpha=0.3, linestyle=':')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

ax2.set_title('Overall Skill: Critical Success Index', fontsize=14, fontweight='bold')

# Sample size note at bottom
fig.text(0.5, 0.01, f'n = {n_exceedances} exceedances (Winter 2022-23)',
         ha='center', fontsize=11, style='italic', color='#555')

# Main title and subtitle
fig.suptitle('AQM vs CLYFAR',
             fontsize=20, fontweight='bold', y=0.98)
fig.text(0.5, 0.93,
         'Head-to-head comparison on Winter 2022-23 ozone exceedances',
         ha='center', fontsize=13, style='italic', color='#333')

plt.tight_layout(rect=[0, 0.04, 1, 0.90])

# Save
output_path = OUTPUT_DIR / 'figure3_clyfar_vs_aqm_poster.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Saved: {output_path}")
