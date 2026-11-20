"""Build presentation data from frozen evidence; no training or selection."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from bearing_diagnosis.data import load_signal
from bearing_diagnosis.signals import (prepare_signal_with_metadata, causal_bandpass,
    closed_window_envelope, spectrum, bearing_frequencies)
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'dist'
read=lambda p:json.loads((ROOT/p).read_text())
config=read('configs/experiment.json')
features_path=ROOT/'outputs/main/features_development.csv'
if not features_path.is_file():
    features_path=ROOT/'outputs/reproduction/features_development.csv'
features=pd.read_csv(features_path)
assert set(features.split_role)=={'development'}
freeze=read('results/freeze.json')
assert hashlib.sha256(features_path.read_bytes()).hexdigest()==freeze['development']['features_development.csv']
manifest=pd.read_csv(ROOT/'data/manifest.csv')
splits=pd.read_csv(ROOT/'data/splits/recordings.csv')
rows=manifest.merge(splits,on=['recording_id','group_id'],validate='one_to_one')
records=features.groupby(['recording_id','class_label'],as_index=False)[['rms','kurtosis','crest_factor']].median()
fs=float(config['fs_analysis_hz']);warmup=float(config['warmup_seconds'])
envelopes=[];waveform=None
for rid in ['IR007_0','OR007@6_0']:
    row=rows.loc[rows.recording_id.eq(rid)].iloc[0]
    assert row.split_role=='development'
    x=load_signal(ROOT,row)
    prepared,_=prepare_signal_with_metadata(x,float(row.fs_native_hz),fs,warmup_seconds=warmup,fir_taps=161)
    filtered=causal_bandpass(prepared,fs,tuple(config['envelope_band_hz']),int(config['filter_order']))
    start=int(np.ceil(warmup*fs));size=int(fs*config['window_seconds'])
    envelope=closed_window_envelope(filtered[start:start+size],int(fs*config['envelope_edge_seconds']))
    f,a=spectrum(envelope,fs);mask=f<=350
    envelopes.append({'id':rid,'rpm':float(row.rpm_used),'frequencies':bearing_frequencies(float(row.rpm_used)),
        'points':np.column_stack([f[mask],a[mask]]).round(9).tolist()})
    if waveform is None:
        waveform={'id':rid,'load_hp':int(row.load_hp),'fs_hz':fs,'duration_ms':50,
            'points':[[round(i/fs*1000,4),float(v)] for i,v in enumerate(prepared[start:start+600])]}
data={'summary':pd.read_csv(ROOT/'results/summary.csv').to_dict('records'),
    'metrics':read('results/final_metrics.json'),'bootstrap':read('results/final_bootstrap.json'),
    'selection':read('results/selection.json'),'config':config,
    'coverage':pd.read_csv(ROOT/'data/classcoverage.csv').to_dict('records'),
    'temporal':records.to_dict('records'),'envelopes':envelopes,'waveform':waveform,
    'authors':[{'name':'Mouhamedou Yahya Cheikh Med Vall','id':'25239'},{'name':"Maryeim Mohamed T'Feil",'id':'22087'}],
    'sources':{'metrics':'results/summary.csv','confusion':'results/final_metrics.json',
        'uncertainty':'results/final_bootstrap.json','temporal':str(features_path.relative_to(ROOT)),
        'spectra':'Development IR007_0 and OR007@6_0; fixed preparation and first one-second window'},
    'generated_from_freeze':hashlib.sha256((ROOT/'results/freeze.json').read_bytes()).hexdigest()}
OUT.mkdir(exist_ok=True,parents=True)
(OUT/'data.js').write_text('window.PROJECT_DATA = '+json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':'))+';\n')
print(f'Written {OUT}/data.js; 30 development recordings, 2 fixed spectra, no fitting.')
