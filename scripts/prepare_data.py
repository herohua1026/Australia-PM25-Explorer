"""Prepare portable, lossless data and simplified display-only geometry."""
import argparse, hashlib, json, zipfile
from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,required=True); p.add_argument('--boundaries',type=Path,required=True); a=p.parse_args()
 out=ROOT/'data'; out.mkdir(exist_ok=True)
 audit=json.loads((a.source/'Product_Export_Audit.json').read_text())
 manifest={'release':'ACAG-v16.6-audited','model':'M7','period':[2011,2024],'units':'µg/m³','boundary_vintage':2021,'source_files':{},'files':{}}
 for freq,rows in [('monthly',412272),('annual',34356)]:
  src=a.source/f'pm25_sa2_{freq}_calibrated.csv'
  expected=audit[f'{freq}_sha256']; assert sha(src)==expected, f'{freq} source hash differs from verified release'
  df=pd.read_csv(src,dtype={'SA2_CODE_2021':str}); keys=['SA2_CODE_2021','year']+(['month'] if freq=='monthly' else [])
  assert len(df)==rows and not df.duplicated(keys).any()
  df.to_parquet(out/f'{freq}.parquet',index=False,compression='zstd')
  manifest['source_files'][freq]={'name':src.name,'sha256':expected,'rows':len(df)}
  if freq=='annual': names=df[['SA2_CODE_2021','SA2_NAME_2021','STATE_NAME','region_class']].drop_duplicates()
  with zipfile.ZipFile(out/f'{freq}_product.zip','w',zipfile.ZIP_DEFLATED) as z:
   z.write(src,src.name)
   z.writestr('README.txt','Australian calibrated PM2.5 research product, ACAG v16.6 audited, M7.\nUnits: micrograms per cubic metre. Fixed 2021 SA2 boundaries.\nPhysical-area averages, not population-weighted. Annual values are equal means of exactly 12 months.\nHistorical estimates, not live readings or AQI. Validation RMSE is not an individual confidence interval.\nSource ACAG: https://www.satpm.org/v6-gl-03\nMonitoring: NAPMD https://doi.org/10.17605/OSF.IO/JXD98\nPublisher citation and redistribution terms must be confirmed before public release.\nSource CSV SHA256: '+expected+'\n')
 geo=gpd.read_file(a.boundaries); geo['SA2_CODE_2021']=geo.SA2_CODE21.astype(str)
 geo=geo[geo.SA2_CODE_2021.isin(names.SA2_CODE_2021)].copy().to_crs(3577)
 assert set(geo.SA2_CODE_2021)==set(names.SA2_CODE_2021)
 geo['geometry']=geo.geometry.simplify(500,preserve_topology=True)
 xmin,ymin,xmax,ymax=geo.total_bounds; width=950; height=640; scale=min((width-40)/(xmax-xmin),(height-40)/(ymax-ymin))
 def ring(coords):
  return 'M'+'L'.join(f'{20+(x-xmin)*scale:.1f},{height-20-(y-ymin)*scale:.1f}' for x,y,*_ in coords)+'Z'
 def path(g):
  polys=list(g.geoms) if g.geom_type=='MultiPolygon' else [g]
  return ''.join(ring(poly.exterior.coords)+''.join(ring(r.coords) for r in poly.interiors) for poly in polys if poly.geom_type=='Polygon')
 info=names.set_index('SA2_CODE_2021'); shapes=[]
 for _,r in geo.iterrows():
  code=r.SA2_CODE_2021; shapes.append({'code':code,'name':info.loc[code,'SA2_NAME_2021'],'state':info.loc[code,'STATE_NAME'],'path':path(r.geometry)})
 (out/'map.json').write_text(json.dumps({'width':width,'height':height,'features':shapes},separators=(',',':')))
 for name in ['Product_Export_Audit.json','Interpretation_and_Limitations.json','Table3_Model_performance_summary.csv']:
  (out/name).write_bytes((a.source/name).read_bytes())
 for file in out.iterdir():
  if file.name!='manifest.json': manifest['files'][file.name]={'bytes':file.stat().st_size,'sha256':sha(file)}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps({f:v['bytes'] for f,v in manifest['files'].items()},indent=2))
if __name__=='__main__': main()
