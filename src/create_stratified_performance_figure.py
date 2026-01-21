#!/usr/bin/env python3
"""
Create stratified performance comparison figure for AMS poster
Shows the devastating 2.4% POD in typical winters vs 39.7% in high-frequency winter
"""

import matplotlib.pyplot as plt
import numpy as np

# Data from interannual_variability.md
scenarios = ['Winter\n2022-23', 'Other 5\nWinters', 'All 6\nWinters', 'Persistence\n(baseline)']
pod_values = [39.7, 2.4, 31.6, 61.7]
csi_values = [0.355, 0.020, 0.279, 0.446]
exceedances = [151, 42, 193, 193]
days = [602, 1955, 2557, 2552]

# Colors: red for AQM failures, green for persistence success
colors = ['#d62728', '#ff7f0e', '#1f77b4', '#2ca02c']

# Create figure with two subplots side by side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# --- Left panel: POD comparison ---
bars1 = ax1.bar(scenarios, pod_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for i, (bar, pod, exc, d) in enumerate(zip(bars1, pod_values, exceedances, days)):
    height = bar.get_height()
    # POD percentage
    ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
             f'{pod:.1f}%',
             ha='center', va='bottom', fontsize=14, fontweight='bold')
    # Sample size below
    ax1.text(bar.get_x() + bar.get_width()/2., -8,
             f'n={exc}/{d}',
             ha='center', va='top', fontsize=10, style='italic', color='#333')

ax1.set_ylabel('Probability of Detection (%)', fontsize=13, fontweight='bold')
ax1.set_ylim(-10, 75)
ax1.axhline(50, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='50% threshold')
ax1.grid(axis='y', alpha=0.3, linestyle=':')
ax1.set_title('Probability of Detection (POD)', fontsize=14, fontweight='bold', pad=15)

# Add annotation for the killer finding
ax1.annotate('Operational\nfailure', 
             xy=(1, 2.4), xytext=(1.5, 15),
             arrowprops=dict(arrowstyle='->', color='red', lw=2),
             fontsize=11, color='red', fontweight='bold',
             ha='center')

ax1.annotate('Beats\nAQM', 
             xy=(3, 61.7), xytext=(2.5, 55),
             arrowprops=dict(arrowstyle='->', color='green', lw=2),
             fontsize=11, color='green', fontweight='bold',
             ha='center')

# --- Right panel: CSI comparison ---
bars2 = ax2.bar(scenarios, [c*100 for c in csi_values], color=colors, alpha=0.8, 
                edgecolor='black', linewidth=1.5)

# Add value labels on bars
for i, (bar, csi) in enumerate(zip(bars2, csi_values)):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 1.5,
             f'{csi:.3f}',
             ha='center', va='bottom', fontsize=14, fontweight='bold')

ax2.set_ylabel('Critical Success Index (%)', fontsize=13, fontweight='bold')
ax2.set_ylim(0, 55)
ax2.axhline(30, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Useful skill')
ax2.grid(axis='y', alpha=0.3, linestyle=':')
ax2.set_title('Critical Success Index (CSI)', fontsize=14, fontweight='bold', pad=15)

# Add annotation
ax2.annotate('No skill', 
             xy=(1, 2), xytext=(1.5, 10),
             arrowprops=dict(arrowstyle='->', color='red', lw=2),
             fontsize=11, color='red', fontweight='bold',
             ha='center')

# Overall title
fig.suptitle('NOAA AQM Performance: Stratified by Event Frequency', 
             fontsize=16, fontweight='bold', y=0.98)

# Add subtitle with key takeaway
fig.text(0.5, 0.92, 
         'AQM shows near-complete failure (2.4% POD) during typical winters when forecasts matter most',
         ha='center', fontsize=12, style='italic', color='#333')

plt.tight_layout(rect=[0, 0, 1, 0.90])

# Save
output_path = 'figures/stratified_performance_poster.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✓ Saved: {output_path}")

plt.show()
