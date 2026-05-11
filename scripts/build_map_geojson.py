"""
Build a small GeoJSON for the NYC map.

Inputs:
  - data/gz_2010_36_140_00_500k.shp  (Census 2010 cartographic tracts, NY state)
  - output/data.json                  (analysis output with tract-level bands)
Output:
  - output/nyc_tracts.geojson         (NYC tracts only, with band properties)
"""
import json, os
import geopandas as gpd

DATA = os.path.join(os.path.dirname(__file__), '..', 'data')
OUT = os.path.join(os.path.dirname(__file__), '..', 'output')

gdf = gpd.read_file(os.path.join(DATA, 'gz_2010_36_140_00_500k.shp'))

# Build 11-char tract id: state(2) + county(3) + tract(6)
gdf['tid'] = gdf['STATE'].str.zfill(2) + gdf['COUNTY'].str.zfill(3) + gdf['TRACT'].str.zfill(6)
NYC = ('36005','36047','36061','36081','36085')
nyc = gdf[gdf['tid'].str.startswith(NYC)].copy()
print('NYC tracts in TIGER:', len(nyc))

# Load analysis output and key tracts by id
data = json.load(open(os.path.join(OUT, 'data.json')))

# Index 1970 and 2019 tract attributes by tract id.
# tracts arrays don't carry tid currently; rebuild from the source CSV.
import csv

def load_csv_band(path, tid_col, pop_col, inc_col, thresholds):
    out = {}
    with open(path, encoding='latin-1') as f:
        for row in csv.DictReader(f):
            tid = (row.get(tid_col) or '').strip()
            if not tid.startswith(NYC):
                continue
            tid = tid.zfill(11)
            try:
                pop = float(row[pop_col] or 0)
                inc = float(row[inc_col]) if row[inc_col] else None
            except ValueError:
                continue
            cat = None
            if inc is not None:
                t = thresholds
                if   inc < t['very_low_max']: cat = 'very_low'
                elif inc < t['low_max']:      cat = 'low'
                elif inc < t['middle_max']:   cat = 'middle'
                elif inc < t['high_max']:     cat = 'high'
                else:                         cat = 'very_high'
            out[tid] = {'pop': pop, 'inc': inc, 'cat': cat}
    return out

t1 = data['meta']['thresholds_1970_dollars']
t2 = data['meta']['thresholds_2019_dollars']

b70 = load_csv_band(os.path.join(DATA, 'nyc_metro_1970.csv'),
                    'TRTID10', 'POP70SP1', 'INCPC70', t1)
b19 = load_csv_band(os.path.join(DATA, 'nyc_2015_19.csv'),
                    'tractid', 'pop19', 'incpc19', t2)

ORDER = ['very_low','low','middle','high','very_high']

def encode_cat(c):
    return ORDER.index(c) if c in ORDER else -1

def encode_move(c1, c2):
    if c1 is None or c2 is None: return None
    i1, i2 = ORDER.index(c1), ORDER.index(c2)
    if i2 > i1: return 'up'
    if i2 < i1: return 'down'
    return 'same'

feats = []
for _, row in nyc.iterrows():
    tid = row['tid']
    r70 = b70.get(tid, {})
    r19 = b19.get(tid, {})
    props = {
        'tid': tid,
        'cat70': r70.get('cat'),
        'cat19': r19.get('cat'),
        'inc70': r70.get('inc'),
        'inc19': r19.get('inc'),
        'pop70': r70.get('pop'),
        'pop19': r19.get('pop'),
        'move':  encode_move(r70.get('cat'), r19.get('cat')),
    }
    feats.append({
        'type': 'Feature',
        'properties': props,
        'geometry': row.geometry.__geo_interface__,
    })

# Round coordinates to 5 decimals to shrink file size
def round_geom(g, n=5):
    if isinstance(g, dict):
        if 'coordinates' in g:
            def rc(x):
                if isinstance(x, (int, float)): return round(x, n)
                return [rc(y) for y in x]
            g['coordinates'] = rc(g['coordinates'])
        for v in g.values():
            if isinstance(v, dict): round_geom(v, n)
    return g

for f in feats:
    round_geom(f['geometry'], 5)

geojson = {'type': 'FeatureCollection', 'features': feats}
path = os.path.join(OUT, 'nyc_tracts.geojson')
with open(path, 'w') as f:
    json.dump(geojson, f, separators=(',', ':'))
print(f'wrote {path} ({os.path.getsize(path)/1024:.1f} KB, {len(feats)} features)')

# Quick coverage report
no70 = sum(1 for f in feats if not f['properties']['cat70'])
no19 = sum(1 for f in feats if not f['properties']['cat19'])
print(f'features missing cat70: {no70}; missing cat19: {no19}')
