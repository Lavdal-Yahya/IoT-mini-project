// Real ECharts SVG animation lifecycle in a simulated DOM; not browser visual QA.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),dist=path.join(__dirname,'dist');
const {JSDOM}=require(path.join(root,'tmp/web-qa/node_modules/jsdom'));
const dom=new JSDOM(fs.readFileSync(path.join(dist,'index.html'),'utf8'),{url:'http://localhost:8765/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window,doc=w.document,errors=[];let motionChanged;
w.matchMedia=()=>({matches:false,addEventListener:(event,fn)=>{motionChanged=fn;}});w.scrollTo=()=>{};
// SVG needs a text-width provider in jsdom; this test does not assess typography.
w.HTMLCanvasElement.prototype.getContext=()=>({measureText:text=>({width:String(text).length*8})});
for(const node of doc.querySelectorAll('.chart')){Object.defineProperty(node,'clientWidth',{get:()=>900});Object.defineProperty(node,'clientHeight',{get:()=>380});}
w.console.error=(...args)=>errors.push(args.map(String).join(' '));w.addEventListener('error',e=>errors.push(e.message));
for(const name of ['vendor/echarts.min.js','data.js','charts.js','app.js'])w.eval(fs.readFileSync(path.join(dist,name),'utf8'));
const get=id=>w.echarts.getInstanceByDom(doc.getElementById(id));
const animating=id=>!get(id).getZr().animation.isFinished();
const go=i=>doc.querySelector(`#slide-progress [data-slide="${i}"]`).click();
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 assert.equal(w.echarts.version,'6.1.0');assert(animating('wave-chart'),'Wave enters with a native animation');
 go(6);const bars=get('development-chart');assert(animating('development-chart'),'Bars animate on entry');
 await wait(1200);assert(!animating('development-chart'),'Entrance finishes and does not loop');doc.dispatchEvent(new w.Event('fullscreenchange'));assert(!animating('development-chart'),'A layout notification does not restart a finished animation');
 const stable=bars.getOption().series[0].data.map(d=>d.value);
 go(7);go(6);assert.equal(get('development-chart'),bars,'Cached chart instance is reused');assert(animating('development-chart'),'Revisiting replays its native entrance');assert.deepEqual(bars.getOption().series[0].data.map(d=>d.value),stable,'Animation preserves values');
 go(2);assert(animating('temporal-chart'),'Scatter entrance animates');
 go(3);assert(animating('inner-chart')&&animating('outer-chart'),'Both line charts animate');
 go(8);assert(animating('confusion-chart'),'Heatmap entrance animates');
 go(9);assert(animating('uncertainty-chart'),'Custom confidence intervals animate');
 motionChanged({matches:true});assert.equal(get('uncertainty-chart').getOption().animation,false);assert(!animating('uncertainty-chart'),'Enabling reduced motion stops the current animation');
 go(6);assert.equal(get('development-chart').getOption().animation,false);assert(!animating('development-chart'),'Reduced motion shows final chart immediately');
 assert.equal(errors.length,0,errors.join('\n'));
 for(const node of doc.querySelectorAll('.chart')){const instance=get(node.id);if(instance)instance.dispose();}
 dom.window.close();console.log(JSON.stringify({status:'pass',engine:'real Apache ECharts 6.1.0 in jsdom SVG',native_entrances:['line','bar','scatter','heatmap','custom confidence interval'],revisit_replays:true,animations_finish_without_looping:true,values_preserved:true,reduced_motion_respected:true,visual_browser_review:false},null,2));
})().catch(error=>{dom.window.close();console.error(error);process.exitCode=1;});
