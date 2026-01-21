# AQM Evaluation Methodology

**Evaluating NOAA Air Quality Model (AQM) Performance for Wintertime Ozone in Utah's Uinta Basin**

---

## Overview

This document describes our comprehensive verification framework for evaluating NOAA's operational Air Quality Model (AQM) against observed wintertime ozone exceedances in Utah's Uinta Basin. Our analysis spans six winter seasons (2019-2025) with varying ozone activity levels across five monitoring stations.

### The Core Question

**Does the NOAA AQM provide skillful forecasts of wintertime ozone exceedances (>70 ppb) in the Uinta Basin?**

This is challenging because:
- **Scale mismatch**: AQM runs at 13 km resolution; basin cold pools are O(100m) deep
- **Rare phenomenon**: Winter ozone is unique to the Uinta Basin in the U.S.
- **Complex physics**: Requires snow-albedo feedback, cold-air pooling, and photochemistry simultaneously
- **Inter-annual variability**: Event frequency ranges from 0.3% to 25% of winter days across years

---

## Verification Framework

### Primary Threshold

**70 ppb MDA8 ozone** (NAAQS exceedance threshold)
- MDA8 = Maximum Daily 8-hour Average
- Used for all categorical verification (hits, misses, false alarms)

### Data Sources

| Source | Variable | Stations | Period |
|--------|----------|----------|--------|
| **Observations** | MDA8 O₃ | QRS, QV4, UBCSP, UBHSP, UB7ST | 2019-2025 (6 winters) |
| **AQM Forecasts** | Daily max 8-hr O₃ | Nearest grid point to each station | 2019-2025 |
| **Snow Depth** | Daily depth | UBHSP, UBCSP, COOP sites | 2016-2025 |
| **Meteorology** | T, RH, wind, solar | All ozone stations + UDOT sites | Variable |
| **CLYFAR Hindcast** | Ensemble forecasts (p50, p90, poss_elevated) | Basin-wide | Winter 2022-23 |

### Inter-Annual Variability in Dataset

**Critical Context**: Ozone exceedances are not uniformly distributed across winters:

| Winter | Days | Exceedances | Event Rate | AQM POD |
|--------|------|-------------|------------|---------|
| 2019-20 | 235 | 21 | 8.9% | 0.0% |
| 2020-21 | 514 | 2 | 0.4% | 0.0% |
| 2021-22 | 377 | 16 | 4.2% | 6.2% |
| **2022-23** | **602** | **151** | **25.1%** | **39.7%** |
| 2023-24 | 242 | 1 | 0.4% | 0.0% |
| 2024-25 | 587 | 2 | 0.3% | 0.0% |

**Key Finding**: Winter 2022-23 was anomalously active (151/193 total events, 78%). This allows us to evaluate AQM performance under **two distinct scenarios**:
1. **High-frequency winter** (2022-23): 25% event rate
2. **Typical low-frequency winters** (other 5): 2% event rate

AQM performance degrades catastrophically during typical conditions (POD: 39.7% → 2.4%).

### Contingency Table

|                    | **Obs ≥ 70 ppb** | **Obs < 70 ppb** |
|--------------------|------------------|------------------|
| **AQM ≥ 70 ppb**   | Hits (H)         | False Alarms (F) |
| **AQM < 70 ppb**   | Misses (M)       | Correct Neg (CN) |

### Core Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **POD** | H / (H + M) | Probability of Detection - what fraction of events did AQM catch? |
| **FAR** | F / (H + F) | False Alarm Ratio - when AQM warns, how often is it wrong? |
| **SR** | 1 - FAR | Success Ratio - when AQM warns, how often is it right? |
| **CSI** | H / (H + M + F) | Critical Success Index - overall skill accounting for hits, misses, and false alarms |
| **Bias** | (H + F) / (H + M) | Frequency bias - does AQM over/underforecast events? |
| **RMSE** | sqrt(mean((fcst - obs)²)) | Root mean square error - continuous magnitude error |
| **Mean Bias** | mean(fcst - obs) | Systematic over/underprediction |

