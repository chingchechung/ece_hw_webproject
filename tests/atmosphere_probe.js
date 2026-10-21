/* Test HTTP-response bridge only: production E/RAF/modal path stays intact. */
const quietVisuals=MazeRpgVisuals.create(TILE),comparisonFrames=[];
let lastAtmosphereRenderTime=0;
const actual2dRender=render,actualOpenQuestion=openQuestion;
render=function(time){lastAtmosphereRenderTime=time;actual2dRender(time);};
openQuestion=function(index){atmosphereTest.events.push({event:'question',index,time:performance.now()});actualOpenQuestion(index);};
function comparisonCanvas(renderer,time){
  const c=document.createElement('canvas');c.width=canvas.width;c.height=canvas.height;
  const g=c.getContext('2d');g.setTransform(ctx.getTransform());
  renderer.render(g,current,done,camera,gameZoom,viewport,time,nearItem,showMap);return c;
}
function changedPixels(a,b){
  const x=a.getContext('2d').getImageData(0,0,a.width,a.height).data;
  const y=b.getContext('2d').getImageData(0,0,b.width,b.height).data;
  let count=0;for(let i=0;i<x.length;i+=4)if(x[i]!==y[i]||x[i+1]!==y[i+1]||x[i+2]!==y[i+2]||x[i+3]!==y[i+3])count++;
  return count;
}
window.atmosphereTest={
 events:[],
 state(){return {pending:pendingInteraction?{index:pendingInteraction.index,start:pendingInteraction.start,revealAt:pendingInteraction.revealAt}:null,
   now:performance.now(),modal:modalOpen,active:activeQuestion,answers:el('dialog').querySelectorAll('[data-answer]').length,
   veil:el('veil').classList.contains('show'),mode:gameMode,atmosphere:atmosphereMode,player:{...current?.player},
   unit:assignment?.unitId,done:[...done],remaining:mapRemainingMs,paused:assignmentPaused,pressed:{...pressed}};},
 close(){hideDialog();},
 mode(value){setAtmosphere(value,false);},
 advanceGameplay(){updateMapBudget(performance.now());update(.1);},
 reset(){newRound(true);},
 hidden(value){Object.defineProperty(document,'hidden',{configurable:true,get:()=>value});document.dispatchEvent(new Event('visibilitychange'));},
 offParity(){render(12);return changedPixels(canvas,comparisonCanvas(priorVisuals,12));},
 effectPixels(){quietVisuals.setAtmosphere(atmosphereMode);return changedPixels(canvas,comparisonCanvas(quietVisuals,lastAtmosphereRenderTime));},
 light(mode,zoom,x,y,camera,map=false){
   refinedVisuals.setAtmosphere(mode);Object.assign(focusMaze.player,{x,y});
   const a=probeCanvas(priorVisuals,focusMaze,0,zoom,camera),b=probeCanvas(refinedVisuals,focusMaze,0,zoom,camera,map);
   const cx=x*zoom-Math.round(camera.x*zoom),cy=(y-8)*zoom-Math.round(camera.y*zoom);
   const corners=[[20,20],[580,20],[20,400],[580,400]].sort((a,b)=>Math.hypot(b[0]-cx,b[1]-cy)-Math.hypot(a[0]-cx,a[1]-cy));
   const ratio=(px,py)=>luminanceAt(b,px,py)/luminanceAt(a,px,py);
   return {near:ratio(cx+45,cy+35),far:ratio(...corners[0]),left:ratio(165,225),right:ratio(495,225)};
 },
 rememberFrame(label){const c=document.createElement('canvas');c.width=canvas.width;c.height=canvas.height;
   c.getContext('2d').drawImage(canvas,0,0);comparisonFrames.push({label,canvas:c});},
 modeSheet(){
   const [c,g]=sheet(1440,260);g.fillText('SAME MAZE / CAMERA / PLAYER / ZOOM — ATMOSPHERE',16,24);
   comparisonFrames.forEach((f,i)=>{g.fillStyle='#253e50';g.fillText(f.label.toUpperCase(),16+i*480,48);
     g.drawImage(f.canvas,8+i*480,58,464,194);});
 },
 async benchmark(renderer,actions=false){
   const original=rpgVisuals;
   if(renderer==='phase5a1')rpgVisuals=PreviousRefinedVisuals.create(TILE);
   try{return await refineTest.benchmark(actions);}finally{rpgVisuals=original;render(0);}
 }
};
window.addEventListener('keydown',event=>{
  if(event.key.toLowerCase()==='e')atmosphereTest.events.push({event:'E',...atmosphereTest.state()});
});
