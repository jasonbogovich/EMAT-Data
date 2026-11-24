"""Download TESS light curves for chosen planets and save them as small CSV files.

Output: data/lightcurves/<planet>_s<sector>.csv   (one row per 2-minute brightness measurement)

MAST stores each light curve as a FITS file (the standard astronomy format, about 2 MB).
This script downloads the file, keeps the four columns this project needs, drops
measurements that NASA's pipeline flagged as bad, and writes a plain CSV.  The original
FITS files are kept in data/_fits/ (not uploaded to GitHub).

Usage:  python fetch_lightcurves.py "WASP-12 b" "Qatar-8 b"      (most recent sector of each)
"""
import sys, pathlib, urllib.request
import pandas as pd
from astropy.io import fits

DOWNLOAD = "https://mast.stsci.edu/api/v0.1/Download/file?uri="
HERE = pathlib.Path(__file__).parent
FITS_DIR = HERE / "data" / "_fits"
CSV_DIR = HERE / "data" / "lightcurves"


def fetch_one(planet_name, tic, sector, mast_uri):
    FITS_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    fits_path = FITS_DIR / mast_uri.split("/")[-1]
    if not fits_path.exists():
        urllib.request.urlretrieve(DOWNLOAD + mast_uri, fits_path)
    with fits.open(fits_path) as f:
        table = f[1].data                                    # extension 1 holds the light curve table
        lc = pd.DataFrame({
            "time_btjd": table["TIME"].astype("float64"),            # days; BTJD = BJD_TDB - 2457000
            "flux": table["PDCSAP_FLUX"].astype("float64"),          # brightness, electrons per second
            "flux_err": table["PDCSAP_FLUX_ERR"].astype("float64"),
            "quality": table["QUALITY"].astype("int64"),             # 0 = good measurement
        })
    raw_rows = len(lc)
    lc = lc[(lc["quality"] == 0) & lc["time_btjd"].notna() & lc["flux"].notna()].drop(columns="quality")
    lc["time_btjd"] = lc["time_btjd"].round(6)                # 0.000001 day = 0.09 seconds
    lc["flux"] = lc["flux"].round(2)
    lc["flux_err"] = lc["flux_err"].round(2)
    out = CSV_DIR / f"{planet_name.replace(' ', '_')}_s{sector:04d}.csv"
    lc.to_csv(out, index=False)
    print(f"{planet_name}: sector {sector}, kept {len(lc)} of {raw_rows} measurements -> {out.name}")


def main(names):
    planets = pd.read_csv(HERE / "data" / "planets.csv").set_index("pl_name")
    inventory = pd.read_csv(HERE / "data" / "tess_inventory.csv")
    for name in names:
        tic = planets.loc[name, "tic"]
        latest = inventory[inventory["tic"] == tic].sort_values("sector").iloc[-1]
        fetch_one(name, tic, int(latest["sector"]), latest["mast_uri"])


if __name__ == "__main__":
    main(sys.argv[1:])
