"""Australia PM2.5 Explorer — read-only Streamlit app."""
import calendar, hashlib, json, os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from data_access import DATA, ROOT, load_data, snapshot, subset_zip, value_columns, aggregate_data, export_area, shared_map_scale

st.set_page_config(page_title='Australia PM₂.₅ Explorer',page_icon='🌏',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
header[data-testid="stHeader"],#MainMenu,footer{display:none!important}
.stApp{background:#f5f7f9;color:#172e43}.block-container{max-width:1540px;padding:1rem 1.6rem 1rem!important}
[data-testid="stVerticalBlock"]{gap:.55rem}[data-testid="stHorizontalBlock"]{gap:1rem}
h1,h2,h3{color:#152d42;letter-spacing:-.03em;padding:0!important;margin:0!important}h1{font-size:1.85rem!important}h3{font-size:1.12rem!important}
[data-testid="stMetricValue"]{font-size:1.55rem;color:#086f76}[data-testid="stVerticalBlockBorderWrapper"]{background:white;border-radius:10px}
[data-testid="stMarkdownContainer"] p{margin-bottom:0;font-size:.88rem} [data-testid="stCaptionContainer"] p{font-size:.75rem;line-height:1.4}
[data-baseweb="select"]>div{min-height:36px;background:#fff;font-size:13px}[data-testid="stWidgetLabel"] p{font-size:12px}
[data-testid="stRadio"] [role="radiogroup"]{gap:5px;flex-wrap:nowrap;overflow-x:auto;padding:3px 0 6px}[data-testid="stRadio"] label{white-space:nowrap;background:#edf3f5;border:1px solid #d9e4e8;border-radius:6px;padding:5px 10px;margin:0;font-size:12px}
[data-testid="stRadio"] label:has(input:checked){background:#d9eeed;border-color:#138387}
[data-testid="stTabs"] [role="tablist"]{gap:24px;height:37px} [data-testid="stTabs"] button{font-size:13px;font-weight:600}
button[kind="primary"]{background:#087e82;border-radius:6px}[data-testid="stDownloadButton"] button{min-height:36px;border-radius:6px;font-size:13px}
.brand{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #dce5e9;padding:0 0 12px;margin-bottom:7px;font-size:32px;font-weight:750;line-height:1.25}.brand span{font-size:12px;color:#176a70;background:#e1f0f0;border-radius:6px;padding:5px 11px;white-space:nowrap}
.map-heading{font-size:18px;font-weight:750;line-height:1.25;padding:10px 0 12px}.annual-label{font-size:12px;color:#627685;padding:10px 8px}.sub{color:#526779;font-size:14px;padding-top:5px;padding-bottom:5px}.coverage{display:flex;align-items:center;justify-content:space-between;gap:12px;border:1px solid #d7e2e7;border-radius:7px;background:#fff;padding:9px 14px;margin:4px 0 8px;font-size:12px;color:#5a6f7e}.coverage strong{color:#203747;margin-left:8px;font-weight:650}
.area-title{font-size:20px;font-weight:750;color:#172f44;line-height:1.2;margin:2px 0 4px}.area-state{font-size:11px;color:#71828e;letter-spacing:.4px}.reading{display:flex;align-items:baseline;justify-content:space-between;background:#e8f3f3;border-radius:7px;padding:9px 12px;margin:7px 0;color:#175f66;font-size:12px}.reading strong{font-size:23px;white-space:nowrap}.comparison{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:#596d7b}.comparison b{color:#213e52}.foot{border-top:1px solid #dce5e9;margin-top:10px;padding-top:10px;color:#5d7181;font-size:11px}

[role="tabpanel"]:has(#download-the-calibrated-product){padding-top:16px}
[role="tabpanel"]:has(#download-the-calibrated-product) [data-testid="stVerticalBlock"]{gap:1rem}
[role="tabpanel"]:has(#download-the-calibrated-product) h3{margin:0 0 10px!important;line-height:1.45}
[role="tabpanel"]:has(#download-the-calibrated-product) [data-testid="stMarkdownContainer"] p{line-height:1.65;margin-bottom:8px}
[role="tabpanel"]:has(#download-the-calibrated-product) [data-testid="stCaptionContainer"] p{line-height:1.6;margin-bottom:10px}
[role="tabpanel"]:has(#download-the-calibrated-product) [data-testid="stDownloadButton"],[role="tabpanel"]:has(#download-the-calibrated-product) [data-testid="stLinkButton"]{margin-top:6px}
.trend-heading{margin-top:20px;margin-bottom:8px;font-size:15px;font-weight:700;line-height:1.4}
.about-intro{width:100%;max-width:none;padding:12px 0 4px}
[role="tabpanel"]:has(.about-intro) [data-testid="stMarkdownContainer"] p,[role="tabpanel"]:has(.about-intro) [data-testid="stMarkdownContainer"] li{text-align:justify;text-align-last:left;hyphens:auto;overflow-wrap:break-word}
.about-intro h3{margin:0 0 14px!important;line-height:1.4}
.about-intro h4{margin:22px 0 10px;font-size:1rem;line-height:1.4}
[data-testid="stMarkdownContainer"] .about-intro p{margin:0 0 16px;font-size:.9rem;line-height:1.7}
.author-credit{text-align:right;margin-top:24px;padding-top:16px;border-top:1px solid #dce5e9;font-size:13px;line-height:1.7;color:#526779}.author-credit a{color:#087e82;overflow-wrap:anywhere}
@media(max-width:700px){[data-testid="stRadio"] [role="radiogroup"]{flex-wrap:wrap;overflow:visible}.block-container{padding:.75rem!important}.brand{font-size:23px}.brand span{font-size:10px}h1{font-size:1.45rem!important}.coverage{flex-wrap:wrap;gap:4px;font-size:10px;padding:8px}.coverage strong{margin-left:3px}.sub{font-size:12px}[data-testid="stHorizontalBlock"]{gap:.5rem}[data-testid="stHorizontalBlock"]:not(:has([data-testid="stPlotlyChart"])):has(> [data-testid="stColumn"] [data-testid="stSelectbox"]) {flex-wrap:wrap!important}[data-testid="stHorizontalBlock"]:not(:has([data-testid="stPlotlyChart"])):has(> [data-testid="stColumn"] [data-testid="stSelectbox"])> [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important;width:calc(50% - .5rem)!important}}
</style>''',unsafe_allow_html=True)

@st.cache_resource
def release():
 m=json.loads((DATA/'manifest.json').read_text())
 for name,info in m['files'].items():
  if hashlib.sha256((DATA/name).read_bytes()).hexdigest()!=info['sha256']: raise ValueError(f'Release integrity check failed: {name}')
 return m,json.loads((DATA/'map.json').read_text())
@st.cache_data
def dataset(freq): return load_data(freq)
@st.cache_data
def geography_data(freq,level): return aggregate_data(dataset(freq),freq,level)
@st.cache_data
def geography_shapes(level): return json.loads((DATA/('map.json' if level=='SA2' else f'map_{level}.json')).read_text())
@st.cache_data(max_entries=6)
def download_subset(freq,scope,start,end): return subset_zip(dataset(freq),freq,scope,start,end,manifest)

manifest,shapes=release()
map_component=components.declare_component('pm25_area_map',path=str(ROOT/'frontend/map'))
st.markdown('<div class="brand">◈ &nbsp; Australia PM₂.₅ Explorer <span>2011–2024</span></div>',unsafe_allow_html=True)
st.markdown('<div class="sub">Monthly and annual calibrated PM₂.₅ estimates by SA2</div>',unsafe_allow_html=True)
explore,downloads,methods=st.tabs(['Explore','Downloads','About the data'])

with explore:
 st.markdown('<div class="coverage"><span>Coverage<strong>2,454 SA2 areas</strong></span><span>Period<strong>2011–2024</strong></span><span>Source<strong>ACAG + Australian monitoring</strong></span></div>',unsafe_allow_html=True)
 left,right=st.columns([2.05,1],gap='small')
 with left:
  map_card=st.container(border=True)
 with map_card:
  heading,views=st.columns([1,2.4],gap='small')
  heading.markdown('<div class="map-heading">PM₂.₅ concentration</div>',unsafe_allow_html=True)
  mode=views.radio('View',['Concentration','Change over time','Calibration adjustment'],horizontal=True,label_visibility='collapsed',key='view')
  controls=st.columns([1,1,1,1.2])
  frequency=controls[0].selectbox('Frequency',['Annual','Monthly'],key='frequency').lower()
  if 'year' not in st.session_state: st.session_state.year=2024
  year=controls[1].selectbox('End year' if mode=='Change over time' else 'Year',list(range(2011,2025)),key='year')
  month=1
  if frequency=='monthly': month=controls[2].selectbox('End month' if mode=='Change over time' else 'Month',list(range(1,13)),format_func=lambda x:calendar.month_name[x],key='month')
  else: controls[2].markdown('<div class="annual-label">All 12 months</div>',unsafe_allow_html=True)
  source=controls[3].selectbox('Product',['Calibrated','Raw ACAG'],disabled=mode=='Calibration adjustment',key='product')
 with right:
  area_card=st.container(border=True)
 with area_card:
  st.subheader('Selected area')
  level=st.selectbox('Geography level',['SA2','SA3','SA4','Australia'],format_func=lambda x:'Whole Australia' if x=='Australia' else x,key='geography_level')
  df=geography_data(frequency,level)
  names=df[['SA2_CODE_2021','SA2_NAME_2021','STATE_NAME']].drop_duplicates().sort_values('SA2_NAME_2021')
  codes=names.SA2_CODE_2021.tolist();labels=names.set_index('SA2_CODE_2021').apply(lambda r:f'{r.SA2_NAME_2021} · {r.STATE_NAME}' if level=='SA2' else r.SA2_NAME_2021,axis=1).to_dict()
  if 'pending_area' in st.session_state: st.session_state.area=st.session_state.pop('pending_area')
  if st.session_state.get('area') not in codes:
   matching=names.loc[names.SA2_NAME_2021.eq('Batemans Bay - South'),'SA2_CODE_2021']
   st.session_state.area=matching.iloc[0] if len(matching) else codes[0]
  selected=st.selectbox('Choose '+('area' if level=='Australia' else level),codes,format_func=lambda x:labels[x],key='area',disabled=level=='Australia')
  active_shapes=geography_shapes(level)
 with map_card:
  by,bm=2011,1
  if mode=='Change over time':
   basecols=st.columns(2)
   if st.session_state.get('baseline_year',2011)>year: st.session_state.baseline_year=year
   by=basecols[0].selectbox('Start year',list(range(2011,year+1)),key='baseline_year')
   if frequency=='monthly':
    months=list(range(1,(month if by==year else 12)+1))
    if st.session_state.get('baseline_month',1) not in months: st.session_state.baseline_month=months[-1]
    bm=basecols[1].selectbox('Start month',months,format_func=lambda x:calendar.month_abbr[x],key='baseline_month')
  snap=snapshot(df,frequency,year,month,mode,source,by,bm); cal,raw=value_columns(frequency)
  period=f'{calendar.month_name[month]} {year}' if frequency=='monthly' else str(year)
  baseline=f'{calendar.month_name[bm]} {by}' if frequency=='monthly' else str(by)
  if mode=='Change over time': st.caption(f'{source}: {period} minus {baseline} · negative = decrease')
  elif mode=='Calibration adjustment': st.caption(f'{period} · calibrated minus raw ACAG')
  else: st.caption(f'{period} · {source} · physical-area averages')
  vals=snap.set_index('SA2_CODE_2021').display_value; diverge=mode!='Concentration'
  scale_min,scale_max=shared_map_scale(df,frequency,year,month,mode,by,bm)
  picked=map_component(shapes=active_shapes,values=vals.to_dict(),selected=selected,min=scale_min,max=scale_max,diverging=diverge,label='Difference' if diverge else 'PM₂.₅',scale_note='Symmetric adjustment scale' if mode=='Calibration adjustment' else 'Shared raw / calibrated scale',key='area_map',default=None)
  if picked and picked.get('nonce')!=st.session_state.get('last_map_nonce'):
   st.session_state.last_map_nonce=picked['nonce']
   if picked['code'] in codes and picked['code']!=selected:
    st.session_state.pending_area=picked['code'];st.rerun()
  st.caption('Simplified display boundaries · concentration uses a shared 0–15 µg/m³ scale, expanding when either product exceeds 15. Change and adjustment scales remain symmetric around zero.')
 with right:
  import html
  row=snap[snap.SA2_CODE_2021.eq(selected)].iloc[0]
  history=df[df.SA2_CODE_2021.eq(selected)].sort_values(['year']+(['month'] if frequency=='monthly' else []))
  with area_card:
   st.markdown(f'<div class="area-state">{html.escape(str(row.STATE_NAME))}</div><div class="area-title">{html.escape(row.SA2_NAME_2021)}</div>',unsafe_allow_html=True)
   st.caption(f'SA2 {selected} · {row.region_class}' if level=='SA2' else f'{level} {selected} · {int(row.n_sa2):,} constituent SA2s')
   reading=f'{row.display_value:+.2f}' if diverge else f'{row.display_value:.2f}'
   st.markdown(f'<div class="reading"><span>{html.escape(mode if diverge else frequency.title()+" PM₂.₅")}</span><strong>{reading} <small style="font-size:12px">µg/m³</small></strong></div><div class="comparison"><span>Calibrated <b>{row[cal]:.2f}</b></span><span>Raw ACAG <b>{row[raw]:.2f}</b></span></div>',unsafe_allow_html=True)
   st.markdown('<div class="trend-heading">Change over time</div>',unsafe_allow_html=True)
   dates=pd.to_datetime(history[['year','month']].assign(day=1)) if frequency=='monthly' else pd.to_datetime(history.year.astype(str)+'-01-01')
   fig=go.Figure()
   fig.add_trace(go.Scatter(x=dates,y=history[cal],name='Calibrated',line=dict(color='#087e82',width=2.5)))
   fig.add_trace(go.Scatter(x=dates,y=history[raw],name='Raw ACAG',line=dict(color='#96a3ad',dash='dash',width=2)))
   fig.update_layout(height=210,margin=dict(l=4,r=4,t=40,b=8),paper_bgcolor='white',plot_bgcolor='white',legend=dict(orientation='h',y=1.04,yanchor='bottom',x=0,font=dict(size=10)),font=dict(color='#425a6d',size=10),yaxis=dict(title='µg/m³',gridcolor='#edf1f4',rangemode='tozero'),xaxis=dict(showgrid=False),hovermode='x unified')
   st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
   st.caption('Area average · Not population weighted' if level=='SA2' else 'Area-weighted summary of SA2 estimates · Not population weighted')
   with st.expander('Monitoring support'):
    if level=='SA2':
     st.caption(f'{row.regional_station_count:.0f} stations in this remoteness class; LOSO RMSE {row.regional_cv_rmse:.2f} µg/m³. This is not an individual-area uncertainty interval.')
     if row.sparse_monitor_support: st.warning('Limited monitoring support in this class.')
    else:
     st.caption('These are area-weighted summaries of the published SA2 estimates, using full polygon areas. They are not separately calibrated or independently validated at this geography. No aggregate RMSE is inferred from SA2 indicators.')
  with st.container(border=True):
   st.subheader('↓ Download the product')
   dl_scope=st.selectbox('Geography',['All Australia','Selected area'],key='quick_scope')
   dl_freq=st.selectbox('Frequency',['Monthly','Annual'],key='quick_frequency').lower()
   st.caption('2011–2024 · Original SA2 CSV + metadata (ZIP)' if dl_scope=='All Australia' else f'2011–2024 · {level} summary CSV')
   if dl_scope=='All Australia':
    file=DATA/f'{dl_freq}_product.zip'
    base=os.environ.get('GITHUB_RELEASE_BASE_URL','').rstrip('/')
    if base.startswith('https://github.com/') and '/releases/download/' in base: st.link_button('Download data',base+'/'+file.name,use_container_width=True,type='primary')
    else: st.download_button('Download data',file.read_bytes(),file_name=file.name,mime='application/zip',use_container_width=True,type='primary',key='quick_download')
   else:
    export=geography_data(dl_freq,level);export=export_area(export[export.SA2_CODE_2021.eq(selected)],level)
    st.download_button('Download data',export.to_csv(index=False),file_name=f'pm25_{level}_{selected}_{dl_freq}.csv',mime='text/csv',use_container_width=True,type='primary',key='quick_download_area')
   st.caption('More filters and complete metadata in Downloads.')
with downloads:
 st.subheader('Download the calibrated product')
 st.write('Choose the complete original release or create a smaller selection. Concentrations are in µg/m³.')
 a,b=st.columns(2)
 for col,freq in [(a,'monthly'),(b,'annual')]:
  with col,st.container(border=True):
   st.subheader(f'{freq.title()} · all Australia')
   file=DATA/f'{freq}_product.zip';st.write(f'{manifest["source_files"][freq]["rows"]:,} rows · {file.stat().st_size/1e6:.1f} MB ZIP')
   st.caption('Original CSV, unchanged, with README and source checksum. 2011–2024.')
   base=os.environ.get('GITHUB_RELEASE_BASE_URL','').rstrip('/')
   if base.startswith('https://github.com/') and '/releases/download/' in base:
    st.link_button('↓ Download complete release',base+'/'+file.name,use_container_width=True)
   else: st.download_button('↓ Download complete release',file.read_bytes(),file_name=file.name,mime='application/zip',key=f'dl_{freq}',use_container_width=True)
 st.divider();st.subheader('Create a selection')
 with st.form('subset'):
  c=st.columns(3);freq=c[0].selectbox('Download frequency',['monthly','annual']);scope=c[1].selectbox('Geography',['All Australia']+sorted(dataset('annual').STATE_NAME.unique()));years=c[2].slider('Year range',2011,2024,(2011,2024))
  submitted=st.form_submit_button('Prepare download',type='primary')
 if submitted:
  with st.spinner('Preparing CSV and metadata…'):
   data,n=download_subset(freq,scope,*years)
  st.session_state.prepared=(data,n,freq,scope,years)
 if 'prepared' in st.session_state:
  data,n,freq,scope,years=st.session_state.prepared;st.success(f'Ready: {scope}, {years[0]}–{years[1]}, {freq}, {n:,} rows.')
  st.download_button('↓ Save prepared ZIP',data,file_name=f'pm25_{freq}_{years[0]}_{years[1]}_subset.zip',mime='application/zip')
 st.caption('Release '+manifest['release']+' · See About the data for source references, methods and limitations.')
with methods:
 st.markdown("""<section class="about-intro">
<h3>A calibrated research product</h3>
<p>Monthly ACAG V6.GL.03 estimates [2] were calibrated against 19,932 station-month observations from 230 Australian monitoring stations, using the National Air Pollution Monitoring Database (NAPMD) [3].</p>
<h4>Calibration model</h4>
<p>The calibration model adjusts ACAG PM₂.₅ estimates using their relationship with ground-monitoring observations. It combines a national intercept and concentration slope with adjustments for each remoteness–season combination and calendar year.</p>
<p>These adjustments are regularised to reduce unstable estimates where observations are sparse. The model was selected by comparing predictions at monitoring stations withheld from model fitting, then fitted to the full monitoring dataset to produce the calibrated estimates [1].</p>
</section>""",unsafe_allow_html=True)
 st.divider()
 c=st.columns(3);c[0].metric('Raw LOSO RMSE','3.438 µg/m³');c[1].metric('Calibrated LOSO RMSE','3.246 µg/m³');c[2].metric('RMSE reduction','5.60%')
 st.caption('Performance figures shown here are from the audited v16.6 release; see the downloadable release manifest for provenance.')
 st.markdown('''- **Geography:** fixed 2021 SA2 boundaries [4]; spherical physical-area weighting, not population weighting (see exactextract operations [5]).
- **SA3, SA4 and Australia:** summaries of published SA2 estimates weighted by full polygon area in EPSG:3577, using the ABS 2021 hierarchy [4]. These aggregations are calculated by this app. They are not fresh grid extractions, population-weighted estimates or separately validated products. Original complete downloads remain at SA2 level; selected-area downloads use the chosen geography.
- **Annual summaries:** equal means of exactly 12 monthly concentrations. The primary validation was at station-month level.
- **Prediction rule:** calibrated values are floored at zero, including primary validation predictions.
- **Scope:** historical estimates, not live air-quality readings or an AQI. Calendar fire-season labels do not establish smoke at a particular site.
- **Reliability:** remoteness-class RMSE describes held-out station performance. It is not a confidence interval for an individual SA2. Very Remote validation uses seven stations; Remote-area RMSE did not improve.
- **Independence:** local cross-validation evaluates incremental calibration conditional on the published ACAG input; upstream monitor independence is unverified.
- **Display geometry:** simplified to make the map fast; concentrations and downloads preserve the audited product.''')
 st.markdown('### References')
 st.markdown("""1. **Calibration study:** *Calibration of satellite-derived PM₂.₅ across monitoring-sparse Australia: reducing structured residual error for fine-area exposure assessment.* DOI: **xxx-xxx-xxx-xxx** (placeholder; to be updated when available).
2. **Satellite PM₂.₅:** [ACAG / SatPM V6.GL.03 data and release documentation](https://www.satpm.org/v6-gl-03). Method reference: Shen, S., Li, C., van Donkelaar, A., Jacobs, N., Wang, C., & Martin, R. V. (2024). *Enhancing Global Estimation of Fine Particulate Matter Concentrations by Including Geophysical a Priori Information in Deep Learning.* ACS ES&T Air. [doi:10.1021/acsestair.3c00054](https://doi.org/10.1021/acsestair.3c00054).
3. **Monitoring observations:** *National Air Pollution Monitoring Database (NAPMD).* [doi:10.17605/OSF.IO/JXD98](https://doi.org/10.17605/OSF.IO/JXD98).
4. **Statistical geography:** Australian Bureau of Statistics. *Australian Statistical Geography Standard (ASGS), Edition 3 (July 2021–June 2026): Statistical Area Level 2.* [Boundaries and geographic hierarchy](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/main-structure-and-greater-capital-city-statistical-areas/statistical-area-level-2).
5. **Spatial extraction:** ISciences. *exactextract documentation: Available Operations.* [Coverage fractions, means and area weights](https://isciences.github.io/exactextract/operations.html).
""")
 st.divider()
 st.download_button('Download release manifest',json.dumps(manifest,indent=2),file_name='manifest.json',mime='application/json')
 st.markdown('<div class="author-credit"><strong>Author information</strong><br><a href="https://orcid.org/0009-0002-3336-3492" target="_blank" rel="noopener noreferrer">ORCID · 0009-0002-3336-3492</a></div>',unsafe_allow_html=True)
st.markdown('<div class="foot">ACAG v16.6 audited · Calibration model &nbsp; / &nbsp; Historical research estimates · 2021 SA2 geography &nbsp; / &nbsp; Built for open exploration</div>',unsafe_allow_html=True)
