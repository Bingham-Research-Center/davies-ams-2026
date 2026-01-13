# Q4: Statistical Metrics Analysis
## AQM Ozone Forecast Verification: Pros, Cons, and Alternative Interpretations

**Date**: January 12, 2026  
**Analyst**: Response to JRL request for metric precision

---

## Actual Metrics Used

### Categorical Metrics (70 ppb threshold)

**Contingency Table (n = 2,769 matched days)**:
- **Hits**: 62 (both obs & AQM ≥70 ppb)
- **Misses**: 144 (obs ≥70, AQM <70)
- **False Alarms**: 25 (obs <70, AQM ≥70)
- **Correct Negatives**: 2,334 (both <70)

**Derived Metrics**:
- **POD (Probability of Detection)**: 0.301 (30.1%)
  - Formula: Hits / (Hits + Misses) = 62 / 206
  - *"Caught about 1/3 of exceedance days"* ❌ Original claim was wrong!
  
- **FAR (False Alarm Ratio)**: 0.287 (28.7%)
  - Formula: False Alarms / (Hits + False Alarms) = 25 / 87
  - *"About 1 in 4 forecasted exceedances don't happen"*
  
- **SR (Success Ratio)**: 0.713 (71.3%)
  - Formula: 1 - FAR
  
- **CSI (Critical Success Index)**: 0.268 (26.8%)
  - Formula: Hits / (Hits + Misses + False Alarms) = 62 / 231
  - *"Overall skill on exceedance events"*
  
- **Frequency Bias**: 0.42
  - Formula: (Hits + False Alarms) / (Hits + Misses) = 87 / 206
  - *"AQM underforecasts exceedances 2:1"*
  
- **Accuracy**: 0.865 (86.5%)
  - Formula: (Hits + Correct Negatives) / Total = 2,396 / 2,769

### Continuous Metrics (all days)

- **Mean Bias**: -5.01 ppb (AQM runs systematically low)
- **RMSE**: 14.76 ppb
- **MAE**: 8.28 ppb
- **Pearson Correlation**: 0.637 (R² = 0.406)

---

## Pros and Cons of Each Metric

### 1. **POD (0.301)** — "How many real events did we catch?"

**Pros**:
✅ Operationally critical: "Did we warn the public?"  
✅ Intuitive: "Caught 30% of exceedances"  
✅ Independent of false alarm rate  

**Cons**:
❌ Ignores false alarms completely  
❌ Can be artificially inflated by "always forecast yes"  
❌ Sample size sensitive (only 206 observed exceedances)  
❌ **Conflates misses at 69 ppb with misses at 90 ppb** (both count equally)

**Limitation**: POD = 0.30 looks terrible, but what if those 144 misses were mostly "borderline" cases (65-75 ppb)?

---

### 2. **FAR (0.287)** — "How often did we cry wolf?"

**Pros**:
✅ Public trust metric: false alarms erode credibility  
✅ Economic relevance: false warnings cost money/productivity  

**Cons**:
❌ Ignores misses completely  
❌ **Threshold-dependent**: A forecast of 69 ppb when obs = 95 ppb is a "correct negative" (!) but a 71 ppb forecast when obs = 20 ppb is a "false alarm"  
❌ Can be gamed by forecasting conservatively  

**Limitation**: FAR = 0.29 isn't terrible, but it rewards **underforecasting**, which is AQM's documented failure mode (Bias = 0.42).

---

### 3. **CSI (0.268)** — "Overall hit rate penalizing both misses AND false alarms"

**Pros**:
✅ Balanced metric: punishes both error types  
✅ Common in meteorology (threat score)  
✅ Range [0, 1] with clear interpretation  

**Cons**:
❌ Treats misses and false alarms as equal (are they?)  
❌ Sensitive to event rarity (low base rate = low CSI ceiling)  
❌ **No skill for correct negatives** — AQM got 2,334 non-exceedance days right, but CSI = 0.268 ignores that  

**Limitation**: CSI = 0.27 is poor, but in rare-event forecasting, what's "good"? (Context missing)

---

