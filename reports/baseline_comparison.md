<!-- Generated: 2026-01-21T01:24:23.813392 -->

# Baseline Comparison Analysis

## Overall Model Comparison

| Model | POD | FAR | CSI | Bias | RMSE | n |
| --- | --- | --- | --- | --- | --- | --- |
| AQM | 31.6% | 29.9% | 27.9% | -4.37 | 14.40 | 2557 |
| Persistence | 61.7% | 38.3% | 44.6% | -0.01 | 16.41 | 2552 |
| Climatology | 0.0% | 0.0% | 0.0% | -0.01 | 16.85 | 2557 |

## POD by Event Phase

| Model | Onset POD | Continuation POD | n Onset | n Cont. |
| --- | --- | --- | --- | --- |
| AQM | 13.5% | 42.9% | 74 | 119 |
| Persistence | 0.0% | 100.0% | 74 | 119 |
| Climatology | 0.0% | 0.0% | 74 | 119 |

## Bootstrap Confidence Interval

- **AQM vs Persistence POD Difference:** -30.1%
- **95% CI:** [-37.8%, -22.3%]
- **P-value:** 1.000


## Interpretation

### Onset Detection

- **AQM onset POD:** 13.5%
- **Persistence onset POD:** 0.0%
- **Assessment:** AQM provides MARGINAL advance warning


### Overall Performance

- **AQM overall POD:** 31.6%
- **Persistence overall POD:** 61.7%
- **Assessment:** AQM adds NO VALUE over simple persistence


### Skill Scores (vs Persistence)

- **CSI skill:** -0.302
- **POD skill:** -0.784