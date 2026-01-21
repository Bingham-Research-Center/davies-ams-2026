# CLYFAR Methodology: Complete Technical Description

**Date**: January 20, 2026  
**System**: CLYFAR (Welsh: "clever")  
**Approach**: Fuzzy inference with possibility theory for Uinta Basin winter ozone forecasting  
**Version**: Current operational system

---

## Core Philosophy: Possibility Theory + Fuzzy Logic

CLYFAR uses **Dubois-Prade possibility theory** (not probability!) to handle uncertainty in ozone forecasting. Instead of "70% chance," it says "ozone can be elevated with possibility 0.8" - representing what's physically plausible given atmospheric conditions.

---

## 1. Inner Core: Fuzzy Inference System (FIS)

### A. Universes of Discourse (domains)

| Variable | Range | Resolution |
|----------|-------|------------|
| Snow | 0-250 mm | 2 mm steps |
| MSLP | 950-1070 hPa | 0.5 hPa steps |
| Wind | 0-15 m/s | 0.25 m/s steps |
| Solar | 0-800 W/m² | 5 W/m² steps |
| **Ozone** | **20-140 ppb** | **0.5 ppb steps** ← OUTPUT |

### B. Membership Functions (fuzzy sets)

Each variable has categories defined by trapezoidal/sigmoid shapes:

**INPUTS:**
- **Snow**: negligible (↘ 60-90mm) | sufficient (↗ 60-90mm)
- **Wind**: calm (↘ 2-4 m/s) | breezy (↗ 2-4 m/s)
- **MSLP**: low (↘ 1010-1015) | moderate (▁ 1015-1030) | high (↗ 1025-1035)
- **Solar**: low (↘ 200-300) | moderate (▁ 300-700) | high (↗ 500-700)

**OUTPUT:**
- **Ozone**: background (20-50ppb) | moderate (40-70) | elevated (50-90) | extreme (60-125)

### C. Six Fuzzy Rules (the brain)

1. `(no_snow OR low_pressure OR windy) → background`
2. `(snow + high_pressure + calm + high_solar) → extreme`
3. `(snow + high_pressure + calm + mod_solar) → elevated`
4. `(snow + high_pressure + calm + low_solar) → moderate`
5. `(snow + mod_pressure + calm + high_solar) → elevated`
6. `(snow + mod_pressure + calm + mod_solar) → moderate`

### D. Inference Engine (every 3 hours)

For each timestep:

1. **Fuzzify**: Inputs → activation levels (0-1) for each category
2. **Fire rules**: AND=min, OR=max → compute possibility for each ozone category
3. **Clip output MFs**: Each ozone category's trapezoid gets α-cut at its activation
4. **Aggregate**: MAX across all clipped shapes → final possibility distribution
5. **Defuzzify**: Extract 10th/50th/90th percentiles from aggregated curve

**Key**: The output is a **subnormal distribution** (max < 1 means ignorance/uncertainty).

---

## 2. Middle Layer: NWP Preprocessing

### Parallel Download Architecture

```
GEFS ensemble (31 members: c00 control + p01-p30 perturbations)
  ↓
ParallelEnsembleProcessor (spawn multiprocessing pool)
  ↓
5 variables × 31 members = 155 tasks → N workers (ncpus)
```

### Variable-Specific Processing

**WIND** (`do_nwpval_wind`):
- Downloads UGRD/VGRD at 0.25°/0.5° resolution
- Computes speed = √(u² + v²) using Herbie's `.with_wind("speed")`
- Masks to low-elevation basin pixels (<1850m elevation threshold)
- Returns **90th percentile** over masked grid (represents basin-wide max exposure)

**SNOW** (`do_nwpval_snow`):
- Snow depth (sde) from both resolutions
- Elevation mask + weighted average smoothing (2×center + neighbors)/3
- Returns **90th percentile** (captures persistent snow cover)

**MSLP** (`do_nwpval_mslp`):
- Mean sea level pressure at Ouray point (40.0891°N, 109.6774°W)
- Nearest neighbor interpolation from 0.25°/0.5° grids
- Returns **raw value** (synoptic-scale representative)

**SOLAR** (`do_nwpval_solar`):
- Downward shortwave radiation (dswrf) - 3-hour temporal resolution
- Basin-wide mask → **median** over terrain (robust to cloud variations)

**TEMP** (visualization only):
- 2m temperature (t2m), same processing as wind/snow

### Time Series Construction

```
0-240h: 0.25° resolution (every 3h)
240-384h: 0.5° resolution (every 6h)
  ↓
Concatenate → single time series per member per variable
  ↓
Save as parquet: {YYYYMMDD_HHMMZ}_{variable}_{member}_df.parquet
```

---

## 3. Outer Layer: Ensemble Inference

