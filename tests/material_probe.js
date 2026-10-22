/* Synthetic observations of production materials; never deployed. */
driveTest.render=function(previous,time=0){if(previous)phase5bRender(time);else renderDrive(time);};
window.materialTest={
  long(){
    let best=null;
    for(let y=1;y<current.height-1;y++)for(let x=1;x<current.width-1;x++){
      if(!driveNode(x,y))continue;
      for(const [dx,dy] of [[1,0],[0,1]]){
        let length=0;while(driveNode(x+dx*length,y+dy*length))length++;
        if(!best||length>best.length)best={x,y,dx,dy,length};
      }
    }
    const p=worldCenter(best.x,best.y);drivePose(p.x,p.y,Math.atan2(best.dy,best.dx));return best;
  },
  native(){renderDrive(0);return driveSurface.toDataURL();},
  memory(){
    const m=driveArtwork.materials;
    return {bytes:m.bytes,floorBytes:m.floor.reduce((n,a)=>n+a.byteLength,0),
      wallBytes:m.walls.flat().reduce((n,c)=>n+c.pixels.byteLength,0),
      floorSizes:m.floor.map(a=>Math.sqrt(a.length)),wallSizes:m.walls[0].map(c=>c.size)};
  },
  stability(){
    renderDrive(0);const m=driveArtwork.materials,reference=m.floor.map(a=>Array.from(a));
    const points=[[84.2,84.7],[90.7,114.3],[300.2,240.6],[1200.4,800.2]];
    const samples=()=>points.map(([x,y])=>m.sampleFloor(x,y,1,.35));
    const wallHashes=()=>m.walls.flat().map(t=>Array.from(t.pixels).reduce((n,v)=>Math.imul(n^v,16777619),2166136261)>>>0);
    const before=samples(),beforeWalls=wallHashes(),initial={...current.player},angle=driveAngle;
    const hit=rayHit(initial.x,initial.y,angle,1350),target={x:initial.x+Math.cos(angle)*hit.dist,y:initial.y+Math.sin(angle)*hit.dist};
    const initialU=hit.side?target.x:target.y;
    testKeys(['w']);testStep(90);testKeys(['d']);testStep(35);testKeys([]);renderDrive(.5);
    const moved={...current.player},turned=driveAngle;
    const after=samples(),afterWalls=wallHashes();
    const aim=Math.atan2(target.y-moved.y,target.x-moved.x),other=rayHit(moved.x,moved.y,aim,1350);
    const worldHit={x:moved.x+Math.cos(aim)*other.dist,y:moved.y+Math.sin(aim)*other.dist};
    const wallAnchorError=Math.abs((other.side?worldHit.x:worldHit.y)-initialU);
    Object.assign(current.player,initial);driveAngle=angle;driveSpeed=0;renderDrive(0);
    return {before,after,beforeWalls,afterWalls,wallAnchorError,moved,turned,angle,initial,reused:m===driveArtwork.materials,
      unmodified:reference.every((a,i)=>a.every((v,j)=>v===m.floor[i][j])),
      wrapError:Math.max(...points.map(([x,y])=>Math.abs(m.sampleFloor(x+128,y+128,1,.35)-m.sampleFloor(x,y,1,.35)))),
      variance:m.floor.map(a=>{const mean=a.reduce((n,v)=>n+v,0)/a.length;return a.reduce((n,v)=>n+(v-mean)**2,0)/a.length;})};
  },
  alias(){
    renderDrive(0);const w=driveSurface.width,h=driveSurface.height,first=dctx.getImageData(0,0,w,h).data;
    renderDrive(1);const same=dctx.getImageData(0,0,w,h).data;
    let stationary=0;for(let i=0;i<first.length;i++)if(first[i]!==same[i])stationary++;
    const initial={...current.player},angle=driveAngle;
    current.player.x+=Math.cos(driveAngle)*.02;current.player.y+=Math.sin(driveAngle)*.02;driveAngle+=.0001;
    renderDrive(0);const second=dctx.getImageData(0,0,w,h).data;let costs=[];
    for(let y=Math.floor(h*.15);y<h*.83;y++)for(let x=Math.floor(w*.08);x<w*.92;x++){
      const i=(y*w+x)*4;costs.push(Math.max(...[0,1,2].map(c=>Math.abs(first[i+c]-second[i+c]))));
    }
    costs.sort((a,b)=>a-b);Object.assign(current.player,initial);driveAngle=angle;renderDrive(0);
    return {stationary,mean:costs.reduce((a,b)=>a+b)/costs.length,p95:costs[Math.floor(costs.length*.95)],
      over30:costs.filter(x=>x>30).length/costs.length};
  }
};
