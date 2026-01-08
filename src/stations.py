from dataclasses import dataclass
from datetime import datetime


@dataclass
class Station:
    stid: str
    name: str
    lat: float
    lon: float
    region: str
    network: str
    has_ozone: bool = True


BASIN_STATIONS: dict[str, Station] = {
    'QRS': Station(stid='QRS', name='Roosevelt', lat=40.2943, lon=-110.009, region='Basin', network='UDAQ'),
    'QV4': Station(stid='QV4', name='Vernal', lat=40.46472, lon=-109.56083, region='Basin', network='UDAQ'),
    'A1386': Station(stid='A1386', name='Whiterocks', lat=40.4838, lon=-109.9062, region='Basin', network='STI'),
    'A3822': Station(stid='A3822', name='Dinosaur NM', lat=40.4372, lon=-109.3047, region='Basin', network='STI'),
    'A1388': Station(stid='A1388', name='Myton', lat=40.2169, lon=-110.1823, region='Basin', network='STI'),
    'A1633': Station(stid='A1633', name='Redwash', lat=40.20443, lon=-109.35321, region='Basin', network='STI'),
    'A1622': Station(stid='A1622', name='Ouray', lat=40.05485, lon=-109.68737, region='Basin', network='STI'),
}

RESEARCH_STATIONS: dict[str, Station] = {
    'UBHSP': Station(stid='UBHSP', name='Horsepool', lat=40.144, lon=-109.467, region='Research', network='BRC'),
    'UB7ST': Station(stid='UB7ST', name='Seven Sisters', lat=39.981, lon=-109.345, region='Research', network='BRC'),
    'UBCSP': Station(stid='UBCSP', name='Castle Peak', lat=40.051, lon=-110.02, region='Research', network='BRC'),
    'UBRVT': Station(stid='UBRVT', name='Roosevelt BRC', lat=40.294, lon=-110.009, region='Research', network='BRC', has_ozone=False),
}

AUXILIARY_STATIONS: dict[str, Station] = {
    'UTASH': Station(stid='UTASH', name='Asphalt Ridge', lat=40.48, lon=-109.55, region='Auxiliary', network='UDOT', has_ozone=False),
    'UTMYT': Station(stid='UTMYT', name='Myton UDOT', lat=40.20, lon=-110.06, region='Auxiliary', network='UDOT', has_ozone=False),
    'COOPDSNU1': Station(stid='COOPDSNU1', name='Duchesne', lat=40.16, lon=-110.40, region='Auxiliary', network='COOP', has_ozone=False),
    'COOPDINU1': Station(stid='COOPDINU1', name='Dinosaur NM COOP', lat=40.44, lon=-109.30, region='Auxiliary', network='COOP', has_ozone=False),
    'COCOUTUN20': Station(stid='COCOUTUN20', name='Vernal 3.1 NW', lat=40.47, lon=-109.56, region='Auxiliary', network='CoCoRaHS', has_ozone=False),
}

OZONE_STATIONS: dict[str, Station] = {
    **BASIN_STATIONS,
    **{k: v for k, v in RESEARCH_STATIONS.items() if v.has_ozone},
}

ALL_STATIONS: dict[str, Station] = {
    **BASIN_STATIONS,
    **RESEARCH_STATIONS,
    **AUXILIARY_STATIONS,
}

SNOW_DATA_START: dict[str, str] = {
    'COOPDSNU1': '2016-06-17',
    'COOPDINU1': '2016-06-14',
    'COCOUTUN20': '2022-12-28',
    'UTASH': '2023-08-14',
    'UTMYT': '2023-08-14',
    'UBHSP': '2016-01-29',
    'UBCSP': '2019-11-20',
    'UBRVT': '2024-12-19',
    'UB7ST': '2024-12-19',
}

RADIATION_DATA_START: dict[str, str] = {
    'UBCSP': '2020-08-18',
    'UBHSP': '2017-04-24',
    'UBRVT': '2024-12-19',
}

