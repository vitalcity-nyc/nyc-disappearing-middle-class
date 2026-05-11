"""
NYC version of the Voorhees / Winship middle-class neighborhood analysis.

Data:
  Brown LTDB Standard Sample, 1970 and 2015-2019 (ACS), all on 2010 tract boundaries.
Method:
  1. Compute NY-Newark-Jersey City CBSA (35620) 1970 population-weighted per-capita income.
  2. Build four per-capita-income thresholds at 60%, 80%, 120%, 140% of the metro average,
     fixed in real terms (the Voorhees relative cuts that Winship held constant via PCE).
  3. Inflate the four thresholds to 2019 dollars with the BEA PCE Price Index
     (1970 = 21.219, 2019 = 105.272; 2017=100 chain-weighted).
  4. Classify every NYC city tract (Bronx, Kings, NY, Queens, Richmond) in 1970 and 2015-19
     by per-capita income, and sum population in each bucket.
"""
import csv, json, os
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), '..', 'data')
# Pre-extracted NYC subsets of the Brown LTDB Standard Sample files.
# Build them with scripts/extract_nyc.py from the full LTDB downloads if missing.
F_1970 = os.path.join(DATA, 'nyc_metro_1970.csv')
F_2019 = os.path.join(DATA, 'nyc_2015_19.csv')
OUT = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUT, exist_ok=True)

NYC_PREFIXES = ('36005', '36047', '36061', '36081', '36085')
BOROUGHS = {'36005': 'Bronx', '36047': 'Brooklyn', '36061': 'Manhattan',
            '36081': 'Queens', '36085': 'Staten Island'}
NY_CBSA = '35620'  # New York-Newark-Jersey City

# BEA PCE Price Index, annual, 2017 = 100 (chain-weighted)
PCE_1970 = 21.219
PCE_2019 = 105.272
PCE_TO_2019 = PCE_2019 / PCE_1970  # 1970$ -> 2019$

# ---------- 1) Metro 1970 per capita income (pop-weighted) ----------
metro_pop = 0.0
metro_inc_pop = 0.0
with open(F_1970, encoding='latin-1') as f:
    for row in csv.DictReader(f):
        if row.get('cbsa10') != NY_CBSA:
            continue
        try:
            pop = float(row['POP70SP1'] or 0)
            inc = float(row['INCPC70']) if row['INCPC70'] else None
        except ValueError:
            continue
        if pop > 0 and inc is not None:
            metro_pop += pop
            metro_inc_pop += pop * inc

metro_pci_1970 = metro_inc_pop / metro_pop
print(f'NY metro 1970 per-capita income (pop-weighted, 1970 $): {metro_pci_1970:,.0f}')

# Voorhees thresholds in 1970 $
T_1970 = {
    'very_low_max': 0.60 * metro_pci_1970,
    'low_max':      0.80 * metro_pci_1970,
    'middle_max':   1.20 * metro_pci_1970,
    'high_max':     1.40 * metro_pci_1970,
}
# Same thresholds inflated to 2019 $ for use against ACS 2015-19
T_2019 = {k: v * PCE_TO_2019 for k, v in T_1970.items()}
print('Thresholds in 1970 $:', {k: round(v) for k, v in T_1970.items()})
print('Thresholds in 2019 $:', {k: round(v) for k, v in T_2019.items()})


def classify(inc, t):
    if inc is None:
        return None
    if inc < t['very_low_max']: return 'very_low'
    if inc < t['low_max']:      return 'low'
    if inc < t['middle_max']:   return 'middle'
    if inc < t['high_max']:     return 'high'
    return 'very_high'


CATS = ['very_low', 'low', 'middle', 'high', 'very_high']

# ---------- 2) Classify NYC tracts in 1970 and 2015-19 ----------
def load_year(path, pop_col, inc_col, thresholds):
    out = {}
    with open(path, encoding='latin-1') as f:
        for row in csv.DictReader(f):
            tid = (row.get('TRTID10') or row.get('tractid') or '').strip()
            if not tid.startswith(NYC_PREFIXES):
                continue
            try:
                pop = float(row[pop_col] or 0)
                inc = float(row[inc_col]) if row[inc_col] else None
            except ValueError:
                continue
            cat = classify(inc, thresholds)
            out[tid] = {'pop': pop, 'inc': inc, 'cat': cat,
                        'borough': BOROUGHS[tid[:5]]}
    return out


tracts_1970 = load_year(F_1970,
                        'POP70SP1', 'INCPC70', T_1970)
tracts_2019 = load_year(F_2019, 'pop19', 'incpc19', T_2019)

print(f'NYC tracts 1970: {len(tracts_1970)}, 2015-19: {len(tracts_2019)}')


def summarize(tracts):
    by_cat = defaultdict(float)
    by_boro_cat = defaultdict(lambda: defaultdict(float))
    total = 0.0
    classified = 0.0
    for t in tracts.values():
        if t['pop'] <= 0:
            continue
        total += t['pop']
        if t['cat'] is None:
            continue
        classified += t['pop']
        by_cat[t['cat']] += t['pop']
        by_boro_cat[t['borough']][t['cat']] += t['pop']
    shares = {c: by_cat[c] / classified for c in CATS}
    boro_shares = {b: {c: by_boro_cat[b][c] / max(sum(by_boro_cat[b].values()), 1)
                        for c in CATS} for b in BOROUGHS.values()}
    boro_pop = {b: sum(by_boro_cat[b].values()) for b in BOROUGHS.values()}
    return {'total_pop': total, 'classified_pop': classified,
            'pop_by_cat': dict(by_cat), 'shares': shares,
            'boro_shares': boro_shares, 'boro_pop': boro_pop}


s1970 = summarize(tracts_1970)
s2019 = summarize(tracts_2019)

# Per capita income distribution at tract level (for histogram)
def hist(tracts, dollars_label):
    arr = []
    for t in tracts.values():
        if t['pop'] > 0 and t['inc'] is not None:
            arr.append({'pop': t['pop'], 'inc': t['inc'], 'cat': t['cat']})
    return arr


payload = {
    'meta': {
        'metro_pci_1970_nominal': round(metro_pci_1970, 0),
        'thresholds_1970_dollars': {k: round(v, 0) for k, v in T_1970.items()},
        'thresholds_2019_dollars': {k: round(v, 0) for k, v in T_2019.items()},
        'pce_1970': PCE_1970, 'pce_2019': PCE_2019,
        'pce_multiplier_1970_to_2019': PCE_TO_2019,
        'cbsa': NY_CBSA, 'nyc_counties': NYC_PREFIXES,
        'data_source_1970': 'Brown LTDB Standard Sample, 1970 (2010 tract boundaries)',
        'data_source_recent': 'Brown LTDB Standard Sample, ACS 2015-2019 (2010 tract boundaries)',
    },
    'summary_1970': s1970,
    'summary_2019': s2019,
    'tracts_1970': hist(tracts_1970, '1970'),
    'tracts_2019': hist(tracts_2019, '2019'),
}

with open(os.path.join(OUT, 'data.json'), 'w') as f:
    json.dump(payload, f)

print('--- 1970 shares ---')
for c in CATS: print(f'  {c}: {s1970["shares"][c]*100:.1f}%')
print('--- 2015-19 shares ---')
for c in CATS: print(f'  {c}: {s2019["shares"][c]*100:.1f}%')
print('total pop 1970:', round(s1970['total_pop']))
print('total pop 2015-19:', round(s2019['total_pop']))