### CLYFAR Hindcast Comparison

**CLYFAR** (Welsh: "clever") provides experimental ensemble forecasts for Uinta Basin ozone exceedances using fuzzy logic and possibility theory. We compare AQM against CLYFAR hindcasts to understand relative model skill.

**CLYFAR Ensemble Structure**:
- 31 ensemble members from GEFS (Global Ensemble Forecast System)
  - 1 control run (c00: best-estimate initial conditions)
  - 30 perturbed runs (p01-p30: IC + model physics perturbations)
- Treated as analog year scenarios (epistemic uncertainty)
- Key variables: `forecast_p50` (median), `forecast_p90` (90th percentile), `poss_elevated` (probability of elevated ozone)
- Basin-wide forecasts (not station-specific)

**Lead Time Matching** (Critical for Fair Comparison):
- **CLYFAR**: Day 1 forecasts (~24h lead time)
- **AQM**: Uses fxx=24 (Day 1, ~24h lead time) for CLYFAR comparison
- This ensures apples-to-apples comparison at matched lead times

**AQM Forecast Hour (fxx) Explanation**:
- **fxx=0 (analysis time)**: The model's best estimate using analysis-time initial conditions. This is NOT a true forecast with lead time—it represents maximum model skill under ideal data availability. Used for standalone AQM skill assessment.
- **fxx=24 (Day 1 forecast)**: A true 24-hour forecast issued the previous day. Used when comparing against other forecast systems (e.g., CLYFAR) to ensure fair lead-time matching.

**Parquet File fxx Values**:
| File | fxx Value | Purpose |
|------|-----------|---------|
| `all_matched_obs_aqm.parquet` | fxx=0 | Main AQM evaluation (6 winters, all stations) |
| `winter2022-23_aqm_fxx24.parquet` | fxx=24 | CLYFAR comparison (matched lead times) |

The fxx value is now stored as a column in the output parquet files for traceability.

**Comparison Methodology**:
- Date matching: AQM fxx=24 valid date = CLYFAR `valid_date`
- For station-based metrics, basin-wide CLYFAR forecasts are compared against individual station observations
- Overlap period: Winter 2022-23 only (92 unique dates, 459 station-day pairs)
- Data source: `data/clyfar_hindcast_stats.csv`, `data/winter2022-23_aqm_fxx24.parquet`

**CLYFAR Thresholds for Binary Classification**:
- `forecast_p50 ≥ 70`: Conservative (median exceeds threshold)
- `forecast_p90 ≥ 70`: Less conservative (90th percentile exceeds)
- `poss_elevated ≥ 0.3`: Probabilistic (30%+ chance of elevated ozone)
- `poss_extreme ≥ 0.1`: Probability of extreme ozone (10%+ chance)
- `poss_moderate ≥ 0.3`: Probability of moderate ozone (30%+ chance)

---

## Analysis Scripts

Each script addresses a specific hypothesis or evaluation dimension.

### 1. **analyze_baseline_comparison.py** — Does AQM Beat Naive Baselines?

**Purpose**: Test whether AQM provides value over simple persistence and climatology forecasts.

**Hypothesis**: AQM should beat "tomorrow = today" and "tomorrow = monthly average" forecasts, especially for **onset detection** (first day of multi-day events).

**Methods**:
- **Persistence baseline**: Use previous day's observation as forecast
- **Climatology baseline**: Use monthly mean observation as forecast
- **Event stratification**: Separate onset days (first exceedance) from continuation days (subsequent days)
  - Persistence has unfair advantage during multi-day events
  - AQM value should be clearest on onset days

**Key Outputs**:
- Overall POD/FAR/CSI for AQM vs baselines
- Onset POD vs continuation POD (stratified)
- Interpretation: Does AQM provide advance warning?

**Figure**: `figures/baseline_comparison.png`

---

### 2. **analyze_station_breakdown.py** — Does Skill Vary Spatially?

**Purpose**: Identify spatial patterns in AQM performance across the basin.

