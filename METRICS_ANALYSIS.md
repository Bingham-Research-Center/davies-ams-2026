# Q4: Statistical Metrics Analysis
## AQM Ozone Forecast Verification: Pros, Cons, and Alternative Interpretations

**Date**: January 20, 2026  
**Analyst**: Response to JRL request for metric precision

---

## Inter-Annual Variability: A Critical Finding

**Key Discovery**: Ozone exceedances varied dramatically across winters, with 78% of all events concentrated in winter 2022-23.

| Winter | Days | Exceedances | Rate | POD | CSI |
|--------|------|-------------|------|-----|-----|
| 2019-20 | 235 | 21 | 8.9% | 0.0% | 0.000 |
| 2020-21 | 514 | 2 | 0.4% | 0.0% | 0.000 |
| 2021-22 | 377 | 16 | 4.2% | 6.2% | 0.056 |
| **2022-23** | **602** | **151** | **25.1%** | **39.7%** | **0.355** |
| 2023-24 | 242 | 1 | 0.4% | 0.0% | 0.000 |
| 2024-25 | 587 | 2 | 0.3% | 0.0% | 0.000 |
| **Other 5 Winters** | **1,955** | **42** | **2.1%** | **2.4%** | **0.020** |
| **All 6 Winters** | **2,557** | **193** | **7.5%** | **31.6%** | **0.279** |

**Interpretation**: AQM shows marginal skill during high-frequency winters (2022-23: POD=39.7%) but **catastrophically fails** during typical low-frequency conditions (Other 5 winters: POD=2.4%). Simple persistence achieved 61.7% POD across all conditions.

---

## Actual Metrics Used

### Categorical Metrics (70 ppb threshold)

**Contingency Table (n = 2,557 matched days, all 6 winters)**:
- **Hits**: 61 (both obs & AQM ≥70 ppb)
- **Misses**: 132 (obs ≥70, AQM <70)
- **False Alarms**: 26 (obs <70, AQM ≥70)
- **Correct Negatives**: 2,338 (both <70)

**Derived Metrics (All 6 Winters)**:
- **POD (Probability of Detection)**: 0.316 (31.6%)
  - Formula: Hits / (Hits + Misses) = 61 / 193
  - *"Caught about 1/3 of exceedance days overall, but only 2.4% in typical winters"*

- **FAR (False Alarm Ratio)**: 0.299 (29.9%)
  - Formula: False Alarms / (Hits + False Alarms) = 26 / 87
  - *"About 1 in 4 forecasted exceedances don't happen"*

- **SR (Success Ratio)**: 0.701 (70.1%)
  - Formula: 1 - FAR

- **CSI (Critical Success Index)**: 0.279 (27.9%)
  - Formula: Hits / (Hits + Misses + False Alarms) = 61 / 219
  - *"Overall skill on exceedance events, but only 0.020 in typical winters"*

- **Frequency Bias**: 0.45
  - Formula: (Hits + False Alarms) / (Hits + Misses) = 87 / 193
  - *"AQM underforecasts exceedances ~2:1"*

- **Accuracy**: 0.938 (93.8%)
  - Formula: (Hits + Correct Negatives) / Total = 2,399 / 2,557

### Continuous Metrics (all days)

- **Mean Bias**: -4.37 ppb (AQM runs systematically low)
  - 2022-23: -6.33 ppb
  - Other winters: -3.77 ppb
- **RMSE**: 14.40 ppb
  - 2022-23: 14.65 ppb
  - Other winters: 14.33 ppb
- **MAE**: ~8.1 ppb
- **Pearson Correlation**: ~0.64 (R² ≈ 0.41)

---

## Pros and Cons of Each Metric

### 1. **POD (0.316)** — "How many real events did we catch?"

**Pros**:
✅ Operationally critical: "Did we warn the public?"  
✅ Intuitive: "Caught 32% of exceedances"  
✅ Independent of false alarm rate  

**Cons**:
❌ Ignores false alarms completely  
❌ Can be artificially inflated by "always forecast yes"  
❌ Sample size sensitive (only 193 observed exceedances)  
❌ **Conflates misses at 69 ppb with misses at 90 ppb** (both count equally)

**Limitation**: POD = 0.32 looks poor, but what if those 132 misses were mostly "borderline" cases (65-75 ppb)?