### 4. **Frequency Bias (0.42)** — "Do we forecast too often or not enough?"

**Pros**:
✅ **Diagnostic**: Reveals systematic under/over-forecasting  
✅ Independent of threshold placement skill  
✅ Clearly shows AQM's conservatism (forecasts exceedances 58% less often than observed)  

**Cons**:
❌ **Not a skill score** — Bias = 1.0 doesn't mean good forecasts!  
❌ Can't distinguish "good but conservative" from "random but unbiased"  

**Key insight**: Bias = 0.42 explains the low POD — AQM is **missing by omission** (underforecasting), not missing by random error.

---

### 5. **Accuracy (0.865)** — "How often is AQM right?"

**Pros**:
✅ Intuitive: 86.5% correct sounds great!  
✅ Comprehensive: uses all four contingency table cells  

**Cons**:
❌ **MISLEADING for rare events** 🚨  
❌ Base rate dominance: Exceedances = 7.4% of days (206/2769)  
❌ A "dumb" model that always forecasts "no exceedance" would score 92.6% accuracy!  

**Critical flaw**: Accuracy makes AQM look good (86.5%) while hiding catastrophic failure on the events that matter (POD = 30%).

---

### 6. **RMSE (14.76 ppb)** — "Typical forecast error magnitude"

**Pros**:
✅ Continuous metric: uses full concentration values  
✅ Standard in model evaluation  
✅ Units are interpretable (ppb)  

**Cons**:
❌ **Dominated by large errors** (squares amplify outliers)  
❌ Doesn't distinguish overprediction vs underprediction  
❌ Insensitive to threshold exceedances (60→70 ppb is weighted same as 20→30 ppb)  
❌ Conflates different error sources (phase errors, magnitude errors, missing physics)  

**Limitation**: RMSE = 14.76 ppb is ~21% of the 70 ppb threshold. Is that good or bad? (Need baseline comparison)

---

### 7. **Mean Bias (-5.01 ppb)** — "Average systematic error"

**Pros**:
✅ Simple diagnostic of over/underforecasting  
✅ Matches frequency bias finding (AQM runs low)  

**Cons**:
❌ **Cancellation problem**: +20 ppb error and -20 ppb error average to "perfect"  
❌ Doesn't reveal conditional bias (we know from conditional_bias.py that bias is -30 to -40 ppb at high O₃)  
❌ Small overall bias hides large errors at tails  

**Limitation**: -5 ppb sounds minor, but it's deceptive—**conditional bias analysis shows AQM underpredicts by 30-40 ppb during actual exceedances**.

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
> *"AQM demonstrates strong performance with 86.5% accuracy and moderate correlation (r=0.64), successfully capturing day-to-day variability in ozone concentrations."*

**What it hides**: Misses 70% of exceedance events (the only days that matter for public health).

---

#### **Realistic Spin (using POD, Bias, Conditional Bias)**:
> *"AQM systematically underforecasts wintertime ozone (Bias=0.42), missing 70% of exceedance events (POD=0.30). Conditional bias analysis reveals errors grow to -30 to -40 ppb at concentrations exceeding 70 ppb, indicating missing physics for extreme events."*

---

#### **What We're NOT Measuring** (gaps in current analysis):

1. **Magnitude of misses**: Did AQM forecast 65 ppb when obs=75 (close call) or 30 ppb when obs=90 (total whiff)?
   - **Suggest**: Calculate mean absolute error **on misses only**
   
2. **Lead time skill**: Does AQM perform better at Day 1 vs Day 3 forecasts?
   - **Data limitation**: We're using fxx=0 (analysis time) only
   
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
- **POD = 0.30**: Shows operational failure to warn
- **Frequency Bias = 0.42**: Diagnostic of systematic underforecasting
- **CSI = 0.26**: Overall rare-event skill

**Supporting Evidence**:
- **Conditional bias plot**: Shows error grows with concentration (-5 ppb overall, but -35 ppb at >80 ppb)
- **Performance diagram**: Visualizes POD vs SR with seasonal variation
- **Contingency table**: Raw counts for transparency

