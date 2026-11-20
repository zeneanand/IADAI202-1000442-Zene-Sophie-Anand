# LogiSight Delivery Intelligence — FA-2 (Mathematics for AI-II)

Interactive last-mile delivery analytics dashboard built with Streamlit, pandas and Plotly.
It turns the FA-1 plan and `delivery_analysis_fa2.ipynb` into a working multi-page app.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data sources (sidebar)
1. **Google Sheets** – the CSV export URL from the notebook (`utils/data_loader.py → SHEET_URL`). The sheet must be shared as "anyone with the link".
2. **Upload CSV / Excel** – `.csv` or `.xlsx`. Expected columns: `Delivery_Time, Weather, Traffic, Vehicle, Agent_Rating, Agent_Age, Area, Category` (`Order_ID` optional). Differently named columns are auto-matched; otherwise use "Map missing columns".
3. **Demo data (synthetic)** – generated, NOT real deliveries; intentionally messy to show cleaning. Download it from the landing screen as a template.

## Maths (details on the Methodology page)
μ = mean(Delivery_Time); σ = sample standard deviation (n − 1); T_late = μ + σ; late if Delivery_Time > T_late.
T_late is fixed on the full cleaned dataset so "late" means the same thing while filters change. It is a project-defined threshold, not a company SLA.

## Notes on differences from the notebook
- The notebook comment says "population" σ but pandas `.std()` is the **sample** σ; the app uses sample σ and says so.
- Orders with missing/invalid `Delivery_Time` are excluded rather than imputed.
- Traffic categories are detected from the data, not hard-coded; ages missing are median-imputed before grouping (the notebook put NaN ages in "40+").

## Deploy (FA-2 Stage 7)
Push this folder to a GitHub repo, then on share.streamlit.io choose the repo, branch and `app.py`.

## Tests
`python tests/test_core.py` checks cleaning, statistics, uploads and edge cases (needs only pandas/numpy/openpyxl).
