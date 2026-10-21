/* Synthetic HTTP-response bridge; effects are started only by real E input. */
const slashCalls=[],originalSlashVisuals=rpgVisuals;
let observedSlash=null;
rpgVisuals=Object.freeze({...originalSlashVisuals,
  beginSlash(...args){
    const duration=originalSlashVisuals.beginSlash(...args);
    observedSlash={event:'slash',args:args.length,time:performance.now(),duration,dir:current.player.dir};
    slashCalls.push(observedSlash);
    return duration;
  },
  activateStation(...args){slashCalls.push({event:'activation',index:args[1],time:performance.now()});return originalSlashVisuals.activateStation(...args);}
});
const approvedLight=ApprovedPhase5a2Visuals.create(TILE),parityVisuals=MazeRpgVisuals.create(TILE);
window.slashTest={
  calls:slashCalls,
  state(){return {...atmosphereTest.state(),slashing:rpgVisuals.isSlashing(performance.now()/1000),
    near:nearItem,failures,grid:pixelGrid(),positionSafe:canStand(current.player.x,current.player.y)};},
  startFrames(){lastFrame=performance.now();requestAnimationFrame(frame);},
  corridor(dir){
    clearInteractionCue();hideDialog();pressed={};
    const target=worldCenter(current.stations[0].x,current.stations[0].y);
    const choices=[[-1,0,'ArrowRight','right'],[1,0,'ArrowLeft','left'],[0,-1,'ArrowDown','down'],[0,1,'ArrowUp','up']];
    for(const distance of [140,112,84])for(const [dx,dy,key,facing] of choices){
      const x=target.x+dx*distance,y=target.y+dy*distance;
      if(!canStand(x,y))continue;
      let clear=true;
      for(let step=0;step<=distance;step+=4)if(!canStand(target.x+dx*step,target.y+dy*step))clear=false;
      if(!clear)continue;
      Object.assign(current.player,{x,y,dir:dir||facing,moving:false,walk:0});fitCamera();findNearby();
      if(nearItem)continue;
      clearTimeout(toastTimer);el('toast').classList.remove('show');render(performance.now()/1000);
      return {key,dir:facing,distance,target,start:{x,y}};
    }
    throw new Error('Synthetic seed has no clear empty approach corridor');
  },
  station(completed){
    clearInteractionCue();visualTest.approach();done[0]=completed;syncHUD();findNearby();
    current.player.dir='right';current.player.moving=false;current.player.walk=0;render(performance.now()/1000);
  },
  start(){clearInteractionCue();Object.assign(current.player,worldCenter(1,1),{dir:'up',moving:false,walk:0});pressed={};fitCamera();findNearby();},
  finish(){clearInteractionCue();Object.assign(current.player,worldCenter(current.exit.x,current.exit.y));fitCamera();findNearby();},
  effect(){
    quietVisuals.setAtmosphere(atmosphereMode);
    const clean=comparisonCanvas(quietVisuals,lastAtmosphereRenderTime);
    const a=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
    const b=clean.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
    let n=0,sx=0,sy=0,minX=canvas.width,minY=canvas.height,maxX=0,maxY=0,hash=2166136261;
    for(let i=0;i<a.length;i+=4){
      const changed=a[i]!==b[i]||a[i+1]!==b[i+1]||a[i+2]!==b[i+2];hash=Math.imul(hash^Number(changed),16777619);
      if(changed){const x=(i/4)%canvas.width,y=Math.floor(i/4/canvas.width);n++;sx+=x;sy+=y;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
    }
    const player=refineTest.screenPlayer();
    return {pixels:n,mask:hash>>>0,offset:n?[sx/n-player.x,sy/n-player.y]:[0,0],box:[minX,minY,maxX-minX+1,maxY-minY+1]};
  },
  lightingParity(mode,zoom,map){
    approvedLight.setAtmosphere(mode);parityVisuals.setAtmosphere(mode);
    function sample(renderer){
      const c=document.createElement('canvas');c.width=canvas.width;c.height=canvas.height;
      const g=c.getContext('2d');g.setTransform(ctx.getTransform());
      renderer.render(g,current,done,camera,zoom,viewport,12,nearItem,map);return c;
    }
    return changedPixels(sample(approvedLight),sample(parityVisuals));
  }
};
function pixelGrid(){return current.grid.map(row=>row.join('')).join('/');}
// Observe native drawing once per action, inside a real production render.
// Python/CI can pause between protocol calls longer than this short effect.
const renderForSlashEvidence=render;
render=function(time){
  renderForSlashEvidence(time);
  if(observedSlash&&!observedSlash.sample&&observedSlash.duration>0){
    const ageMs=time*1000-observedSlash.time;
    if(ageMs>=150&&ageMs<400){
      observedSlash.sample={ageMs,pending:!!pendingInteraction,modal:modalOpen,player:{...current.player},...slashTest.effect()};
    }
  }
};
