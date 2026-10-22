import { generateMap } from '../src/maze/generate.js';
import { planRoute } from './control-route.mjs';
const [w,h,seed,count]=process.argv.slice(2).map(Number);
const result=planRoute(generateMap(w,h,seed,count),process.argv[6]==='exit'?0:count);
for(const step of result.steps)if(step.kind==='activate'&&step.id!=='EXIT')step.id=`Q${step.id.slice(1).padStart(2,'0')}`;
console.log(JSON.stringify(result));
