/* Test-response-only deterministic clock and control driver; never deployed.
 * Player coordinates, speed and angle are read-only to this driver.
 * Every movement goes through keyboard events and the real update(dt).
 */
const testHeld = new Set();
const routeStats = {frames:0,edges:0,turns:0,walkEdges:0,driveEdges:0,keys:new Set()};
function testKeys(keys) {
  for(const key of testHeld) if(!keys.includes(key)) {
    window.dispatchEvent(new KeyboardEvent('keyup',{key:key,bubbles:true}));
    testHeld.delete(key);
  }
  for(const key of keys) if(!testHeld.has(key)) {
    window.dispatchEvent(new KeyboardEvent('keydown',{key:key,bubbles:true}));
    testHeld.add(key);routeStats.keys.add(key);
  }
}
function testStep(dt=1/120) {
  updateMapBudget(mapLastTick+dt*1000);
  update(dt);routeStats.frames++;
}
function testDraw() {
  if(gameMode==='drive')renderDrive(0);else render(0);
}
function testPath(target) {
  const start={x:Math.round(current.player.x/56-.5),y:Math.round(current.player.y/56-.5)};
  const key=p=>p.x+','+p.y,queue=[start],previous=new Map([[key(start),null]]);
  for(let i=0;i<queue.length&&!previous.has(key(target));i++) {
    const p=queue[i];
    for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
      const n={x:p.x+dx,y:p.y+dy};
      if(current.grid[n.y*2]?.[n.x*2]===0&&!previous.has(key(n))) {
        previous.set(key(n),p);queue.push(n);
      }
    }
  }
  if(!previous.has(key(target)))throw Error('No route to target');
  const path=[];
  for(let p=target;p;p=previous.get(key(p)))path.push(p);
  return path.reverse();
}
function testWalkTo(point) {
  const target=worldCenter(point.x,point.y),p=current.player;
  for(const axis of ['x','y']) {
    for(let n=0;Math.abs(target[axis]-p[axis])>.0001;n++) {
      if(n>300)throw Error('Walking collision on route '+JSON.stringify(point));
      const delta=target[axis]-p[axis];
      const wasd=routeStats.edges%2===0;
      const key=axis==='x'?(delta>0?(wasd?'d':'ArrowRight'):(wasd?'a':'ArrowLeft')):
        (delta>0?(wasd?'s':'ArrowDown'):(wasd?'w':'ArrowUp'));
      testKeys([key]);testStep(Math.min(1/120,Math.abs(delta)/175));
    }
  }
  testKeys([]);testStep();routeStats.walkEdges++;
}
function testDriveTo(point) {
  const target=worldCenter(point.x,point.y),p=current.player;
  let delta=()=>Math.atan2(Math.sin(Math.atan2(target.y-p.y,target.x-p.x)-driveAngle),
                          Math.cos(Math.atan2(target.y-p.y,target.x-p.x)-driveAngle));
  if(Math.hypot(target.x-p.x,target.y-p.y)<.4)return;
  let turns=0;
  while(Math.abs(delta())>.000001) {
    if(turns++>200)throw Error('Could not turn at junction');
    testKeys([delta()>0?'d':'a']);testStep(Math.min(1/120,Math.abs(delta())/2.8));
  }
  if(turns>2)routeStats.turns++;
  testKeys([]);
  for(let n=0;;n++) {
    const distance=Math.hypot(target.x-p.x,target.y-p.y);
    if(distance<.36&&driveSpeed===0)break;
    if(n>6000)throw Error('Driving stuck '+JSON.stringify({point,player:p,driveSpeed,distance}));
    const stopping=driveSpeed*driveSpeed/(2*620*DRIVE_SCALE)+Math.max(0,driveSpeed)/DRIVE_SCALE/120;
    if(distance>stopping+.32) {
      testKeys(['w']);testStep();
    } else if(driveSpeed>0) {
      testKeys(['s']);testStep(Math.min(1/120,driveSpeed/620));
    } else break;
  }
  testKeys([]);testStep();routeStats.driveEdges++;
  if(Math.hypot(target.x-p.x,target.y-p.y)>1)throw Error('Driver missed waypoint');
}
window.gameplayTest={
  state:()=>({unit:assignment,done,failures,mode:gameMode,player:current?.player,
    stations:current?.stations,exit:current?.exit,width:current?.width,height:current?.height,
    speed:driveSpeed,angle:driveAngle,remaining:mapRemainingMs,map:showMap,paused:assignmentPaused,
    camera:{...camera},zoom:gameZoom,distance:driveDistance,pressed:{...pressed}}),
  step(frames){for(let i=0;i<frames;i++)testStep();testDraw();},
  route(index){
    const point=index===null?current.exit:current.stations[index];
    const path=testPath(point);
    for(const p of path){if(gameMode==='drive')testDriveTo(p);else testWalkTo(p);routeStats.edges++;}
    findNearby();testDraw();
    return {edges:path.length,frames:routeStats.frames,turns:routeStats.turns,
      walkEdges:routeStats.walkEdges,driveEdges:routeStats.driveEdges,keys:[...routeStats.keys]};
  },
  draw:testDraw,
  generate:generateMaze,buildRoad:buildDriveRoad
};
