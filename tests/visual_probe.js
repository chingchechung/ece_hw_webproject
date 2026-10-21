window.visualTest={
 state:()=>JSON.stringify({grid:current.grid,stations:current.stations,player:current.player,
   done,failures,camera,zoom:gameZoom,mode:gameMode,remaining:mapRemainingMs}),
 draw(time=0){if(gameMode==='2d')render(time);else renderDrive(time);},
 overview(){
   sizeCanvas();
   const s=current.stations[0];let p=s;
   for(const [dx,dy] of [[1,0],[0,1],[-1,0],[0,-1]])if(current.grid[(s.y+dy)*2]?.[(s.x+dx)*2]===0){p={x:s.x+dx,y:s.y+dy};break;}
   Object.assign(current.player,worldCenter(p.x,p.y));current.player.dir='down';
   current.player.moving=false;current.player.walk=0;fitCamera();findNearby();
   clearTimeout(toastTimer);el('toast').classList.remove('show');const start=performance.now();render(0);
   if(window.__firstSceneMs===undefined)window.__firstSceneMs=performance.now()-start;
 },
 parkExit(){
   const e=current.exit;
   const p=current.grid[e.y*2][(e.x-1)*2]===0?{x:e.x-1,y:e.y}:{x:e.x,y:e.y-1};
   Object.assign(current.player,worldCenter(p.x,p.y));current.player.dir='right';fitCamera();findNearby();render(0);
 },
 intersection(){
   let best=null;
   for(let y=1;y<current.height-1;y++)for(let x=1;x<current.width-1;x++)if(current.grid[y*2][x*2]===0){
     const degree=[[1,0],[-1,0],[0,1],[0,-1]].filter(([dx,dy])=>current.grid[(y+dy)*2]?.[(x+dx)*2]===0).length;
     const score=Math.abs(x-current.width/2)+Math.abs(y-current.height/2);
     if(degree>=3&&(!best||score<best.score))best={x,y,degree,score};
   }
   Object.assign(current.player,worldCenter(best.x,best.y));fitCamera();findNearby();render(0);return best;
 },
 step(n){for(let i=0;i<n;i++)update(1/60);render(0);},
 pixels(){return canvas.toDataURL('image/png');},
 passAll(){done.fill(true);syncHUD();findNearby();render(0);},
 passFirst(){done[0]=true;syncHUD();findNearby();render(0);},
 approach(){visualTest.overview();const s=worldCenter(current.stations[0].x,current.stations[0].y);
   current.player.x=s.x+.75*(current.player.x-s.x);current.player.y=s.y+.75*(current.player.y-s.y);fitCamera();findNearby();render(0);},
 async ready(){if(typeof playerSheet!=='undefined'&&!playerSheet.complete)await new Promise(r=>{playerSheet.onload=r;});},
 async benchmark(){
   const firstStart=performance.now();render(0);const firstDrawMs=performance.now()-firstStart;
   for(let i=0;i<40;i++)render(i/60);
   const costs=[],timestamps=[],baseX=camera.x,baseY=camera.y;
   await new Promise(resolve=>{
     function sample(t){camera.x=baseX+Math.sin(costs.length*.04)*28;camera.y=baseY+Math.cos(costs.length*.04)*18;
       const start=performance.now();render(t/1000);costs.push(performance.now()-start);timestamps.push(t);
       if(costs.length<120)requestAnimationFrame(sample);else resolve();}
     requestAnimationFrame(sample);
   });
   camera.x=baseX;camera.y=baseY;render(0);
   const sorted=[...costs].sort((a,b)=>a-b);
   return {viewport:[innerWidth,innerHeight],zoom:gameZoom,maze:[current.width,current.height],
     meanRenderMs:costs.reduce((a,b)=>a+b,0)/costs.length,p95RenderMs:sorted[Math.floor(costs.length*.95)],
     observedFps:(timestamps.length-1)*1000/(timestamps.at(-1)-timestamps[0]),firstDrawMs,
     artworkSetupMs:window.__assetMs||0,firstSceneRenderMs:window.__firstSceneMs,workload:'camera sweep, idle player, animated station lights'};
 }
};

