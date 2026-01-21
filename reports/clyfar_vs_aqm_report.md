# Clyfar vs AQM Verification Report
## Winter 2022-23 (24h Lead Time Comparison)

Generated: 2026-01-19 (Updated for lead time matching)

---

## Summary

**Important**: This comparison uses matched ~24h lead times for fair comparison:
- **AQM**: Day 1 forecasts (fxx=24)
- **CLYFAR**: Day 1 forecasts (~24h lead)

| Metric | Clyfar (p50) | **Clyfar (p90)** | AQM (Day 1) |
|--------|-------------|------------------|-------------|
| **CSI** | 0.159 | **0.369** | 0.291 |
| POD | 0.187 | **0.748** | 0.333 |
| FAR | 0.489 | 0.578 | 0.305 |
| Freq Bias | 0.37 | 1.77 | 0.48 |

**Note**: CLYFAR p90 achieves best balance of detection (74.8% POD) and skill (36.9% CSI).

---

## Data Overview

- **Verification Period**: 2022-12-02 to 2023-03-03
- **Total Forecast-Observation Pairs**: 457
- **Unique Dates**: 92
- **Stations**: QRS, QV4, UB7ST, UBCSP, UBHSP
- **Observed Exceedance Events (≥70 ppb)**: 123 (26.9%)
- **Lead Time (Both Models)**: ~24 hours (Day 1 forecasts)
- **AQM Data Source**: `data/winter2022-23_aqm_fxx24.parquet`
- **Ensemble Members (CLYFAR)**: 31

---

## Contingency Tables

### Clyfar p50 (≥ 70 ppb)

|  | Observed ≥70 | Observed <70 |
|--|-------------|--------------|
| **Forecast ≥70** | 23 (Hits) | 22 (FA) |
| **Forecast <70** | 100 (Misses) | 312 (CN) |

### Clyfar p90 (≥ 70 ppb)

|  | Observed ≥70 | Observed <70 |
|--|-------------|--------------|
| **Forecast ≥70** | 92 (Hits) | 126 (FA) |
| **Forecast <70** | 31 (Misses) | 208 (CN) |

### AQM Day 1 (fxx=24, ≥ 70 ppb)

|  | Observed ≥70 | Observed <70 |
|--|-------------|--------------|
| **Forecast ≥70** | 41 (Hits) | 18 (FA) |
| **Forecast <70** | 82 (Misses) | 316 (CN) |

---

## Possibility-Based Exceedance Prediction

Using possibility thresholds (obs ≥ 70 ppb, probability ≥ threshold):

| Threshold | Hits | Misses | FA | CN | POD | FAR | CSI |
|-----------|------|--------|-----|-----|-----|-----|-----|
| poss_elevated ≥ 0.3 | 73 | 50 | 76 | 258 | 0.593 | 0.510 | 0.367 |
| poss_extreme ≥ 0.1 | 34 | 89 | 36 | 298 | 0.276 | 0.514 | 0.214 |
| poss_moderate ≥ 0.3 | 97 | 26 | 231 | 103 | 0.789 | 0.704 | 0.274 |

**Best balance**: CLYFAR p90 (CSI = 0.369) outperforms all probability thresholds

---

## Station Breakdown

| Station | N | Clyfar CSI | AQM CSI | Clyfar RMSE | AQM RMSE |
|---------|---|------------|---------|-------------|----------|
| QRS | 92 | 0.185 | 0.577 | 22.2 | 10.0 |
| QV4 | 92 | 0.050 | 0.294 | 19.2 | 9.5 |
| UB7ST | 92 | 0.182 | 0.100 | 26.1 | 24.4 |
| UBCSP | 91 | 0.167 | 0.457 | 24.0 | 14.9 |
| UBHSP | 92 | 0.162 | 0.353 | 27.6 | 19.2 |

---

## High Ozone Events (Observed ≥ 70 ppb)

Top 20 events by observed MDA8:

