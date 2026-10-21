/* Test-response-only visual staging and pixel measurements. Never deployed. */
const focusMaze={grid:Array.from({length:38},()=>Array(50).fill(0)),stations:[],
  exit:{x:1000,y:1000},player:{x:260,y:200,dir:'right',moving:false,walk:0}};
const priorVisuals=PreviousPhase5aVisuals.create(TILE);
const refinedVisuals=MazeRpgVisuals.create(TILE);
function probeCanvas(renderer,maze,time,zoom=1.5,camera={x:100,y:80},map=false){
  const c=document.createElement('canvas');c.width=600;c.height=420;
  renderer.render(c.getContext('2d'),maze,maze.stations.map(()=>false),camera,zoom,{w:600,h:420},time,null,map);return c;
}
function luminanceAt(c,x,y){
  const p=c.getContext('2d').getImageData(Math.round(x),Math.round(y),1,1).data;
  return p[0]*.2126+p[1]*.7152+p[2]*.0722;
}
window.refineTest={
 focus(zoom,x,y,camera,map=false){
   Object.assign(focusMaze.player,{x,y});
   const before=probeCanvas(priorVisuals,focusMaze,0,zoom,camera),after=probeCanvas(refinedVisuals,focusMaze,0,zoom,camera,map);
   const cx=x*zoom-Math.round(camera.x*zoom),cy=(y-8)*zoom-Math.round(camera.y*zoom);
   const corners=[[20,20],[580,20],[20,400],[580,400]].sort((a,b)=>Math.hypot(b[0]-cx,b[1]-cy)-Math.hypot(a[0]-cx,a[1]-cy));
   const ratio=(px,py)=>luminanceAt(after,px,py)/luminanceAt(before,px,py);
   return {center:[cx,cy],near:ratio(cx+45,cy+35),far:ratio(...corners[0]),left:ratio(165,225),right:ratio(495,225)};
 },
 swipe(dir){
   const maze={...focusMaze,stations:[{x:1000,y:1000}],player:{x:300,y:240,dir,moving:false,walk:0}};
   refinedVisuals.clearInteraction();const before=probeCanvas(refinedVisuals,maze,10);
   const started=refinedVisuals.beginInteraction(maze,0,10),during=probeCanvas(refinedVisuals,maze,10.08);
   const expired=probeCanvas(refinedVisuals,maze,10.25);
   refinedVisuals.clearInteraction();const clean=probeCanvas(refinedVisuals,maze,10.25);
   const a=before.getContext('2d').getImageData(0,0,600,420).data,b=during.getContext('2d').getImageData(0,0,600,420).data;
   let sx=0,sy=0,n=0;
   for(let i=0;i<a.length;i+=4)if(a[i]!==b[i]||a[i+1]!==b[i+1]||a[i+2]!==b[i+2]){
     sx+=(i/4)%600;sy+=Math.floor(i/4/600);n++;
   }
   return {started,changed:n,offset:n?[sx/n-300,sy/n-229.5]:[0,0],during:pixelHash(during),
     expired:pixelHash(expired),clean:pixelHash(clean)};
 },
 stage(dir){
   hideDialog();done.fill(false);syncHUD();
   const offsets={right:[-36,0],left:[36,0],down:[0,-36],up:[0,36]},d=offsets[dir];
   let index=current.stations.findIndex(s=>{const p=worldCenter(s.x,s.y);return canStand(p.x+d[0],p.y+d[1]);});
   if(index<0){visualTest.approach();index=0;current.player.dir=dir;}
   else{
     const p=worldCenter(current.stations[index].x,current.stations[index].y);
     Object.assign(current.player,{x:p.x+d[0],y:p.y+d[1],dir,moving:false,walk:0});
   }
   clearTimeout(toastTimer);el('toast').classList.remove('show');
   fitCamera();findNearby();rpgVisuals.beginInteraction(current,index,10);render(10.08);
 },
 states(){
   const c=document.createElement('canvas');c.width=96;c.height=96;const g=c.getContext('2d');
   const sample=(kind,passed,t)=>{g.clearRect(0,0,96,96);
     if(kind==='exit')rpgVisuals.drawExit(g,48,55,passed,t,false);
     else rpgVisuals.drawStation(g,48,55,0,passed,t,true);return pixelHash(c);};
   return {idle:[sample('q',false,0),sample('q',false,.6)],
     passed:[sample('q',true,0),sample('q',true,.6)],
     locked:sample('exit',false,0),unlocked:sample('exit',true,0)};
 },
 labelCheck(){
   const maze={...focusMaze,stations:[{x:6,y:4}],player:{...focusMaze.player,x:180,y:210}};
   refinedVisuals.clearInteraction();const before=probeCanvas(refinedVisuals,maze,10);
   refinedVisuals.beginInteraction(maze,0,10);const after=probeCanvas(refinedVisuals,maze,10.08);
   const label=c=>Array.from(c.getContext('2d').getImageData(378,197,36,20).data);
   refinedVisuals.clearInteraction();return {before:label(before),after:label(after)};
 },
 modal(){return {open:modalOpen,active:activeQuestion,cue:el('veil').classList.contains('interaction-cue'),
   opacity:getComputedStyle(el('dialog')).opacity,pressed:{...pressed},speed:driveSpeed,paused:assignmentPaused};},
 map(value){setMapVisible(value);render(0);},
 screenPlayer(){return {x:(current.player.x-camera.x)*gameZoom,y:(current.player.y-8-camera.y)*gameZoom};},
 async benchmark(interactions=false){
   rpgVisuals.clearInteraction?.();
   for(let i=0;i<40;i++)render(i/60);
   const costs=[],timestamps=[],baseX=camera.x,baseY=camera.y;
   await new Promise(resolve=>{
     function sample(t){
       camera.x=baseX+Math.sin(costs.length*.04)*28;camera.y=baseY+Math.cos(costs.length*.04)*18;
       const start=performance.now();
       if(interactions&&costs.length%30===0)rpgVisuals.beginInteraction(current,0,t/1000);
       render(t/1000);costs.push(performance.now()-start);timestamps.push(t);
       if(costs.length<120)requestAnimationFrame(sample);else resolve();
     }
     requestAnimationFrame(sample);
   });
   camera.x=baseX;camera.y=baseY;rpgVisuals.clearInteraction?.();render(0);
   const sorted=[...costs].sort((a,b)=>a-b);
   return {viewport:[innerWidth,innerHeight],zoom:gameZoom,maze:[current.width,current.height],
     meanRenderMs:costs.reduce((a,b)=>a+b,0)/costs.length,p95RenderMs:sorted[Math.floor(costs.length*.95)],
     observedFps:(timestamps.length-1)*1000/(timestamps.at(-1)-timestamps[0]),
     workload:interactions?'camera sweep + repeated 0.2s interactions':'camera sweep + nearby incomplete station'};
 }
};
// Observe the real keyboard handler in the same event turn, before a slow
// screenshot or host scheduling can consume the 160ms presentation cue.
window.addEventListener('keydown',event=>{
  if(event.key.toLowerCase()==='e')refineTest.keyModal=refineTest.modal();
});
