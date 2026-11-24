"""Download the list of target planets from the NASA Exoplanet Archive.

Output: data/planets.csv  (one row per planet)

The archive's "Planetary Systems Composite" table (pscomppars) has one row per
confirmed planet.  We ask its public query service (TAP) for transiting planets
whose dips are deep enough, and whose stars are bright enough, for the TESS
telescope to time a single transit well.

Usage:  python fetch_planets.py
"""
import io, re, html, datetime, pathlib, urllib.parse, urllib.request
import pandas as pd

TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
COLUMNS = ["pl_name", "hostname", "tic_id", "disc_year", "disc_facility",
           "pl_orbper", "pl_orbpererr1", "pl_orbpererr2", "pl_orbper_reflink",
           "pl_tranmid", "pl_tranmiderr1", "pl_tranmiderr2", "pl_tranmid_systemref", "pl_tranmid_reflink",
           "pl_trandep", "pl_trandur", "pl_rade", "pl_bmasse", "st_teff", "sy_tmag", "ra", "dec"]
WHERE = ("tran_flag = 1"            # the planet transits its star
         " and pl_trandep >= 0.5"   # dip of at least 0.5% of the star's light
         " and sy_tmag < 12"        # star bright enough for TESS
         " and pl_orbper < 10"      # short orbit, so TESS sees several transits per month
         " and pl_tranmid is not null and pl_orbpererr1 is not null")
OUT = pathlib.Path(__file__).parent / "data" / "planets.csv"


def reference_name(link):
    """'<a refstr=... href=...> Bouchy et al. 2010 </a>'  ->  'Bouchy et al. 2010'"""
    return html.unescape(re.sub(r"<[^>]+>", "", link)).strip() if isinstance(link, str) else link


def main():
    query = f"select {', '.join(COLUMNS)} from pscomppars where {WHERE} order by pl_name"
    url = TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})
    with urllib.request.urlopen(url, timeout=120) as r:
        planets = pd.read_csv(io.BytesIO(r.read()))
    for col in ["pl_orbper_reflink", "pl_tranmid_reflink"]:
        planets[col] = planets[col].map(reference_name)
    planets = planets.rename(columns={"pl_orbper_reflink": "pl_orbper_ref", "pl_tranmid_reflink": "pl_tranmid_ref"})
    planets["tic"] = planets["tic_id"].str.replace("TIC ", "").astype("Int64")   # plain number, used to find TESS files
    planets["retrieved"] = datetime.date.today().isoformat()
    planets.to_csv(OUT, index=False)
    print(f"{len(planets)} planets saved to {OUT}")


if __name__ == "__main__":
    main()
