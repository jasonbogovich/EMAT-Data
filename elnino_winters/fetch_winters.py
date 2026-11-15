"""Download daily winter (Dec-Feb) weather for Northeast Ohio from the Open-Meteo
Historical Weather API, one small request per winter, and combine everything into
a single JSON file: data/neo_winters_era5.json

Why one request per winter?  Open-Meteo's free tier "weighs" a request by how many
days and variables it asks for.  Asking for all 76 years at once costs about four
times more than asking only for the 90 winter days we actually need.

Why models=era5?  The default "best match" stitches together different weather
models over time (a newer one takes over in 2017).  For a 76-year comparison we
want ONE consistent source, so we pin the ERA5 reanalysis.

Usage:  python fetch_winters.py            (safe to re-run; finished winters are cached)
"""
import json, sys, time, calendar, datetime, pathlib, urllib.request, urllib.parse, urllib.error

SITES = {  # name: (latitude, longitude)
    "kent":       (41.1537, -81.3579),   # Kent State University campus
    "akron":      (40.9161, -81.4422),   # Akron-Canton airport
    "cleveland":  (41.4117, -81.8498),   # Cleveland Hopkins airport
    "youngstown": (41.2544, -80.6739),   # Youngstown-Warren airport
    "chardon":    (41.5800, -81.2040),   # Lake Erie snowbelt
}
VARIABLES = ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
             "precipitation_sum", "snowfall_sum", "sunshine_duration",
             "daylight_duration", "shortwave_radiation_sum", "cloud_cover_mean"]
FIRST_WINTER, LAST_WINTER = 1950, 2025      # winter 1950 = Dec 1950 - Feb 1951
API = "https://archive-api.open-meteo.com/v1/archive"
HERE = pathlib.Path(__file__).parent
CACHE = HERE / "data" / "_cache"
OUT = HERE / "data" / "neo_winters_era5.json"


def fetch_winter(site, start_year):
    """Return the API response for Dec 1 (start_year) .. end of Feb (start_year+1)."""
    cache_file = CACHE / f"{site}_{start_year}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    lat, lon = SITES[site]
    feb_end = calendar.monthrange(start_year + 1, 2)[1]
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": f"{start_year}-12-01",
        "end_date": f"{start_year + 1}-02-{feb_end}",
        "daily": ",".join(VARIABLES),
        "timezone": "America/New_York",
        "temperature_unit": "fahrenheit", "precipitation_unit": "inch",
        "models": "era5",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    while True:
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = json.loads(r.read())
            cache_file.write_text(json.dumps(data))
            time.sleep(0.4)                      # be polite to the free API
            return data
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            wait = 300 if "Hourly" in body else 3600 if "Daily" in body else 65
            print(f"  {site} {start_year}: HTTP {e.code} {body[:90]} -> waiting {wait}s", flush=True)
            time.sleep(wait)
        except Exception as e:                   # network hiccup: short pause, retry
            print(f"  {site} {start_year}: {e!r} -> retry in 30s", flush=True)
            time.sleep(30)


def main(sites):
    CACHE.mkdir(parents=True, exist_ok=True)
    combined = {
        "source": "Open-Meteo Historical Weather API (https://open-meteo.com/en/docs/historical-weather-api)",
        "model": "ERA5 reanalysis (models=era5)",
        "retrieved": datetime.date.today().isoformat(),
        "note": "Daily values for meteorological winter only (Dec 1 - end of Feb), one API call per winter.",
        "sites": {},
    }
    if OUT.exists():                              # keep sites fetched on an earlier run
        combined["sites"] = json.loads(OUT.read_text())["sites"]
    for site in sites:
        daily = {k: [] for k in ["time"] + VARIABLES}
        first = None
        for y in range(FIRST_WINTER, LAST_WINTER + 1):
            resp = fetch_winter(site, y)
            first = first or resp
            for k in daily:
                daily[k].extend(resp["daily"][k])
        combined["sites"][site] = {
            "requested_latitude": SITES[site][0], "requested_longitude": SITES[site][1],
            "grid_latitude": first["latitude"], "grid_longitude": first["longitude"],
            "elevation_m": first["elevation"], "timezone": first["timezone"],
            "daily_units": first["daily_units"], "daily": daily,
        }
        OUT.write_text(json.dumps(combined))
        print(f"{site}: {len(daily['time'])} days saved", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(SITES))