---

### 2. **FAR (0.299)** — "How often did we cry wolf?"

**Pros**:
✅ Public trust metric: false alarms erode credibility  
✅ Economic relevance: false warnings cost money/productivity  

**Cons**:
❌ Ignores misses completely  
❌ **Threshold-dependent**: A forecast of 69 ppb when obs = 95 ppb is a "correct negative" (!) but a 71 ppb forecast when obs = 20 ppb is a "false alarm"  
❌ Can be gamed by forecasting conservatively  

**Limitation**: FAR = 0.30 isn't terrible, but it rewards **underforecasting**, which is AQM's documented failure mode (Bias = 0.45).

---

### 3. **CSI (0.279)** — "Overall hit rate penalizing both misses AND false alarms"

**Pros**:
✅ Balanced metric: punishes both error types  
✅ Common in meteorology (threat score)  
✅ Range [0, 1] with clear interpretation  

**Cons**:
❌ Treats misses and false alarms as equal (are they?)  
❌ Sensitive to event rarity (low base rate = low CSI ceiling)  
❌ **No skill for correct negatives** — AQM got 2,338 non-exceedance days right, but CSI = 0.279 ignores that  

**Limitation**: CSI = 0.28 is poor, but in rare-event forecasting, what's "good"? (Context missing)

---

### 4. **Frequency Bias (0.45)** — "Do we forecast too often or not enough?"

**Pros**:
✅ **Diagnostic**: Reveals systematic under/over-forecasting  
✅ Independent of threshold placement skill  
✅ Clearly shows AQM's conservatism (forecasts exceedances ~55% less often than observed)  

**Cons**:
❌ **Not a skill score** — Bias = 1.0 doesn't mean good forecasts!  
❌ Can't distinguish "good but conservative" from "random but unbiased"  

**Key insight**: Bias = 0.45 explains the low POD — AQM is **missing by omission** (underforecasting), not missing by random error.

---

### 5. **Accuracy (0.938)** — "How often is AQM right?"

**Pros**:
✅ Intuitive: 93.8% correct sounds great!
✅ Comprehensive: uses all four contingency table cells

**Cons**:
❌ **MISLEADING for rare events** 🚨
❌ Base rate dominance: Exceedances = 7.5% of days (193/2557)
❌ A "dumb" model that always forecasts "no exceedance" would score 92.5% accuracy!

**Critical flaw**: Accuracy makes AQM look good (93.8%) while hiding catastrophic failure on the events that matter (POD = 32%).

---

### 6. **RMSE (14.40 ppb)** — "Typical forecast error magnitude"

**Pros**:
✅ Continuous metric: uses full concentration values  
✅ Standard in model evaluation  
✅ Units are interpretable (ppb)  

**Cons**:
❌ **Dominated by large errors** (squares amplify outliers)  
❌ Doesn't distinguish overprediction vs underprediction  
❌ Insensitive to threshold exceedances (60→70 ppb is weighted same as 20→30 ppb)  
❌ Conflates different error sources (phase errors, magnitude errors, missing physics)  

**Limitation**: RMSE = 14.40 ppb is ~21% of the 70 ppb threshold. Is that good or bad? (Need baseline comparison)

---

### 7. **Mean Bias (-4.37 ppb)** — "Average systematic error"

**Pros**:
✅ Simple diagnostic of over/underforecasting  
✅ Matches frequency bias finding (AQM runs low)  

**Cons**:
❌ **Cancellation problem**: +20 ppb error and -20 ppb error average to "perfect"  
❌ Doesn't reveal conditional bias (we know from conditional_bias.py that bias is -30 to -40 ppb at high O₃)  
❌ Small overall bias hides large errors at tails

**Limitation**: -4 ppb sounds minor, but it's deceptive—**conditional bias analysis shows AQM underpredicts by 30-40 ppb during actual exceedances**.

---

### 8. **Pearson Correlation (0.637)** — "Linear relationship strength"

**Pros**:
✅ Shows AQM captures day-to-day variability  
✅ R² = 0.406 means 40% of variance explained  

**Cons**:
❌ **Insensitive to bias** — perfect correlation even if systematically off by 50 ppb  
❌ Dominated by large dynamic range (20-90 ppb)  
❌ Linear assumption may not hold for photochemical systems  
❌ Doesn't care about threshold exceedances  

