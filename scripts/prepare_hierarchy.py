"""Build ABS 2021 lookup, physical polygon areas, and display shapes."""
from pathlib import Path
import argparse,json,hashlib
import geopandas as gpd
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--boundaries',required=True);a=p.parse_args()
 data=ROOT/'data';codes=set(pd.read_parquet(data/'annual.parquet').SA2_CODE_2021)
 g=gpd.read_file(a.boundaries);g['SA2_CODE_2021']=g.SA2_CODE21.astype(str);g=g[g.SA2_CODE_2021.isin(codes)].to_crs(3577)
 assert set(g.SA2_CODE_2021)==codes
 g['area_km2']=g.geometry.area/1e6
 for level in ['SA3','SA4']:
  g[level+'_CODE_2021']=g[level+'_CODE21'].astype(str);g[level+'_NAME_2021']=g[level+'_NAME21']
 g['Australia_CODE_2021']='AUS';g['Australia_NAME_2021']='Australia'
 columns=['SA2_CODE_2021','area_km2','SA3_CODE_2021','SA3_NAME_2021','SA4_CODE_2021','SA4_NAME_2021']
 g[columns].to_parquet(data/'hierarchy.parquet',index=False)
 xmin,ymin,xmax,ymax=g.total_bounds;scale=min(910/(xmax-xmin),600/(ymax-ymin))
 def ring(coords):return 'M'+'L'.join(f'{20+(x-xmin)*scale:.1f},{620-(y-ymin)*scale:.1f}' for x,y,*_ in coords)+'Z'
 def path(geom):
  polys=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
  return ''.join(ring(p.exterior.coords)+''.join(ring(r.coords) for r in p.interiors) for p in polys if p.geom_type=='Polygon')
 for level in ['SA3','SA4','Australia']:
  key=level+'_CODE_2021';name=level+'_NAME_2021'
  parts=g[[key,name,'geometry']].dissolve(by=key,aggfunc='first');parts.geometry=parts.geometry.simplify(500,preserve_topology=True)
  features=[{'code':str(code),'name':r[name],'state':'Australia' if level=='Australia' else '', 'path':path(r.geometry)} for code,r in parts.iterrows()]
  (data/f'map_{level}.json').write_text(json.dumps({'width':950,'height':640,'features':features},separators=(',',':')))
  print(level,len(features))
 manifest=json.loads((data/'manifest.json').read_text())
 for f in [data/'hierarchy.parquet']+list(data.glob('map_*.json')):manifest['files'][f.name]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 manifest['aggregation']={'source':'ABS 2021 SA2 hierarchy from original boundary file','weights':'Full SA2 polygon area in EPSG:3577','method':'Area-weighted mean of published calibrated SA2 values; not re-extracted grid values or population-weighted exposure','levels':['SA2','SA3','SA4','Australia']}
 (data/'manifest.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
