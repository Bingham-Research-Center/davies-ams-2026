# Challenges with Wintertime Ozone and Modeling in Complex Terrain

**Authors**: Michael J. Davies, Utah State University, Vernal, UT; and J. R. Lawson
**Conference**: 24th Joint Conference on Applications of Air Pollution Meteorology (AMS)

---

## Abstract

Air-quality forecasting in Utah's Uinta Basin faces unique challenges due to complex terrain, persistent winter cold-air pools, and a rare dependence of ozone on snowpack. We compare two different modeling systems and their predictive skill: (1) NOAA's Air Quality Model (AQM) which is likely to miss shallow cold pools by nature of its coarse (13km) resolution, and (2) CLYFAR, our in-house ozone-concentration prediction system based on statistical (fuzzy-logic) techniques. Sparse and noisy snow-depth measurements complicated diagnosis of crucial conditions, with filtering and observation uncertainty persistently high. We show a case study where AQM missed a high-ozone event likely due to its small scale, in contrast to AQM's ability to capture large-scale wildfire pollutants. Regardless of NWP or AI approach, improving model fidelity in the Uinta Basin relies on improved data collection and appropriately designed prediction models, considering an unrealistic need for huge ensembles of fine resolution.

---

## Poster Structure (3 Columns)

### Column 1: Background / Introduction

**The Uinta Basin Challenge**
- Utah's Uinta Basin has a rare winter ozone problem (most U.S. ozone happens in summer)
- Three things come together to cause it:
  1. **Bowl-shaped terrain** traps pollutants in the basin
  2. **Cold air gets stuck** at the surface for days, preventing pollution from escaping
  3. **Snow on the ground** reflects sunlight and speeds up ozone-forming reactions
- This leads to unhealthy air quality days that exceed the federal 70 ppb limit

**How Winter Ozone Forms** (Davies et al. 2025)
1. Heavy snow covers the basin and a layer of cold air settles in
2. The cold air acts like a lid, trapping pollution from oil and gas operations
3. Sunlight hits the snow but isn't strong enough to melt it
4. Snow reflects sunlight back up, increasing the UV light in the trapped air
5. This extra UV drives chemical reactions that create ozone
6. Ozone builds up to unhealthy levels (above 70 ppb federal limit)

> "Snow coverage is paramount in initiating the cold pool and driving ozone generation."

**The Scale Problem**
- NOAA AQM uses a 13 km grid—each grid cell covers a large area
- The cold air pools that trap pollution are only about 100 meters deep
- The model can't "see" features this small
- AQM works well for large events like wildfires, but struggles with small-scale winter ozone

**Research Question**
> How well do operational and statistical modeling approaches predict wintertime ozone in the Uinta Basin, and what limits their skill?

### Column 2: Methods / Results

**Two Modeling Approaches**

| Model | Type | Resolution | Notes |
|-------|------|------------|-------|
| NOAA AQM | Operational (CMAQ/GFS) | 13 km | Coarse resolution |
| CLYFAR | Statistical (fuzzy-logic) | N/A | Designed for Uinta Basin |

**Observations**

| STID | Name | Network | O₃ | Met | Snow | Radiation | NOx |
|------|------|---------|:--:|:---:|:----:|:---------:|:---:|
| QRS | Roosevelt | UDAQ | ✓ | ✓ | | ✓ (2021+) | ✓ (2022+) |
| QV4 | Vernal | UDAQ | ✓ | ✓ | | ✓ (2021+) | ✓ (2022+) |
| UTASH | Asphalt Ridge | UDOT | | ✓ | ✓ (2023+) | | |
| UTMYT | Myton | UDOT | | ✓ | ✓ (2023+) | | |
| COOPDSNU1 | Duchesne | COOP | | | ✓ (2016+) | | |
| COOPDINU1 | Dinosaur NM | COOP | | | ✓ (2016+) | | |
| COCOUTUN20 | Vernal 3.1 NW | CoCoRaHS | | | ✓ (2022+) | | |
| UBCSP | Castle Peak | BRC | ✓ | ✓ | ✓ (2019+) | ✓ (full) | ✓ (2024+) |
| UBRVT | Roosevelt | BRC | | ✓ | ✓ (2024+) | ✓ (full) | ✓ (2024+) |
| UBHSP | Horsepool | BRC | ✓ | ✓ | ✓ (2016+) | ✓ (full) | ✓ (2024+) |
| UB7ST | Seven Sisters | BRC | ✓ | ✓ | ✓ (2024+) | | |

