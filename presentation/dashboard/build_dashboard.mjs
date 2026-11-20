// Alternate editable presentation. Results are loaded from the frozen evidence.
import fs from 'node:fs/promises';
const C={ink:'#162C3A',muted:'#50626B',teal:'#007D78',context:'#8B9CA5',light:'#E6F2EF',line:'#DBE3E6',amber:'#80561B',warning:'#FFF0D5',white:'#FFFFFF'};
const EXP=['E1','E2','E3','E4'];
const LABELS=['Sain','Interne','Externe','Bille'];
const DURATIONS=[35,60,55,70,55,55,75,80,65,50];
const pct=x=>(100*x).toFixed(2).replace('.',',');
const points=x=>(x>=0?'+':'−')+Math.abs(x*100).toFixed(2).replace('.',',');
export async function loadEvidence(root){
  const read=async p=>JSON.parse(await fs.readFile(`${root}/${p}`,'utf8'));
  const csv=(await fs.readFile(`${root}/results/summary.csv`,'utf8')).trim().split(/\r?\n/);
  const keys=csv.shift().split(',');
  const summary=csv.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[keys[i],i<2?v:Number(v)])));
  const stages=Object.fromEntries(['development','final'].map(stage=>[stage,EXP.map(experiment=>{
    const row=summary.find(x=>x.stage===stage&&x.experiment===experiment);
    if(!row||!Number.isFinite(row.balanced_accuracy))throw Error(`Missing ${stage}/${experiment}`);
    return row;
  })]));
  const [metrics,bootstrap,selection,config]=await Promise.all([read('results/final_metrics.json'),read('results/final_bootstrap.json'),read('results/selection.json'),read('configs/experiment.json')]);
  const coverage=(await fs.readFile(`${root}/data/classcoverage.csv`,'utf8')).trim().split(/\r?\n/).slice(1).map(line=>line.split(','));
  const classes=['healthy','inner_race','outer_race','ball'];
  const counts=classes.map(label=>[0,1,2,3].map(hp=>Number(coverage.find(r=>r[0]===label&&Number(r[1])===hp)[2])));
  return {root,stages,metrics,bootstrap,selection,config,counts};
}
function text(s,value,x,y,w,h,size=22,bold=false,color=C.ink){
  const t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  t.text=String(value);t.text.style={fontSize:`${size}pt`,typeface:'Liberation Sans',bold,color};t.text.insets=0;return t;
}
function slide(p,title,n,scope){
  const s=p.slides.add({width:1280,height:720});s.background.fill=C.white;
  text(s,title,60,36,1150,65,32,true);
  text(s,scope,62,110,1150,42,17,false,C.muted);
  text(s,`${String(n).padStart(2,'0')} / 10`,1135,677,95,24,11,false,C.muted);return s;
}
function notes(s,n,body,sources){s.speakerNotes.text=`Durée estimée : ${DURATIONS[n-1]} secondes.\n${body}\nSources : ${sources}`;}
function table(s,values,x,y,w,h,{focusRow=-1}={}){
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values});
  t.borders.assign({style:'solid',fill:C.line,width:0.6});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);cell.fill=r===0?C.ink:r===focusRow?C.light:C.white;
    cell.text.style={fontSize:'18pt',typeface:'Liberation Sans',bold:r===0||r===focusRow,color:r===0?C.white:C.ink};
  }return t;
}
function bars(s,rows,x,y,w,h){
  return s.charts.add('bar',{
    position:{left:x,top:y,width:w,height:h},categories:EXP,
    series:[{name:'Exactitude équilibrée (%)',values:rows.map(r=>Number((r.balanced_accuracy*100).toFixed(2))),fill:C.context,points:[{idx:3,fill:C.teal}]}],
    barOptions:{direction:'column',grouping:'clustered',gapWidth:105},hasLegend:false,
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:'18pt',typeface:'Liberation Sans',fill:C.ink}},
    yAxis:{min:0,max:100,majorUnit:20,numberFormatCode:'0" %"',textStyle:{fontSize:'14pt',typeface:'Liberation Sans'},majorGridlines:{fill:C.line,width:0.6,style:'solid'}},
    xAxis:{textStyle:{fontSize:'18pt',typeface:'Liberation Sans'}},chartFill:'none',plotAreaFill:'none',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0}
  });
}
async function image(s,root,path,x,y,w,h,alt){const blob=await fs.readFile(`${root}/${path}`);s.images.add({blob:new Uint8Array(blob),contentType:'image/png',position:{left:x,top:y,width:w,height:h},fit:'contain',alt});}
export default async function build({presentation,input}){
  const {phase,evidence:e}=input||{};
  if(!e)throw Error('input.evidence from loadEvidence(root) is required');
  const dev=e.stages.development,final=e.stages.final,winner=e.selection.winner;
  const d=e.bootstrap.comparisons;
  if(phase==='cover'){
    const s=presentation.slides.items.length?presentation.slides.getItem(0):presentation.slides.add({width:1280,height:720});s.background.fill=C.white;
    text(s,'Diagnostic de\nroulements par\nvibrations',60,80,725,242,44,true);
    text(s,'CWRU, quatre états\nTransfert vers une charge réservée',63,354,720,88,24,false,C.muted);
    text(s,'Exactitude équilibrée pondérée',814,122,405,35,18,false,C.muted);
    text(s,`${pct(final[3].balanced_accuracy)} %`,810,166,415,100,55,true,C.teal);
    text(s,'E4 sur la charge 3 HP',814,284,405,42,22,true);
    text(s,`Baseline E1 : ${pct(final[0].balanced_accuracy)} %\n10 essais, 92 fenêtres`,814,342,405,90,20,false,C.muted);
    text(s,'Un seul essai sain final',814,469,400,46,20,true,C.amber);
    text(s,'Mouhamedou Yahya Cheikh Med Vall · 25239',63,552,1140,39,21,true);
    text(s,"Maryeim Mohamed T'Feil · 22087",63,602,1140,39,21,true);
    text(s,'AML313, groupe 7 — Version analytique',63,666,1000,28,15,false,C.muted);
    notes(s,1,'Poser la question de l’enrichissement spectral et du transfert. Le score montré est l’exactitude équilibrée des fenêtres avec poids égal par essai. E4 a été choisi avant le test. Le résultat est limité par un seul essai sain final.','results/summary.csv ; results/selection.json ; results/final_bootstrap.json');
    return {phase,slides:presentation.slides.items.length};
  }
  if(phase==='a'){
    let s=slide(presentation,'Quarante essais, une charge réservée',2,'CWRU côté entraînement, canal DE. Effectifs par classe et charge.');
    table(s,[['Classe','0 HP','1 HP','2 HP','3 HP'],...LABELS.map((l,i)=>[l,...e.counts[i].map(String)])],60,185,790,335);
    text(s,`${dev[0].n_recordings} essais`,904,187,310,63,34,true);
    text(s,`Charges 0 à 2 HP\n${dev[0].n_windows} fenêtres`,904,267,310,90,20,false,C.muted);
    text(s,`${final[0].n_recordings} essais`,904,398,310,63,34,true,C.teal);
    text(s,`Test réservé : 3 HP\n${final[0].n_windows} fenêtres`,904,478,310,90,20,false,C.muted);
    text(s,'Sains : 48 kHz. Défauts : 12 kHz. Préparation commune à 12 kHz.',60,578,790,74,20,false,C.muted);
    notes(s,2,'Lire les effectifs : un sain et neuf défauts par charge. La colonne 3 HP a été réservée avant les modèles. Les trois autres charges forment trois plis, chacun validant une charge entière. Les fréquences natives ont été vérifiées, sans les déduire du nom des dossiers. Deux vitesses saines sont approximatives et documentées.','data/classcoverage.csv ; data/splits/recordings.csv ; docs/data_audit.md');
    s=slide(presentation,'Trois indicateurs pour la baseline',3,'Développement uniquement. Un point représente la médiane d’un enregistrement.');
    await image(s,e.root,'results/figures/temporal_features.png',45,160,1190,406,'Distributions RMS, kurtosis de Pearson et facteur de crête sur les essais de développement');
    text(s,'RMS : amplitude efficace',63,596,360,58,21,true);
    text(s,'Kurtosis : valeurs extrêmes',438,596,390,58,21,true);
    text(s,'Crête : pic / RMS',875,596,335,58,21,true);
    notes(s,3,'Décrire les trois mesures et leurs conventions : signal localement centré, kurtosis de Pearson corrigée du biais, référence gaussienne égale à trois. Les distributions se recouvrent et ne prouvent pas seules un diagnostic. La baseline utilise exactement ces trois colonnes.','results/figures/temporal_features.png ; docs/features.md');
    s=slide(presentation,'L’enveloppe révèle les fréquences de défaut',4,'Deux exemples du développement. Les échelles d’amplitude sont propres à chaque signal.');
    text(s,'BPFO = 3,5848 × rpm/60',62,166,570,48,25,true);
    text(s,'BPFI = 5,4152 × rpm/60',653,166,565,48,25,true);
    await image(s,e.root,'presentation/envelope_examples.png',45,225,1190,403,'Pics près de BPFI pour IR007_0 et de BPFO pour OR007@6_0');
    text(s,'Bande fixe 2–5 kHz. Les énergies BPFO et BPFI sont calculées pour toutes les classes.',64,640,1110,38,17,false,C.muted);
    notes(s,4,'Le premier pic dominant coïncide avec BPFI, le second avec BPFO. Les facteurs viennent de la fiche CWRU du roulement DE. Les unités d’amplitude de la source ne sont pas certifiées. On ne compare pas les hauteurs comme si les axes étaient identiques. Le choix d’une bande 2–5 kHz est fixé et non présenté comme optimal. Les six énergies utilisent trois harmoniques et ±3 Hz.','presentation/envelope_examples.png ; docs/features.md ; https://engineering.case.edu/bearingdatacenter/bearing-information');
    return {phase,slides:presentation.slides.items.length};
  }
  if(phase==='b'){
    let s=slide(presentation,'Une fenêtre, une résolution annoncée',5,'Préparation causale commune. Prédiction disponible à la fin de la fenêtre.');
    table(s,[['Étape','Convention'],['Passe-bas commun','4,8 kHz, FIR causal'],['Début des fenêtres','0,2 s après le départ'],['Fenêtre brute','1 s, sans recouvrement'],['Fenêtrage FFT','Hann, amplitude corrigée']],60,185,680,355);
    text(s,'1 Hz',808,190,370,85,48,true,C.teal);
    text(s,'FFT brute\n12 000 points à 12 kHz',811,284,380,90,23,false,C.ink);
    text(s,'1,111 Hz',808,428,380,65,34,true);
    text(s,'FFT d’enveloppe sur 0,9 s',811,510,380,65,21,false,C.muted);
    text(s,'Hann élargit les pics : un espacement FFT de 1 Hz ne garantit pas leur séparation.',62,602,1135,67,20,false,C.muted);
    notes(s,5,'Le FIR a le même comportement physique aux deux fréquences natives. Les transitoires exclus conduisent à des fenêtres débutant à 0,2 seconde. La FFT brute d’une seconde a un pas de 1 Hz. Le retrait de 0,05 seconde à chaque bord de l’enveloppe laisse 0,9 seconde et un pas de 1,111 Hz. Hilbert utilise la fenêtre complète, donc pas de décision avant sa fermeture.','configs/experiment.json ; results/filter_diagnostics.json ; docs/features.md');
    s=slide(presentation,'Séparer l’effet des entrées et du modèle',6,'Mêmes 268 fenêtres et mêmes trois plis de développement.');
    table(s,[['Classifieur','3 indicateurs temporels','13 caractéristiques'],['Arbre','E1 : baseline imposée','E2 : entrées enrichies'],['Forêt, 200 arbres','E3 : modèle enrichi','E4 : deux enrichissements']],60,188,1160,255);
    text(s,'Comparer les entrées',62,490,550,43,25,true);
    text(s,'E2 avec E1, puis E4 avec E3',62,550,550,70,22,false,C.muted);
    text(s,'Comparer les classifieurs',665,490,550,43,25,true);
    text(s,'E3 avec E1, puis E4 avec E2',665,550,550,70,22,false,C.muted);
    notes(s,6,'L’ablation change un facteur à la fois. Les dix colonnes supplémentaires comprennent quatre descripteurs de forme spectrale et six énergies d’harmoniques : elle ne mesure pas le seul effet de l’enveloppe. La charge, l’étiquette, les identifiants et les plis restent hors de X. Les paramètres sont sélectionnés avec une grille bornée sur le développement.','results/selection.json ; docs/protocol.md ; results/feature_dictionary.csv');
    s=slide(presentation,'E4 retenu avant le test final',7,`Exactitude équilibrée, poids égal par essai. ${dev[0].n_recordings} essais, ${dev[0].n_windows} fenêtres hors pli.`);
    bars(s,dev,47,182,790,355);
    text(s,`${pct(dev[3].balanced_accuracy)} %`,881,190,330,80,39,true,C.teal);
    text(s,'Forêt enrichie E4',884,282,330,45,23,true);
    text(s,`${points(dev[3].balanced_accuracy-dev[2].balanced_accuracy)} points`,884,376,330,55,27,true,C.teal);
    text(s,'E4 comparé à E3',884,439,330,46,20,false,C.muted);
    text(s,`Arbre : E2 − E1 = ${points(dev[1].balanced_accuracy-dev[0].balanced_accuracy)} points`,62,574,1140,44,23,true,C.amber);
    text(s,'Scores utilisés pour la sélection : leur niveau est optimiste, sans validation imbriquée.',62,634,1140,40,18,false,C.muted);
    notes(s,7,'Le graphique conserve les quatre expériences dans le même ordre et part de zéro. L’enrichissement aide la forêt mais dégrade l’arbre sur le développement. Le meilleur score est E4, retenu avant le test. Les scores de sélection ne sont pas une estimation indépendante.','results/summary.csv ; results/selection.json ; docs/development_decision.md');
    return {phase,slides:presentation.slides.items.length};
  }
  if(phase==='c'){
    let s=slide(presentation,'Transfert vers la charge réservée à 3 HP',8,`Exactitude équilibrée, poids égal par essai. ${final[0].n_recordings} essais, ${final[0].n_windows} fenêtres finales.`);
    bars(s,final,47,182,790,355);
    text(s,`${pct(final[3].balanced_accuracy)} %`,881,190,330,80,39,true,C.teal);
    text(s,'E4 retenu avant le test',884,282,330,78,22,true);
    text(s,`${points(d.E4_minus_E1.point_difference)} points`,884,386,330,55,27,true,C.teal);
    text(s,'Face à la baseline E1',884,449,330,46,20,false,C.muted);
    text(s,`E2 égale E4 à ${pct(final[1].balanced_accuracy)} %. Le choix reste E4.`,62,575,1140,47,22,true);
    text(s,`Gain E4 − E1, IC 95 % : [${pct(d.E4_minus_E1.ci95[0])} ; ${pct(d.E4_minus_E1.ci95[1])}] points. Un seul essai sain final.`,62,635,1140,42,18,false,C.amber);
    notes(s,8,'Une seule campagne E1–E4 a suivi le gel. E4 et E2 ont le même score final affiché. E3 est légèrement inférieur à E1. Les contre-exemples restent visibles. Le score ne sert pas à changer le modèle retenu. L’intervalle du gain E4 contre E1 touche zéro.','results/summary.csv ; results/final_bootstrap.json ; results/test_consulted.json');
    s=slide(presentation,'Deux fenêtres externes prédites comme bille',9,'E4 sur 3 HP. Matrice brute : lignes réelles, colonnes prédites, 92 fenêtres.');
    const cm=e.metrics.E4.raw_window.confusion;
    const t=table(s,[['Réel / prédit',...LABELS],...LABELS.map((l,i)=>[l,...cm[i].map(String)])],60,186,790,337);
    for(let i=0;i<4;i++)for(let j=0;j<4;j++){
      const cell=t.getCell(i+1,j+1),value=cm[i][j];
      cell.fill=i===j?(value>=25?'#B7DED5':'#E1F1ED'):value>0?C.warning:C.white;
      cell.text.style={fontSize:'23pt',bold:value>0,color:i!==j&&value>0?C.amber:C.ink,typeface:'Liberation Sans'};
    }
    text(s,`${Math.round(e.metrics.E4.record.accuracy*final[3].n_recordings)}/${final[3].n_recordings}`,900,185,310,90,48,true,C.teal);
    text(s,'Essais bien classés\naprès agrégation',904,294,310,100,22,true);
    text(s,`${pct(e.metrics.E4.weighted_window.recall_by_class.outer_race)} %`,900,427,310,65,32,true);
    text(s,'Rappel externe pondéré',904,507,310,65,20,false,C.muted);
    text(s,'Les fenêtres voisines sont dépendantes. L’agrégation moyenne les probabilités par essai.',62,603,1110,69,20,false,C.muted);
    notes(s,9,'Les nombres de la matrice sont bruts par fenêtre, distincts de la métrique principale pondérée. Les deux seules erreurs d’E4 concernent la bague externe. Le rappel pondéré externe diffère du rapport brut 26/28 parce que chaque essai a le même poids. Dix essais agrégés corrects ne valent pas 92 essais indépendants.','results/final_metrics.json ; docs/protocol.md');
    s=slide(presentation,'Un gain observé, une conclusion limitée au banc',10,`Bootstrap apparié par enregistrement, ${e.bootstrap.n_bootstrap} tirages stratifiés par classe. Différences en points.`);
    const pairs=[['E4 − E1','E4_minus_E1'],['E4 − E3','E4_minus_E3'],['E4 − E2','E4_minus_E2']];
    table(s,[['Comparaison','Gain','IC 95 %'],...pairs.map(([l,k])=>[l,points(d[k].point_difference),`[${pct(d[k].ci95[0])} ; ${pct(d[k].ci95[1])}]`])],60,186,730,270);
    text(s,'1 seul essai sain',849,189,365,58,29,true,C.amber);
    text(s,'Variabilité entre essais sains\nnon estimable au test final',852,270,365,107,21,false,C.muted);
    text(s,'Roulements physiques',849,414,365,45,23,true);
    text(s,'Identité entre charges inconnue',852,477,365,88,21,false,C.muted);
    text(s,'E4 − E1 : la borne basse vaut zéro. Le gain strict n’est pas établi.',62,552,730,72,22,true,C.amber);
    text(s,'Conclusion : diagnostic du banc CWRU étudié, à confirmer sur d’autres machines.',62,645,1140,39,19,false,C.muted);
    notes(s,10,'Conclure sur l’information apportée par les caractéristiques, dépendante du modèle. Le bootstrap donne le même tirage aux modèles comparés et garde les classes. Avec un seul essai sain il ne mesure aucune variabilité inter-essais pour cette classe. Les défauts sont artificiels. L’identité des roulements entre charges reste inconnue et l’incertitude ne couvre pas un changement de machine. Préparer les cinq minutes de questions à partir du document partagé.','results/final_bootstrap.json ; docs/data_audit.md ; presentation/questions_reponses.md');
    return {phase,slides:presentation.slides.items.length};
  }
  throw Error(`Unknown phase: ${phase}`);
}
