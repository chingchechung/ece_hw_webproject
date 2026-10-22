import {mkdirSync,writeFileSync} from 'node:fs';
import {generateMap} from '../src/maze/generate.js';
import {planRoute} from './control-route.mjs';
const out=new URL('../../test-results/3d-p1/',import.meta.url);
mkdirSync(out,{recursive:true});
writeFileSync(new URL('control-route.json',out),JSON.stringify(planRoute(generateMap(13,9,20264049)),null,2));
