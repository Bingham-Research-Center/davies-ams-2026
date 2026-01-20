# Analysis Complete: Stratified 6-Winter Evaluation

**Date Completed**: January 20, 2026  
**Analysis Approach**: Stratified by event frequency (high vs typical winters)

---

## What Changed (Jan 20, 2026)

### Previous Approach
- Reported aggregate metrics across all 6 winters
- Overall POD = 31.6% (seemed mediocre)
- Didn't explain why 78% of events were in one winter

### Updated Approach
- **Stratified reporting** by event frequency
- High-frequency winter (2022-23): POD = 39.7%
- **Typical winters (5 others): POD = 2.4%** ← The devastating finding
- Shows AQM fails when it matters most

---

## Key Documents Updated

### Core Analysis Documents
✅ **METHODOLOGY.md** - Added inter-annual variability section and context
✅ **METRICS_ANALYSIS.md** - Lead with stratified table, updated bottom line
✅ **README.md** - Filled in TBD sections with actual results
✅ **CASE_STUDIES.md** - Added stratified baseline comparison context

### New Reports Created
✅ **reports/interannual_variability.md** - Full 6-winter breakdown and interpretation
✅ **reports/EXECUTIVE_SUMMARY.md** - One-page summary for quick reference

### New Figures Generated
✅ **figures/interannual_variability.png** - Exceedances + POD by winter
✅ **figures/stratified_performance.png** - High vs typical winter comparison

---

## Final Metrics Summary

### Stratified Performance Table

| Scenario | Days | Exceedances | Rate | POD | CSI |
|----------|------|-------------|------|-----|-----|
| **Winter 2022-23** | 602 | 151 | 25.1% | **39.7%** | **0.355** |
| **Other 5 Winters** | 1,955 | 42 | 2.1% | **2.4%** | **0.020** |
| **All 6 Winters** | 2,557 | 193 | 7.5% | **31.6%** | **0.279** |
| **Persistence (All)** | 2,552 | 193 | 7.6% | **61.7%** | **0.446** |

### The Story in 3 Numbers
1. **2.4%** - AQM POD during typical winters (operationally useless)
2. **61.7%** - Persistence POD (beats AQM decisively)
3. **78%** - Fraction of events in one winter (shows rarity problem)

### CLYFAR vs AQM (Winter 2022-23, matched 24h lead)
- **CLYFAR moderate≥0.3**: POD = 71.7%, FAR = 0%, CSI = 0.717
- **AQM (Day 1)**: POD = 34.8%, FAR = 22%, CSI = 0.317
- **CLYFAR p90**: POD = 71.2%, FAR = 57.1%, CSI = 0.366

**Key insight**: Statistical ensemble approach (CLYFAR) achieves 2× AQM detection rate with zero false alarms when tuned conservatively (moderate threshold).

---

## Files Inventory

### Documentation (7 files)
```
README.md                   - Main project overview (updated with results)
METHODOLOGY.md              - Analysis framework (added stratified context)
METRICS_ANALYSIS.md         - Detailed metric discussion (stratified leading)
CASE_STUDIES.md             - Three case studies with context
ANALYSIS_COMPLETE.md        - This file (analysis roadmap)
reports/EXECUTIVE_SUMMARY.md - One-page summary
reports/interannual_variability.md - 6-winter breakdown
```

### Reports (8 files)
```
reports/baseline_comparison.md      - Persistence vs AQM
reports/station_breakdown.md        - Spatial analysis
reports/clyfar_vs_aqm_report.md     - CLYFAR comparison
reports/case_studies.md             - Case study validation
reports/snow_bias_analysis.md       - Snow depth relationship
reports/stratified_analysis.md      - POD by severity
reports/comparison_plot_guide.md    - Figure interpretation
reports/interannual_variability.md  - NEW: 6-winter analysis
reports/EXECUTIVE_SUMMARY.md        - NEW: One-page summary
```

