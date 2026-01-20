<!-- Generated: 2026-01-20T01:36:22.662053 -->

# Snow Depth vs AQM Bias Analysis

## All Days Analysis

### Dataset Size

- **Total records:** 2,224
- **Unique days:** 597

### Data Completeness Note

⚠️ **Important**: This subset (2,224 records) contains only **42 exceedance days** compared to **193 exceedances** in the full dataset (2,557 station-days). Only 22% of exceedance days have matching snow depth data.

This affects interpretation:
- The 42 exceedance days with snow data are **biased toward extreme events** (mean obs = 124 ppb vs 94 ppb for all exceedances)
- Mean bias for this subset is -76.7 ppb (vs -31.5 ppb for all 193 exceedance days)
- Snow-bias correlations should be interpreted with caution due to sample size limitations

### Snow Depth Statistics (cm)

- **Mean:** 24.39
- **Median:** 3.95
- **Std:** 37.94
- **Range:** 0.00 - 177.80


### Bias Statistics (ppb)

- **Mean:** -3.67
- **Median:** -2.23
- **Std:** 13.40
- **Range:** -124.75 - 34.82


### Regression Results

- **Correlation (r):** -0.061
- **Slope:** -0.0214
- **Intercept:** -3.15
- **P-value:** 0.0043


## Exceedance Days Analysis

### Dataset Size

- **Total records:** 42
- **Unique days:** 41


### Snow Depth Statistics (cm)

- **Mean:** 27.97
- **Median:** 16.94
- **Std:** 31.33
- **Range:** 0.00 - 90.17


### Bias Statistics (ppb)

- **Mean:** -76.65
- **Median:** -88.79
- **Std:** 35.83
- **Range:** -124.75 - 2.55


### Regression Results

- **Correlation (r):** 0.264
- **Slope:** 0.3023
- **Intercept:** -85.11
- **P-value:** 0.0907