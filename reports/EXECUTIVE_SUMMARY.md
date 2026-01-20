# AQM Evaluation: Executive Summary

**Date**: January 20, 2026  
**Study Period**: 6 Winter Seasons (2019-2025)  
**Total Matched Days**: 2,557  
**Total Exceedances**: 193

---

## Bottom Line (One Sentence)

**NOAA's Air Quality Model shows marginal skill during active ozone winters (POD=39.7%) but catastrophic failure during typical conditions (POD=2.4%), losing decisively to simple persistence forecasts (POD=61.7%) across all scenarios.**

---

## Key Findings

### 1. Inter-Annual Variability Reveals Systematic Failure

| Scenario | Days | Exceedances | POD | CSI |
|----------|------|-------------|-----|-----|
| Winter 2022-23 (Active) | 602 | 151 (25% rate) | 39.7% | 0.355 |
| Other 5 Winters (Typical) | 1,955 | 42 (2% rate) | **2.4%** | **0.020** |
| All 6 Winters | 2,557 | 193 (7.5% rate) | 31.6% | 0.279 |

**Interpretation**: AQM performance collapses precisely when needed most—during typical winters with rare, unexpected events.

### 2. Persistence Baseline Dominates

| Model | POD | FAR | CSI |
|-------|-----|-----|-----|
| **Persistence** ("tomorrow = today") | **61.7%** | 38.3% | **0.446** |
| AQM (analysis time) | 31.6% | 29.9% | 0.279 |

**AQM shows negative skill** relative to the simplest possible baseline.

### 3. Conditional Bias Grows with Severity

| Observed Range | Mean AQM Bias | n |
|----------------|---------------|---|
| All days | -4.37 ppb | 2,557 |
| Exceedance days (≥70 ppb) | **-31.5 ppb** | 193 |
| Extreme events with snow | **-76.7 ppb** | 42 |

**Interpretation**: AQM systematically underpredicts high-ozone events by 30-80 ppb, missing the magnitude that matters for public health.

### 4. Spatial Gradient Indicates Physical Mechanism

| Station | Location | POD | Miss Rate |
|---------|----------|-----|-----------|
| QRS | Western basin | 66.7% | 33.3% |
| UBCSP | Southern basin | 42.2% | 57.8% |
| UBHSP | Central basin | 23.5% | 76.5% |
| UB7ST | **Eastern basin** | **7.5%** | **92.5%** |

**9× difference** in POD across basin suggests snow shadow effect (Davies et al. 2025).

### 5. GFS Snow Depth Errors

| Metric | Value |
|--------|-------|
| Mean bias (GFS - Obs) | -5.0 cm (-48%) |
| Days underestimated | 69.8% |
| Bias for deep snow (20+ cm) | **-19.8 cm (-66%)** |
| Correlation | r = 0.687 |

**Interpretation**: GFS systematically underestimates snow depth, especially during deep snow events most critical for ozone formation.

---

## Root Causes

1. **Scale Mismatch**: 13 km grid cannot resolve 100m cold pools
2. **Missing Physics**: Snow-albedo feedback not in photolysis scheme
3. **Input Errors**: GFS snow underestimation propagates to AQM
4. **Rare Event Problem**: Model optimized for typical conditions fails on extremes

---

## Operational Impact

### Public Health Consequences

- **132 missed exceedances** (68% of events): No public warning
- **26 false alarms**: Erodes public trust
- **2.4% POD in typical winters**: Operationally useless when surprise events occur

### Economic Costs

- Missed warnings: Health impacts, emergency response
- False alarms: Unnecessary business disruptions, advisory costs
- **Simple persistence would be more cost-effective**

---

## Comparison to CLYFAR (Winter 2022-23)

| Model | POD | FAR | CSI | Lead Time |
|-------|-----|-----|-----|-----------|
| AQM (Day 1) | 34.8% | 22.0% | 0.317 | 24h |
| CLYFAR p50 | 18.2% | 46.7% | 0.157 | 24h |
| CLYFAR p90 | 71.2% | 57.1% | 0.366 | 24h |
| **CLYFAR moderate≥0.3** | **71.7%** | **0.0%** | **0.717** | 24h |

**At matched lead times**, CLYFAR moderate threshold outperforms both AQM and CLYFAR p50/p90.

---

## Recommendations

### Immediate (Operational)

1. **Use persistence forecast** until AQM improvements implemented
2. **Hybrid approach**: AQM for transport, statistical correction for local enhancement
3. **Lower threshold**: Issue advisories at 60 ppb to improve advance warning

### Near-Term (Research)

1. **Nested domain**: 1-3 km resolution over Uinta Basin
2. **Snow assimilation**: Incorporate basin snow depth observations
3. **Photolysis update**: Add snow-albedo enhancement parameterization

### Long-Term (Infrastructure)

1. **Dense observing network**: Fill gaps in eastern basin
2. **Snow monitoring**: Real-time snow depth at all ozone sites
3. **Ensemble forecasting**: Probabilistic guidance (CLYFAR-style)

---

## Supporting Evidence

### Reports
- `reports/interannual_variability.md` - Full 6-winter breakdown
- `reports/baseline_comparison.md` - Persistence vs AQM
- `reports/station_breakdown.md` - Spatial analysis
- `reports/snow_bias_analysis.md` - Snow-bias relationship
- `reports/clyfar_vs_aqm_report.md` - CLYFAR comparison

### Figures
- `figures/interannual_variability.png` - Events by winter
- `figures/stratified_performance.png` - High vs low frequency
- `figures/baseline_comparison.png` - Persistence dominance
- `figures/conditional_bias.png` - Bias vs concentration
- `figures/station_performance_map.png` - Spatial gradient
- `figures/gfs_snow_scatter.png` - GFS snow errors

---

## For AMS Poster

### Lead Message
> "NOAA AQM shows near-zero skill (POD=2.4%) for detecting winter ozone exceedances during typical low-frequency winters in Utah's Uinta Basin, losing to simple persistence (POD=61.7%). Root causes: 13 km grid cannot resolve 100m cold pools, missing snow-albedo physics, and GFS snow underestimation."

### Key Numbers for Impact
- **2.4% POD** in typical winters (5 of 6 studied)
- **61.7% vs 31.6%**: Persistence beats AQM
- **9× spatial gradient**: East (7.5%) vs West (66.7%) POD
- **-77 ppb bias** on extreme events with snow
- **70% of days**: GFS underestimates snow

### Figures for Poster
1. **Interannual variability** - Shows 2022-23 dominance
2. **Stratified performance** - High vs typical winter POD
3. **Baseline comparison** - Persistence beats AQM
4. **Station map** - Spatial POD gradient
5. **GFS snow scatter** - Input data error
6. **Conditional bias** - Error grows with severity

---

**Conclusion**: AQM requires fundamental improvements (resolution, physics, inputs) before it can provide operational value for Uinta Basin winter ozone forecasting. Current guidance is worse than "tomorrow will be like today."
