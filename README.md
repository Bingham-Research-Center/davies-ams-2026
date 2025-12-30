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
- Utah's Uinta Basin = rare **winter ozone** problem (most U.S. ozone is summer)
- Three factors create the "perfect storm":
  1. **Complex terrain** - Basin topography traps pollutants
  2. **Cold-air pools** - Persistent inversions prevent vertical mixing
  3. **Snowpack** - Enhances UV via albedo → drives photochemical ozone production
- **Public health**: Exceedances >70 ppb NAAQS threshold during winter months

**Research Question**
> How well do operational and statistical modeling approaches predict wintertime ozone in the Uinta Basin, and what limits their skill?

### Column 2: Methods / Results

**Two Modeling Approaches**

| Model | Type | Resolution | Notes |
|-------|------|------------|-------|
| NOAA AQM | Operational (CMAQ/GFS) | 13 km | Coarse resolution |
| CLYFAR | Statistical (fuzzy-logic) | N/A | Designed for Uinta Basin |

**Observations**
- Stations: Vernal, Roosevelt, Whiterocks, Dinosaur NM
- Variables: Ozone concentration, air temperature, snow depth
- Challenge: Snow depth measurements are sparse and noisy

**Case Study Results**
- *TBD - pending analysis*

### Column 3: Conclusions / Future Work

**Key Takeaways**
- *TBD - pending analysis*

**Future Work**
- *TBD - pending analysis*

---

## TODO

### Data/Analysis Tasks
- [ ] Identify 2-3 winter ozone events (NAAQS exceedances)
- [ ] Pull AQM forecasts for each event
- [ ] Pull observations for each event
- [ ] Create AQM vs Obs comparison plots
- [ ] Create snow depth visualization
- [ ] Find wildfire case for scale contrast

### Figures to Create
- [ ] Basin map with stations and topography
- [ ] Event comparison plots (time series + bias)
- [ ] Snow depth time series showing data quality
- [ ] Wildfire case showing AQM success

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

## References

- [NOAA NAQFC on AWS](https://registry.opendata.aws/noaa-nws-naqfc-pds/)
- [Herbie Documentation](https://herbie.readthedocs.io/)
- [SynopticPy Documentation](https://synopticpy.readthedocs.io/)
