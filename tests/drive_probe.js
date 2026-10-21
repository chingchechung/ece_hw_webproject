/* Test-response-only scene setup/observations. No fixtures or hooks are deployed. */
const driveStates=[],driveNative={frame:0,running:false};
function drivePose(x,y,angle){
  hideDialog();pressed={};testHeld.clear();driveSpeed=0;driveDistance=0;
  Object.assign(current.player,{x,y,moving:false,walk:0});
  if(gameMode!=='drive')toggleMode();driveAngle=angle;fitCamera();findNearby();
  clearTimeout(toastTimer);el('toast').classList.remove('show');
}
function driveNode(x,y){return current.grid[y*2]?.[x*2]===0;}
function driveJunction(kind){
  for(let y=2;y<current.height-2;y++)for(let x=2;x<current.width-2;x++){
    if(!driveNode(x,y))continue;
    for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]]){
      const back=driveNode(x-dx,y-dy),front=driveNode(x+dx,y+dy);
      const left=driveNode(x+dy,y-dx),right=driveNode(x-dy,y+dx);
      const match=kind==='straight'?back&&front&&!left&&!right:
        kind==='left'||kind==='corner'?back&&left&&!right&&!front:
        kind==='right'?back&&right&&!left&&!front:
        kind==='t'?back&&left&&right&&!front:back&&front&&left&&right;
      if(!match)continue;
      const target=worldCenter(x,y),distance=kind==='corner'?24:56;
      const px=target.x-dx*distance,py=target.y-dy*distance;
      if(!canDriveStand(px,py))continue;
      drivePose(px,py,Math.atan2(dy,dx)+(kind==='corner' ? .22 : 0));
      return {node:{x,y},directions:{back,front,left,right},distance};
    }
  }
  throw Error('Missing deterministic '+kind+' scene');
}
function driveStation(index,distance){
  const target=worldCenter(current.stations[index].x,current.stations[index].y);
  for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
    const x=target.x-dx*distance,y=target.y-dy*distance;
    if(canDriveStand(x,y)&&lineVisible(x,y,target.x,target.y)){
      drivePose(x,y,Math.atan2(dy,dx));renderDrive(0);
      const ob=driveObjects()[index];
      if(projectDriveObject(ob,driveSurface.width,driveSurface.height,Math.round(driveSurface.height*.49),driveSurface.width/(2*Math.tan(.67))))return;
    }
  }
  throw Error('No visible station approach at '+distance);
}
window.driveTest={
  state(){return {player:{...current.player},speed:driveSpeed,angle:driveAngle,distance:driveDistance,
    done:[...done],failures,remaining:mapRemainingMs,mode:gameMode,camera:{...camera},zoom:gameZoom,
    unit:assignment,grid:current.grid.map(row=>row.join('')).join('/'),road:Array.from(current.driveRoad.bits),
    modal:modalOpen,pending:!!pendingInteraction,pressed:{...pressed}};},
  snapshot(){return JSON.stringify(this.state());},
  stage(kind){
    done.fill(false);let description={};
    if(['straight','left','right','corner','t','four'].includes(kind))description=driveJunction(kind);
    else if(kind==='near-wall')drivePose(48.5,84,Math.PI);
    else if(kind.startsWith('station')){
      driveStation(0,kind==='station-far'?140:60);
      if(kind==='station-passed')done[0]=true;
    }else if(kind.startsWith('finish')){
      const target=worldCenter(current.exit.x,current.exit.y);
      let found=false;
      for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){
        const x=target.x-dx*60,y=target.y-dy*60;
        if(canDriveStand(x,y)&&lineVisible(x,y,target.x,target.y)){drivePose(x,y,Math.atan2(dy,dx));found=true;break;}
      }
      if(!found)throw Error('No finish approach');
      if(kind==='finish-unlocked')done.fill(true);
    }else throw Error('Unknown scene');
    syncHUD();findNearby();renderDrive(0);
    return {kind,...description,player:{...current.player},angle:driveAngle,seedCounter,maze:[current.width,current.height]};
  },
  render(previous,time=0){if(previous)approvedDriveRender(time);else renderDrive(time);},
  minimap(){return mini.toDataURL();},
  map(value){setMapVisible(value);},
  projections(){
    renderDrive(0);const w=driveSurface.width,h=driveSurface.height;
    return driveObjects().map(ob=>({index:ob.index,finish:ob.finish,pos:ob.pos,
      projection:projectDriveObject(ob,w,h,Math.round(h*.49),w/(2*Math.tan(.67)))}));
  },
  hiddenObject(){
    const w=driveSurface.width,h=driveSurface.height;
    return projectDriveObject({pos:{x:current.player.x-100,y:current.player.y},finish:false},w,h,Math.round(h*.49),w/(2*Math.tan(.67)));
  },
  station(index,distance){done.fill(false);driveStation(index,distance);renderDrive(0);},
  newMaze(w,h){
    current=generateMaze(w,h);buildDriveRoad(current);done=Array(MAX_QUESTS).fill(false);
    current.player={};
    drivePose(84,84,Math.PI/2);syncHUD();renderDrive(0);
  },
  roadAgreement(){
    renderDrive(0);const road=current.driveRoad;let checked=0;
    for(let y=1;y<road.h-1;y++)for(let x=1;x<road.w-1;x++)if(road.bits[y*road.w+x]){
      for(const fraction of [.1,.5,.9]){
        const wx=(x+fraction)*14,wy=(y+fraction)*14,flags=driveArtwork.marks[y*road.w+x];
        if(!!(flags&1)!==(driveRoadAt(wx-56,wy)&&driveRoadAt(wx+56,wy)))throw Error('False horizontal lane');
        if(!!(flags&2)!==(driveRoadAt(wx,wy-56)&&driveRoadAt(wx,wy+56)))throw Error('False vertical lane');
        for(const [bit,dx,dy] of [[4,-1,0],[8,1,0],[16,0,-1],[32,0,1]]){
          if(!!(flags&bit)===driveRoadAt((x+dx+.5)*14,(y+dy+.5)*14))throw Error('False edge light');
        }
        checked++;
      }
    }
    return {checked,maze:[current.width,current.height],questions:done.length};
  },
  depthAgreement(){
    renderDrive(0);const w=driveSurface.width,focal=w/(2*Math.tan(.67));let maxError=0;
    for(let x=0;x<w;x+=2){
      const off=Math.atan((x+.5-w*.5)/focal),hit=rayHit(current.player.x,current.player.y,driveAngle+off,1350);
      if(hit.hit)maxError=Math.max(maxError,Math.abs(driveArtwork.depths[x]-Math.max(88,hit.dist*12*Math.cos(off))));
    }
    return maxError;
  },
  objectAssets(){
    renderDrive(0);const images=driveArtwork.checkpoints;
    const labels=[];
    for(let i=0;i<5;i++){
      const masks=images.map(row=>{
        const a=row[i].getContext('2d').getImageData(16,15,64,23).data,result=[];
        for(let j=0;j<a.length;j+=4)result.push(a[j]===22&&a[j+1]===50&&a[j+2]===68);
        return result;
      });
      labels.push({before:masks[0],after:masks[1],hashes:images.map(row=>pixelHash(row[i]))});
    }
    return {labels,finish:images.map(row=>pixelHash(row[5]))};
  },
  replay(previous){
    const initial={current:structuredClone(current),done:[...done],angle:driveAngle,speed:driveSpeed,distance:driveDistance};
    const frames=[];
    for(const [keys,count] of [[['w'],100],[['s'],90],[['a'],45],[['w','d'],60],[[],45],[['s'],90],[['w'],90]]){
      testKeys(keys);
      for(let i=0;i<count;i++){
        testStep();
        if(i%12===0){const before=this.snapshot();this.render(previous,i/120);if(this.snapshot()!==before)throw Error('Renderer wrote gameplay state');}
        frames.push({player:{...current.player},speed:driveSpeed,angle:driveAngle,distance:driveDistance,remaining:mapRemainingMs});
      }
    }
    testKeys([]);
    current=initial.current;done=initial.done;driveAngle=initial.angle;driveSpeed=initial.speed;driveDistance=initial.distance;
    return frames;
  },
  motionPose(){driveSpeed=360;driveDistance=150;pressed={d:true};},
  async benchmark(previous){
    const base={player:{...current.player},angle:driveAngle,speed:driveSpeed,distance:driveDistance};
    const costs=[],draws=[],raf=[];let last=0;
    driveSpeed=300;
    for(let i=0;i<20;i++)this.render(previous,i/30);
    await new Promise(resolve=>{
      const sample=t=>{
        raf.push(t);
        if(t-last>=32){
          last=t;driveAngle=base.angle+Math.sin(costs.length*.035)*.28;
          const offset=Math.sin(costs.length*.04)*10;
          current.player.x=base.player.x+Math.cos(base.angle)*offset;
          current.player.y=base.player.y+Math.sin(base.angle)*offset;driveDistance=costs.length*10;
          const start=performance.now();this.render(previous,t/1000);costs.push(performance.now()-start);draws.push(t);
        }
        if(costs.length<90)requestAnimationFrame(sample);else resolve();
      };
      requestAnimationFrame(sample);
    });
    Object.assign(current.player,base.player);driveAngle=base.angle;driveSpeed=base.speed;driveDistance=base.distance;renderDrive(0);
    const sorted=[...costs].sort((a,b)=>a-b);
    return {meanRenderMs:costs.reduce((a,b)=>a+b)/costs.length,p95RenderMs:sorted[Math.floor(costs.length*.95)],
      renderedFps:(draws.length-1)*1000/(draws.at(-1)-draws[0]),rafFps:(raf.length-1)*1000/(raf.at(-1)-raf[0]),
      viewport:[innerWidth,innerHeight],surface:[driveSurface.width,driveSurface.height],frames:costs.length,
      floorBytes:driveArtwork.floor.data.byteLength,markBytes:driveArtwork.marks.byteLength,
      atlasBytes:12*96*128*4,depthBytes:driveArtwork.depths.byteLength};
  },
  startVideo(){
    // Find a real corner on a straight approach to Q1; start one cell before
    // that corner. Corridor cells between odd junctions cannot themselves turn.
    const target=current.stations[0];let route=null;
    for(let length=1;length<Math.max(current.width,current.height)&&!route;length++){
      for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]])for(const [ex,ey] of [[-dy,dx],[dy,-dx]]){
        const corner={x:target.x+dx*length,y:target.y+dy*length},start={x:corner.x+ex,y:corner.y+ey};
        let clear=true;
        for(let i=1;i<=length;i++)if(!driveNode(target.x+dx*i,target.y+dy*i))clear=false;
        if(clear&&driveNode(start.x,start.y)){
          const q=worldCenter(target.x,target.y);
          route=[start,corner,{x:target.x,y:target.y,world:{x:q.x+dx*50,y:q.y+dy*50}}];break;
        }
      }
    }
    if(!route)throw Error('No short native question route');
    const first=worldCenter(route[0].x,route[0].y),second=worldCenter(route[1].x,route[1].y);
    // Use 2D setup, then the Python test presses real V before starting motion.
    if(gameMode==='drive')toggleMode();Object.assign(current.player,first,{moving:false,walk:0});
    driveAngle=Math.atan2(second.y-first.y,second.x-first.x);
    current.player.dir=Math.abs(second.x-first.x)>0?(second.x>first.x?'right':'left'):(second.y>first.y?'down':'up');
    fitCamera();findNearby();render(0);driveNative.route=route;return route;
  },
  runVideo(){
    driveNative.running=true;driveNative.index=1;driveNative.events=[];lastFrame=performance.now();requestAnimationFrame(frame);
    const control=()=>{
      if(!driveNative.running)return;
      const point=driveNative.route[driveNative.index];
      if(!point){testKeys([]);driveNative.running=false;return;}
      const target=point.world||worldCenter(point.x,point.y),p=current.player,distance=Math.hypot(target.x-p.x,target.y-p.y);
      const delta=Math.atan2(Math.sin(Math.atan2(target.y-p.y,target.x-p.x)-driveAngle),Math.cos(Math.atan2(target.y-p.y,target.x-p.x)-driveAngle));
      let keys=[];
      if(distance<2.2&&Math.abs(driveSpeed)<10){
        if(driveSpeed===0){driveNative.events.push({event:'stopped',index:driveNative.index,player:{...p},time:performance.now()});driveNative.index++;}
      }else if(Math.abs(delta)>.05&&Math.abs(driveSpeed)<1.4){keys=[delta>0?'d':'a'];}
      else if(Math.abs(delta)>.15&&Math.abs(driveSpeed)>=10){keys=['s'];}
      else{
        const stopping=driveSpeed*driveSpeed/(2*620*12)+Math.max(0,driveSpeed)/12*.05;
        if(driveSpeed<0)keys=['w'];else if(distance>stopping+1.2)keys=['w'];else if(driveSpeed>=10)keys=['s'];
        if(Math.abs(delta)>.05&&keys.includes('w'))keys.push(delta>0?'d':'a');
      }
      testKeys(keys);driveNative.frame=requestAnimationFrame(control);
    };
    requestAnimationFrame(control);
  },
  videoState(){return {running:driveNative.running,route:driveNative.route,events:driveNative.events,stats:{...routeStats,keys:[...routeStats.keys]},...this.state()};}
};