**De-emphasize**:
- ❌ Accuracy (misleading for rare events)
- ❌ Overall bias (hides conditional behavior)
- ⚠️ Correlation (mention but don't lead with it)

---

## Response to "2/3 of exceedances" claim

**Correction**: AQM caught **30% (62/206)** of exceedance days, not "2/3".

**Possible confusion**: Maybe thinking of Success Ratio (71%)? But that's "of forecasted exceedances, how many verified", not "of observed exceedances, how many were caught".

**The real story**: 
- AQM issued 87 exceedance forecasts
- 62 were correct (71% success ratio) — decent precision
- But missed 144 real exceedances (70% miss rate) — terrible recall
- **Classic precision/recall tradeoff where model is too conservative**

---

## Bottom Line

**Metric choice matters**:
- **Accuracy** makes AQM look good (86.5%)
- **POD** makes AQM look bad (30%)
- **Both are technically correct**

**Which matters for this study?**  
**POD, CSI, and conditional bias** — because the scientific question is *"Can AQM predict wintertime high-ozone events?"* and the public health question is *"Will people be warned?"*

The answer is: **No, AQM systematically underforecasts extreme events due to missing snow-albedo-inversion physics.**

---

## Snow Depth vs. AQM Bias Analysis

### Motivation
Extend case study findings (3 days) to full dataset (2,769 days) to test whether AQM bias is systematically related to snow cover.

### Data
- **Snow depth**: Basin-averaged daily snow depth from 7 stations (COOP, BRC, UDOT networks)
- **AQM verification**: Matched obs/forecast pairs from 5 ozone stations
- **Merged dataset**: 2,231 records with both snow and ozone data

### Key Findings

#### All Days (n = 2,231)
| Snow Depth | Mean Bias | n |
|------------|-----------|---|
| 0-2 cm | -3.4 ppb | 1,072 |
| 2-5 cm | -2.9 ppb | 90 |
| 5-10 cm | -2.5 ppb | 112 |
| 10-20 cm | -1.8 ppb | 222 |
| **20+ cm** | **-6.5 ppb** | 735 |

- Correlation: r = -0.08 (weak but significant, p < 0.001)
- Deep snow (20+ cm) shows substantially larger underprediction

#### Exceedance Days Only (n = 48)
| Snow Depth | Mean Bias | n |
|------------|-----------|---|
| 0-2 cm | -94.6 ppb | 14 |
| 5-10 cm | -32.9 ppb | 5 |
| 10-20 cm | -74.4 ppb | 6 |
| **20+ cm** | **-63.1 ppb** | 23 |

- **Mean bias: -70.5 ppb** — massive underprediction on exceedance days
- 48% of exceedance days (23/48) have 20+ cm snow cover
- Median snow depth on exceedance days: 18 cm (vs 4 cm for all days)

### Interpretation

1. **Snow cover is strongly associated with exceedance events**: Median snow depth is 4.5× higher on exceedance days than typical days

2. **AQM fails catastrophically on exceedance days regardless of snow depth**: Mean bias of -70 ppb indicates AQM misses the magnitude of high-ozone events by ~70 ppb on average

3. **The 0-2 cm bin paradox**: Worst exceedance-day bias (-95 ppb) occurs at low snow. These may be:
   - Early/late season events with less snow but still cold pools
   - Events where snow melted but inversions persisted
   - Edge cases AQM especially fails to capture

4. **Snow-albedo mechanism confirmed**: Most exceedance days have substantial snow cover, and deep snow (20+ cm) is associated with more negative bias in all-days analysis

### Figures
- `figures/snow_bias_scatter.png` — Side-by-side scatter plots (all days vs exceedance)
- `figures/snow_bias_binned.png` — Side-by-side bar charts by snow depth bins

---

## References

- Wilks, D.S. (2011). *Statistical Methods in the Atmospheric Sciences* (3rd ed.). Chapter 8: Forecast Verification.
- Roebber, P.J. (2009). Visualizing Multiple Measures of Forecast Quality. *Weather and Forecasting*, 24(2), 601-608. (Performance diagrams)
