# Clyfar vs AQM Comparison Plots

## Recommended Visualizations

### 1. Performance Diagram (Roebber 2009)
**Best single plot for exceedance skill comparison**

- X-axis: Success Ratio (1 - FAR)
- Y-axis: Probability of Detection (POD)
- Contours: CSI isolines
- Diagonal lines: Frequency Bias

Plot points for:
- Clyfar p50
- Clyfar p90
- Clyfar poss_elevated (multiple thresholds: 0.2, 0.3, 0.4)
- AQM

**Why**: Shows POD, FAR, CSI, and bias simultaneously. Easy to see trade-offs.

---

### 2. Scatter Plot: Forecast vs Observed
**Shows continuous forecast skill**

```
Panel A: Clyfar p50 vs Observed MDA8
Panel B: AQM vs Observed MDA8
```

- Add 1:1 line (perfect forecast)
- Add regression line with R² value
- Color points by exceedance (obs ≥ 70 ppb)
- Add horizontal/vertical lines at 70 ppb threshold

**Why**: Shows bias, spread, and where each model fails.

---

### 3. Time Series: High Ozone Episode
**Focus on Feb 4-14, 2023 (major event)**

- X-axis: Date
- Y-axis: Ozone (ppb)
- Lines: Observed (black), Clyfar p50 (blue), Clyfar p90 (light blue fill), AQM (red)
- Horizontal line at 70 ppb threshold
- Shade Clyfar p10-p90 range

**Why**: Shows how each model tracked the biggest event of the season.

---

### 4. Box Plot: Forecast Error by Ozone Category
**Shows conditional bias**

Categories:
- Background (obs < 50 ppb)
- Moderate (50-70 ppb)
- Elevated (70-90 ppb)
- Extreme (> 90 ppb)

Plot forecast error (forecast - observed) for Clyfar and AQM side-by-side.

**Why**: Reveals if models systematically fail at high/low ozone.

---

### 5. ROC Curve
**Probabilistic skill for exceedance prediction**

- X-axis: False Alarm Rate (1 - Specificity)
- Y-axis: Hit Rate (POD / Sensitivity)
- Curves:
  - Clyfar poss_elevated (varying threshold)
  - AQM (single point, deterministic)
- Diagonal = no skill

Calculate AUC (Area Under Curve) for Clyfar.

**Why**: Shows full probabilistic skill, not just at one threshold.

---

### 6. Reliability Diagram
**Calibration of possibility-based forecasts**

- X-axis: Forecast probability (poss_elevated bins: 0-0.2, 0.2-0.4, etc.)
- Y-axis: Observed frequency of exceedance
- Diagonal = perfect reliability
- Bar chart below showing sample size per bin

**Why**: Shows if "50% possibility of elevated" really means 50% chance.

---

### 7. Station Comparison Bar Chart
**Per-station skill**

Grouped bars showing CSI (or RMSE) for each station:
- QRS, QV4, UB7ST, UBCSP, UBHSP

Two bars per station: Clyfar (blue), AQM (red)

**Why**: Shows spatial variability in skill.

---

## Quick Implementation

```python
import matplotlib.pyplot as plt
import numpy as np

# Performance Diagram
fig, ax = plt.subplots(figsize=(8, 8))

# CSI contours
sr = np.linspace(0.01, 1, 100)
pod = np.linspace(0.01, 1, 100)
SR, POD = np.meshgrid(sr, pod)
CSI = 1 / (1/SR + 1/POD - 1)
ax.contour(SR, POD, CSI, levels=[0.1, 0.2, 0.3, 0.4, 0.5], colors='gray')

# Bias lines
for bias in [0.5, 1.0, 2.0]:
    pod_line = np.linspace(0, 1, 100)
    sr_line = pod_line / bias
    ax.plot(sr_line[sr_line <= 1], pod_line[sr_line <= 1], 'k--', alpha=0.3)

# Plot models (SR = 1 - FAR, POD)
models = {
    'Clyfar p50': (0.511, 0.187),      # (SR, POD)
    'Clyfar p90': (0.422, 0.748),
    'Clyfar poss≥0.3': (0.490, 0.593),
    'AQM': (0.695, 0.333),
}

colors = {'Clyfar p50': 'blue', 'Clyfar p90': 'lightblue',
          'Clyfar poss≥0.3': 'green', 'AQM': 'red'}

for name, (sr, pod) in models.items():
    ax.scatter(sr, pod, s=150, c=colors[name], label=name, edgecolors='black')

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xlabel('Success Ratio (1 - FAR)')
ax.set_ylabel('Probability of Detection')
ax.legend()
ax.set_aspect('equal')
plt.title('Performance Diagram: Clyfar vs AQM')
```

---

## Priority Order

1. **Performance Diagram** - Single most informative plot
2. **Scatter Plot** - Shows continuous skill
3. **Time Series** - Shows episode tracking
4. **ROC Curve** - If emphasizing probabilistic advantage

---

## Notes

- Always use consistent colors: Clyfar = blue shades, AQM = red
- Include sample sizes and confidence intervals where possible
- For Clyfar, show uncertainty range (p10-p90) when plotting time series
- Threshold of 70 ppb should always be marked
