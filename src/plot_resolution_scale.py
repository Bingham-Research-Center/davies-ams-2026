"""
AQM Resolution vs Basin Scale Map

Uses high-resolution DEM data for terrain visualization.
Shows 13 km grid overlay on hillshade terrain.
Key message: the entire Basin floor fits in ~4-6 grid cells.
"""
from pathlib import Path

import elevation
import geopandas as gpd
import rioxarray as rxr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature import ShapelyFeature
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from stations import OZONE_STATIONS

# Paths
OUTPUT_DIR = Path(__file__).parent.parent / 'figures'
DATA_DIR = Path(__file__).parent.parent / 'data'
DEM_FILE = DATA_DIR / 'uinta_basin_expanded.tif'

# Grid parameters (at ~40°N latitude)
AQM_RESOLUTION_KM = 13
GRID_DEG_LAT = AQM_RESOLUTION_KM / 111.0  # ~0.117°
GRID_DEG_LON = AQM_RESOLUTION_KM / 85.0   # ~0.153°

# Map extent
LON_MIN, LON_MAX = -111.0, -108.5
LAT_MIN, LAT_MAX = 39.5, 41.0

# Stations to plot
STATION_IDS = ['QRS', 'UBCSP', 'UBHSP', 'QV4', 'UB7ST']

# County FIPS codes for Uinta Basin
UINTAH_FIPS = '047'
DUCHESNE_FIPS = '013'
UTAH_STATE_FIPS = '49'


def download_dem():
    """Download SRTM 30m DEM for the expanded extent if not present."""
    if not DEM_FILE.exists():
        print('Downloading SRTM 30m DEM for expanded extent...')
        DATA_DIR.mkdir(exist_ok=True)
        bounds = (LON_MIN, LAT_MIN, LON_MAX, LAT_MAX)
        elevation.clip(bounds=bounds, output=str(DEM_FILE))
        print(f'DEM saved to {DEM_FILE}')
    return DEM_FILE


def get_basin_boundary():
    """Get merged Uintah + Duchesne county boundary."""
    print('Loading county boundaries...')
    # Load US counties from Census Bureau
    counties_url = 'https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip'
    counties = gpd.read_file(counties_url)

    # Filter to Utah
    utah_counties = counties[counties['STATEFP'] == UTAH_STATE_FIPS]

    # Get Uintah and Duchesne counties
    basin_counties = utah_counties[
        utah_counties['COUNTYFP'].isin([UINTAH_FIPS, DUCHESNE_FIPS])
    ]

    # Merge into single polygon (dissolve removes internal border)
    basin_merged = basin_counties.dissolve()

    return basin_merged


def calculate_hillshade(elev_data, azimuth=315, altitude=45):
    """Create hillshade from elevation data."""
    azimuth_rad = np.radians(360 - azimuth + 90)
    altitude_rad = np.radians(altitude)

    # Calculate gradients
    x, y = np.gradient(elev_data)
    slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-x, y)

    # Calculate hillshade
    hillshade = (np.sin(altitude_rad) * np.cos(slope) +
                 np.cos(altitude_rad) * np.sin(slope) *
                 np.cos(azimuth_rad - aspect))

    # Scale to 0-255 range
    hillshade = ((hillshade + 1) / 2 * 255).astype(np.uint8)
    return hillshade


