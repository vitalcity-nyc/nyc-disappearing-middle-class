# New York City's neighborhoods by income, 1970 vs. 2015-2019

A reanalysis applying [Scott Winship's method](https://www.aei.org/articles/chicagos-disappearing-middle-class-can-be-found-in-its-proliferating-upper-middle-class-neighborhoods/) (American Enterprise Institute, May 2025) to the five boroughs of New York City.

**Full credit to Winship and AEI** for the method, income thresholds, inflation index choice, and framing — which themselves build on the University of Illinois Chicago Voorhees Center's tract classification scheme. This repository contributes only the New York data assembly and the charts.

**Live:** https://vital-city-nyc.github.io/nyc-disappearing-middle-class/

## Headline result

Applying the same 1970-anchored, inflation-adjusted per-capita-income thresholds Winship used for Chicago to every New York City census tract:

| Band | 1970 | 2015-2019 |
|---|---|---|
| Lower (under 80% of 1970 NY metro per-capita income) | 43.0% | 20.4% |
| Middle (80-120%) | 43.2% | 31.5% |
| Upper (over 120%) | 13.8% | 48.1% |
| Very high (over 140%) | 8.0% | 35.8% |

Same pattern Winship found in Chicago: New York City's middle-income neighborhoods shrank as a share of residents because so many of them moved up into upper-middle and upper-income tracts, not down.

## Data

- `data/nyc_metro_1970.csv` — Brown LTDB 1970 sample, filtered to New York-Newark-Jersey City CBSA (used for the metro per-capita-income anchor) plus the five NYC counties.
- `data/nyc_2015_19.csv` — Brown LTDB ACS 2015-2019 sample, filtered to the five NYC counties.
- Both are on 2010 census tract boundaries. Source: [s4.ad.brown.edu/projects/diversity/Researcher/LTDB.htm](https://s4.ad.brown.edu/projects/diversity/Researcher/LTDB.htm).

## Reproduce

```bash
python3 scripts/analyze.py
```

This writes `output/data.json`, which `index.html` reads to build the charts.

## Method (in one paragraph)

For each NYC census tract in 1970 and 2015-2019, classify by per-capita income relative to four thresholds set at 60%, 80%, 120%, and 140% of the 1970 New York-Newark-Jersey City metropolitan-area per-capita income, then held fixed in real terms using the Bureau of Economic Analysis Personal Consumption Expenditures price index (1970 = 21.219, 2019 = 105.272). Sum tract population in each band, citywide and by borough. Full methodology, sources, and limitations are in the expandable section at the bottom of the live page.

## Credit

- **Method, framing, inflation choices:** Scott Winship, American Enterprise Institute, May 2025.
- **Original tract classification scheme:** University of Illinois Chicago Voorhees Center.
- **New York data assembly and charts:** Josh Greenman, May 2026.
- **Page styling:** [Vital City design system](https://vital-city-nyc.github.io/vital-city-design-system/).
