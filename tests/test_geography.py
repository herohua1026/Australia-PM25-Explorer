import unittest,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from data_access import DATA,load_data,aggregate_data,export_area
class GeographyTests(unittest.TestCase):
 def test_hierarchy_and_national_conservation(self):
  df=load_data('annual');df=df[df.year.eq(2024)]
  lookup=pd.read_parquet(DATA/'hierarchy.parquet');joined=df.merge(lookup,on='SA2_CODE_2021')
  expected=np.average(joined.pm25_calibrated_annual,weights=joined.area_km2)
  for level,count in [('SA3',340),('SA4',89),('Australia',1)]:
   out=aggregate_data(df,'annual',level)
   self.assertEqual(len(out),count);self.assertEqual(out.n_sa2.sum(),2454)
   self.assertAlmostEqual(np.average(out.pm25_calibrated_annual,weights=out.area_km2),expected,places=12)
   shapes=json.loads((DATA/f'map_{level}.json').read_text())
   self.assertEqual(set(out.SA2_CODE_2021),{f['code'] for f in shapes['features']})
   export=export_area(out,level);self.assertIn('area_code',export);self.assertNotIn('SA2_CODE_2021',export)
 def test_single_sa3_expected_weighting(self):
  d=load_data('monthly');d=d[d.year.eq(2020)&d.month.eq(1)]
  lookup=pd.read_parquet(DATA/'hierarchy.parquet');code=lookup.SA3_CODE_2021.iloc[0]
  rows=d.merge(lookup[lookup.SA3_CODE_2021.eq(code)],on='SA2_CODE_2021')
  result=aggregate_data(d,'monthly','SA3').set_index('SA2_CODE_2021').loc[code]
  self.assertAlmostEqual(result.pm25_calibrated_monthly,np.average(rows.pm25_calibrated_monthly,weights=rows.area_km2),places=12)
 def test_app_all_geographies_and_downloads(self):
  from streamlit.testing.v1 import AppTest
  app=AppTest.from_file(str(DATA.parent/'app.py'),default_timeout=30).run()
  for level in ['SA3','SA4','Australia','SA2']:
   app.selectbox(key='geography_level').select(level).run()
   self.assertEqual(len(app.exception),0,str(app.exception))
   app.selectbox(key='quick_scope').select('Selected area').run()
   self.assertEqual(len(app.exception),0,str(app.exception))
  app.selectbox(key='year').select(2018).run()
  self.assertEqual(app.selectbox(key='year').value,2018)
  self.assertNotIn('timeline',[x.key for x in app.slider])

class ScaleTests(unittest.TestCase):
 def test_shared_scale_covers_both_products(self):
  from data_access import shared_map_scale,snapshot,value_columns
  for freq in ['annual','monthly']:
   df=load_data(freq);cal,raw=value_columns(freq)
   for mode in ['Concentration','Change over time']:
    lo,hi=shared_map_scale(df,freq,2020,1,mode,2017,1)
    for source in ['Calibrated','Raw ACAG']:
     v=snapshot(df,freq,2020,1,mode,source,2017,1).display_value
     self.assertGreaterEqual(v.min(),lo);self.assertLessEqual(v.max(),hi)
    if mode=='Change over time':self.assertEqual(lo,-hi)
 def test_endpoint_controls(self):
  from streamlit.testing.v1 import AppTest
  app=AppTest.from_file(str(DATA.parent/'app.py'),default_timeout=30).run()
  self.assertEqual(app.selectbox(key='year').label,'Year')
  app.radio(key='view').set_value('Change over time').run()
  self.assertEqual(app.selectbox(key='year').label,'End year')
  self.assertEqual(app.selectbox(key='baseline_year').label,'Start year')
  app.selectbox(key='year').select(2015).run()
  self.assertTrue(all(int(y)<=2015 for y in app.selectbox(key='baseline_year').options))
  self.assertEqual(len(app.exception),0)
