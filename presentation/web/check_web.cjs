// Data, SVG-render and DOM wiring checks. This is not a live-browser visual test.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),dist=path.join(__dirname,'dist');
const {JSDOM}=require(path.join(root,'tmp/web-qa/node_modules/jsdom'));
const echarts=require(path.join(dist,'vendor/echarts.min.js'));
const G=require(path.join(dist,'charts.js'));
const sandbox={window:{}};vm.runInNewContext(fs.readFileSync(path.join(dist,'data.js'),'utf8'),sandbox);const D=JSON.parse(JSON.stringify(sandbox.window.PROJECT_DATA));
const out=path.join(root,'tmp/web-qa/renders');fs.mkdirSync(out,{recursive:true});
const cases=[['wave-chart',{}],['coverage-chart',{}],...['rms','kurtosis','crest_factor'].map(feature=>['temporal-chart',{feature}]),['inner-chart',{}],['outer-chart',{}],['development-chart',{}],['transfer-chart',{}],['transfer-chart',{compare:true}],...['E1','E2','E3','E4'].flatMap(model=>['raw_window','record'].map(grain=>['confusion-chart',{model,grain}])),['uncertainty-chart',{}]];
let n=0;
for(const [width,narrow]of [[900,false],[360,true]])for(const [id,state]of cases){
 const chart=echarts.init(null,null,{renderer:'svg',ssr:true,width,height:380});
 chart.setOption(G.buildOptions(id,D,{...state,narrow,reducedMotion:true}));
 const svg=chart.renderToSVGString();assert(svg.includes('<svg'));assert(!/NaN|Infinity|undefined/.test(svg),id);
 fs.writeFileSync(path.join(out,`${++n}-${id}.svg`),svg);chart.dispose();
}
const temp=fs.readFileSync(path.join(out,'3-temporal-chart.svg'),'utf8');for(const name of ['Sain','Interne','Externe','Bille'])assert(temp.includes(name));
const summary=JSON.parse(fs.readFileSync(path.join(root,'results/final_metrics.json')));
assert.deepEqual(D.metrics,summary);assert.equal(D.temporal.length,30);assert.equal(D.envelopes.length,2);assert.equal(D.waveform.points.length,600);
const errors=[];const dom=new JSDOM(fs.readFileSync(path.join(dist,'index.html'),'utf8'),{url:'http://localhost:8765/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;w.PROJECT_DATA=D;w.PresentationCharts=G;w.matchMedia=()=>({matches:false});w.scrollTo=()=>{};
w.HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','');};w.HTMLDialogElement.prototype.close=function(){this.removeAttribute('open');};
w.echarts={init:()=>({setOption:option=>assert(option.series.length>0),resize:()=>{}})};
w.console.error=(...args)=>errors.push(args.map(String).join(' '));w.addEventListener('error',e=>errors.push(e.message));
w.eval(fs.readFileSync(path.join(dist,'app.js'),'utf8'));
const doc=w.document,click=selector=>{const el=doc.querySelector(selector);assert(el,selector);el.click();};
const visible=()=>[...doc.querySelectorAll('.slide')].findIndex(s=>!s.hidden);
assert.equal(visible(),0);assert(doc.querySelector('.authors').textContent.includes("Maryeim Mohamed T'Feil"));
click('#next-button');assert.equal(visible(),1);click('#previous-button');assert.equal(visible(),0);
w.document.body.dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));assert.equal(visible(),1);
for(let i=0;i<10;i++){click(`#slide-progress [data-slide="${i}"]`);assert.equal(visible(),i);assert.equal(doc.querySelector('#slide-number').textContent,String(i+1).padStart(2,'0'));}
click('#slide-progress [data-slide="2"]');click('[data-feature="kurtosis"]');assert(doc.querySelector('#feature-definition').textContent.includes('Pearson'));assert.equal(doc.querySelector('[data-feature="kurtosis"]').getAttribute('aria-pressed'),'true');assert.equal(doc.querySelectorAll('#temporal-table tbody tr').length,30);
click('#slide-progress [data-slide="7"]');click('#compare-development');assert(doc.querySelector('#transfer-note').textContent.includes('optimistes'));assert(doc.querySelector('#transfer-scope').textContent.includes('30 essais'));click('#compare-development');assert(doc.querySelector('#transfer-scope').textContent.includes('92 fenêtres'));
click('#slide-progress [data-slide="8"]');assert(doc.querySelector('#error-headline').textContent.includes('2 erreurs'));assert.equal(doc.querySelector('#record-score').textContent,'10/10');click('[data-grain="record"]');assert(doc.querySelector('#error-headline').textContent.includes('aucune'));assert.equal(doc.querySelector('#outer-recall').textContent,'100,00 %');
const select=doc.querySelector('#confusion-model');select.value='E1';select.dispatchEvent(new w.Event('change'));assert.equal(doc.querySelector('#record-score').textContent,'9/10');assert(doc.querySelector('#confusion-caption').textContent.startsWith('E1'));
click('#notes-button');assert(!doc.querySelector('#notes-panel').hidden);click('#close-notes');assert(doc.querySelector('#notes-panel').hidden);
click('#plan-button');assert(doc.querySelector('#plan-dialog').open);click('#plan-links [data-slide="4"]');assert.equal(visible(),4);assert(!doc.querySelector('#plan-dialog').open);
click('#sources-button');assert(doc.querySelector('#sources-dialog').open);click('[data-close="sources-dialog"]');assert(!doc.querySelector('#sources-dialog').open);
assert.equal(doc.querySelectorAll('#slide-progress button').length,10);assert.equal(errors.length,0,errors.join('\n'));dom.window.close();
console.log(JSON.stringify({status:'pass',echarts:echarts.version,svg_states:n,dom_checks:'navigation, keyboard, all slides, features, comparison, models, grain, notes, plan, sources',data:'frozen metrics identical; 30 development recordings; 2 spectra; both authors',browser_visual_qa:'unavailable: local browser use disabled in Work settings'},null,2));