def main():
    """Create the AQM resolution vs basin scale map."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Download/load DEM
    download_dem()
    print(f'Loading DEM from {DEM_FILE}...')
    dem = rxr.open_rasterio(DEM_FILE).squeeze()

    # Create hillshade
    print('Creating hillshade...')
    hillshade = calculate_hillshade(dem.values)

    # Create figure
    fig, ax = plt.subplots(
        figsize=(12, 10),
        subplot_kw={'projection': ccrs.PlateCarree()}
    )
    ax.set_extent([LON_MIN, LON_MAX, LAT_MIN, LAT_MAX], crs=ccrs.PlateCarree())

    # Colored elevation
    dem_extent = [
        float(dem.x.min()), float(dem.x.max()),
        float(dem.y.min()), float(dem.y.max())
    ]

    # Show colored elevation
    ax.imshow(dem.values, extent=dem_extent, origin='upper',
              cmap='terrain', transform=ccrs.PlateCarree(), zorder=1,
              vmin=1400, vmax=3200)

    # Hillshade overlay
    ax.imshow(hillshade, extent=dem_extent, origin='upper',
              cmap='gray', transform=ccrs.PlateCarree(), zorder=2,
              alpha=0.3)

    # 13 km grid lines
    print('Drawing grid lines...')
    grid_lats = np.arange(LAT_MIN, LAT_MAX + 0.01, GRID_DEG_LAT)
    grid_lons = np.arange(LON_MIN, LON_MAX + 0.01, GRID_DEG_LON)

    for lat in grid_lats:
        ax.plot([LON_MIN, LON_MAX], [lat, lat],
                color='red', alpha=0.8, linewidth=1.5,
                transform=ccrs.PlateCarree(), zorder=4)

    for lon in grid_lons:
        ax.plot([lon, lon], [LAT_MIN, LAT_MAX],
                color='red', alpha=0.8, linewidth=1.5,
                transform=ccrs.PlateCarree(), zorder=4)

    # Scale bar (upper-left, showing 13 km = one grid cell)
    scale_lon = LON_MIN + 0.15
    scale_lat = LAT_MAX - 0.15
    ax.plot([scale_lon, scale_lon + GRID_DEG_LON], [scale_lat, scale_lat],
            color='black', linewidth=4, transform=ccrs.PlateCarree(), zorder=10)
    ax.text(scale_lon + GRID_DEG_LON / 2, scale_lat - 0.05, '13 km',
            ha='center', fontsize=10, fontweight='bold',
            transform=ccrs.PlateCarree(), zorder=10)

    # Basin outline
    basin_gdf = get_basin_boundary()
    basin_feature = ShapelyFeature(
        basin_gdf.geometry, ccrs.PlateCarree(),
        facecolor='none', edgecolor='saddlebrown',
        linewidth=3, linestyle='--'
    )
    ax.add_feature(basin_feature, zorder=5)

    # State borders
    ax.add_feature(cfeature.STATES.with_scale('50m'),
                   edgecolor='black', linewidth=1, facecolor='none', zorder=6)

    # Station markers
    print('Adding station markers...')
    for stid in STATION_IDS:
        if stid in OZONE_STATIONS:
            station = OZONE_STATIONS[stid]
            ax.plot(
                station.lon, station.lat, 'o',
                markersize=14, markerfacecolor='yellow',
                markeredgecolor='black', markeredgewidth=2,
                transform=ccrs.PlateCarree(), zorder=7
            )
            offset_y = 0.04
            ax.text(
                station.lon, station.lat + offset_y,
                f'{station.name}\n({stid})', ha='center', va='bottom',
                fontsize=8, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='gray',
                          alpha=0.9, boxstyle='round,pad=0.3'),
                transform=ccrs.PlateCarree(), zorder=8
            )

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='none', edgecolor='saddlebrown',
                       linestyle='--', linewidth=2,
                       label='Uintah + Duchesne Counties'),
        plt.Line2D([0], [0], color='red', linewidth=1.5, alpha=0.7,
                   label='13 km AQM Grid'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow',
                   markeredgecolor='black', markersize=10,
                   label='Ozone Station'),
    ]
    legend = ax.legend(handles=legend_elements, loc='lower right', fontsize=9,
                       framealpha=1.0, edgecolor='gray', facecolor='white')
    legend.set_zorder(20)

    # Gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0, alpha=0)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'fontsize': 10}
    gl.ylabel_style = {'fontsize': 10}

    # Grid cell count annotation (lower-left)
    ax.text(0.02, 0.02, 'Basin floor: ~6 grid cells east-west',
            transform=ax.transAxes, fontsize=11, fontweight='bold',
            verticalalignment='bottom',
            bbox=dict(facecolor='white', edgecolor='gray', alpha=0.9,
                      boxstyle='round,pad=0.4'), zorder=20)

    # Title
    ax.set_title(
        'AQM 13 km Grid vs. Basin Scale',
        fontsize=14, fontweight='bold', pad=10
    )

    plt.tight_layout()

    # Save figure
    output_path = OUTPUT_DIR / 'aqm_resolution_mismatch.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f'Saved figure to {output_path}')

    plt.close(fig)


if __name__ == '__main__':
    main()
