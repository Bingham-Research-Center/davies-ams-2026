# herbie-aqm

Herbie model template for NOAA Air Quality Model (AQM/NAQFC) data.

## What is AQM?

The **National Air Quality Forecast Capability (NAQFC)** uses the Community Multiscale Air Quality (CMAQ) model driven by GFS meteorology to produce ozone and PM2.5 forecasts at 13km resolution.

- **Forecast range**: 72 hours
- **Cycles**: 06Z and 12Z
- **Coverage**: CONUS, Alaska, Hawaii
- **Variables**: Ozone (O3) and Fine Particulate Matter (PM2.5)

## Installation

Copy `src/herbie_aqm/__init__.py` to your Herbie custom template location:

```bash
cp src/herbie_aqm/__init__.py ~/.config/herbie/custom_template.py
```

Or for a system-wide installation via PR to Herbie, copy to `herbie/models/aqm.py`.

## Usage

```python
from herbie import Herbie

# Get max 8-hour ozone forecast
H = Herbie("2024-01-15 12:00", model="aqm", product="max_8hr_o3", fxx=0)
local_file = H.download()

# Load as xarray (without subsetting)
import xarray as xr
ds = xr.open_dataset(local_file, engine='cfgrib', decode_times=False)

# Alaska grid
H = Herbie("2024-01-15 12:00", model="aqm_ak", product="max_8hr_o3", fxx=0)

# Hawaii grid
H = Herbie("2024-01-15 12:00", model="aqm_hi", product="max_8hr_o3", fxx=0)
```

## Available Products

| Product | Description |
|---------|-------------|
| `max_8hr_o3` | Daily maximum 8-hour average ozone (default) |
| `ave_1hr_o3` | Hourly average ozone |
| `ave_8hr_o3` | 8-hour average ozone |
| `max_1hr_o3` | Daily maximum 1-hour ozone |
| `ave_24hr_pm25` | 24-hour average PM2.5 |
| `ave_1hr_pm25` | Hourly average PM2.5 |
| `max_1hr_pm25` | Daily maximum 1-hour PM2.5 |

## Model Classes

| Model | Region | Grid |
|-------|--------|------|
| `aqm` | CONUS | 227 (5 km) |
| `aqm_ak` | Alaska | 198 (6 km) |
| `aqm_hi` | Hawaii | 196 (2.5 km) |
| `naqfc` | CONUS (alias) | 227 |

## Data Sources

This template automatically searches:

1. **AWS Open Data**: `s3://noaa-nws-naqfc-pds/` (historical back to Jan 2020)
2. **NOMADS**: Recent ~7 days of data

No credentials required for AWS access.

## AQM Versions

The template automatically selects the correct version based on date:

- **AQMv5**: Before July 20, 2021
- **AQMv6**: July 20, 2021 - May 13, 2024
- **AQMv7**: May 14, 2024 - present

## References

- [NOAA NAQFC on AWS](https://registry.opendata.aws/noaa-nws-naqfc-pds/)
- [NCO AQM Products](https://www.nco.ncep.noaa.gov/pmb/products/aqm/)
- [NOAA-EMC/AQM GitHub](https://github.com/NOAA-EMC/AQM)
- [Herbie Documentation](https://herbie.readthedocs.io/)

## License

MIT
