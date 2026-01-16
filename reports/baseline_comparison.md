<!-- Generated: 2026-01-16T15:38:21.013942 -->

# Baseline Comparison Analysis

## Overall Model Comparison

| Model | POD | FAR | CSI | Bias | RMSE | n |
| --- | --- | --- | --- | --- | --- | --- |
| AQM | 30.1% | 28.7% | 26.8% | -5.01 | 14.76 | 2565 |
| Persistence | 64.6% | 35.4% | 47.7% | -0.02 | 16.00 | 2560 |
| Climatology | 0.0% | 0.0% | 0.0% | -0.02 | 17.09 | 2565 |

## POD by Event Phase

| Model | Onset POD | Continuation POD | n Onset | n Cont. |
| --- | --- | --- | --- | --- |
| AQM | 13.7% | 39.1% | 73 | 133 |
| Persistence | 0.0% | 100.0% | 73 | 133 |
| Climatology | 0.0% | 0.0% | 73 | 133 |

## Bootstrap Confidence Interval

- **AQM vs Persistence POD Difference:** -34.5%
- **95% CI:** [-42.2%, -26.7%]
- **P-value:** 1.000


## Interpretation

### Onset Detection

- **AQM onset POD:** 13.7%
- **Persistence onset POD:** 0.0%
- **Assessment:** AQM provides MARGINAL advance warning


### Overall Performance

- **AQM overall POD:** 30.1%
- **Persistence overall POD:** 64.6%
- **Assessment:** AQM adds NO VALUE over simple persistence


### Skill Scores (vs Persistence)

- **CSI skill:** -0.398
- **POD skill:** -0.973