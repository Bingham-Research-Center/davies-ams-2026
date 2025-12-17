"""
Herbie model template for NOAA Air Quality Model (AQM/NAQFC) data.

The National Air Quality Forecast Capability (NAQFC) uses the Community
Multiscale Air Quality (CMAQ) model driven by GFS meteorology at 13km
resolution to produce ozone and PM2.5 forecasts.

Data Sources:
- AWS: s3://noaa-nws-naqfc-pds/ (historical back to Jan 2020)
- NOMADS: https://nomads.ncep.noaa.gov/pub/data/nccf/com/aqm/prod/

References:
- https://registry.opendata.aws/noaa-nws-naqfc-pds/
- https://www.nco.ncep.noaa.gov/pmb/products/aqm/
- https://github.com/NOAA-EMC/AQM

To use locally, copy this file to ~/.config/herbie/custom_template.py
or add it to herbie/models/ for a Herbie PR.
"""

__all__ = ["aqm", "naqfc", "aqm_ak", "aqm_hi"]

from datetime import datetime


def _get_aqm_version(date) -> str:
    """Determine which AQM version was operational on date."""
    if isinstance(date, str):
        date = datetime.strptime(date[:10], "%Y-%m-%d")

    if date < datetime(2021, 7, 20):
        return "AQMv5"
    elif date < datetime(2024, 5, 14):
        return "AQMv6"
    else:
        return "AQMv7"


class aqm:
    """
    NOAA Air Quality Model (AQM) - CONUS domain.

    CMAQ-based ozone and PM2.5 forecasts at 13km resolution.
    Produces 72-hour forecasts at 06Z and 12Z cycles.

    AQM Versions:
    - AQMv5: before July 20, 2021
    - AQMv6: July 20, 2021 - May 13, 2024
    - AQMv7: May 14, 2024 - present

    Example:
        H = Herbie("2024-01-15 12:00", model="aqm", product="max_8hr_o3", fxx=0)
        ds = H.xarray()
    """

    def template(self):
        self.DESCRIPTION = "NOAA Air Quality Model (CMAQ) - CONUS"
        self.DETAILS = {
            "NOAA NAQFC on AWS": "https://registry.opendata.aws/noaa-nws-naqfc-pds/",
            "NCO AQM Products": "https://www.nco.ncep.noaa.gov/pmb/products/aqm/",
            "NOAA-EMC GitHub": "https://github.com/NOAA-EMC/AQM",
        }

        # Available products (first is default)
        self.PRODUCTS = {
            "max_8hr_o3": "Daily maximum 8-hour average ozone",
            "ave_1hr_o3": "Hourly average ozone",
            "ave_8hr_o3": "8-hour average ozone",
            "max_1hr_o3": "Daily maximum 1-hour ozone",
            "ave_24hr_pm25": "24-hour average PM2.5",
            "ave_1hr_pm25": "Hourly average PM2.5",
            "max_1hr_pm25": "Daily maximum 1-hour PM2.5",
        }

        # Determine AQM version and grid
        version = _get_aqm_version(self.date)
        grid = getattr(self, 'grid', '227')  # 227=CONUS default

        # Bias correction suffix (default: corrected)
        bc = getattr(self, 'bc', True)
        bc_suffix = "_bc" if bc else ""

        # Build source paths
        # AWS: s3://noaa-nws-naqfc-pds/AQMv6/CS/YYYYMMDD/CC/filename
        # NOMADS: https://nomads.ncep.noaa.gov/pub/data/nccf/com/aqm/prod/aqm.YYYYMMDD/filename
        self.SOURCES = {
            "aws": f"https://noaa-nws-naqfc-pds.s3.amazonaws.com/{version}/CS/{self.date:%Y%m%d}/{self.date:%H}/aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{self.date:%Y%m%d}.{grid}.grib2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/aqm/prod/aqm.{self.date:%Y%m%d}/aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{grid}.grib2",
        }

        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{self.date:%Y%m%d}.{grid}.grib2"


class naqfc(aqm):
    """Alias for AQM (National Air Quality Forecast Capability)."""
    pass


class aqm_ak:
    """NOAA Air Quality Model - Alaska domain."""

    def template(self):
        self.DESCRIPTION = "NOAA Air Quality Model (CMAQ) - Alaska"
        self.DETAILS = {
            "NOAA NAQFC on AWS": "https://registry.opendata.aws/noaa-nws-naqfc-pds/",
            "NCO AQM Products": "https://www.nco.ncep.noaa.gov/pmb/products/aqm/",
        }

        self.PRODUCTS = {
            "max_8hr_o3": "Daily maximum 8-hour average ozone",
            "ave_1hr_o3": "Hourly average ozone",
            "ave_24hr_pm25": "24-hour average PM2.5",
            "ave_1hr_pm25": "Hourly average PM2.5",
        }

        version = _get_aqm_version(self.date)
        bc = getattr(self, 'bc', True)
        bc_suffix = "_bc" if bc else ""
        grid = "198"  # Alaska grid

        self.SOURCES = {
            "aws": f"https://noaa-nws-naqfc-pds.s3.amazonaws.com/{version}/CS/{self.date:%Y%m%d}/{self.date:%H}/aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{self.date:%Y%m%d}.{grid}.grib2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/aqm/prod/aqm.{self.date:%Y%m%d}/aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{grid}.grib2",
        }

        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{self.date:%Y%m%d}.{grid}.grib2"


class aqm_hi:
    """NOAA Air Quality Model - Hawaii domain."""

    def template(self):
        self.DESCRIPTION = "NOAA Air Quality Model (CMAQ) - Hawaii"
        self.DETAILS = {
            "NOAA NAQFC on AWS": "https://registry.opendata.aws/noaa-nws-naqfc-pds/",
            "NCO AQM Products": "https://www.nco.ncep.noaa.gov/pmb/products/aqm/",
        }

        self.PRODUCTS = {
            "max_8hr_o3": "Daily maximum 8-hour average ozone",
            "ave_1hr_o3": "Hourly average ozone",
            "ave_24hr_pm25": "24-hour average PM2.5",
            "ave_1hr_pm25": "Hourly average PM2.5",
        }

        version = _get_aqm_version(self.date)
        bc = getattr(self, 'bc', True)
        bc_suffix = "_bc" if bc else ""
        grid = "196"  # Hawaii grid

        self.SOURCES = {
            "aws": f"https://noaa-nws-naqfc-pds.s3.amazonaws.com/{version}/CS/{self.date:%Y%m%d}/{self.date:%H}/aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{self.date:%Y%m%d}.{grid}.grib2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/aqm/prod/aqm.{self.date:%Y%m%d}/aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{grid}.grib2",
        }

        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"aqm.t{self.date:%H}z.{self.product}{bc_suffix}.{self.date:%Y%m%d}.{grid}.grib2"