**Summary by variable:**
- **O₃**: QRS, QV4, UBCSP, UBHSP, UB7ST
- **Met**: QRS, QV4, UTASH, UTMYT, UBCSP, UBRVT, UBHSP, UB7ST
- **Snow (2016+)**: COOPDSNU1, COOPDINU1, UBHSP
- **Snow (all)**: Above + COCOUTUN20, UTASH, UTMYT, UBCSP, UBRVT, UB7ST
- **Full radiation budget**: UBCSP, UBRVT, UBHSP

**Data Quality Challenges**
- Basin distant from NEXRAD radars (KMTX Salt Lake, KGJX Grand Junction)
- Radar beam blocking by terrain creates "radar hole"
- RTMA precipitation estimates unreliable due to radar gaps
- COOP stations: once-daily, 2.54 cm (1 inch) precision
- Snow complications: sublimation, melting, refreezing, settling, drifting

**Results: Two Scenarios**

*High-Ozone Winter (2022-23):*
- 151 bad air days (25% of the winter)
- AQM predicted 40% of these events correctly
- But simply using yesterday's ozone did better (62% correct)

*Typical Low-Ozone Winters (5 others):*
- Only 42 bad air days across 5 winters (2% of days)
- AQM predicted only 2.4% of these events
- The model essentially missed almost everything

**CLYFAR Comparison (Winter 2022-23, n=457 station-days):**

