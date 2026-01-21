#!/usr/bin/env python3
"""
Figure 2: Inter-Annual Variability in Ozone Events and AQM Skill
Shows extreme year-to-year variation in event frequency and model performance
"""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Paths (following project conventions)
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'

# Data from reports/interannual_variability.md
winters = ['2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']
exceedances = [21, 2, 16, 151, 1, 2]
pod = [0.0, 0.0, 6.2, 39.7, 0.0, 0.0]

# Create figure (12" x 7" for poster readability)
fig, ax1 = plt.subplots(figsize=(12, 7))

# X positions
x = np.arange(len(winters))

# Bar colors: highlight 2022-23 (index 3) in bright orange, others in muted gray
bar_colors = ['#888888'] * len(winters)
bar_colors[3] = '#ff6b35'  # Bright orange for the outlier

# Left Y-axis: Exceedance counts as bars
bars = ax1.bar(x, exceedances, color=bar_colors, edgecolor='black', linewidth=1.5,
               alpha=0.85, zorder=2, width=0.65)

ax1.set_xlabel('Winter Season', fontsize=14, fontweight='bold')
ax1.set_ylabel('Number of Exceedances', fontsize=14, fontweight='bold', color='#444')
ax1.set_xticks(x)
ax1.set_xticklabels(winters, fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor='#444', labelsize=11)

# Use log scale for left axis to handle the extreme range (1-151)
ax1.set_yscale('log')
ax1.set_ylim(0.8, 300)
ax1.set_yticks([1, 2, 5, 10, 20, 50, 100, 150])
ax1.get_yaxis().set_major_formatter(plt.ScalarFormatter())

# Right Y-axis: POD as line with markers
ax2 = ax1.twinx()
line = ax2.plot(x, pod, color='#5c4d9a', linewidth=3, marker='o', markersize=12,
                markerfacecolor='#7c6cb0', markeredgecolor='#3d3266', markeredgewidth=2,
                zorder=3, label='POD (%)')
ax2.set_ylabel('Probability of Detection (%)', fontsize=14, fontweight='bold', color='#5c4d9a')
ax2.tick_params(axis='y', labelcolor='#5c4d9a', labelsize=11)
ax2.set_ylim(-5, 60)

# Add value labels on bars (exceedance counts)
for i, (bar, exc) in enumerate(zip(bars, exceedances)):
    # Position above bar
    y_pos = exc * 1.15  # log scale adjustment
    ax1.text(bar.get_x() + bar.get_width()/2., y_pos, str(exc),
             ha='center', va='bottom', fontsize=13, fontweight='bold',
             color='#333')

# Add POD labels near markers
for i, (xi, p) in enumerate(zip(x, pod)):
    if p > 0:
        # Non-zero POD: label above
        ax2.text(xi, p + 4, f'{p:.1f}%', ha='center', va='bottom',
                 fontsize=12, fontweight='bold', color='black')
    else:
        # Zero POD: label below with "0%"
        ax2.text(xi, p + 3, '0%', ha='center', va='bottom',
                 fontsize=11, fontweight='bold', color='black')

# Annotation: "78% of all events" callout for 2022-23
ax1.annotate('78% of all events\n(151 exceedances)',
             xy=(3, 151), xytext=(4.2, 100),
             fontsize=12, fontweight='bold', color='#cc3300',
             ha='center',
             arrowprops=dict(arrowstyle='->', color='#cc3300', lw=2),
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff5f0', edgecolor='#cc3300'))

# Title and subtitle
fig.suptitle('Extreme Inter-Annual Variability in Ozone Events and AQM Skill',
             fontsize=18, fontweight='bold', y=0.97)
fig.text(0.5, 0.90,
         '78% of exceedances occurred in winter 2022-23; 4 of 6 winters had 0% POD',
         ha='center', fontsize=13, style='italic', color='#333')

# Grid and styling
ax1.grid(axis='y', alpha=0.3, linestyle=':', zorder=1)
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)

# Legend
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
legend_elements = [
    Patch(facecolor='#ff6b35', edgecolor='black', label='Exceedances (2022-23)'),
    Patch(facecolor='#888888', edgecolor='black', label='Exceedances (other winters)'),
    Line2D([0], [0], color='#5c4d9a', linewidth=3, marker='o', markersize=10,
           markerfacecolor='#7c6cb0', label='POD (%)')
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=11)

plt.tight_layout(rect=[0, 0, 1, 0.88])

# Save
output_path = OUTPUT_DIR / 'figure2_interannual_variability_poster.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Saved: {output_path}")
