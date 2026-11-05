"""Read-only access to the frozen, audited release. No external database."""
from pathlib import Path
import io, json, zipfile
import pandas as pd
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
def load_data(frequency):
 if frequency not in ('monthly','annual'): raise ValueError('Unknown frequency')
 return pd.read_parquet(DATA/f'{frequency}.parquet')
def value_columns(frequency):
 return ('pm25_calibrated_monthly','acag_pm25_area_weighted') if frequency=='monthly' else ('pm25_calibrated_annual','pm25_acag_annual')
def snapshot(df,frequency,year,month,mode,source,baseline_year,baseline_month):
 calibrated,raw=value_columns(frequency); col=calibrated if source=='Calibrated' else raw
 rows=df[df.year.eq(year)]
 if frequency=='monthly': rows=rows[rows.month.eq(month)]
 rows=rows.copy(); rows['display_value']=rows[col]
 if mode=='Calibration adjustment': rows['display_value']=rows[calibrated]-rows[raw]
 if mode=='Change over time':
  before=df[df.year.eq(baseline_year)]
  if frequency=='monthly': before=before[before.month.eq(baseline_month)]
  before=before.set_index('SA2_CODE_2021')[col]
  rows['display_value']=rows[col]-rows.SA2_CODE_2021.map(before)
 return rows

def subset_zip(df,frequency,scope,start,end,manifest):
 if start>end: raise ValueError('Start year must not exceed end year')
 rows=df[df.year.between(start,end)]
 if scope!='All Australia': rows=rows[rows.STATE_NAME.eq(scope)]
 if rows.empty: raise ValueError('No data in selection')
 buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr(f'pm25_{frequency}_{start}_{end}.csv',rows.to_csv(index=False))
  metadata={'release':manifest['release'],'units':'µg/m³','scope':scope,'start_year':start,'end_year':end,'rows':len(rows),'source':manifest['source_files'][frequency],'note':'CSV reserialized from lossless Parquet; exact original CSV available in full-release download.'}
  z.writestr('metadata.json',json.dumps(metadata,indent=2))
  z.writestr('README.txt','Historical research estimates. Fixed 2021 SA2 boundaries. Physical-area averages, not population weighted. Annual means use exactly 12 equal-weight months. Validation RMSE is not individual uncertainty.\nACAG: https://www.satpm.org/v6-gl-03\nNAPMD: https://doi.org/10.17605/OSF.IO/JXD98\nRedistribution terms and publisher citation must be confirmed before public release.\n')
 return buf.getvalue(),len(rows)

def aggregate_data(df,frequency,level):
 """Aggregate published SA2 estimates; never average RMSE or monitor counts."""
 if level=='SA2': return df.copy()
 if level not in ('SA3','SA4','Australia'): raise ValueError('Unknown geography')
 lookup=pd.read_parquet(DATA/'hierarchy.parquet')
 if level=='Australia': lookup=lookup.assign(Australia_CODE_2021='AUS',Australia_NAME_2021='Australia')
 joined=df.merge(lookup,on='SA2_CODE_2021',how='left',validate='many_to_one')
 if joined.area_km2.isna().any() or (joined.area_km2<=0).any():raise ValueError('Invalid aggregation areas')
 code,name=level+'_CODE_2021',level+'_NAME_2021';keys=[code,name,'year']+(['month'] if frequency=='monthly' else [])
 cal,raw=value_columns(frequency)
 joined['_cal']=joined[cal]*joined.area_km2;joined['_raw']=joined[raw]*joined.area_km2
 out=joined.groupby(keys,as_index=False).agg(_cal=('_cal','sum'),_raw=('_raw','sum'),area_km2=('area_km2','sum'),n_sa2=('SA2_CODE_2021','nunique'))
 out[cal]=out.pop('_cal')/out.area_km2;out[raw]=out.pop('_raw')/out.area_km2
 out[f'pm25_correction_{frequency}']=out[cal]-out[raw]
 out=out.rename(columns={code:'SA2_CODE_2021',name:'SA2_NAME_2021'}) # Internal map/snapshot interface; rename on export.
 out['STATE_NAME']='Australia' if level=='Australia' else 'ABS 2021 '+level
 out['geography_level']=level;out['aggregation_method']='SA2-polygon-area-weighted mean of published SA2 estimates'
 return out

def export_area(df,level):
 if level=='SA2': return df
 return df.rename(columns={'SA2_CODE_2021':'area_code','SA2_NAME_2021':'area_name'}).drop(columns=['STATE_NAME'])


def shared_map_scale(df,frequency,year,month,mode,baseline_year=2011,baseline_month=1):
 """One scale across both products for a given geography, period and view."""
 if mode=='Concentration':
  cal,raw=value_columns(frequency)
  rows=df[df.year.eq(year)]
  if frequency=='monthly': rows=rows[rows.month.eq(month)]
  return 0.0,max(float(rows[[cal,raw]].max().max()),0.01)
 if mode=='Change over time':
  changes=[snapshot(df,frequency,year,month,mode,source,baseline_year,baseline_month).display_value.abs().max() for source in ['Calibrated','Raw ACAG']]
  limit=max(float(max(changes)),0.01)
 else:
  limit=max(float(snapshot(df,frequency,year,month,mode,'Calibrated',baseline_year,baseline_month).display_value.abs().max()),0.01)
 return -limit,limit
