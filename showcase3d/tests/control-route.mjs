// Offline test planner. Produces real key holds and clock durations, never poses.
import { stepDriving, initialVehicle } from '../src/gameplay/driving.js';
import { logicalToLite } from '../src/gameplay/coordinates.js';
export function path(map, start, finish) {
  const queue=[start],prev=new Map([[`${start.x},${start.y}`,null]]);
  for(let i=0;i<queue.length;i++){
    const p=queue[i];if(p.x===finish.x&&p.y===finish.y)break;
    for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){
      const x=p.x+dx,y=p.y+dy,key=`${x},${y}`;
      if(x>0&&x<map.width-1&&y>0&&y<map.height-1&&map.grid[y*2][x*2]===0&&!prev.has(key)){prev.set(key,p);queue.push({x,y});}
    }
  }
  if(!prev.has(`${finish.x},${finish.y}`))throw new Error('Unreachable route target');
  const nodes=[];let p=finish;while(p){nodes.unshift(p);p=prev.get(`${p.x},${p.y}`);}return nodes;
}
export function planRoute(map) {
  let vehicle=initialVehicle(map),logical={x:1,y:1};
  const output=[],visited=new Set(),dt=1/60;
  const apply=(keys,seconds)=>{
    let remaining=seconds;const input=Object.fromEntries(keys.map(k=>[k,true]));
    while(remaining>1e-10){const step=Math.min(dt,remaining);vehicle=stepDriving(map,vehicle,input,step);remaining-=step;}
    const last=output.at(-1);
    if(last?.kind==='drive'&&last.keys.join()===keys.join()&&last.seconds+seconds<=15)last.seconds+=seconds;
    else output.push({kind:'drive',keys,seconds});
  };
  const normalize=a=>Math.atan2(Math.sin(a),Math.cos(a));
  const driveTo=point=>{
    const target=logicalToLite(point);
    const heading=Math.atan2(target.y-vehicle.y,target.x-vehicle.x),error=normalize(heading-vehicle.heading);
    if(Math.abs(error)>1e-10)apply([error>0?'d':'a'],Math.abs(error)/2.8);
    let braking=false;
    for(let tick=0;tick<2000;tick++){
      const distance=Math.hypot(target.x-vehicle.x,target.y-vehicle.y);
      if(distance<1.8&&vehicle.speed<25){if(vehicle.speed>0)apply(['s'],vehicle.speed/620);return;}
      const stopping=vehicle.speed*vehicle.speed/(2*620*12);
      if(distance<=stopping+1.2)braking=true;
      if(braking&&vehicle.speed<25){if(vehicle.speed>0)apply(['s'],vehicle.speed/620);braking=false;continue;}
      const keys=braking?['s']:['w'];
      apply(keys,dt);
      if(vehicle.speed<0)throw new Error('Planner reversed unexpectedly');
    }
    throw new Error('Could not drive to route point '+JSON.stringify(point));
  };
  while(visited.size<5){
    let chosen=-1,best=null;
    map.stations.forEach((station,index)=>{if(visited.has(index))return;const p=path(map,logical,station);if(!best||p.length<best.length){best=p;chosen=index;}});
    // Compress straight logical runs; turn only after braking at a real corner.
    const waypoints=[];
    for(let i=1;i<best.length;i++)if(i===best.length-1||best[i+1].x-best[i].x!==best[i].x-best[i-1].x||best[i+1].y-best[i].y!==best[i].y-best[i-1].y)waypoints.push(best[i]);
    waypoints.forEach(driveTo);logical=map.stations[chosen];visited.add(chosen);
    output.push({kind:'activate',id:`Q${chosen+1}`,expected:{...vehicle}});
  }
  const finishPath=path(map,logical,map.exit),waypoints=[];
  for(let i=1;i<finishPath.length;i++)if(i===finishPath.length-1||finishPath[i+1].x-finishPath[i].x!==finishPath[i].x-finishPath[i-1].x||finishPath[i+1].y-finishPath[i].y!==finishPath[i].y-finishPath[i-1].y)waypoints.push(finishPath[i]);
  waypoints.forEach(driveTo);output.push({kind:'activate',id:'EXIT',expected:{...vehicle}});
  return {seed:map.seed,size:`${map.width}x${map.height}`,steps:output,virtualDistance:vehicle.distance};
}