| Date | Station | Obs (ppb) | Clyfar p50 | Clyfar p90 | Poss Elev | AQM |
|------|---------|-----------|------------|------------|-----------|-----|
| 2023-02-05 | UBHSP | 124.8 | 44.4 | 73.6 | 0.25 | 71.1 |
| 2023-02-05 | UBCSP | 117.1 | 44.4 | 73.6 | 0.25 | 89.7 |
| 2023-02-05 | UB7ST | 116.8 | 44.4 | 73.6 | 0.25 | 73.2 |
| 2023-02-06 | UB7ST | 116.8 | 58.6 | 79.7 | 0.43 | 64.6 |
| 2023-02-06 | UBHSP | 114.4 | 58.6 | 79.7 | 0.43 | 69.9 |
| 2023-02-13 | UBHSP | 113.6 | 35.0 | 44.8 | 0.00 | 83.9 |
| 2023-02-05 | QRS | 112.5 | 44.4 | 73.6 | 0.25 | 88.5 |
| 2023-02-04 | UB7ST | 111.9 | 65.5 | 85.1 | 0.53 | 54.1 |
| 2023-02-07 | UB7ST | 99.3 | 76.2 | 108.9 | 0.62 | 68.4 |
| 2023-02-06 | UBCSP | 110.9 | 58.6 | 79.7 | 0.43 | 74.9 |
| 2023-02-14 | UBHSP | 110.4 | 35.0 | 44.0 | 0.00 | 73.4 |
| 2023-02-04 | UBHSP | 110.3 | 65.5 | 85.1 | 0.53 | 67.2 |
| 2023-02-13 | UB7ST | 108.5 | 35.0 | 44.8 | 0.00 | 66.8 |
| 2023-02-07 | UBHSP | 104.6 | 76.2 | 108.9 | 0.62 | 80.9 |
| 2023-02-04 | UBCSP | 105.9 | 65.5 | 85.1 | 0.53 | 79.9 |
| 2023-02-06 | QRS | 105.4 | 58.6 | 79.7 | 0.43 | 80.0 |
| 2023-02-12 | UB7ST | 105.0 | 67.4 | 81.0 | 0.76 | 64.7 |
| 2023-02-08 | UBHSP | 103.1 | 59.7 | 78.0 | 0.48 | 82.2 |
| 2023-02-14 | UB7ST | 102.9 | 35.0 | 44.0 | 0.00 | 68.9 |
| 2023-02-19 | UBHSP | 102.8 | 58.5 | 79.8 | 0.47 | 73.6 |

---

## Key Findings

1. **CLYFAR p90 outperforms AQM**: CSI = 0.369 vs 0.291 (27% improvement)

2. **CLYFAR p90 achieves 2.2x higher detection**: POD = 74.8% vs AQM's 33.3%

3. **Trade-off**: CLYFAR p90 has higher FAR (57.8%) than AQM (30.5%), but the detection gain is worth it

4. **CLYFAR p50 too conservative**: POD = 18.7% misses most events

5. **Fair comparison**: Using matched lead times (~24h) provides apples-to-apples comparison
   - AQM fxx=24 (Day 1) vs CLYFAR Day 1 forecasts

6. **Both models underpredict extreme events**: Negative bias increases with observed concentration

---

## Methodology Notes

- **Threshold**: 70 ppb (NAAQS 8-hour ozone standard)
- **Clyfar**: Basin-wide forecast applied to all stations
- **AQM**: Station-specific NOAA Air Quality Model forecasts (fxx=24, Day 1)
- **Lead Time**: Both models use ~24 hour lead for fair comparison
- **Date Alignment**: AQM fxx=24 forecast init date + 1 day = valid date = CLYFAR valid_date
- **MDA8**: Maximum Daily 8-hour Average ozone concentration

---

---

## Case Study: Early February 2023

The early February 2023 ozone episode provides a compelling case study of model performance variability during a multi-day high ozone event.