BRC_NAME_TO_STID: dict[str, str] = {
    'Roosevelt': 'QRS',
    'Vernal': 'QV4',
    'Whiterocks': 'A1386',
    'Dinosaur N.M.': 'A3822',
    'DinosaurNM': 'A3822',
    'Dinosaur, CO': 'A3822',
    'Myton': 'A1388',
    'Red Wash': 'A1633',
    'RedWash': 'A1633',
    'Ouray': 'A1622',
    'Horsepool': 'UBHSP',
    'Seven Sisters': 'UB7ST',
    'Castle Peak': 'UBCSP',
    'Rangely': 'RANGELY',
    'Fruitland': 'FRUITLAND',
    'Duchesne': 'DUCHESNE',
    'Ft. Duchesne': 'FT_DUCHESNE',
    'Jensen': 'JENSEN',
    'Lapoint': 'LAPOINT',
    'Altamont': 'ALTAMONT',
    'Gusher': 'GUSHER',
    'Starvation': 'STARVATION',
    'Price': 'PRICE',
    'Meeker': 'MEEKER',
    'Rifle': 'RIFLE',
    'BoulderWY': 'BOULDER_WY',
    'Little Mtn': 'LITTLE_MTN',
    'Little Mtn.': 'LITTLE_MTN',
    'Sand Wash': 'SAND_WASH',
    'Flat Rock': 'FLAT_ROCK',
    'Rabbit Mtn': 'RABBIT_MTN',
    'Rabbit Mtn.': 'RABBIT_MTN',
    'Pariette Draw': 'PARIETTE_DRAW',
    'Seep Ridge': 'SEEP_RIDGE',
    'Wells Draw': 'WELLS_DRAW',
    'Cedarview': 'CEDARVIEW',
    'Dry Fork': 'DRY_FORK',
    'Bitter Creek': 'BITTER_CREEK',
    'Pine Spring': 'PINE_SPRING',
    "King's Well": 'KINGS_WELL',
    'Moondance': 'MOONDANCE',
    'WildHorse': 'WILDHORSE',
    'Willow Creek': 'WILLOW_CREEK',
    '9 Mile Canyon': '9_MILE_CANYON',
    'Mountain Home': 'MOUNTAIN_HOME',
    'Idaho Falls': 'IDAHO_FALLS',
    'Logan': 'LOGAN',
    'SLC Hawthorne': 'SLC_HAWTHORNE',
}

STID_TO_NAME: dict[str, str] = {
    stid: name for name, stid in BRC_NAME_TO_STID.items()
    if not any(c in name for c in ['.', ','])
}
STID_TO_NAME.update({s.stid: s.name for s in ALL_STATIONS.values()})


def get_stations_by_region(region: str) -> list[Station]:
    return [s for s in ALL_STATIONS.values() if s.region == region]


def get_stations_by_network(network: str) -> list[Station]:
    return [s for s in ALL_STATIONS.values() if s.network == network]


def get_ozone_stations() -> list[Station]:
    return [s for s in ALL_STATIONS.values() if s.has_ozone]


def get_station_coords(stids: list[str] | None = None) -> dict[str, tuple[float, float]]:
    if stids is None:
        stids = list(ALL_STATIONS.keys())
    return {
        stid: (ALL_STATIONS[stid].lat, ALL_STATIONS[stid].lon)
        for stid in stids
        if stid in ALL_STATIONS
    }


def get_station_ids(region: str | None = None, network: str | None = None, ozone_only: bool = False) -> list[str]:
    stations = ALL_STATIONS.values()
    if region:
        stations = [s for s in stations if s.region == region]
    if network:
        stations = [s for s in stations if s.network == network]
    if ozone_only:
        stations = [s for s in stations if s.has_ozone]
    return [s.stid for s in stations]


def get_available_snow_stations(start_date: str) -> list[str]:
    query_start = datetime.strptime(start_date, '%Y-%m-%d')
    available = []
    for stid, avail_date in SNOW_DATA_START.items():
        if query_start >= datetime.strptime(avail_date, '%Y-%m-%d'):
            available.append(stid)
    return available


def get_available_radiation_stations(start_date: str) -> list[str]:
    query_start = datetime.strptime(start_date, '%Y-%m-%d')
    available = []
    for stid, avail_date in RADIATION_DATA_START.items():
        if query_start >= datetime.strptime(avail_date, '%Y-%m-%d'):
            available.append(stid)
    return available
