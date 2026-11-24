// Run with the bundled Artifact Tool runtime. See README.md in this directory.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import build,{loadEvidence} from './build_dashboard.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const modules=process.env.ARTIFACT_NODE_MODULES;
const skill=process.env.PRESENTATIONS_SKILL;
const python=process.env.ARTIFACT_PYTHON;
if(!modules||!skill||!python)throw Error('Set ARTIFACT_NODE_MODULES, PRESENTATIONS_SKILL and ARTIFACT_PYTHON; see README.md.');
process.env.RUNTIME_NODE_MODULES ??= modules;
const require=createRequire(path.join(modules,'package.json'));
const {Presentation,PresentationFile}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
const evidence=await loadEvidence(root);
for(const phase of ['cover','a','b','c'])await build({presentation,input:{phase,evidence}});
await fs.mkdir(path.join(root,'tmp'),{recursive:true});
const staging=await fs.mkdtemp(path.join(root,'tmp/dashboard-build-'));
const finalPath=path.resolve(process.argv[2]??path.join(root,'presentation/dashboard/diagnostic_dashboard.pptx'));
await fs.mkdir(staging,{recursive:true});await fs.mkdir(path.dirname(finalPath),{recursive:true});
for(const [index,slide] of presentation.slides.items.entries()){
 const png=await presentation.export({slide,format:'png',scale:1});
 await fs.writeFile(path.join(staging,`slide-${index+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidatePath=path.join(staging,'candidate.pptx');
await(await PresentationFile.exportPptx(presentation)).save(candidatePath);
const requirements={explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[2,5,6,9,10],requiredNativeChartOwnerSlides:[7,8],materializeLiteralChartWorkbooks:true};
const result=await finalizePresentation({
 ...requirements,workspaceDir:root,candidatePath,finalPath,pythonExecutable:python,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...requirements.requiredNativeTableOwnerSlides.flatMap(n=>['--require-native-table-slide',String(n)])],
 fontPolicy:{basis:'design',families:['Liberation Sans']},verifyArtifactToolImport:true,
 receiptPath:path.join(staging,'validation.json')
});
console.log(JSON.stringify({slides:presentation.slides.items.length,finalPath,result},null,2));
