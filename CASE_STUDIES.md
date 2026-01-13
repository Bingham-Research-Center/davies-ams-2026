# Case Study Analysis

Three validated case studies for the AMS poster, selected using strict multi-station criteria to ensure data quality.

## Summary

| Case | Date | Station | Obs | AQM | Bias | Validation |
|------|------|---------|-----|-----|------|------------|
| **Worst Miss** | 2023-02-04 | UB7ST | 112 ppb | 54 ppb | -58 ppb | All 5 stations exceeded |
| **False Alarm** | 2021-02-01 | UBCSP | 53 ppb | 87 ppb | +35 ppb | No station exceeded |
| **Best Hit** | 2023-02-08 | QV4 | 76 ppb | 77 ppb | +1 ppb | All 5 stations exceeded |

## Meteorological Context

| Date | Case | Snow | ΔT (°C) | Wind | RH | Obs | AQM |
|------|------|------|---------|------|-----|-----|-----|
| 2023-02-04 | Worst Miss | 12.5" | 19.3 | 1.3 m/s | 79% | 112 | 54 |
| 2021-02-01 | False Alarm | 6.6" | 13.4 | 1.1 m/s | 77% | 53 | 87 |
| 2023-02-08 | Best Hit | 12.5" | 20.4 | 0.9 m/s | 85% | 76 | 77 |

ΔT = diurnal temperature range (smaller = stronger inversion)

## GFS Snow Depth Comparison

| Date | Case | GFS Snow | Obs Snow | Error |
|------|------|----------|----------|-------|
| 2023-02-04 | Worst Miss | 4.7" | 12.5" | -63% |
| 2021-02-01 | False Alarm | 4.3" | 6.6" | -35% |
| 2023-02-08 | Best Hit | 3.4" | 12.5" | -73% |

GFS consistently underestimates snow depth in the Uinta Basin by 35-73%.

## AQM Error Evolution (Feb 2023 Event)

The worst miss and best hit both occurred during the same multi-day event:

| Date | Mean Obs | Mean AQM | Mean Bias | Phase |
|------|----------|----------|-----------|-------|
| Feb 3 | 85 ppb | 64 ppb | -20 ppb | Onset |
| Feb 4 | 102 ppb | 68 ppb | **-35 ppb** | Ramp-up |
| Feb 5 | 115 ppb | 78 ppb | -36 ppb | Peak |
| Feb 6 | 108 ppb | 72 ppb | -36 ppb | Peak |
| Feb 7 | 93 ppb | 76 ppb | -17 ppb | Decay |
| Feb 8 | 91 ppb | 80 ppb | **-11 ppb** | Decay |

**Key finding: AQM struggles at event onset, improves as event matures.**

## Case Study Details

### Worst Miss: February 4, 2023

- All 5 stations exceeded 70 ppb threshold (range: 88-112 ppb)
- Part of multi-day basin-wide event (Feb 3-8)
- Deep snow cover (12.5") with albedo enhancement
- AQM underpredicted by 58 ppb at UB7ST
- GFS underestimated snow by 63%

**Story**: Real basin-wide ozone event that AQM failed to capture at onset.

### False Alarm: February 1, 2021

- No station exceeded 70 ppb (max obs: 54 ppb)
- AQM predicted up to 87 ppb at UBCSP
- Only 6.6" snow (half of real event days)
- Smaller ΔT suggests stronger inversion signal

**Story**: AQM predicted the meteorological setup, but ozone didn't develop - possibly due to insufficient snow for albedo enhancement or missing precursors.

### Best Hit: February 8, 2023

- All 5 stations exceeded 70 ppb
- Same event as worst miss, but 4 days later
- AQM forecast within 1 ppb at QV4
- Model had "caught up" as event matured

**Story**: By event decay phase, AQM had adjusted and produced accurate forecasts.

## Data Quality Notes

Initial analysis found isolated spikes at UBHSP (140-168 ppb) that were rejected:
- Nearby stations showed 45-55 ppb on same days
- Likely instrument errors, not real ozone events

Selection criteria to avoid misrepresentation:
- **Worst miss/Best hit**: Require ALL reporting stations to exceed threshold
- **False alarm**: Require NO station to exceed threshold