### Per-Member CLYFAR Execution

```python
for each of 31 GEFS members:
    Load 5 variable parquets
    for each 3-hour timestep (skip t=0 solar):
        Lookup snow/mslp/wind/solar values
        FIS.compute_ozone(inputs) → percentiles + possibilities
        Store in clyfar_df[member]
```

### Output Tables

- `clyfar{000-030}_df.parquet`: 3-hourly ozone (10/50/90pc + 4 category possibilities + inputs)
- `clyfar{000-030}_dailymax.parquet`: Daily MDA8 aggregation (local timezone max)

### UOD Guardrails

- NaN inputs → skip inference, log warning
- Out-of-domain values → clip to UOD bounds + log warning
- E.g., MSLP=955 hPa → clipped to 950 hPa (universe minimum)

---

## 4. Post-Processing & Export

### Visualization

- **Meteograms**: GEFS 5-variable ensemble spreads
- **Heatmaps**: Ozone category possibility evolution (3-hourly + daily-max)
- **Percentile plots**: Optimist (10pc) vs Pessimist (90pc) scenarios

### BasinWx Export (`export/to_basinwx.py`)

**95 JSON files per run:**
- 31 percentiles (10/50/90pc scenarios)
- 31 possibilities (category heatmaps)
- 1 exceedance probability (ensemble consensus)
- 32 weather (31 members + 1 percentile summary)

**PNG uploads:**
- 31 ozone heatmaps
- 5 GEFS meteograms
- LLM outlook PDF (when generated)

---

## 5. AI Outlook Generation (Optional)

### LLM-GENERATE.sh Workflow

```
CLYFAR outputs → templates/llm/prompt_body.md
  ↓
Inject: current forecasts, weather context, verification stats
  ↓
Claude API (system: "You are Ffion, an air quality forecaster")
  ↓
LLM-OUTLOOK-{init}.md → Pandoc → .pdf → BasinWx upload
```

---

## Key Innovations

1. **Subnormal Possibility Distributions**: Acknowledges ignorance (max < 1)
2. **Ensemble Diversity Preservation**: 31 scenarios, not just mean/variance
3. **Geography-Aware Processing**: Elevation masks + spatial aggregation
4. **Operational Resilience**: Retry logic for 404s (data latency), timeout handling
5. **Transparency**: Logs all UOD clips, NaN counts, diagnostic percentiles

---

## Data Flow Summary

```
NOMADS AWS (GEFS GRIB2)
  ↓ Herbie parallel download
0.25°/0.5° gridded forecasts
  ↓ Spatial aggregation (per variable strategy)
Representative basin time series
  ↓ FIS inference (31× parallel)
Ozone possibility distributions
  ↓ Defuzzification + aggregation
10/50/90pc scenarios + category heatmaps
  ↓ JSON/PNG export
BasinWx.com visualization + LLM outlook
```

**Runtime**: ~8-15 min for 31 members on 16 CPUs (CHPC notchpeak-shared-short)

---

## Comparison to Traditional Ensemble Forecasting

| Aspect | Traditional NWP Ensemble | CLYFAR |
|--------|-------------------------|--------|
| **Uncertainty representation** | Probability (frequentist) | Possibility (epistemic) |
| **Member interpretation** | Equiprobable scenarios | Analog year plausibility |
| **Aggregation** | Mean/variance/percentiles | Fuzzy max-aggregation |
| **Output** | Deterministic value ± spread | Possibility distribution |
| **Physical constraints** | Model physics | Fuzzy rules (expert knowledge) |
| **Handles ignorance** | No (assumes ergodicity) | Yes (subnormal distributions) |

---

## Why 31 Members?

GEFS operational ensemble structure:
- **1 control run** (c00): Best-estimate initial conditions
- **30 perturbed runs** (p01-p30): Initial condition + model physics perturbations

Total = **31 members** representing plausible atmospheric states

CLYFAR treats each as an **analog year scenario**, not equiprobable outcomes. The ensemble spread represents **epistemic uncertainty** (what we don't know about initial conditions) rather than **aleatory uncertainty** (intrinsic randomness).

---

## References

- Dubois, D., & Prade, H. (1988). *Possibility Theory*. Springer.
- Zadeh, L. A. (1978). "Fuzzy sets as a basis for a theory of possibility." *Fuzzy Sets and Systems*, 1(1), 3-28.
- NOAA GEFS: https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast

---

**For AMS Poster**: Emphasize that CLYFAR p90's 74.8% POD (vs AQM's 33.3%) comes from:
1. Physics-based fuzzy rules capturing snow-albedo-inversion mechanism
2. Ensemble preserving diverse scenarios (not averaging them away)
3. 90th percentile threshold capturing high-end risk scenarios

This is fundamentally different from AQM's deterministic physics-based approach.