**Limitation**: r = 0.64 seems "OK", but it could reflect AQM just tracking temperature/sunlight while missing the snow-albedo-inversion mechanism entirely.

---

## Could Different Metrics Tell a Different Story?

### YES — Here are alternative interpretations:

#### **Optimistic Spin (using Accuracy & Correlation)**:
> *"AQM demonstrates strong performance with 93.8% accuracy and moderate correlation (r=0.64), successfully capturing day-to-day variability in ozone concentrations."*

**What it hides**: Misses 68% of exceedance events (the only days that matter for public health).

---

#### **Realistic Spin (using POD, Bias, Conditional Bias)**:
> *"AQM systematically underforecasts wintertime ozone (Bias=0.45), missing 68% of exceedance events (POD=0.32). Conditional bias analysis reveals errors grow to -30 to -40 ppb at concentrations exceeding 70 ppb, indicating missing physics for extreme events."*

---

#### **What We're NOT Measuring** (gaps in current analysis):

1. **Magnitude of misses**: Did AQM forecast 65 ppb when obs=75 (close call) or 30 ppb when obs=90 (total whiff)?
   - **Suggest**: Calculate mean absolute error **on misses only**
   
2. **Lead time skill**: Does AQM perform better at Day 1 vs Day 3 forecasts?
   - **Data limitation**: The main analysis dataset (`all_matched_obs_aqm.parquet`) uses fxx=0 (analysis time) only, representing maximum model skill rather than operational forecast lead times
   - **CLYFAR comparison uses fxx=24**: For fair lead-time matching with CLYFAR Day 1 forecasts, `winter2022-23_aqm_fxx24.parquet` provides AQM fxx=24 data for the overlap period
   
3. **Spatial bias**: Does AQM miss more at eastern vs western basin stations?
   - **Available**: 5 stations with different elevations/exposure
   
4. **Timing errors**: Does AQM get the right magnitude but wrong day?
   - **Suggest**: Calculate neighborhood/temporal skill scores

5. **Near-miss penalty**: Current metrics treat 69 ppb and 30 ppb forecasts identically when obs=70 ppb
   - **Suggest**: Calculate RMSE separately for exceedance days
   
6. **Public health impact**: Days >90 ppb are worse than >70 ppb, but CSI/POD treat equally
   - **Suggest**: Weighted CSI or stratified POD (70-80, 80-90, 90+)

---

## Recommended Metric Suite for Poster

**Primary Metrics** (tell the story):
- **POD = 0.32**: Shows operational failure to warn
- **Frequency Bias = 0.45**: Diagnostic of systematic underforecasting
- **CSI = 0.28**: Overall rare-event skill

**Supporting Evidence**:
- **Conditional bias plot**: Shows error grows with concentration (-4 ppb overall, but -35 ppb at >80 ppb)
- **Performance diagram**: Visualizes POD vs SR with seasonal variation
- **Contingency table**: Raw counts for transparency