Comparing forecasts at the same 24-hour lead time:
- **CLYFAR p90**: Detected 75% of events, but 58% of warnings were false alarms
- **AQM (Day 1)**: Detected 33% of events, with 31% false alarms
- **Persistence** (yesterday's ozone): Detected 76% of events, 22% false alarms

CLYFAR catches more events but triggers more false alarms. Each approach has trade-offs depending on whether missing events or false warnings is more costly.

### Column 3: Conclusions / Future Work

**Key Takeaways**
- AQM struggles to predict winter ozone in the Uinta Basin
- Simply assuming "tomorrow = today" catches more events than AQM (76% vs 33%)
- In typical winters with few events, AQM detected only 2.4% of exceedances
- Weather models underestimate snow depth 70% of the time (off by 20 cm for deep snow)
- Eastern basin stations are harder to predict than western stations
- AQM underpredicts more as ozone gets higher (-4 ppb overall, -32 ppb on bad days)

**Why AQM Struggles Here**
- The model grid (13 km) is too coarse to see the shallow cold air pools (100 m deep)
- The model doesn't account for how snow reflects sunlight and speeds up ozone formation
- The weather model feeding AQM consistently underestimates snow depth

**Future Work**
- High-resolution nested domain (1-3 km) over Uinta Basin
- Incorporate snow-albedo enhancement into photolysis rates
- Data assimilation of basin snow depth observations
- Hybrid statistical-dynamical approach combining strengths

---

## Analysis Status

✅ **COMPLETE** - All analysis, documentation, and figures ready for AMS 2026

**Key Deliverables:**
- 2,557 station-days analyzed across 6 winter seasons
- 22 figures for publication
- 11 detailed reports
- Analysis grouped by high-ozone vs typical winters
- Side-by-side comparison of AQM and CLYFAR forecasts

**Contact:** Michael J. Davies (michael.davies@usu.edu)

---

## Code Tools

### NOAA AQM Data Access (Herbie Template)

Access NOAA Air Quality Model forecasts using Herbie. See [src/herbie_aqm/README.md](src/herbie_aqm/README.md) for full documentation.

**Installation**
```bash
cp src/herbie_aqm/__init__.py ~/.config/herbie/custom_template.py
```

**Usage**
```python
from herbie import Herbie

# Get max 8-hour ozone forecast
H = Herbie("2024-01-15 12:00", model="aqm", product="max_8hr_o3", fxx=0)
ds = H.xarray()
```

**Available Products**: `max_8hr_o3`, `ave_1hr_o3`, `ave_8hr_o3`, `max_1hr_o3`, `ave_24hr_pm25`, `ave_1hr_pm25`

### Synoptic Observation Data

Fetch observation data from Synoptic API.

**Setup**
```bash
pip install SynopticPy
export SYNOPTIC_TOKEN="your_token_here"
```

**Usage**: Edit `fetch_synoptic.py` with station IDs, variables, and date range, then run:
```bash
python fetch_synoptic.py
```

---

## Uinta Basin Station Reference

### Abbreviations & Glossary

| Abbreviation | Full Name |
|--------------|-----------|
| API | Application Programming Interface (here: Synoptic Data API) |
| AQM | Air Quality Model (NOAA's operational air quality forecast system) |
| BRC | Bingham Research Center (Utah State University, Vernal) |
| CO | Carbon Monoxide |
| CoCoRaHS | Community Collaborative Rain, Hail and Snow Network |
| Elev | Elevation |
| EPA | Environmental Protection Agency |
| Est. | Estimated |
| ft | Feet |
| hr | Hour |
| Lat | Latitude |
| Lon | Longitude |
| LW | Longwave (infrared radiation) |
| MDA8 | Maximum Daily 8-hour Average (ozone metric used for NAAQS compliance; calculated by taking rolling 8-hour averages and selecting the daily maximum) |
| MP | Mile Post (highway marker) |
| NAAQS | National Ambient Air Quality Standards (EPA threshold: 70 ppb for ozone) |
| NM | National Monument |
| NO | Nitric Oxide |
| NO₂ | Nitrogen Dioxide |
| NOAA | National Oceanic and Atmospheric Administration |
| NOx | Nitrogen Oxides (NO + NO₂) |
| NOy | Total Reactive Nitrogen (NOx + HNO₃ + PAN + other oxidized N species) |
| NRCS | Natural Resources Conservation Service (operates SNOTEL) |
| NWS COOP | National Weather Service Cooperative Observer Program |
| O₃ | Ozone |
| PBL | Planetary Boundary Layer (depth of atmospheric mixing) |
| PM2.5 | Particulate Matter ≤2.5 micrometers in diameter |
| ppb | Parts per billion |
| RH | Relative Humidity |
| SLC | Salt Lake City |
| SNOTEL | Snow Telemetry (NRCS snow monitoring network) |
| STID | Station Identifier (Synoptic Data API) |
| SW | Shortwave (solar radiation) |
| T | Temperature |
| UB-AIR | Uintah Basin Air Quality Network (operated by USU BRC) |
| UDAQ | Utah Division of Air Quality |
| UDOT | Utah Department of Transportation |
| US-40 | U.S. Route 40 (highway through Uinta Basin) |
| USU | Utah State University |
| UV | Ultraviolet radiation |

---

### Purpose

This document supports evaluation of NOAA's Air Quality Model (AQM) performance for wintertime ozone in Utah's Uinta Basin.

---

### What We're Comparing & Why

#### 1. Ozone: AQM Forecast vs Observations

| Compare | Why |
|---------|-----|
| AQM max 8-hr O₃ vs observed MDA8 | Direct forecast skill evaluation |
| Exceedance detection (>70 ppb) | Operational relevance — did it warn the public? |
| Diurnal cycle (hourly obs vs daily AQM) | AQM outputs daily values; real ozone swings significantly in cold pools |

#### 2. Snow Depth

| Compare | Why |
|---------|-----|
| Snow presence during hit vs miss events | Snow-covered ground enhances UV → accelerates photochemistry |
| Basin-wide snow coverage (west to east) | Check for snow shadow pattern; AQM doesn't use snow for photolysis |

#### 3. Temperature

| Compare | Why |
|---------|-----|
| Surface T during events | Cold temps = stable stratification = trapped pollutants |
| Diurnal T range | Small range = persistent inversion; large range = mixing |

#### 4. Wind Speed

| Compare | Why |
|---------|-----|
| Wind speed during hit vs miss events | Sustained low winds = stagnation = accumulation |
| Wind direction | Persistent drainage flows or calm = trapped air mass |

#### 5. Solar Radiation

| Compare | Why |
|---------|-----|
| Incoming solar during events | Photochemistry requires sunlight; clear skies + snow = amplified UV |
| Cloud cover proxy (if solar is low) | Cloudy days suppress ozone production |

#### 6. Spatial Comparison: Basin vs Wasatch Front

| Compare | Why |
|---------|-----|
| Same-day O₃: Basin sites vs SLC/Wasatch | Shows whether the problem is local vs regional |
| AQM skill in Basin vs Wasatch | Check if AQM performs differently by region |

---

### Ozone & Air Quality Sites

#### UDAQ Regulatory Sites

| STID | Name | Network | Lat | Lon | Elev (ft) |
|------|------|---------|-----|-----|-----------|
| QRS | Roosevelt | UDAQ | 40.2943 | -110.009 | 5210 |
| QV4 | Vernal | UDAQ | 40.4647 | -109.5608 | 5466 |

#### USU Bingham Research Center Sites (UB-AIR Network)

| STID | Name | Network | Lat | Lon | Elev (ft) |
|------|------|---------|-----|-----|-----------|
| UBCSP | Castle Peak | UB-AIR | 40.051 | -110.020 | 5266 |
| UBRVT | Roosevelt | UB-AIR | 40.2943 | -110.009 | 5210 |
| UBHSP | Horsepool | UB-AIR | 40.144 | -109.467 | 5148 |
| UB7ST | Seven Sisters | UB-AIR | 39.981 | -109.345 | 5308 |

#### Available Variables — UDAQ Sites

| STID | Variable | API Name | Start Date | End Date |
|------|----------|----------|------------|----------|
| QRS | Ozone | `ozone_concentration` | Jun 17, 2015 | present |
| QRS | PM2.5 | `PM_25_concentration` | Jul 5, 2015 | present |
| QRS | NOx | `NOx_concentration` | Jan 25, 2022 | present |
| QRS | NO | `NO_concentration` | Jan 25, 2022 | present |
| QV4 | Ozone | `ozone_concentration` | Jul 18, 2015 | present |
| QV4 | PM2.5 | `PM_25_concentration` | Jul 18, 2015 | present |
| QV4 | NOx | `NOx_concentration` | Jan 25, 2022 | present |
| QV4 | NO | `NO_concentration` | Jan 25, 2022 | present |

#### Available Variables — BRC Sites

| STID | Variable | API Name | Start Date | End Date |
|------|----------|----------|------------|----------|
| UBCSP | Ozone | `ozone_concentration` | Jan 29, 2016 | Nov 5, 2025 |
| UBCSP | NOx | `NOx_concentration` | Dec 19, 2024 | Nov 5, 2025 |
| UBCSP | NO | `NO_concentration` | Dec 19, 2024 | Nov 5, 2025 |
| UBCSP | NO₂ | `NO2_concentration` | Dec 19, 2024 | Nov 5, 2025 |
| UBHSP | Ozone | `ozone_concentration` | Jan 29, 2016 | Jul 2, 2025 |
| UBHSP | PM2.5 | `PM_25_concentration` | Dec 20, 2024 | Jul 2, 2025 |
| UBHSP | NOx | `NOx_concentration` | Dec 19, 2024 | Aug 26, 2025 |
| UBHSP | NO | `NO_concentration` | Dec 19, 2024 | Sep 3, 2025 |
| UBHSP | CO | `co_concentration` | Dec 19, 2024 | Sep 3, 2025 |
| UBHSP | Total Reactive N | `NOy_concentration` | Dec 19, 2024 | Aug 26, 2025 |
| UBRVT | NOx | `NOx_concentration` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | NO | `NO_concentration` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | NO₂ | `NO2_concentration` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Total Reactive N | `NOy_concentration` | Dec 19, 2024 | Aug 11, 2025 |
| UB7ST | Ozone | `ozone_concentration` | Jan 29, 2016 | Dec 23, 2025 |

---

### Meteorology Sites

#### UDAQ Sites

| STID | Name | Network | Lat | Lon | Elev (ft) |
|------|------|---------|-----|-----|-----------|
| QRS | Roosevelt | UDAQ | 40.2943 | -110.009 | 5210 |
| QV4 | Vernal | UDAQ | 40.4647 | -109.5608 | 5466 |

#### UDOT Road Weather Sites

| STID | Name | Network | Lat | Lon | Elev (ft) |
|------|------|---------|-----|-----|-----------|
| UTASH | Asphalt Ridge (US-40 MP 140) | UDOT | 40.4164 | -109.5822 | 5710 |
| UTMYT | Myton (US-40 MP 105) | UDOT | 40.1994 | -110.0679 | 5087 |

#### USU Bingham Research Center Sites

| STID | Name | Network | Lat | Lon | Elev (ft) |
|------|------|---------|-----|-----|-----------|
| UBCSP | Castle Peak | UB-AIR | 40.051 | -110.020 | 5266 |
| UBRVT | Roosevelt | UB-AIR | 40.2943 | -110.009 | 5210 |
| UBHSP | Horsepool | UB-AIR | 40.144 | -109.467 | 5148 |
| UB7ST | Seven Sisters | UB-AIR | 39.981 | -109.345 | 5308 |

#### Available Variables — UDAQ Sites

| STID | Variable | API Name | Start Date | End Date |
|------|----------|----------|------------|----------|
| QRS | Temperature | `air_temp` | Jan 31, 2012 | present |
| QRS | Relative Humidity | `relative_humidity` | Jan 31, 2012 | present |
| QRS | Wind Speed | `wind_speed` | Jan 31, 2012 | present |
| QRS | Wind Direction | `wind_direction` | Jan 31, 2012 | present |
| QRS | Solar Radiation | `solar_radiation` | May 11, 2021 | present |
| QRS | Pressure | `pressure` | Dec 4, 2015 | May 11, 2021 |
| QV4 | Temperature | `air_temp` | Oct 31, 2011 | present |
| QV4 | Relative Humidity | `relative_humidity` | Oct 31, 2011 | present |
| QV4 | Wind Speed | `wind_speed` | Oct 31, 2011 | present |
| QV4 | Wind Direction | `wind_direction` | Oct 31, 2011 | present |
| QV4 | Solar Radiation | `solar_radiation` | May 11, 2021 | present |
| QV4 | Pressure | `pressure` | Dec 4, 2015 | May 11, 2021 |

#### Available Variables — UDOT Sites

| STID | Variable | API Name | Start Date | End Date |
|------|----------|----------|------------|----------|
| UTASH | Temperature | `air_temp` | Jun 3, 2020 | present |
| UTASH | Relative Humidity | `relative_humidity` | Jun 3, 2020 | present |
| UTASH | Wind Speed | `wind_speed` | Jun 3, 2020 | present |
| UTASH | Wind Direction | `wind_direction` | Jun 3, 2020 | present |
| UTASH | Wind Gust | `wind_gust` | Jun 3, 2020 | present |
| UTASH | Visibility | `visibility` | Jun 3, 2020 | present |
| UTASH | Soil Temperature | `soil_temp` | Jun 3, 2020 | present |
| UTASH | Road Temperature | `road_temp` | Jun 15, 2020 | present |
| UTMYT | Temperature | `air_temp` | Jun 3, 2020 | present |
| UTMYT | Relative Humidity | `relative_humidity` | Jun 3, 2020 | present |
| UTMYT | Wind Speed | `wind_speed` | Jun 3, 2020 | present |
| UTMYT | Wind Direction | `wind_direction` | Jun 3, 2020 | present |
| UTMYT | Wind Gust | `wind_gust` | Jun 3, 2020 | present |
| UTMYT | Visibility | `visibility` | Jun 3, 2020 | present |
| UTMYT | Soil Temperature | `soil_temp` | Jun 3, 2020 | present |
| UTMYT | Road Temperature | `road_temp` | Jun 3, 2020 | present |

#### Available Variables — BRC Sites

| STID | Variable | API Name | Start Date | End Date |
|------|----------|----------|------------|----------|
| UBCSP | Temperature | `air_temp` | Jan 6, 2017 | Nov 5, 2025 |
| UBCSP | Relative Humidity | `relative_humidity` | Jan 6, 2017 | Nov 5, 2025 |
| UBCSP | Wind Speed | `wind_speed` | Jan 29, 2016 | Nov 5, 2025 |
| UBCSP | Wind Direction | `wind_direction` | Jan 29, 2016 | Nov 5, 2025 |
| UBCSP | Pressure | `pressure` | Jan 6, 2017 | Nov 5, 2025 |
| UBCSP | Solar Radiation (incoming SW) | `solar_radiation` | Jan 29, 2016 | Nov 5, 2025 |
| UBCSP | Outgoing SW Radiation | `outgoing_shortwave_radiation` | Aug 18, 2020 | Nov 5, 2025 |
| UBCSP | Incoming LW Radiation | `incoming_longwave_radiation` | Aug 18, 2020 | Nov 5, 2025 |
| UBCSP | Outgoing LW Radiation | `outgoing_longwave_radiation` | Aug 18, 2020 | Nov 5, 2025 |
| UBRVT | Temperature | `air_temp` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Relative Humidity | `relative_humidity` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Solar Radiation (incoming SW) | `solar_radiation` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Outgoing SW Radiation | `outgoing_shortwave_radiation` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Incoming LW Radiation | `incoming_longwave_radiation` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Outgoing LW Radiation | `outgoing_longwave_radiation` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Net Radiation | `net_radiation` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Net SW Radiation | `net_shortwave_radiation` | Dec 19, 2024 | Aug 11, 2025 |
| UBRVT | Net LW Radiation | `net_longwave_radiation` | Dec 19, 2024 | Aug 11, 2025 |
| UBHSP | Temperature | `air_temp` | Jan 29, 2016 | Sep 3, 2025 |
| UBHSP | Relative Humidity | `relative_humidity` | Jan 29, 2016 | Sep 3, 2025 |
| UBHSP | Wind Speed | `wind_speed` | Jan 29, 2016 | Sep 3, 2025 |
| UBHSP | Wind Direction | `wind_direction` | Jan 29, 2016 | Sep 3, 2025 |
| UBHSP | Pressure | `pressure` | Jan 29, 2016 | Sep 3, 2025 |
| UBHSP | Solar Radiation (incoming SW) | `solar_radiation` | Apr 24, 2017 | Sep 3, 2025 |
| UBHSP | Outgoing SW Radiation | `outgoing_shortwave_radiation` | Apr 24, 2017 | Sep 3, 2025 |
| UBHSP | Incoming LW Radiation | `incoming_longwave_radiation` | Apr 24, 2017 | Sep 3, 2025 |
| UBHSP | Outgoing LW Radiation | `outgoing_longwave_radiation` | Apr 24, 2017 | Sep 3, 2025 |
| UB7ST | Temperature | `air_temp` | Jan 29, 2016 | Dec 23, 2025 |
| UB7ST | Relative Humidity | `relative_humidity` | Jan 29, 2016 | Dec 23, 2025 |
| UB7ST | Wind Speed | `wind_speed` | Jan 29, 2016 | Dec 23, 2025 |
| UB7ST | Wind Direction | `wind_direction` | Jan 29, 2016 | Dec 23, 2025 |
| UB7ST | Pressure | `pressure` | Jan 29, 2016 | Dec 23, 2025 |

---

### Snow Depth Sites

#### NWS COOP Sites (Longest Records)

| STID | Name | Network | Lat | Lon | Elev (ft) | Location |
|------|------|---------|-----|-----|-----------|----------|
| COOPDSNU1 | Duchesne | NWS COOP | 40.1703 | -110.3978 | 5551 | Western basin |
| COOPDINU1 | Dinosaur NM | NWS COOP | 40.4384 | -109.307 | 4802 | Eastern edge |

#### USU Bingham Research Center Sites

| STID | Name | Network | Lat | Lon | Elev (ft) | Location |
|------|------|---------|-----|-----|-----------|----------|
| UBHSP | Horsepool | UB-AIR | 40.144 | -109.467 | 5148 | Central-east basin |
| UBCSP | Castle Peak | UB-AIR | 40.051 | -110.020 | 5266 | Southern basin |
| UBRVT | Roosevelt | UB-AIR | 40.2943 | -110.009 | 5210 | Central basin |
| UB7ST | Seven Sisters | UB-AIR | 39.981 | -109.345 | 5308 | Southeast basin |

#### Other Networks

| STID | Name | Network | Lat | Lon | Elev (ft) | Location |
|------|------|---------|-----|-----|-----------|----------|
| COCOUTUN20 | Vernal 3.1 NW | CoCoRaHS | 40.4776 | -109.5833 | 5591 | Eastern basin |
| UTASH | Asphalt Ridge | UDOT | 40.4164 | -109.5822 | 5710 | Near Vernal |
| UTMYT | Myton | UDOT | 40.1994 | -110.0679 | 5087 | Central basin |

#### Available Variables

| STID | Variable | API Name | Start Date | End Date |
|------|----------|----------|------------|----------|
| COOPDSNU1 | Snow Depth | `snow_depth` | Jun 17, 2016 | present |
| COOPDSNU1 | 24hr Snowfall | `snow_accum_24_hour` | Jun 17, 2016 | present |
| COOPDSNU1 | 24hr High Temp | `air_temp_high_24_hour` | Jun 17, 2016 | present |
| COOPDSNU1 | 24hr Low Temp | `air_temp_low_24_hour` | Jun 17, 2016 | present |
| COOPDSNU1 | 24hr Precip | `precip_accum_24_hour` | Jun 17, 2016 | present |
| COOPDINU1 | Snow Depth | `snow_depth` | Jun 14, 2016 | present |
| COOPDINU1 | 24hr Snowfall | `snow_accum_24_hour` | Jun 14, 2016 | present |
| COOPDINU1 | 24hr High Temp | `air_temp_high_24_hour` | Jun 11, 2016 | present |
| COOPDINU1 | 24hr Low Temp | `air_temp_low_24_hour` | Jun 11, 2016 | present |
| COOPDINU1 | 24hr Precip | `precip_accum_24_hour` | Jun 11, 2016 | present |
| COCOUTUN20 | Snow Depth | `snow_depth` | Dec 28, 2022 | present |
| COCOUTUN20 | Snow Interval | `snow_interval` | Dec 23, 2022 | present |
| COCOUTUN20 | Precip Interval | `precip_accum` | Dec 23, 2022 | present |
| UTASH | Snow Depth | `snow_depth` | Aug 14, 2023 | present |
| UTASH | Est. Snowfall Rate | `snow_rate` | Sep 8, 2020 | present |
| UTMYT | Snow Depth | `snow_depth` | Aug 14, 2023 | present |
| UTMYT | Est. Snowfall Rate | `snow_rate` | Sep 8, 2020 | present |
| UBHSP | Snow Depth | `snow_depth` | Jan 29, 2016 | Sep 3, 2025 |
| UBCSP | Snow Depth | `snow_depth` | Nov 20, 2019 | Nov 5, 2025 |
| UBRVT | Snow Depth | `snow_depth` | Dec 19, 2024 | Aug 11, 2025 |
| UB7ST | Snow Depth | `snow_depth` | Dec 19, 2024 | Dec 23, 2025 |

---

### Case Study Data Availability

#### Winter 2021 (Jan–Feb 2021)

| Category | Available STIDs |
|----------|-----------------|
| Ozone | QRS, QV4, UBCSP, UBHSP, UB7ST |
| Meteorology | QRS, QV4, UBCSP, UBHSP, UB7ST |
| Snow Depth | COOPDSNU1, COOPDINU1, UBHSP |

#### Winter 2023 (Jan–Feb 2023)

| Category | Available STIDs |
|----------|-----------------|
| Ozone | QRS, QV4, UBCSP, UBHSP, UB7ST |
| Meteorology | QRS, QV4, UTASH, UTMYT, UBCSP, UBHSP, UB7ST |
| Snow Depth | COOPDSNU1, COOPDINU1, COCOUTUN20, UBHSP, UBCSP |

#### Winter 2025 (Jan–Feb 2025)

| Category | Available STIDs |
|----------|-----------------|
| Ozone | QRS, QV4, UBCSP, UBHSP, UB7ST |
| Meteorology | QRS, QV4, UTASH, UTMYT, UBCSP, UBRVT, UBHSP, UB7ST |
| Snow Depth | COOPDSNU1, COOPDINU1, COCOUTUN20, UTASH, UTMYT, UBHSP, UBCSP, UBRVT, UB7ST |
| Radiation (full budget) | UBCSP, UBRVT, UBHSP |

---

### Quick Reference: Common Variable Groups

```python
# Synoptic API variable strings

# Ozone & AQ
AQ_VARS = "ozone_concentration,PM_25_concentration,NOx_concentration,NO_concentration"

# Basic meteorology
MET_VARS = "air_temp,relative_humidity,wind_speed,wind_direction,solar_radiation"

# Full radiation budget (BRC sites only)
RAD_VARS = "solar_radiation,outgoing_shortwave_radiation,incoming_longwave_radiation,outgoing_longwave_radiation"

# Snow
SNOW_VARS = "snow_depth,snow_accum_24_hour"

# Station groups by network
UDAQ_STIDS = "QRS,QV4"
UDOT_STIDS = "UTASH,UTMYT"
BRC_STIDS = "UBCSP,UBRVT,UBHSP,UB7ST"
COOP_STIDS = "COOPDSNU1,COOPDINU1"

# Station groups by variable
OZONE_STIDS = "QRS,QV4,UBCSP,UBHSP,UB7ST"
MET_STIDS = "QRS,QV4,UTASH,UTMYT,UBCSP,UBRVT,UBHSP,UB7ST"
SNOW_STIDS = "COOPDSNU1,COOPDINU1,COCOUTUN20,UTASH,UTMYT,UBHSP,UBCSP,UBRVT,UB7ST"
SNOW_STIDS_LONGTERM = "COOPDSNU1,COOPDINU1,UBHSP"  # 2016+
RAD_STIDS = "UBCSP,UBRVT,UBHSP"  # Full radiation budget
```

---

### Notes

- UDAQ sites (QRS, QV4) are the state's regulatory ozone monitors
- BRC/UB-AIR sites (UBCSP, UBRVT, UBHSP, UB7ST) are USU research stations with enhanced instrumentation
- UBHSP (Horsepool) has the longest continuous snow depth record in the basin (2016+)
- BRC sites have full radiation budget (incoming/outgoing SW and LW) for albedo and energy balance analysis
- UDOT sites (UTASH, UTMYT) have snow depth only from Aug 2023+
- NWS COOP sites have long snow records (2016+) but limited variables
- Solar radiation only available from May 2021+ at UDAQ sites
- NOx/NO only available from Jan 2022+ at UDAQ sites, Dec 2024+ at BRC sites

---

## References

- Davies, M.J.; Lawson, J.R.; O'Neil, T.; Lyman, S.N.; Zager, K.; Coxson, T.D. "Uinta Basin Snow Shadow: Impact of Snow-Depth Variation on Winter Ozone Formation." *Air* 2025, 3(3), 22. [DOI: 10.3390/air3030022](https://doi.org/10.3390/air3030022)
- Blaylock, B.K. (2024). Herbie: Retrieve Numerical Weather Prediction Model Data [Computer software]. [DOI: 10.5281/zenodo.4567540](https://doi.org/10.5281/zenodo.4567540)
- Blaylock, B.K. (2024). SynopticPy: Synoptic API for Python [Computer software]. [GitHub](https://github.com/blaylockbk/SynopticPy)
- [NOAA NAQFC on AWS](https://registry.opendata.aws/noaa-nws-naqfc-pds/)