### Figures (19 files)
```
Core Performance:
- baseline_comparison.png           - Persistence beats AQM
- performance_diagram.png           - POD vs SR (Roebber diagram)
- contingency_table.png             - 2x2 table with metrics
- exceedance_scatter.png            - Obs vs forecast scatter

Stratified Analysis:
- interannual_variability.png       - NEW: Events + POD by winter
- stratified_performance.png        - NEW: High vs typical comparison
- stratified_pod.png                - POD by observed severity
- near_miss_heatmap.png             - Miss error distribution

Spatial/Snow:
- station_performance_map.png       - Geographic POD distribution
- station_pod_comparison.png        - POD by station bars
- conditional_bias.png              - Bias vs concentration
- snow_bias_scatter.png             - Snow depth vs bias
- snow_bias_binned.png              - Binned snow analysis
- gfs_snow_scatter.png              - GFS vs obs snow
- gfs_snow_error_histogram.png      - GFS error distribution

Case Studies:
- case_study_feb2023_timeseries.png - Multi-day event evolution
- case_study_feb5_vs_feb7.png       - Worst vs best comparison
- case_study_three_days.png         - Three-day comparison

Infrastructure:
- aqm_resolution_mismatch.png       - Scale problem illustration
```

### Data Files (Key)
```
data/all_matched_obs_aqm.parquet           - Main dataset (fxx=0, n=2,758)
data/winter2022-23_aqm_fxx24.parquet       - CLYFAR comparison (fxx=24)
data/clyfar_hindcast_stats.csv             - CLYFAR forecasts
data/winter[YYYY-YY]_*.parquet             - Individual winter data
```

---

## For AMS Poster Presentation

### Recommended 6-Panel Layout

**Panel 1: Introduction**
- Winter ozone mechanism (snow-albedo-inversion)
- Scale problem (13 km vs 100 m)

**Panel 2: Methods**
- 6 winters, 5 stations, 2,557 days
- Stratified by event frequency
- Metrics: POD, CSI, bias

**Panel 3: Inter-Annual Variability** ← NEW EMPHASIS
- Figure: `interannual_variability.png`
- Shows 78% of events in 2022-23
- POD ranges 0-40% across years

**Panel 4: Stratified Performance** ← KEY FINDING
- Figure: `stratified_performance.png`
- High-frequency (2022-23): POD = 39.7%
- **Typical winters: POD = 2.4%** ← Highlight this
- Persistence: POD = 61.7%
- CLYFAR moderate≥0.3: POD = 71.7% (statistical approach)

**Panel 5: Root Causes**
- Figure: `gfs_snow_scatter.png` + `station_performance_map.png`
- GFS snow underestimation (70% of days)
- Spatial gradient (9× difference)
- Conditional bias (-77 ppb on extremes)

**Panel 6: Conclusions & Alternatives**
- AQM operationally useless in typical conditions
- Persistence forecast superior to AQM
- CLYFAR statistical ensemble shows promise (71.7% POD, 0% FAR)
- Recommendations: hybrid approach, nested domain, snow assimilation

### Elevator Pitch (30 seconds)
> "We evaluated NOAA's Air Quality Model for winter ozone in Utah's Uinta Basin across six winters. While one active year showed marginal skill (40% detection), five typical years revealed catastrophic failure (2% detection). Simple persistence forecasts beat AQM by 2:1. Our statistical ensemble system (CLYFAR) achieved 72% detection with zero false alarms. Root causes: 13 km grid can't resolve 100-meter cold pools, missing snow-albedo physics, and systematic GFS snow underestimation. Results suggest hybrid statistical-dynamical approaches may outperform traditional NWP for this rare, small-scale phenomenon."

---

## What's Next (Optional Enhancements)

### If Time Permits
1. Generate skill score plots (AQM - Persistence)
2. Add threshold sensitivity analysis (60, 70, 80 ppb)
3. Separate isolated vs multi-day event POD
4. Bootstrap confidence intervals on stratified metrics

### Not Critical for Poster
- Lead time analysis (fxx=48, fxx=72)
- Ensemble spread analysis
- Cost-loss decision framework

---

## Analysis Validation Checklist

✅ All numbers verified against source data
✅ Sample sizes clearly documented
✅ Inter-annual variability explained
✅ Stratified metrics calculated
✅ Figures generated and saved
✅ Executive summary created
✅ README placeholders filled
✅ METHODOLOGY updated with context
✅ METRICS_ANALYSIS leads with key finding
✅ All reports cross-referenced

---

## Contact & Attribution

**Primary Analyst**: Michael J. Davies, Utah State University  
**Supervisor**: J. R. Lawson  
**Conference**: 24th Joint Conference on Applications of Air Pollution Meteorology (AMS)  
**Date**: January 2026

---

**Status**: ✅ **ANALYSIS COMPLETE AND READY FOR POSTER**

The stratified approach strengthens your conclusions by showing AQM's failure is systematic across conditions, not an artifact of one bad winter. The 2.4% POD in typical winters is the smoking gun.
