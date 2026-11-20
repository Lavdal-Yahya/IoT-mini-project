// Callback for the connected Spaces artifact session. Invoke in four separate
// artifactSession.run calls with input.phase = cover, a, b, c.
import fs from 'node:fs/promises';
let ROOT;
export async function loadScores(root) {
  const csv = await fs.readFile(`${root}/results/summary.csv`, 'utf8');
  const rows = csv.trim().split(/\r?\n/).slice(1).map(line => line.split(','));
  const stages = {development:{}, final:{}};
  for(const row of rows) {
    const [stage,experiment,balancedAccuracy] = row;
    if(stage in stages && /^E[1-4]$/.test(experiment)) stages[stage][experiment] = Number((Number(balancedAccuracy) * 100).toFixed(2));
  }
  return Object.fromEntries(Object.entries(stages).map(([stage,values]) => {
    const scores = ['E1','E2','E3','E4'].map(name => values[name]);
    if(scores.some(value => !Number.isFinite(value))) throw new Error(`Missing scores for ${stage}`);
    return [stage,scores];
  }));
}
const C = {navy:'#12223D', teal:'#008F90', ink:'#182638', muted:'#506177', line:'#CCD6DD', white:'#FFFFFF', pale:'#E9F4F2'};
function textbox(slide, value, x, y, w, h, size=24, bold=false, color=C.ink) {
  const shape = slide.shapes.add({geometry:'textbox', position:{left:x,top:y,width:w,height:h}, fill:'none', line:{fill:'none',width:0}});
  shape.text = value;
  shape.text.style = {fontSize:`${size}pt`, bold, color, typeface:'Aptos'};
  shape.text.insets = 0;
  return shape;
}
function base(presentation, title, number) {
  const slide = presentation.slides.add({width:1280,height:720});
  slide.background.fill = C.white;
  textbox(slide,title,58,34,1150,68,32,true,C.navy);
  textbox(slide,`${number} / 10`,1160,674,70,24,10,false,C.muted);
  return slide;
}
function note(slide, duration, body, sources='') {
  slide.speakerNotes.text = `Durée estimée : ${duration}.\n${body}${sources ? `\nSources : ${sources}` : ''}`;
}
function softLine(slide, y=112) { slide.shapes.add({geometry:'rect',position:{left:58,top:y,width:1164,height:3},fill:C.teal,line:{fill:'none',width:0}}); }
function addImage(slide, relative, x,y,w,h,alt) {
  slide.images.add({path:`${ROOT}/${relative}`,alt,fit:'contain',position:{left:x,top:y,width:w,height:h}});
}
function table(slide, rows, x,y,w,h) {
  const t=slide.tables.add({rows:rows.length,columns:rows[0].length,left:x,top:y,width:w,height:h,values:rows});
  t.styleOptions={headerRow:true,bandedRows:true};
  for (let j=0;j<rows[0].length;j++) {
    const cell=t.getCell(0,j);
    cell.fill=C.navy;
    cell.text.style={fontSize:'18pt',bold:true,color:C.white,typeface:'Aptos'};
  }
  for (let i=1;i<rows.length;i++) for(let j=0;j<rows[0].length;j++) {
    t.getCell(i,j).text.style={fontSize:'18pt',color:C.ink,typeface:'Aptos'};
  }
  t.borders.assign({style:'solid',fill:C.line,width:1});
  return t;
}
function chart(slide, categories, values, x,y,w,h) {
  return slide.charts.add('bar',{
    position:{left:x,top:y,width:w,height:h},
    categories,
    series:[{name:'Exactitude équilibrée pondérée (%)',values,fill:C.teal}],
    barOptions:{direction:'column',grouping:'clustered',gapWidth:85},
    hasLegend:false,
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:'16pt',typeface:'Aptos',fill:C.navy}},
    yAxis:{min:0,max:100,majorUnit:20,numberFormatCode:'0" %"',textStyle:{fontSize:'14pt',typeface:'Aptos',fill:C.ink},majorGridlines:{style:'solid',fill:C.line,width:1}},
    xAxis:{textStyle:{fontSize:'16pt',typeface:'Aptos'}},
    chartFill:'none',plotAreaFill:'none',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0}
  });
}
export default async function build({presentation,input}) {
  if(!input?.root) throw new Error('input.root is required');
  ROOT=input.root;
  const phase=input?.phase;
  if((phase==='b'||phase==='c') && !input?.scores) throw new Error('input.scores from loadScores(root) is required');
  if(phase==='cover') {
    const slide=presentation.slides.getItem(0);
    slide.background.fill=C.navy;
    const existing=slide.shapes.items;
    if(existing.length){
      const first=existing[0];
      first.text='Diagnostic de roulements par vibrations';
      first.position={left:66,top:152,width:1100,height:150};
      first.text.style={fontSize:'44pt',bold:true,color:C.white,typeface:'Aptos'};
      first.text.insets=0;
      for(let i=1;i<existing.length;i++) existing[i].text='';
    } else textbox(slide,'Diagnostic de roulements par vibrations',66,152,1100,150,44,true,C.white);
    textbox(slide,'CWRU · quatre états · transfert de charge',68,322,1050,55,24,false,'#CFEBE9');
    textbox(slide,'Mouhamedou Yahya Cheikh Med Vall',68,548,1060,42,21,true,C.white);
    textbox(slide,'25239  ·  AML313, groupe 7',68,595,1060,34,18,false,'#CFEBE9');
    note(slide,'0 min 30 s','Présenter les quatre états : sain, bague interne, bague externe et bille. Question : les caractéristiques spectrales et d’enveloppe ajoutent-elles de l’information aux trois indicateurs temporels, et le diagnostic tient-il sur une charge absente de l’apprentissage ?');
    return {phase,slides:presentation.slides.items.length};
  }
  if(phase==='a') {
    let s=base(presentation,'Données CWRU et séparation des essais',2);softLine(s);
    table(s,[['Charge','Essais','Usage'],['0 HP','10','Développement'],['1 HP','10','Développement'],['2 HP','10','Développement'],['3 HP','10','Test final réservé']],88,151,750,384);
    textbox(s,'40 essais au total',884,174,310,60,24,true,C.navy);
    textbox(s,'30 en développement\n10 au test final',884,252,310,110,21,false,C.ink);
    textbox(s,'Sains 48 kHz, défauts 12 kHz\nFIR causal commun · analyse 12 kHz',88,576,1100,74,18,false,C.muted);
    note(s,'0 min 55 s','Chaque charge contient un essai sain et neuf essais avec défaut. Les charges 0 à 2 HP servent au développement ; chaque pli valide une charge entière. Les dix essais à 3 HP restent réservés jusqu’au gel. Un passe-bas causal de 4,8 kHz est appliqué aux deux fréquences natives. Deux vitesses saines utilisent une valeur officielle approximative, faute de mesure dans le MAT.','data/classcoverage.csv ; data/splits/recordings.csv ; docs/data_audit.md');
    s=base(presentation,'Tâche 1 · indicateurs temporels',3);softLine(s);
    textbox(s,'RMS     Kurtosis de Pearson     Facteur de crête',68,132,1150,45,24,true,C.navy);
    addImage(s,'results/figures/temporal_features.png',48,184,1184,398,'Distributions des trois indicateurs temporels sur le développement');
    textbox(s,'Mêmes fenêtres pour la baseline et les modèles enrichis',70,607,1120,42,18,false,C.muted);
    note(s,'1 min 00 s','Nous retirons la moyenne locale de chaque fenêtre. RMS mesure l’amplitude efficace. La kurtosis de Pearson corrigée du biais caractérise les valeurs extrêmes ; la référence gaussienne est 3. Le facteur de crête compare le pic à RMS. Ces trois entrées définissent E1. La figure décrit les signaux du développement, sans prouver seule la qualité de classification.','docs/features.md ; results/figures/temporal_features.png');
    s=base(presentation,'Tâche 2 · fréquences de défaut et enveloppe',4);softLine(s);
    textbox(s,'BPFO = 3,5848 × rpm/60',70,138,565,48,25,true,C.navy);
    textbox(s,'BPFI = 5,4152 × rpm/60',650,138,565,48,25,true,C.navy);
    addImage(s,'presentation/envelope_examples.png',46,200,1188,403,'Spectres d’enveloppe des essais de développement IR007_0 et OR007@6_0');
    textbox(s,'Passe-bande causal 2–5 kHz · enveloppe à fenêtre fermée',105,611,1050,39,18,false,C.muted);
    note(s,'1 min 00 s','Les facteurs BPFO et BPFI viennent de la fiche du roulement côté entraînement CWRU. Nous filtrons causalement entre 2 et 5 kHz. L’enveloppe est calculée à la fin d’une fenêtre complète, après coupe de 0,05 seconde à chaque bord. Les énergies près des trois premières harmoniques de BPFO et BPFI sont calculées pour toutes les classes ; l’étiquette ne choisit aucune bande. La bande fixe n’est pas présentée comme une résonance optimale.','docs/features.md ; CWRU bearing information ; presentation/envelope_examples.png ; résultats issus de deux essais du développement');
    return {phase,slides:presentation.slides.items.length};
  }
  if(phase==='b') {
    let s=base(presentation,'Tâche 3 · fenêtre et résolution FFT',5);softLine(s);
    textbox(s,'1 seconde',83,220,345,75,38,true,C.navy);
    textbox(s,'12 000 échantillons',455,220,430,75,35,true,C.navy);
    textbox(s,'Δf = 1 Hz',910,220,280,75,36,true,C.teal);
    textbox(s,'Enveloppe après coupe des bords : 0,9 s et Δf ≈ 1,111 Hz',85,390,1090,86,24,false,C.ink);
    textbox(s,'Hann réduit la fuite spectrale ; deux pics à 1 Hz d’écart ne sont pas forcément séparables.',85,515,1090,76,20,false,C.muted);
    note(s,'0 min 50 s','Une fenêtre dure une seconde sans recouvrement. À 12 kHz, elle compte 12 000 points, donc le pas FFT brut vaut 1 Hz. La fenêtre de Hann réduit la fuite mais élargit les pics. L’enveloppe conserve 0,9 seconde après retrait de 0,05 seconde à chaque bord et son pas vaut environ 1,111 Hz. La prédiction attend la fin de la fenêtre.','docs/features.md');
    s=base(presentation,'Tâche 4 · quatre expériences appariées',6);softLine(s);
    table(s,[['Expérience','Classifieur','Entrées'],['E1','Arbre','3 temporelles'],['E2','Arbre','13 caractéristiques'],['E3','Forêt','3 temporelles'],['E4','Forêt','13 caractéristiques']],100,153,1080,372);
    textbox(s,'Mêmes 268 fenêtres hors pli · mêmes 3 charges de validation',100,568,1080,45,21,true,C.teal);
    note(s,'1 min 00 s','E1 est la baseline imposée. E2 contre E1 compare les caractéristiques avec le même arbre ; E4 contre E3 fait pareil avec la forêt. E3 contre E1 compare le classifieur à trois entrées. Toutes les expériences utilisent les mêmes observations et partitions. Classe, charge, identifiants et plis restent hors de la matrice X.','results/summary.csv ; docs/features.md');
    s=base(presentation,'Résultats du développement',7);softLine(s);
    chart(s,['E1','E2','E3','E4'],input.scores.development,100,150,1080,385);
    textbox(s,'E2 − E1 : −5,56 points',110,566,510,40,21,true,C.ink);
    textbox(s,'E4 − E3 : +4,63 points',644,566,510,40,21,true,C.teal);
    textbox(s,'Exactitude équilibrée pondérée par enregistrement · 30 essais',110,627,1050,35,16,false,C.muted);
    note(s,'1 min 20 s','Sur les 30 essais de développement et 268 fenêtres hors pli, E4 atteint 99,69 % et a été choisi avant le test final. Les nouvelles caractéristiques baissent le score de l’arbre de 5,56 points, mais augmentent celui de la forêt de 4,63 points. L’effet dépend donc du classifieur. L’ablation réunit dix nouvelles colonnes ; elle ne mesure pas la seule enveloppe.','results/summary.csv');
    return {phase,slides:presentation.slides.items.length};
  }
  if(phase==='c') {
    let s=base(presentation,'Tâche 5 · transfert à 3 HP',8);softLine(s);
    chart(s,['E1','E2','E3','E4'],input.scores.final,100,152,1080,387);
    textbox(s,'E4 retenu sur le développement : 98,15 % à 3 HP',108,569,1060,43,22,true,C.teal);
    textbox(s,'92 fenêtres · 10 enregistrements · une campagne finale après gel',108,621,1060,36,17,false,C.muted);
    note(s,'1 min 25 s','Après le gel, les quatre expériences ont été réentraînées sur le développement puis évaluées dans une seule campagne sur 3 HP. E4 atteint 98,15 % d’exactitude équilibrée pondérée, contre 90,74 % pour E1. E2 atteint aussi 98,15 %. Nous gardons E4 parce qu’il a été choisi avant la lecture du test.','results/summary.csv ; results/final_metrics.json');
    s=base(presentation,'Erreurs finales de la forêt enrichie',9);softLine(s);
    table(s,[['Vraie classe','Sain','Bague interne','Bague externe','Bille'],['Sain','9','0','0','0'],['Bague interne','0','28','0','0'],['Bague externe','0','0','26','2'],['Bille','0','0','0','27']],80,149,1120,376);
    textbox(s,'10/10 essais bien classés après agrégation',88,563,1100,43,24,true,C.teal);
    textbox(s,'Rappel bague externe : 92,59 % avec poids par enregistrement',88,619,1100,37,17,false,C.muted);
    note(s,'1 min 10 s','La matrice présente les 92 fenêtres du test final : deux fenêtres de bague externe sont prédites bille. Après moyenne des probabilités par essai, E4 classe correctement les dix enregistrements. Le rappel pondéré de bague externe vaut 92,59 %. Il faut distinguer les fenêtres voisines des essais indépendants.','results/final_metrics.json ; results/figures/final_window_confusion.png');
    s=base(presentation,'Conclusion et limites',10);softLine(s);
    textbox(s,'E4 : 99,69 % en développement',82,158,1100,55,29,true,C.navy);
    textbox(s,'E4 : 98,15 % sur la charge 3 HP',82,226,1100,55,29,true,C.teal);
    textbox(s,'Gain final E4 − E1 : +7,41 points',82,324,1100,50,24,true,C.ink);
    textbox(s,'Bootstrap par essai : IC 95 % [0 ; 17,59 points]',82,385,1100,45,21,false,C.ink);
    textbox(s,'Un seul essai sain final · roulement physique entre charges inconnu\nCes résultats concernent le banc CWRU étudié.',82,500,1100,105,20,false,C.muted);
    note(s,'0 min 50 s','La forêt enrichie E4 a le meilleur score de développement et 98,15 % sur la charge réservée. E2 atteint le même score final, mais n’a pas été sélectionné sur le développement. Le gain E4 contre E1 est de 7,41 points, avec un intervalle bootstrap qui touche zéro. Il n’y a qu’un essai sain au test final et l’identité du roulement physique entre charges est inconnue. Nous ne concluons pas à une généralisation industrielle.','results/summary.csv ; results/final_bootstrap.json ; docs/data_audit.md');
    return {phase,slides:presentation.slides.items.length};
  }
  throw new Error(`phase inconnue: ${phase}`);
}