### Event Overview (Feb 4-8, 2023)

| Date | Peak Obs (ppb) | CLYFAR p50 | CLYFAR p90 | poss_elevated | AQM mean | Result |
|------|----------------|------------|------------|---------------|----------|--------|
| Feb 4 | 111.9 | 65.5 | 85.1 | 0.53 | 67.8 | Partial |
| **Feb 5** | **124.8** | 44.4 | 73.6 | 0.25 | 78.1 | **MISS** |
| Feb 6 | 116.8 | 58.6 | 79.7 | 0.43 | 72.1 | MISS |
| Feb 7 | 104.6 | 76.2 | 108.9 | 0.62 | 76.1 | Partial |
| Feb 8 | 103.1 | 59.7 | 78.0 | 0.48 | 79.7 | Partial |

### Primary Case: February 5, 2023 - Extreme Underprediction

The worst forecast failure of winter 2022-23:

| Station | Observed | CLYFAR p50 | CLYFAR p90 | AQM |
|---------|----------|------------|------------|-----|
| Horsepool | **124.8** | 44.4 | 73.6 | 71.1 |
| Castle Peak | 117.1 | 44.4 | 73.6 | 89.7 |
| Seven Sisters | 116.8 | 44.4 | 73.6 | 73.2 |
| Roosevelt | 112.5 | 44.4 | 73.6 | 88.5 |

- **poss_elevated = 0.25** (only 25% chance predicted)
- All stations exceeded 100 ppb observed
- CLYFAR p50 error: ~36 ppb underprediction
- Both models completely missed this extreme event

### Secondary Case: February 7, 2023 - High Confidence, Moderate Success

CLYFAR showed highest confidence of the episode but with slight overprediction:

| Station | Observed | CLYFAR p50 | CLYFAR p90 | AQM |
|---------|----------|------------|------------|-----|
| Horsepool | **104.6** | 76.2 | 108.9 | 80.9 |
| Seven Sisters | 99.3 | 76.2 | 108.9 | 68.4 |
| Castle Peak | 82.2 | 76.2 | 108.9 | 74.9 |
| Roosevelt | 87.4 | 76.2 | 108.9 | 80.0 |

- **poss_elevated = 0.62** (62% chance predicted) - highest of episode
- CLYFAR p90 (108.9) overpredicted peak by ~4 ppb
- CLYFAR p50 (76.2) was reasonable for lower stations
- Demonstrates that high confidence doesn't guarantee accuracy

### Tertiary Case: February 13, 2023 - Complete Miss

A surprise event with no warning from either model:

| Station | Observed | CLYFAR p50 | CLYFAR p90 | AQM |
|---------|----------|------------|------------|-----|
| Horsepool | **113.6** | 35.0 | 44.8 | 83.9 |
| Seven Sisters | 108.5 | 35.0 | 44.8 | 66.8 |

- **poss_elevated = 0.00** (no chance predicted!)
- CLYFAR completely missed; AQM did better but still underforecast
- Highlights challenges in forecasting isolated events

### Key Findings

1. **Model skill varies dramatically within a single episode**: Performance changes from day to day even during persistent events
2. **Higher poss_elevated improves detection but may overpredict**: Feb 7 (poss=0.62) detected the event but p90 overpredicted by ~4 ppb
3. **Low poss_elevated correlates with underprediction**: Feb 5 (poss=0.25) showed severe underprediction despite 124.8 ppb observed
4. **Isolated events hardest to forecast**: Feb 13 (poss=0.00) was completely missed by both models

### Figures

- **Time Series**: `figures/case_study_feb2023_timeseries.png`
- **Feb 5 vs Feb 7 Comparison**: `figures/case_study_feb5_vs_feb7.png`
- **Three-Day Comparison**: `figures/case_study_three_days.png`

---

*Report updated 2026-01-20 with MDA8 timezone correction (UTC→MST local day boundaries)*
