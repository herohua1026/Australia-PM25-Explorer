import hashlib, io, json, sys, unittest, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from data_access import DATA,load_data,snapshot,subset_zip
class ProductTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=load_data('monthly');cls.a=load_data('annual');cls.manifest=json.loads((DATA/'manifest.json').read_text())
 def test_integrity_and_map_join(self):
  for name,info in self.manifest['files'].items(): self.assertEqual(hashlib.sha256((DATA/name).read_bytes()).hexdigest(),info['sha256'])
  geo=json.loads((DATA/'map.json').read_text());codes=[f['code'] for f in geo['features']]
  self.assertEqual(len(codes),2454);self.assertEqual(set(codes),set(self.a.SA2_CODE_2021));self.assertEqual(len(codes),len(set(codes)))
 def test_annual_reaggregation(self):
  grouped=self.m.groupby(['SA2_CODE_2021','year']).pm25_calibrated_monthly.agg(['mean','size'])
  annual=self.a.set_index(['SA2_CODE_2021','year']).pm25_calibrated_annual.reindex(grouped.index)
  self.assertTrue((grouped['size']==12).all());np.testing.assert_allclose(grouped['mean'],annual,atol=1e-12)
 def test_changes_and_adjustments(self):
  same=snapshot(self.m,'monthly',2020,1,'Change over time','Calibrated',2020,1)
  np.testing.assert_allclose(same.display_value,0)
  one=snapshot(self.a,'annual',2024,1,'Change over time','Raw ACAG',2011,1).set_index('SA2_CODE_2021')
  expected=self.a[self.a.year.eq(2024)].set_index('SA2_CODE_2021').pm25_acag_annual-self.a[self.a.year.eq(2011)].set_index('SA2_CODE_2021').pm25_acag_annual
  np.testing.assert_allclose(one.display_value,expected.reindex(one.index))
  adj=snapshot(self.m,'monthly',2020,1,'Calibration adjustment','Raw ACAG',2011,1)
  np.testing.assert_allclose(adj.display_value,adj.pm25_correction_monthly,atol=1e-12)
 def test_download_filter_and_values(self):
  data,n=subset_zip(self.a,'annual','Tasmania',2020,2021,self.manifest)
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   df=pd.read_csv(io.BytesIO(z.read('pm25_annual_2020_2021.csv')),dtype={'SA2_CODE_2021':str})
   self.assertEqual(set(df.STATE_NAME),{'Tasmania'});self.assertEqual(set(df.year),{2020,2021});self.assertEqual(n,len(df));self.assertIn('metadata.json',z.namelist())
   expected=self.a[self.a.STATE_NAME.eq('Tasmania') & self.a.year.between(2020,2021)]
   np.testing.assert_allclose(df.pm25_calibrated_annual,expected.pm25_calibrated_annual)
 def test_original_download_hash(self):
  for freq in ['annual','monthly']:
   with zipfile.ZipFile(DATA/f'{freq}_product.zip') as z:
    src=self.manifest['source_files'][freq];self.assertEqual(hashlib.sha256(z.read(src['name'])).hexdigest(),src['sha256'])
 def test_app_load_and_filters(self):
  from streamlit.testing.v1 import AppTest
  app=AppTest.from_file(str(DATA.parent/'app.py'),default_timeout=30).run()
  self.assertEqual(len(app.exception),0)
  app.selectbox(key='frequency').select('Monthly').run()
  self.assertEqual(len(app.exception),0)
  app.radio(key='view').set_value('Change over time').run()
  self.assertEqual(len(app.exception),0)
  app.radio(key='view').set_value('Calibration adjustment').run()
  self.assertEqual(len(app.exception),0)
if __name__=='__main__': unittest.main()