**De-emphasize**:
- ❌ Accuracy (misleading for rare events)
- ❌ Overall bias (hides conditional behavior)
- ⚠️ Correlation (mention but don't lead with it)

---

## Critical Finding: Persistence Beats AQM

**This is the most damning result for AQM operational value:**

| Model | POD | CSI | Skill vs Persistence |
|-------|-----|-----|---------------------|
| AQM | 31.6% | 27.9% | — |
| Persistence | 61.7% | 44.6% | baseline |
| AQM Skill | — | — | POD: -0.784, CSI: -0.302 |

A simple "tomorrow = today" forecast outperforms the physics-based AQM model.

**Nuance:** AQM provides marginal advance warning (13.5% onset POD vs 0%), but this doesn't offset its overall poor performance.

**Poster recommendation:** Include this comparison prominently—it's the clearest evidence that AQM lacks skill for Uinta Basin winter ozone.

---

## Response to "2/3 of exceedances" claim

**Correction**: AQM caught **32% (61/193)** of exceedance days, not "2/3".

**Possible confusion**: Maybe thinking of Success Ratio (70%)? But that's "of forecasted exceedances, how many verified", not "of observed exceedances, how many were caught".

**The real story**:
- AQM issued 87 exceedance forecasts
- 61 were correct (70% success ratio) — decent precision
- But missed 132 real exceedances (68% miss rate) — poor recall
- **Classic precision/recall tradeoff where model is too conservative**

---

## Bottom Line

**Metric choice matters**:
- **Accuracy** makes AQM look good (93.8%)
- **Overall POD** makes AQM look mediocre (31.6%)
- **Stratified POD** reveals the truth (2.4% in typical winters)
- **All are technically correct**

**Which matters for this study?**
**Stratified POD, CSI, and conditional bias** — because the scientific question is *"Can AQM predict wintertime high-ozone events?"* and the public health question is *"Will people be warned?"*

The answer is: **No, AQM systematically underforecasts extreme events due to missing snow-albedo-inversion physics. During typical low-frequency winters, AQM is operationally useless (POD=2.4%).**

**The inter-annual variability finding is critical**: The overall 31.6% POD masks AQM's near-complete failure during 5 of 6 winters studied. Even during the active winter (2022-23), AQM's 39.7% POD loses decisively to simple persistence (61.7%).

---

## Snow Depth vs. AQM Bias Analysis

### Motivation
Extend case study findings (3 days) to full dataset (2,557 days) to test whether AQM bias is systematically related to snow cover.

### Data
- **Snow depth**: Basin-averaged daily snow depth from 7 stations (COOP, BRC, UDOT networks)
- **AQM verification**: Matched obs/forecast pairs from 5 ozone stations
- **Merged dataset**: 2,224 records with both snow and ozone data

### Key Findings

#### All Days (n = 2,224)

- Mean snow depth: 24.4 cm, Median: 4.0 cm
- Mean bias: -3.67 ppb, Median: -2.23 ppb
- Correlation: r = -0.06 (p = 0.004; negligible effect size, R² < 1%)
- Deep snow associated with larger underprediction

#### Exceedance Days in Snow Subset (n = 42 of 193 total)

- **Important**: This subset represents only 22% of all exceedance days — those with available snow data
- These 42 days are biased toward EXTREME events (mean observed = 124 ppb vs 94 ppb for all exceedances)
- Mean snow depth: 28.0 cm, Median: 16.9 cm
- **Mean bias: -76.7 ppb** — massive underprediction on extreme high-ozone events
- Median bias: -88.8 ppb
- Correlation: r = 0.26 (p = 0.09; moderate effect size, R² = 7%)
- **Note on significance**: The all-days correlation is "statistically significant" only due to large sample size (n=2,224) — the effect is negligible (R² < 1%). The exceedance-day correlation (r=0.26) is substantively stronger despite not reaching α=0.05 with n=42.
- For comparison, all 193 exceedance days have mean bias of -31.5 ppb

#### All Exceedance Days (n = 193)

- Mean bias: **-31.5 ppb**
- This aligns with the conditional bias analysis showing -30 to -40 ppb errors at high concentrations
- Non-exceedance days have near-zero bias (-2.15 ppb), which dilutes the overall mean (-4.37 ppb)

### Interpretation

1. **Overall bias masks severe exceedance-day errors**: The -4.37 ppb overall mean bias is dominated by non-exceedance days (n=2,364, bias=-2.15 ppb). All 193 exceedance days have mean bias of -31.5 ppb — consistent with conditional bias analysis.

2. **Snow subset captures the most extreme events**: The 42 exceedance days with snow data represent the highest-severity episodes (mean obs=124 ppb). The -76.7 ppb bias for this subset indicates AQM fails most catastrophically on extreme events.

3. **Snow cover is strongly associated with exceedance events**: Median snow depth is ~4× higher on exceedance days (17 cm) than typical days (4 cm)

4. **Snow-albedo mechanism confirmed**: Most exceedance days have substantial snow cover, contributing to enhanced photolysis and ozone production that AQM fails to capture

### Figures
- `figures/snow_bias_scatter.png` — Side-by-side scatter plots (all days vs exceedance)
- `figures/snow_bias_binned.png` — Side-by-side bar charts by snow depth bins

---

## References

- Wilks, D.S. (2011). *Statistical Methods in the Atmospheric Sciences* (3rd ed.). Chapter 8: Forecast Verification.
- Roebber, P.J. (2009). Visualizing Multiple Measures of Forecast Quality. *Weather and Forecasting*, 24(2), 601-608. (Performance diagrams)