**Hypothesis**: Eastern basin stations (snow shadow region) may show worse POD due to model snow/radiation errors.

**Methods**:
- Calculate POD, bias, RMSE for each of 5 stations
- Compare western basin (UBCSP, QRS) vs eastern/central (UBHSP, QV4, UB7ST)
- Map visualization with POD color-coded by location

**Key Outputs**:
- Station-by-station verification table
- Spatial map showing POD at each station
- Horizontal bar chart comparing POD (west to east)

**Figures**:
- `figures/station_performance_map.png`
- `figures/station_pod_comparison.png`

---

### 3. **plot_conditional_bias.py** — Does Bias Depend on Ozone Magnitude?

**Purpose**: Diagnose whether AQM and CLYFAR systematically under/overpredict at different ozone concentrations.

**Hypothesis**: AQM underpredicts high-ozone events (misses the extreme tail).

**Methods**:
- Bin observations by concentration (20-40, 40-50, ..., 90+ ppb)
- Calculate mean bias (forecast - obs) and standard deviation for each bin
- Compare AQM bias vs CLYFAR p50 bias side-by-side
- Bar chart with error bars, color-coded by over/underprediction

**Key Outputs**:
- Conditional bias by observed bin for both AQM and CLYFAR p50
- Visual identification of bias regime change at threshold (70 ppb)
- Model comparison: AQM shows consistent underprediction; CLYFAR p50 shows stronger negative bias

**Figure**: `figures/conditional_bias.png`

---

### 4. **plot_stratified_analysis.py** — How Badly Does AQM Miss?

**Purpose**: 
1. Assess POD by **event severity** (70-80, 80-90, 90+ ppb)
2. Cross-tabulate **near-misses** (how far off was AQM when it missed?)

**Hypothesis**:
- Borderline events (70-80 ppb) are hardest to detect
- Severe misses (obs 90+, AQM <50) indicate fundamental model failure

**Methods**:
- **Part 1**: Calculate POD separately for three observed severity tiers
- **Part 2**: For miss days only, create 2D histogram of observed vs forecasted bins

**Key Outputs**:
- POD by severity (are extreme events easier or harder to catch?)
- Near-miss heatmap showing distribution of forecast errors
- Mean AQM forecast on miss days by severity tier

**Figures**:
- `figures/stratified_pod.png`
- `figures/near_miss_heatmap.png`

---

### 5. **plot_performance_diagram.py** — Multi-Model Performance Comparison

**Purpose**: Visualize POD vs Success Ratio on a performance diagram with CSI contours and bias lines; compare AQM against CLYFAR variants.

**Hypothesis**: Performance may vary significantly by winter season and forecast system.

**Methods**:
- Calculate POD, SR, CSI, bias for each of 6 winter seasons (AQM)
- Plot on performance diagram (Roebber 2009)
  - X-axis: Success Ratio (1 - FAR)
  - Y-axis: POD
  - Curved lines: CSI contours
  - Straight lines: Frequency bias
- Overlay all-seasons aggregate for AQM
- **Multi-model comparison** (winter 2022-23 overlap period):
  - AQM (station-specific)
  - CLYFAR p50 ≥ 70
  - CLYFAR p90 ≥ 70
  - CLYFAR poss_elevated ≥ 0.3

**Key Outputs**:
- Season-by-season performance points for AQM
- Multi-model comparison showing trade-offs between POD and FAR
- CLYFAR p90 shows highest POD but also highest FAR
- AQM achieves best balance (highest CSI)

**Figure**: `figures/performance_diagram.png`

---

### 6. **plot_exceedance_scatter.py** — Forecast vs Observed Scatter

**Purpose**: Visual scatter plot showing all matched obs/AQM pairs, color-coded by event type.

**Hypothesis**: Visually identify systematic patterns (e.g., clustering of misses at specific ranges).

**Methods**:
- Scatter plot: obs (x-axis) vs AQM (y-axis)
- Color code:
  - **Green**: Hits (both ≥70)
  - **Red**: Misses (obs ≥70, AQM <70)
  - **Orange**: False Alarms (obs <70, AQM ≥70)
  - **Gray**: Correct Negatives (both <70)
