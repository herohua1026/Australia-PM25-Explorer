AUSTRALIA PM2.5 EXPLORER

Open http://127.0.0.1:8502 while the local server is running.

Run again on this computer:
  cd Open_PM25_Explorer
  /opt/anaconda3/bin/python start.py

Portable installation (Python 3.11 recommended):
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python start.py

WHAT IS INCLUDED
- Real audited M7 monthly/annual product, 2011–2024, 2,454 fixed 2021 SA2s.
- Clickable offline SVG map, area search, zoom and drag.
- Concentration, difference between chosen periods, and calibration adjustment.
- Raw/calibrated area trends and regional validation context.
- Original complete CSV ZIPs, selected-area CSV and state/year subset ZIPs.
- Download manifest, source checksums, methods and limitations.
- Eleven automated tests, including Streamlit app execution and source-download integrity.

ARCHITECTURE
American Double Hero's local Python -> GitHub -> Streamlit pattern is retained.
For a free hosting option replace Railway with Streamlit Community Cloud.
GitHub stores source, the compact Parquet product and display geometry. No database,
Google login, Supabase, map-tile service or paid API is required for this read-only app.
Optional GitHub Release links can serve complete ZIP downloads directly.
Railway remains supported through railway.toml and python start.py, but is not
assumed to be free. Local server binds only to 127.0.0.1; Railway binds to 0.0.0.0.

GITHUB AND STREAMLIT COMMUNITY CLOUD
1. Create a dedicated repository for this folder, not the complete calibration workspace.
2. Add app.py, start.py, data_access.py, requirements.txt, frontend/, data/,
   .streamlit/config.toml, tests/, .github/ and this guide. Do not add credentials.
3. Use a private repository during review if your account's hosting integration supports it.
   Decide the public audience and confirm redistribution terms before publishing data.
4. At share.streamlit.io select the repository, branch and main file app.py.
   Use Python 3.11. No secrets or database connection are needed.
5. Verify map selection and downloads at the assigned streamlit.app URL.

OPTIONAL GITHUB RELEASE DOWNLOADS
The initial bundle is only about 39 MB; its largest file is about 21.1 MB.
Each file is below GitHub's 100 MiB Git-file limit. No Git LFS is needed.
To avoid repeatedly committing ZIP archives, attach annual_product.zip and
monthly_product.zip to a GitHub Release and set this environment variable:
  GITHUB_RELEASE_BASE_URL=https://github.com/OWNER/REPOSITORY/releases/download/TAG
The app will use direct release links for complete downloads. Subset downloads
are still generated locally in the app. Keep bundled ZIPs for the integrity tests
and local fallback unless you deliberately revise the manifest/packaging workflow.
Avoid adding every new historical data version to Git: use releases for revisions.

RAILWAY OPTION
Connect the dedicated repository, set start command python start.py. Railway sets
PORT; HOST=0.0.0.0 can be set explicitly. Health endpoint: /_stcore/health.
Do not enable a paid plan unless you intend to incur charges.

VERIFICATION
  python -m unittest discover -s tests -v
Tests check SHA256 for every packaged artifact, original CSV checksums inside ZIPs,
map/product code joins, 12-month annual reaggregation, change/adjustment arithmetic,
subset filtering and app execution in multiple modes. The live UI was also checked.

DATA PREPARATION
Runtime needs no GIS libraries. scripts/prepare_data.py is a separate maintainer
step requiring geopandas/shapely plus the original audited output and ABS shapefile:
  python scripts/prepare_data.py --source /path/to/audited/outputs --boundaries /path/to/SA2_2021_AUST.shp
It verifies source CSV hashes against Product_Export_Audit.json, writes lossless
Parquet, preserves original CSVs in ZIPs and simplifies map boundaries at 500 m
in EPSG:3577. Simplification affects display only. It never refits calibration.

LIMITS
Raw and calibrated use the same map scale for the selected geography and period.
Difference mode uses a symmetric scale covering both products. Scales can change
between periods; use the change view for direct comparisons.
Very Remote validation uses seven stations. Regional RMSE is not a confidence
interval for an individual area. Annual values are equal-month physical-area means,
not population-weighted exposure. This is a historical research product, not live AQI.
The calibration manuscript DOI is a placeholder pending publication.
Source references are listed in About the data.

Provider references checked 5 November 2026:
https://streamlit.io/cloud
https://docs.railway.com/pricing
https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
https://supabase.com/docs/guides/platform/billing-on-supabase
Free hosting remains subject to provider resource, availability and usage policies.

GEOGRAPHY EXTENSION
Choose SA2, SA3, SA4 or Whole Australia in the right Selected area panel.
SA3 (340), SA4 (89) and Australia are area-weighted summaries of the published
SA2 product using full polygon areas in EPSG:3577 and the ABS 2021 hierarchy.
They are not re-extracted raster means or population-weighted exposures.
Aggregated downloads have area_code/area_name and identify their geography and
aggregation method. No aggregate validation RMSE is manufactured.
To regenerate lookup and maps after prepare_data.py:
  python scripts/prepare_hierarchy.py --boundaries /path/to/SA2_2021_AUST.shp

CONTROLS
Concentration and calibration-adjustment views select a single year/month.
Change-over-time selects explicit start and end dates (end minus start).
The ambiguous year slider has been removed.
