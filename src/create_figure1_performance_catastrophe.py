#!/usr/bin/env python3
"""
Figure 1: The Performance Catastrophe
Shows AQM's systematic failure compared to persistence baseline
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Paths (following project conventions)
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'

# Pre-calculated data - apples-to-apples comparison
# AQM vs Persistence for each period
data = {
    'scenarios': ['AQM', 'Persistence', 'AQM', 'Persistence'],
    'period': ['2022-23 (High-Freq)', '2022-23 (High-Freq)',
               '5 Typical Winters', '5 Typical Winters'],
    'pod': [39.7, 76.2, 2.4, 7.5],
    'events': [151, 151, 42, 40],
    'days': [602, 602, 1955, 1363],
    'event_rate': [25.1, 25.1, 2.1, 2.9],
    'colors': ['#ff9999', '#66bb66', '#cc0000', '#2ca02c']  # light red, light green, dark red, dark green
}

# Create figure (12" x 8" for poster readability)
fig, ax = plt.subplots(figsize=(12, 8))

# Grouped bar positions
x = np.array([0, 1.0])  # Group centers (2022-23, 5 Typical) - closer together
width = 0.35
offsets = [-width/2 - 0.02, width/2 + 0.02]  # AQM left, Persistence right

# Draw bars by group
bars = []
for i, (scenario, pod, color) in enumerate(zip(data['scenarios'], data['pod'], data['colors'])):
    group_idx = i // 2  # 0 for first two, 1 for last two
    bar_idx = i % 2     # 0 for AQM, 1 for Persistence
    bar = ax.bar(x[group_idx] + offsets[bar_idx], pod, width, color=color,
                 edgecolor='black', linewidth=2)
    bars.append(bar[0])

# POD values on/above bars
for i, (bar, pod) in enumerate(zip(bars, data['pod'])):
    if pod > 15:  # Enough space for white text inside
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height()/2.,
                f'{pod:.1f}%', ha='center', va='center',
                fontsize=24, fontweight='bold', color='white')
    else:  # Too short - put text above bar, centered
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                f'{pod:.1f}%', ha='center', va='bottom',
                fontsize=24, fontweight='bold', color=data['colors'][i])

# Group labels below x-axis
ax.text(x[0], -12, '2022-23\n(High-Frequency Winter)', ha='center', fontsize=13, fontweight='bold')
ax.text(x[1], -12, '5 Typical Winters', ha='center', fontsize=13, fontweight='bold')

# Bar labels (AQM / Persistence) - smaller, below group labels
for i, bar in enumerate(bars):
    label = data['scenarios'][i]
    ax.text(bar.get_x() + bar.get_width()/2., -28, label,
            ha='center', fontsize=11, color='#555')

# 50% reference line
ax.axhline(50, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
ax.text(1.5, 51, '50% POD', fontsize=10, color='gray', va='bottom')

# Annotation: OPERATIONAL FAILURE (above the 2.4% bar)
ax.text(x[1] + offsets[0], 18, 'OPERATIONAL\nFAILURE', ha='center', va='bottom',
        fontsize=13, color='#cc0000', fontweight='bold')

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#ff9999', edgecolor='black', label='AQM'),
                   Patch(facecolor='#66bb66', edgecolor='black', label='Persistence')]
ax.legend(handles=legend_elements, loc='upper right', fontsize=12)

# Title and subtitle
fig.suptitle('NOAA Air Quality Model: Persistence Beats AQM in All Conditions',
             fontsize=18, fontweight='bold', y=0.97)
fig.text(0.5, 0.91,
         'Six-winter evaluation shows simple persistence outperforms the operational model',
         ha='center', fontsize=13, style='italic', color='#333')

# Formatting
ax.set_ylabel('Probability of Detection (%)', fontsize=14, fontweight='bold')
ax.set_ylim(-35, 95)
ax.set_xlim(-0.5, 1.5)
ax.set_xticks([])  # Remove default x-ticks
ax.grid(axis='y', alpha=0.3, linestyle=':')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout(rect=[0, 0.08, 1, 0.88])

# Save
output_path = OUTPUT_DIR / 'figure1_performance_catastrophe.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Saved: {output_path}")
