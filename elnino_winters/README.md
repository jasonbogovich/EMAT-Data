# Does El Niño Brighten a Kent Winter?

A data-analysis report on 76 winters (1950–51 to 2025–26) of weather at Kent, Ohio, compared with the El Niño / La Niña cycle.

**Open the report:** [`elnino_kent_winters.ipynb`](elnino_kent_winters.ipynb)

| File | Purpose |
|---|---|
| `elnino_kent_winters.ipynb` | The report: data loading, cleaning, figures, statistics, conclusions |
| `fetch_winters.py` | Downloads December–February daily weather from Open-Meteo |
| `data/neo_winters_era5.json` | Winter daily weather (Open-Meteo, ERA5 reanalysis) |
| `data/oni.json`, `data/oni_raw.txt` | NOAA Oceanic Niño Index |

## Data sources

- Open-Meteo Historical Weather API — https://open-meteo.com/en/docs/historical-weather-api
- NOAA Climate Prediction Center, Oceanic Niño Index — https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt

## Running it

Requires Python with `pandas`, `numpy`, `matplotlib`, `scipy` and `statsmodels`. The data files are included, so the notebook runs without downloading anything.