function previewSprite(dir,moving,walk,time=0){
  const c=document.createElement('canvas');c.width=48;c.height=56;
  const g=c.getContext('2d');g.imageSmoothingEnabled=false;
  rpgVisuals.drawCharacter(g,{x:24,y:29,dir,moving,walk},time);return c;
}
function previewObject(kind,passed,near=false){
  const c=document.createElement('canvas');c.width=96;c.height=96;
  const g=c.getContext('2d');g.imageSmoothingEnabled=false;
  if(kind==='exit')rpgVisuals.drawExit(g,48,55,passed,0,near);
  else rpgVisuals.drawStation(g,48,55,kind,passed,0,near);
  return c;
}
function pixelHash(c){
  let hash=2166136261;const pixels=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
  for(const p of pixels)hash=Math.imul(hash^p,16777619);return hash>>>0;
}
function sheet(w,h){
  document.getElementById('visualSheet')?.remove();
  const c=document.createElement('canvas');c.width=w;c.height=h;c.id='visualSheet';
  c.style.cssText='position:fixed;left:10px;top:10px;z-index:30';
  document.body.append(c);const g=c.getContext('2d');g.imageSmoothingEnabled=false;
  g.fillStyle='#e7ecdf';g.fillRect(0,0,w,h);g.fillStyle='#253e50';g.font='bold 16px monospace';
  return [c,g];
}
visualTest.characterSheet=function(){
  const [c,g]=sheet(1010,820),directions=['down','left','right','up'],result=[];
  const frames=[{moving:false,walk:0,t:0},{moving:false,walk:0,t:1.3},
    ...[0,1.3,2.6,3.9].map(walk=>({moving:true,walk,t:0}))];
  g.fillText('ORIGINAL LAB STUDENT / idle + walk cycle',24,27);
  for(let row=0;row<4;row++){
    const hashes=[];g.fillStyle='#253e50';g.fillText(directions[row],16,92+row*190);
    for(let column=0;column<6;column++){
      const f=frames[column],sprite=previewSprite(directions[row],f.moving,f.walk,f.t);
      g.fillStyle='#cbd8cc';g.fillRect(100+column*148,46+row*190,144,168);
      g.drawImage(sprite,100+column*148,46+row*190,144,168);hashes.push(pixelHash(sprite));
    }
    result.push(hashes);
  }
  return result;
};
visualTest.closeup=function(){const [c,g]=sheet(240,280);g.drawImage(previewSprite('down',false,0),0,0,240,280);};
visualTest.objectSheet=function(){
  const [c,g]=sheet(940,670),items=[[0,false],[0,true],['exit',false],['exit',true],[4,false],[4,true]],hashes=[];
  g.fillText('LAB TERMINALS / LOCKED + UNLOCKED EXIT',20,28);
  for(let i=0;i<6;i++){
    const [kind,passed]=items[i],x=16+(i%3)*310,y=46+Math.floor(i/3)*310;
    g.fillStyle='#253e50';g.fillText((kind==='exit'?'EXIT':'Q'+(kind+1))+' / '+(kind==='exit'?(passed?'UNLOCKED':'LOCKED'):(passed?'PASSED':'INCOMPLETE')),x+12,y+18);
    const c=previewObject(kind,passed);g.drawImage(c,x,y+24,288,288);hashes.push(pixelHash(c));
  }
  const labelMask=passed=>{
    const pixels=previewObject(0,passed).getContext('2d').getImageData(41,16,14,10).data,result=[];
    for(let i=0;i<pixels.length;i+=4)result.push(pixels[i]===37&&pixels[i+1]===62&&pixels[i+2]===80);
    return result;
  };
  return {hashes,labelBefore:labelMask(false),labelAfter:labelMask(true),
    nearHash:pixelHash(previewObject(0,false,true)),farHash:pixelHash(previewObject(0,false,false))};
};
visualTest.removeSheet=function(){document.getElementById('visualSheet')?.remove();};
