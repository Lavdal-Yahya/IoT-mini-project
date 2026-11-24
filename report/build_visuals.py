"""Readable article figures from saved evidence and the same development examples.

Does not fit models or change the frozen scientific pipeline. Raw/envelope plots
replay the existing development-only figure method with the fixed configuration.
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
from bearing_diagnosis.data import load_signal
from bearing_diagnosis.signals import bearing_frequencies, causal_bandpass, closed_window_envelope, prepare_signal_with_metadata, spectrum

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'report/figures'
INK='#000814';NAVY='#003566';PRUSSIAN='#001d3d';YELLOW='#ffc300';GOLD='#ffd60a';MUTED='#41566d';LINE='#d6dfe9';PALE='#f5f7fa'
CLASSES=['healthy','inner_race','outer_race','ball'];LABELS=['Sain','Interne','Externe','Bille'];EXP=['E1','E2','E3','E4']
COLORS=[PRUSSIAN,NAVY,YELLOW,INK]
plt.rcParams.update({'font.family':'Liberation Sans','font.size':10.5,'text.color':INK,'axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':LINE,'axes.spines.top':False,'axes.spines.right':False,'grid.color':LINE,'grid.alpha':.65,'figure.facecolor':'white','axes.facecolor':PALE,'savefig.facecolor':'white','axes.titleweight':'bold','axes.titlecolor':NAVY})

def save(fig,name):
    fig.savefig(OUT/name,dpi=220);plt.close(fig)

def temporal(data):
    fig,axes=plt.subplots(1,3,figsize=(8.6,4.1),layout='constrained')
    for ax,key,title in zip(axes,['rms','kurtosis','crest_factor'],['RMS','Kurtosis de Pearson','Facteur de crête']):
        for i,cls in enumerate(CLASSES):
            vals=[r[key] for r in data['temporal'] if r['class_label']==cls]
            ax.scatter([i+(j%5-2)*.06 for j in range(len(vals))],vals,c=COLORS[i],marker=['o','D','^','s'][i],s=30,edgecolors=INK,lw=.4,zorder=3)
            ax.plot([i-.22,i+.22],[np.median(vals)]*2,color=INK,lw=1.7,zorder=4)
        ax.set_xticks(range(4),LABELS,rotation=30,ha='right');ax.set_xlim(-.5,3.5);ax.set_title(title,fontsize=11)
        ax.grid(axis='y');ax.set_axisbelow(True)
    axes[0].set_ylabel('Médiane par essai')
    save(fig,'temporal_features.png')

def spectra():
    config=json.loads((ROOT/'configs/experiment.json').read_text())
    manifest=pd.read_csv(ROOT/'data/manifest.csv');splits=pd.read_csv(ROOT/'data/splits/recordings.csv')
    selected=manifest.merge(splits,on=['recording_id','group_id'],validate='one_to_one');selected=selected[selected.split_role.eq('development')]
    fs=float(config['fs_analysis_hz']);warmup=float(config['warmup_seconds']);n=round(fs*config['window_seconds']);edge=round(fs*config['envelope_edge_seconds'])
    fig,axes=plt.subplots(4,2,figsize=(8.6,7.3),layout='constrained')
    for i,cls in enumerate(CLASSES):
        row=selected[selected.class_label.eq(cls)].sort_values('recording_id').iloc[0]
        prepared,_=prepare_signal_with_metadata(load_signal(ROOT,row),float(row.fs_native_hz),fs,warmup_seconds=warmup,fir_taps=int(config.get('fir_taps',161)))
        filtered=causal_bandpass(prepared,fs,tuple(config['envelope_band_hz']),int(config['filter_order']))
        start=int(np.ceil(warmup*fs));raw=prepared[start:start+n];env=closed_window_envelope(filtered[start:start+n],edge)
        for j,signal in enumerate([raw,env]):
            f,a=spectrum(signal,fs);ax=axes[i,j];ax.plot(f,a,color=NAVY,lw=.7);ax.set_xlim(0,fs/2 if j==0 else 600);ax.set_ylim(bottom=0);ax.grid(axis='y');ax.set_axisbelow(True);ax.tick_params(labelsize=9)
        axes[i,0].set_ylabel(LABELS[i]+'\nAmplitude',fontsize=10)
        for key,color,label in [('bpfo_hz',YELLOW,'BPFO'),('bpfi_hz',PRUSSIAN,'BPFI')]:
            axes[i,1].axvline(bearing_frequencies(float(row.rpm_used))[key],color=color,ls='--',lw=1.2,label=label)
        axes[i,1].text(.03,.92,f'{row.recording_id} · {row.rpm_used:.0f} tr/min',transform=axes[i,1].transAxes,va='top',fontsize=8.5,bbox={'facecolor':'white','edgecolor':'none','alpha':.8,'pad':1})
    axes[0,0].set_title('Vibration brute · Hann',fontsize=11);axes[0,1].set_title('Enveloppe · 2–5 kHz',fontsize=11)
    axes[0,1].legend(loc='upper right',fontsize=8.5,facecolor='white',edgecolor=LINE)
    axes[-1,0].set_xlabel('Fréquence (Hz)');axes[-1,1].set_xlabel('Fréquence (Hz)')
    save(fig,'spectra_envelope.png')

def scores(summary):
    rows=summary[summary.stage.eq('development')].set_index('experiment').loc[EXP]
    fig,ax=plt.subplots(figsize=(8.6,2.8),layout='constrained')
    values=rows.balanced_accuracy.to_numpy()*100
    ax.barh(EXP,values,color=['#8cabc6']*3+[GOLD],height=.55,edgecolor=['#8cabc6']*3+[YELLOW]);ax.invert_yaxis();ax.set_xlim(0,110);ax.set_xticks([0,25,50,75,100],[f'{n} %' for n in [0,25,50,75,100]])
    for i,v in enumerate(values):ax.text(v+1,i,f'{v:.2f}'.replace('.',',')+' %',va='center',fontsize=11,fontweight='bold' if i==3 else 'normal',color=INK)
    ax.set_xlabel('Exactitude équilibrée · poids égal par essai');ax.grid(axis='x');ax.set_axisbelow(True)
    ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
    save(fig,'development_scores.png')

def confusion(metrics):
    fig,axes=plt.subplots(1,2,figsize=(8.6,3.7),layout='constrained')
    cmap=LinearSegmentedColormap.from_list('navy',['#ffffff','#e6ebf0','#8cabc6',NAVY])
    for ax,key,title in zip(axes,['raw_window','record'],['E4 · 92 fenêtres brutes','E4 · 10 essais agrégés']):
        m=np.array(metrics['E4'][key]['confusion']);ax.imshow(m,cmap=cmap,vmin=0,vmax=m.max())
        for (i,j),v in np.ndenumerate(m):
            if i!=j and v>0:ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor='#fff6cc',edgecolor=YELLOW,lw=1.5))
            ax.text(j,i,str(v),ha='center',va='center',color='white' if v>m.max()*.65 else INK,fontweight='bold' if v else 'normal',fontsize=12)
        ax.set_xticks(range(4),LABELS,rotation=30,ha='right');ax.set_yticks(range(4),LABELS);ax.tick_params(length=0);ax.set_title(title,fontsize=11);ax.set_xlabel('Classe prédite')
        for spine in ax.spines.values():spine.set_visible(False)
    axes[0].set_ylabel('Classe réelle');save(fig,'final_confusion.png')

def comparisons(summary,bootstrap):
    fig,(a,b)=plt.subplots(1,2,figsize=(8.6,3.0),layout='constrained',gridspec_kw={'width_ratios':[1,1.2]})
    y=np.arange(4)
    for offset,stage,color,label in [(-.17,'development','#8cabc6','Développement'),(.17,'final',GOLD,'Test 3 HP')]:
        values=summary[summary.stage.eq(stage)].set_index('experiment').loc[EXP].balanced_accuracy.to_numpy()*100
        a.barh(y+offset,values,height=.3,color=color,edgecolor=NAVY if stage=='development' else YELLOW,lw=.5,label=label)
    a.set_yticks(y,EXP);a.invert_yaxis();a.set_xlim(0,105);a.set_xticks([0,50,100],['0 %','50 %','100 %']);a.grid(axis='x');a.set_axisbelow(True);a.legend(loc='lower left',bbox_to_anchor=(0,1.01),frameon=False,fontsize=9);a.set_xlabel('Exactitude équilibrée')
    pairs=['E4_minus_E1','E4_minus_E3','E4_minus_E2']
    for i,key in enumerate(pairs):
        d=bootstrap['comparisons'][key];lo,hi=np.array(d['ci95'])*100;point=d['point_difference']*100
        b.plot([lo,hi],[i,i],color=NAVY,lw=2);b.plot([lo,hi],[i,i],linestyle='none',marker='|',color=NAVY,markersize=10);b.scatter([point],[i],color=INK,s=35,zorder=3)
    b.axvline(0,ls='--',color=MUTED,lw=1);b.set_yticks(range(3),['E4 − E1','E4 − E3','E4 − E2']);b.invert_yaxis();b.set_xlim(-5,20);b.set_xticks([-5,0,5,10,15,20]);b.set_xlabel('Gain et IC 95 % · points');b.set_title('Bootstrap par enregistrement',fontsize=10);b.grid(axis='x');b.set_axisbelow(True)
    save(fig,'ablation.png')

def main():
    OUT.mkdir(exist_ok=True)
    source=(ROOT/'presentation/web/dist/data.js').read_text();data=json.loads(source.split('=',1)[1].strip().rstrip(';'))
    summary=pd.read_csv(ROOT/'results/summary.csv');metrics=json.loads((ROOT/'results/final_metrics.json').read_text());bootstrap=json.loads((ROOT/'results/final_bootstrap.json').read_text())
    temporal(data);spectra();scores(summary);confusion(metrics);comparisons(summary,bootstrap)
    print('Five article figures generated. Same development examples, saved results, no model fitting.')

if __name__=='__main__':main()