- Reference lines at 70 ppb and 1:1 diagonal

**Key Outputs**:
- Visual pattern recognition
- Identification of outliers
- Confirmation of conditional bias trends

**Figure**: `figures/exceedance_scatter.png`

---

### 7. **plot_contingency_table.py** — Visual 2x2 Table

**Purpose**: Create publication-quality visualization of contingency tables with metrics annotated; compare AQM vs CLYFAR.

**Methods**:
- 2x2 grid showing H, M, F, CN counts
- Color-coded cells (green = good, red = bad)
- Annotate with POD, FAR, CSI, Bias
- **Side-by-side comparison**: AQM vs CLYFAR p90 (winter 2022-23 overlap)

**Key Outputs**:
- Simple visual summary for presentations
- Quick reference for overall performance
- Direct visual comparison of AQM and CLYFAR contingency counts

**Figure**: `figures/contingency_table.png`

---

### 8. **analyze_snow_bias.py** — Snow-Bias Relationship

**Purpose**: Test whether AQM bias correlates with basin-averaged snow depth.

**Hypothesis**: AQM underpredicts more when snow is deep (because it doesn't use snow for albedo enhancement in photolysis).

**Methods**:
- Match AQM/obs pairs with daily basin-averaged snow depth
- Bin by snow depth (0-5, 5-10, 10-15, 15+ cm)
- Calculate mean bias and POD for each bin
- Scatter plot with regression line

**Key Outputs**:
- Correlation between snow depth and bias
- POD degradation with increasing snow
- Statistical significance (p-value, R²)

**Figure**: `figures/snow_bias_analysis.png`

---

### 9. **plot_resolution_scale.py** — Resolution vs Basin Scale

**Purpose**: Visualize the fundamental scale mismatch between AQM grid resolution and basin features.

**Hypothesis**: AQM's 13 km grid cannot resolve O(100m) cold pool depth or O(10 km) snow gradients.

**Methods**:
- Visual diagram showing:
  - AQM 13 km grid cell
  - Basin cold pool depth (~100-300 m)
  - Station locations
  - Snow gradient west-to-east
- Annotate with key dimensional mismatches

**Key Outputs**:
- Conceptual figure for poster/paper
- Illustrates why AQM struggles with this phenomenon

**Figure**: `figures/aqm_resolution_mismatch.png`

---

## CLYFAR Comparison Key Findings

A detailed comparison of AQM vs CLYFAR hindcasts for winter 2022-23 is documented in `reports/clyfar_vs_aqm_report.md`. Summary metrics for the overlap period (n=457 station-days, 123 exceedances), using **matched 24h lead times**:

| Model | CSI | POD | FAR | Bias |
|-------|-----|-----|-----|------|
| **AQM (Day 1)** | 0.291 | 0.333 | 0.305 | 0.48 |
| **CLYFAR p50** | 0.159 | 0.187 | 0.489 | 0.37 |
| **CLYFAR p90** | 0.369 | 0.748 | 0.578 | 1.77 |
| **CLYFAR poss≥0.3** | 0.367 | 0.593 | 0.510 | 1.21 |
| **CLYFAR extreme≥0.1** | 0.214 | 0.276 | 0.514 | 0.57 |
| **CLYFAR moderate≥0.3** | 0.274 | 0.789 | 0.704 | 2.67 |
| **Persistence** | 0.631 | 0.764 | 0.217 | 0.98 |

**Key Insights**:
- **CLYFAR p90 is the best CLYFAR variant** (CSI = 0.369, POD = 74.8%)
- CLYFAR p90 achieves 2.2× higher detection than AQM (74.8% vs 33.3% POD)
- CLYFAR p90 has 27% better skill than AQM (CSI 0.369 vs 0.291)
- CLYFAR p50 is too conservative, missing most events (POD = 18.7%)
- All CLYFAR probability thresholds have ~50-70% FAR (trade-off for higher detection)
- Persistence baseline outperforms all models on CSI (0.631)

---

## Refinement Recommendations

### Code Quality Improvements

1. **Create shared verification module** (`src/verification_metrics.py`):
   - Consolidate POD/FAR/CSI/bias calculations
   - Reduce code duplication across scripts
   - Ensure consistent metric definitions

2. **Add statistical significance tests**:
   - Bootstrap confidence intervals for POD differences
   - Test whether AQM improvement over persistence is significant
   - Spatial POD differences (western vs eastern basin)

3. **Fix climatology data leakage** (`analyze_baseline_comparison.py`):
   - Exclude future observations when computing climatology
   - Use only past data for true out-of-sample baseline

4. **Handle edge cases** (`analyze_station_breakdown.py`):
   - Division by zero when n_exceedance = 0 for a station
   - Graceful degradation with missing data

5. **Add lead-time stratification**:
   - Does AQM skill vary with forecast horizon (+24h, +48h, +72h)?
   - Currently analyzing only "day 0" forecasts

---

## Interpretation Guidelines

### What Constitutes "Skillful" Performance?

| Metric | Minimum Acceptable | Good | Excellent |
|--------|-------------------|------|-----------|
| POD | >50% (beats random) | >70% | >85% |
| FAR | <50% (beats random) | <30% | <15% |
| CSI | >0.45 (persistence) | >0.5 | >0.7 |
| Bias | 0.8-1.2 (±20%) | 0.9-1.1 (±10%) | 0.95-1.05 (±5%) |

### Red Flags Indicating Fundamental Limitations

- **POD ≤ Persistence POD**: AQM adds no value
- **Onset POD < 10%**: No advance warning capability
- **Strong snow-bias correlation**: Physics missing from model
- **Spatial POD gradient**: Systematic regional failure (e.g., snow shadow)

---

## Current Status (as of January 2026)

**Completed**:
- ✅ All 9 analysis scripts implemented
- ✅ 6 winter seasons of matched obs/AQM data (2019-2025)
- ✅ Baseline comparison framework
- ✅ Spatial breakdown across 5 stations
- ✅ Performance diagram with seasonal stratification
- ✅ Conditional bias and severity stratification
- ✅ CLYFAR hindcast comparison (winter 2022-23)
- ✅ Multi-model performance diagram
- ✅ Side-by-side contingency tables

**Pending**:
- ⏳ Bootstrap confidence intervals
- ⏳ Statistical significance tests
- ⏳ Lead-time analysis (+24h, +48h, +72h)
- ⏳ Final manuscript figures with updated styling
- ⏳ Shared verification metrics module

---

## References

### Verification Methodology
- Wilks, D.S. (2011). *Statistical Methods in the Atmospheric Sciences* (3rd ed.). Academic Press.
- Roebber, P.J. (2009). "Visualizing Multiple Measures of Forecast Quality." *Weather and Forecasting*, 24(2), 601-608.

### Uinta Basin Ozone
- Davies, M.J.; Lawson, J.R.; O'Neil, T.; Lyman, S.N.; Zager, K.; Coxson, T.D. (2025). "Uinta Basin Snow Shadow: Impact of Snow-Depth Variation on Winter Ozone Formation." *Air*, 3(3), 22. https://doi.org/10.3390/air3030022

### AQM Documentation
- NOAA National Air Quality Forecast Capability (NAQFC): https://registry.opendata.aws/noaa-nws-naqfc-pds/

---

## Quick Reference: Run All Analyses

```bash
# Navigate to project root
cd /path/to/davies-ams-2026

# Run all verification scripts
python src/analyze_baseline_comparison.py
python src/analyze_station_breakdown.py
python src/analyze_snow_bias.py
python src/plot_conditional_bias.py
python src/plot_stratified_analysis.py
python src/plot_performance_diagram.py
python src/plot_exceedance_scatter.py
python src/plot_contingency_table.py
python src/plot_resolution_scale.py

# All figures saved to figures/
ls -lh figures/
```

---

**Last Updated**: January 19, 2026  
**Contact**: Michael J. Davies, Utah State University
