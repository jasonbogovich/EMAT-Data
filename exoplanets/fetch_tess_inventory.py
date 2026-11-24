"""List every TESS light curve that exists for the planets in data/planets.csv.

Output: data/tess_inventory.csv  (one row per star per TESS "sector", about 27 days of observing)

TESS data is stored at MAST, the Mikulski Archive for Space Telescopes.  This script asks
MAST's public search service which 2-minute-cadence light curves it holds for our stars.
Nothing large is downloaded here; this is only the catalogue of what is available.

Usage:  python fetch_tess_inventory.py
"""
import json, pathlib, urllib.parse, urllib.request
import pandas as pd

MAST = "https://mast.stsci.edu/api/v0/invoke"
HERE = pathlib.Path(__file__).parent


def mast_search(tic_numbers):
    """Ask MAST for all TESS time-series observations of the given stars (TIC catalogue numbers)."""
    request = {"service": "Mast.Caom.Filtered", "format": "json", "pagesize": 50000,
               "params": {"columns": "target_name,sequence_number,t_min,t_max,t_exptime,provenance_name,dataURL",
                          "filters": [{"paramName": "obs_collection", "values": ["TESS"]},
                                      {"paramName": "dataproduct_type", "values": ["timeseries"]},
                                      {"paramName": "target_name", "values": [str(t) for t in tic_numbers]}]}}
    body = urllib.parse.urlencode({"request": json.dumps(request)}).encode()
    with urllib.request.urlopen(urllib.request.Request(MAST, data=body), timeout=300) as r:
        return json.loads(r.read())["data"]


def main():
    planets = pd.read_csv(HERE / "data" / "planets.csv")
    tics = sorted(planets["tic"].dropna().unique())
    rows = []
    for start in range(0, len(tics), 100):                      # 100 stars per request
        rows += mast_search(tics[start:start + 100])
        print(f"  searched {min(start + 100, len(tics))} of {len(tics)} stars", flush=True)
    found = pd.DataFrame(rows)
    # keep the standard 2-minute light curves made by NASA's own pipeline (file names end in s_lc.fits)
    lc = found[found["dataURL"].str.endswith("s_lc.fits", na=False) & (found["t_exptime"] == 120)
               & (found["sequence_number"] < 1000)].copy()          # drops one non-standard short observation
    lc = lc.rename(columns={"target_name": "tic", "sequence_number": "sector", "dataURL": "mast_uri"})
    lc["tic"] = lc["tic"].astype(int)
    # MAST gives start/end as Modified Julian Dates; convert to calendar dates for readability
    lc["start_date"] = pd.to_datetime(lc["t_min"] + 2400000.5, unit="D", origin="julian").dt.date
    lc["end_date"] = pd.to_datetime(lc["t_max"] + 2400000.5, unit="D", origin="julian").dt.date
    lc = lc[["tic", "sector", "start_date", "end_date", "mast_uri"]].drop_duplicates().sort_values(["tic", "sector"])
    lc.to_csv(HERE / "data" / "tess_inventory.csv", index=False)
    print(f"{len(lc)} light curves for {lc['tic'].nunique()} of {len(tics)} stars saved")


if __name__ == "__main__":
    main()
