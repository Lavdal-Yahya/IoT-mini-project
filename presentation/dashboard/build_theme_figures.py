"""Style saved web-presentation data for the editable PowerPoint. No analysis or fit."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'presentation/dashboard/assets'
INK='#000814'; NAVY='#003566'; PRUSSIAN='#001d3d'; YELLOW='#ffc300'; GOLD='#ffd60a'
COLORS=[PRUSSIAN,NAVY,YELLOW,INK]
plt.rcParams.update({'font.family':'Liberation Sans','font.size':13,'text.color':INK,'axes.labelcolor':INK,'xtick.color':'#41566d','ytick.color':'#41566d','axes.edgecolor':'#d6dfe9','axes.spines.top':False,'axes.spines.right':False,'grid.color':'#d6dfe9','grid.alpha':.65,'figure.facecolor':'white','axes.facecolor':'#f5f7fa','savefig.facecolor':'white'})

def main():
    source=(ROOT/'presentation/web/dist/data.js').read_text()
    data=json.loads(source.split('=',1)[1].strip().rstrip(';'))
    OUT.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,3,figsize=(16,5.35),layout='constrained')
    for ax,key,title in zip(axes,['rms','kurtosis','crest_factor'],['RMS','Kurtosis de Pearson','Facteur de crête']):
        for i,cls in enumerate(['healthy','inner_race','outer_race','ball']):
            values=[row[key] for row in data['temporal'] if row['class_label']==cls]
            jitter=[i+(j%5-2)*.06 for j in range(len(values))]
            ax.scatter(jitter,values,c=COLORS[i],marker=['o','D','^','s'][i],s=43,edgecolors=INK,linewidths=.5,zorder=3)
            ax.plot([i-.22,i+.22],[np.median(values)]*2,color=INK,lw=2,zorder=4)
        ax.set_title(title,pad=13,fontweight='bold',color=NAVY)
        ax.set_xticks(range(4),['Sain','Interne','Externe','Bille']);ax.set_xlim(-.5,3.5)
        ax.grid(axis='y');ax.set_axisbelow(True)
    axes[0].set_ylabel('Médiane par enregistrement')
    fig.suptitle('Développement uniquement. Trait court : médiane de classe.',fontsize=15,color=PRUSSIAN)
    fig.savefig(OUT/'temporal_features.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(16,5.4),layout='constrained')
    for ax,row,name in zip(axes,data['envelopes'],['Bague interne','Bague externe']):
        points=np.array(row['points']);ax.plot(points[:,0],points[:,1],color=NAVY,lw=1.4)
        for key,label,color in [('bpfo_hz','BPFO',YELLOW),('bpfi_hz','BPFI',PRUSSIAN)]:
            ax.axvline(row['frequencies'][key],color=color,linestyle='--',lw=2,label=label)
        ax.set_xlim(0,350);ax.set_ylim(bottom=0);ax.set_xlabel('Fréquence (Hz)');ax.grid(axis='y');ax.set_axisbelow(True)
        ax.set_title(name,pad=13,fontweight='bold',color=NAVY)
        ax.legend(frameon=True,facecolor='white',edgecolor='#d6dfe9',loc='upper right')
    axes[0].set_ylabel('Amplitude, unité source non certifiée')
    fig.suptitle('IR007_0 et OR007@6_0. Une fenêtre de développement par essai.',fontsize=15,color=PRUSSIAN)
    fig.savefig(OUT/'envelope_examples.png',dpi=150);plt.close(fig)
    print('Two figures rendered from saved web data; no signal analysis or training.')

if __name__=='__main__':main()
