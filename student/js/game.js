(function(){
  'use strict';
  var TILE=28, DRIVE_SCALE=12, DRIVE_TILE=14, DRIVE_TOP_SPEED=590, MAZE_SIZES=[[25,19],[21,15],[17,13],[13,9]], MAX_QUESTS=0, gameZoom=1.5;
  // Keep the validated public unit intact, including v2 accepted-label arrays.
  var assignment=null, assignmentPaused=false, FORM_URL='', QUESTIONS=[];
  var el=function(id){return document.getElementById(id)};
  var canvas=el('maze'),ctx=canvas.getContext('2d'),mini=el('minimap'),mctx=mini.getContext('2d');
  var current=null, failures=0, done=[], pressed={}, modalOpen=false, activeQuestion=-1, showMap=false, nearItem=null;
  var pendingInteraction=null,interactionFrame=0,atmosphereMode='strong',ATMOSPHERE_KEY='emi-maze.atmosphere';
  var motionPreference=window.matchMedia('(prefers-reduced-motion: reduce)');
  try{var savedAtmosphere=localStorage.getItem(ATMOSPHERE_KEY);if(['off','normal','strong'].includes(savedAtmosphere))atmosphereMode=savedAtmosphere;}catch(ignore){}
  var MAP_LIMIT_MS=30000, mapRemainingMs=MAP_LIMIT_MS, mapLastTick=null;
  var viewport={w:850,h:560}, camera={x:0,y:0}, lastFrame=0, toastTimer=null, seedCounter=0;
  var gameMode='2d', driveAngle=Math.PI/2, driveSpeed=0, driveDistance=0, driveRenderAt=0, driveTurn=0;
  var driveSurface=document.createElement('canvas'),dctx=driveSurface.getContext('2d',{alpha:false});
  function randomizer(seed){var a=seed>>>0;return function(){a^=a<<13;a^=a>>>17;a^=a<<5;return (a>>>0)/4294967296}}
  function shuffle(items,rnd){for(var i=items.length-1;i>0;i--){var j=Math.floor(rnd()*(i+1)),t=items[i];items[i]=items[j];items[j]=t}return items}
  function generateMaze(w,h){
    var rnd=randomizer(((Date.now()+Math.floor(Math.random()*999999)+seedCounter++*9973)>>>0)||29);
    var maze=Array.from({length:h},function(){return Array(w).fill(1)});
    var stack=[[1,1]];maze[1][1]=0;
    while(stack.length){var p=stack[stack.length-1], dirs=shuffle([[2,0],[-2,0],[0,2],[0,-2]],rnd), found=false;
      for(var j=0;j<dirs.length;j++){var nx=p[0]+dirs[j][0],ny=p[1]+dirs[j][1];if(nx>0&&nx<w-1&&ny>0&&ny<h-1&&maze[ny][nx]){maze[p[1]+dirs[j][1]/2][p[0]+dirs[j][0]/2]=0;maze[ny][nx]=0;stack.push([nx,ny]);found=true;break}}
      if(!found)stack.pop();
    }
    // Create loops in roughly a fifth of candidate dividers so the map is not exhausting to explore.
    var dividers=[];
    for(var y=1;y<h-1;y++)for(var x=1;x<w-1;x++){if(maze[y][x]!==1)continue;
      if((x%2===0&&y%2===1&&maze[y][x-1]===0&&maze[y][x+1]===0)||(x%2===1&&y%2===0&&maze[y-1][x]===0&&maze[y+1][x]===0))dividers.push([x,y]);
    }
    shuffle(dividers,rnd);for(var i=0;i<Math.floor(dividers.length*.22);i++)maze[dividers[i][1]][dividers[i][0]]=0;
    // Logical tiles are upscaled 2x2. This increases display size, not maze branching.
    var fine=Array.from({length:h*2},function(_,yy){return Array.from({length:w*2},function(_,xx){return maze[Math.floor(yy/2)][Math.floor(xx/2)]})});
    // Spread question stations across the four general areas, but vary
    // their precise positions every round. Randomizing labels also prevents Q1
    // from always appearing in the same corner.
    var regions=[[],[],[],[]],start={x:1,y:1},finish={x:w-2,y:h-2};
    for(var cy=1;cy<h-1;cy+=2)for(var cx=1;cx<w-1;cx+=2){
      if(maze[cy][cx]!==0||(cx===start.x&&cy===start.y)||(cx===finish.x&&cy===finish.y))continue;
      var zone=(cy<h/2?0:2)+(cx<w/2?0:1);
      regions[zone].push({x:cx,y:cy});
    }
    var selected=[];
    regions.forEach(function(candidates,zone){
      if(!candidates.length)return;
      // Each region has a new target on every generation rather than a fixed
      // 23%/77% anchor. Favor a nearby candidate, with some random variation.
      var left=zone%2===0,top=zone<2;
      var tx=(w-1)*(left ? .16+rnd()*.29 : .55+rnd()*.29);
      var ty=(h-1)*(top ? .16+rnd()*.29 : .55+rnd()*.29);
      var scored=candidates.map(function(p){
        var distance=Math.hypot(p.x-tx,p.y-ty);
        var startDist=Math.abs(p.x-1)+Math.abs(p.y-1);
        var finishDist=Math.abs(p.x-finish.x)+Math.abs(p.y-finish.y);
        var crowding=selected.some(function(q){return Math.abs(p.x-q.x)+Math.abs(p.y-q.y)<4})?10:0;
        return {x:p.x,y:p.y,score:distance+(startDist<4?7:0)+(finishDist<4?4:0)+crowding+rnd()*1.5};
      }).sort(function(a,b){return a.score-b.score});
      // Pick randomly among the best few choices, so nearby-looking mazes
      // don't repeatedly yield the same answer locations.
      var topCount=Math.min(3,scored.length);
      selected.push(scored[Math.floor(rnd()*topCount)]);
    });
    // Ensure all questions have a unique position even if a tiny map lacks an
    // eligible point in one of the regions.
    if(selected.length<MAX_QUESTS){
      var fallback=[];
      for(var fy=1;fy<h-1;fy+=2)for(var fx=1;fx<w-1;fx+=2){
        if(maze[fy][fx]===0&&!(fx===1&&fy===1)&&!(fx===finish.x&&fy===finish.y)&&
           !selected.some(function(q){return q.x===fx&&q.y===fy}))fallback.push({x:fx,y:fy});
      }
      shuffle(fallback,rnd);
      while(selected.length<MAX_QUESTS&&fallback.length)selected.push(fallback.pop());
    }
    // The selected stations become question labels in a new random order each time.
    var stations=shuffle(selected,rnd);
    return {width:w,height:h,grid:fine,stations:stations,exit:{x:w-2,y:h-2}};
  }
  // The 2D maze is authoritative. Drive mode gets its own widened road mask.
  // Each original corridor is 2 * TILE = 56 map pixels across. Expanding its
  // sides by DRIVE_TILE = 14 pixels yields an 84-pixel TWO-LANE roadway;
  // 90-degree junctions gain equally wide aprons. Walls still separate routes.
  function buildDriveRoad(m){
    var w=m.grid[0].length*2,h=m.grid.length*2,base=new Uint8Array(w*h),expanded=new Uint8Array(w*h);
    for(var y=0;y<m.grid.length;y++)for(var x=0;x<m.grid[0].length;x++)if(m.grid[y][x]===0){
      var i=2*y*w+2*x;base[i]=1;base[i+1]=1;base[i+w]=1;base[i+w+1]=1;
    }
    for(var gy=0;gy<h;gy++)for(var gx=0;gx<w;gx++){
      if(!base[gy*w+gx])continue;
      // 1 fine-cell safety apron in all directions; leaves >=2 subcells of
      // separation between otherwise distinct neighboring maze corridors.
      for(var oy=-1;oy<=1;oy++)for(var ox=-1;ox<=1;ox++){
        var xx=gx+ox,yy=gy+oy;
        if(xx>=0&&yy>=0&&xx<w&&yy<h)expanded[yy*w+xx]=1;
      }
    }
    m.driveRoad={w:w,h:h,bits:expanded};
  }
  function driveRoadAt(x,y){
    if(!current||!current.driveRoad)return false;
    var road=current.driveRoad,gx=Math.floor(x/DRIVE_TILE),gy=Math.floor(y/DRIVE_TILE);
    return gx>=0&&gy>=0&&gx<road.w&&gy<road.h&&road.bits[gy*road.w+gx]===1;
  }
  function canDriveStand(x,y){
    var r=6;
    return driveRoadAt(x,y)&&driveRoadAt(x-r,y-r)&&driveRoadAt(x+r,y-r)&&
      driveRoadAt(x-r,y+r)&&driveRoadAt(x+r,y+r)&&driveRoadAt(x-r,y)&&
      driveRoadAt(x+r,y)&&driveRoadAt(x,y-r)&&driveRoadAt(x,y+r);
  }
  function worldCenter(lx,ly){return {x:(2*lx+1)*TILE,y:(2*ly+1)*TILE}}
  function newRound(resetAll){
    if(!assignment)return;
    resetMapBudget();
    if(resetAll)failures=0;var sz=MAZE_SIZES[Math.min(failures,MAZE_SIZES.length-1)];current=generateMaze(sz[0],sz[1]);buildDriveRoad(current);done=Array(MAX_QUESTS).fill(false);var start=worldCenter(1,1);current.player={x:start.x,y:start.y,dir:'down',moving:false,walk:0};driveSpeed=0;driveAngle=chooseDriveHeading(start.x,start.y,Math.PI/2);driveDistance=0;el('tripValue').textContent='0.00';el('speedValue').textContent='0';camera.x=0;camera.y=0;nearItem=null;hideDialog();pressed={};syncHUD();fitCamera();notify(failures?'新迷宮已縮小：'+sz[0]+' × '+sz[1]+'（邏輯格）':'新的迷宮已產生。開始探索！')}
  function syncHUD(){el('roundN').textContent=failures+1;el('mazeSize').textContent=current.width+' × '+current.height;el('failureCount').textContent=failures;el('doneCount').textContent=done.filter(Boolean).length+' / '+MAX_QUESTS;
    el('progressStrip').innerHTML='<span class="progress-strip-label">作業 '+done.filter(Boolean).length+'/'+MAX_QUESTS+'</span>'+done.map(function(ok,i){return '<span class="progress-dot '+(ok?'passed':'')+'" title="Q'+(i+1)+(ok?' 已完成':' 未完成')+'">'+(ok?'✓':(i+1))+'</span>'}).join('');
    el('questlist').innerHTML=QUESTIONS.map(function(q,i){return '<div class="quest '+(done[i]?'done':'')+'"><div class="seal">'+(done[i]?'✓':'Q'+(i+1))+'</div><div><div class="qtitle">'+escapeHtml(q.title||q.id)+'</div><div class="qstatus">'+(done[i]?'已通過 · Passed':'尚未通過 · Find in maze')+'</div></div></div>'}).join('');
    var all=done.every(Boolean);el('finalStatus').textContent=all?'全部題目已通過！找到紫色終點即可開啟表單。':'終點尚未解鎖。完成全部 '+MAX_QUESTS+' 題才可通關。';
    el('finalStatus').style.borderColor=all?'#38b99f':'#466655';
  }
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
  function notify(msg){var node=el('toast');node.textContent=msg;node.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(function(){node.classList.remove('show')},3000)}
  function sizeCanvas(){var r=canvas.getBoundingClientRect();viewport.w=Math.max(1,r.width);viewport.h=Math.max(1,r.height);var dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(viewport.w*dpr);canvas.height=Math.round(viewport.h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.imageSmoothingEnabled=false;fitCamera()}
  function clamp(x,min,max){return Math.max(min,Math.min(x,max))}
  function visibleWorld(){return {w:viewport.w/gameZoom,h:viewport.h/gameZoom}}
  function cameraAxis(player,worldSize,viewSize){
    // Center a small maze instead of pinning it to the top-left corner.
    if(worldSize<=viewSize)return (worldSize-viewSize)/2;
    return clamp(player-viewSize/2,0,worldSize-viewSize);
  }
  function fitCamera(){if(!current)return;var cw=current.width*2*TILE,ch=current.height*2*TILE,view=visibleWorld();camera.x=cameraAxis(current.player.x,cw,view.w);camera.y=cameraAxis(current.player.y,ch,view.h)}
  function passable(x,y){if(!current)return false;var xx=Math.floor(x/TILE),yy=Math.floor(y/TILE);return yy>=0&&yy<current.grid.length&&xx>=0&&xx<current.grid[0].length&&current.grid[yy][xx]===0}
  function canStand(x,y){var r=10;return passable(x-r,y-r)&&passable(x+r,y-r)&&passable(x-r,y+r)&&passable(x+r,y+r)&&passable(x,y-r)&&passable(x,y+r)&&passable(x-r,y)&&passable(x+r,y)}
  function update(dt){if(assignmentPaused||modalOpen||pendingInteraction||el('sidePanel').classList.contains('open')||!current)return;
    if(gameMode==='drive'){updateDrive(dt);findNearby();return;}
    var dx=0,dy=0;if(pressed.arrowup||pressed.w)dy--;if(pressed.arrowdown||pressed.s)dy++;if(pressed.arrowleft||pressed.a)dx--;if(pressed.arrowright||pressed.d)dx++;
    var p=current.player;p.moving=!!(dx||dy);if(dx||dy){if(Math.abs(dx)>Math.abs(dy))p.dir=dx>0?'right':'left';else p.dir=dy>0?'down':'up';var len=Math.sqrt(dx*dx+dy*dy);dx=dx/len*175*dt;dy=dy/len*175*dt;if(canStand(p.x+dx,p.y))p.x+=dx;if(canStand(p.x,p.y+dy))p.y+=dy;p.walk=(p.walk||0)+dt*10}else p.walk=0;
    var worldW=current.width*2*TILE,worldH=current.height*2*TILE,view=visibleWorld(),tx=cameraAxis(current.player.x,worldW,view.w),ty=cameraAxis(current.player.y,worldH,view.h);
    camera.x+=(tx-camera.x)*Math.min(1,dt*12);camera.y+=(ty-camera.y)*Math.min(1,dt*12);
    findNearby();
  }
  function findNearby(){var nearest=null,best=gameMode==='drive'?70:50;
    current.stations.forEach(function(s,i){if(done[i])return;var pt=worldCenter(s.x,s.y),dist=Math.hypot(pt.x-current.player.x,pt.y-current.player.y);if(dist<best){nearest={type:'question',index:i};best=dist}});
    var exit=worldCenter(current.exit.x,current.exit.y),d=Math.hypot(exit.x-current.player.x,exit.y-current.player.y);if(d<best){nearest={type:'finish'};best=d}
    nearItem=nearest;var tip=el('interactTip');if(nearest){tip.textContent=nearest.type==='finish'?(done.every(Boolean)?'★ 終點已解鎖：按 E 完成作業':'🔒 終點需通過全部 '+MAX_QUESTS+' 題才能啟用'):'● 找到 Q'+(nearest.index+1)+'：按 E 或點擊題目';tip.classList.add('show')}else tip.classList.remove('show');
    el('status').textContent=gameMode==='drive'?(nearest?'接近 '+(nearest.type==='finish'?'終點':'Q'+(nearest.index+1))+' · 停車按 E':'迷宮駕駛 · W 加速、A/D 轉向、V 切換'): (nearest?(nearest.type==='finish'?'已抵達終點':'已找到 Q'+(nearest.index+1)):'方向鍵 / WASD 移動 · 按 E 互動');
  }
  // BEGIN 2D VISUALS — artwork reads shared state; gameplay and driving stay here.
  var rpgVisuals=MazeRpgVisuals.create(TILE);
  function render(time){
    if(!current)return;
    rpgVisuals.render(ctx,current,done,camera,gameZoom,viewport,time,nearItem,showMap);
    if(showMap)drawMinimap();
  }
  // END 2D VISUALS
  function clearInteractionCue(){
    var wasPending=!!pendingInteraction;pendingInteraction=null;
    if(interactionFrame)cancelAnimationFrame(interactionFrame);interactionFrame=0;
    if(rpgVisuals&&rpgVisuals.clearInteraction)rpgVisuals.clearInteraction();
    if(wasPending){pressed={};driveSpeed=0;mapLastTick=performance.now();if(current&&gameMode==='2d')render(performance.now()/1000);}
  }
  function validPending(p){
    return pendingInteraction===p&&current===p.maze&&assignment===p.unit&&gameMode==='2d'&&
      !assignmentPaused&&!modalOpen&&!document.hidden&&!done[p.index];
  }
  function revealPending(p){
    if(pendingInteraction!==p)return;
    var valid=validPending(p);clearInteractionCue();if(valid)openQuestion(p.index);
  }
  function presentInteraction(index){
    var start=performance.now();
    var duration=rpgVisuals&&rpgVisuals.beginInteraction?rpgVisuals.beginInteraction(current,index,start/1000):0;
    if(typeof duration!=='number'||duration<=0){openQuestion(index);return;}
    updateMapBudget(start);pressed={};driveSpeed=0;
    var pending={maze:current,unit:assignment,index:index,start:start,revealAt:start+duration*1000};
    pendingInteraction=pending;render(start/1000);
    function animate(t){
      if(pendingInteraction!==pending)return;
      interactionFrame=0;
      if(!validPending(pending)){clearInteractionCue();return;}
      if(t>=pending.revealAt||motionPreference.matches){revealPending(pending);return;}
      render(t/1000);interactionFrame=requestAnimationFrame(animate);
    }
    interactionFrame=requestAnimationFrame(animate);
  }
  function setAtmosphere(value,persist){
    if(!['off','normal','strong'].includes(value))return;
    clearInteractionCue();atmosphereMode=value;
    if(rpgVisuals&&rpgVisuals.setAtmosphere)rpgVisuals.setAtmosphere(value);
    el('atmosphereSelect').value=value;el('drawerAtmosphereSelect').value=value;
    if(persist){try{localStorage.setItem(ATMOSPHERE_KEY,value);}catch(ignore){}}
    if(current&&gameMode==='2d')render(performance.now()/1000);
  }
  function resetMapBudget(){
    // Close any active preview and reset the quota for this new attempt.
    showMap=false;mini.classList.remove('show');
    mapRemainingMs=MAP_LIMIT_MS;mapLastTick=performance.now();
    updateMapControls();
  }
  function updateMapControls(){
    var seconds=Math.ceil(Math.max(0,mapRemainingMs)/1000),expired=mapRemainingMs<=0;
    var label=expired?'老師視角：已用完':(showMap?'關閉地圖 · '+seconds+'s':'老師視角：'+seconds+'s');
    var btn=el('mapToggle'),drawer=el('drawerMapToggle');
    btn.textContent=label;drawer.textContent=label;btn.disabled=expired;drawer.disabled=expired;
    btn.setAttribute('aria-label',expired?'老師視角時間已用完':('老師視角剩餘 '+seconds+' 秒；'+(showMap?'點擊關閉':'點擊開啟')));
    el('mapSeconds').textContent=seconds+'s';
    el('mapTimeFill').style.width=(100*mapRemainingMs/MAP_LIMIT_MS)+'%';
    el('mapTimer').classList.toggle('show',showMap);
  }
  function setMapVisible(visible){
    if(!current)return;
    if(visible&&mapRemainingMs<=0){notify('老師視角 30 秒已用完。');return}
    showMap=visible&&mapRemainingMs>0;mapLastTick=performance.now();
    mini.classList.toggle('show',showMap);
    updateMapControls();
  }
  function updateMapBudget(now){
    if(mapLastTick===null){mapLastTick=now;return}
    var elapsed=Math.max(0,now-mapLastTick);mapLastTick=now;
    // Only time that the map can actually be viewed counts.
    if(showMap&&!assignmentPaused&&!document.hidden&&!modalOpen&&!pendingInteraction&&!el('sidePanel').classList.contains('open')){
      mapRemainingMs=Math.max(0,mapRemainingMs-elapsed);
      if(mapRemainingMs===0){setMapVisible(false);notify('老師視角 30 秒已使用完畢，地圖已自動關閉。')}
    }
    updateMapControls();
  }
  function drawMinimap(){if(!mctx||!current)return;var W=mini.width,H=mini.height,m=current,scale=Math.min((W-14)/m.width,(H-14)/m.height),ox=(W-m.width*scale)/2,oy=(H-m.height*scale)/2;
    mctx.fillStyle='#07131f';mctx.fillRect(0,0,W,H);
    for(var y=0;y<m.height;y++)for(var x=0;x<m.width;x++){mctx.fillStyle=m.grid[y*2][x*2]?'#344e65':'#0e2630';mctx.fillRect(ox+x*scale,oy+y*scale,Math.ceil(scale),Math.ceil(scale))}
    m.stations.forEach(function(s,i){mctx.fillStyle=done[i]?'#55e3bc':'#ffdb8a';mctx.beginPath();mctx.arc(ox+(s.x+.5)*scale,oy+(s.y+.5)*scale,Math.max(2,scale*.35),0,7);mctx.fill()});
    mctx.fillStyle='#a99aff';mctx.beginPath();mctx.arc(ox+(m.exit.x+.5)*scale,oy+(m.exit.y+.5)*scale,3,0,7);mctx.fill();
    mctx.fillStyle='#76ffff';mctx.beginPath();mctx.arc(ox+m.player.x/(TILE*2)*scale,oy+m.player.y/(TILE*2)*scale,3.5,0,7);mctx.fill();
    // Teacher minimap rectangle is also based on the zoom-adjusted visible world.
    var v=visibleWorld(),worldW=m.width*2*TILE,worldH=m.height*2*TILE;
    var left=clamp(camera.x,0,worldW),top=clamp(camera.y,0,worldH);
    var right=clamp(camera.x+v.w,0,worldW),bottom=clamp(camera.y+v.h,0,worldH);
    mctx.strokeStyle='#b4d8ff';mctx.lineWidth=.8;
    mctx.strokeRect(ox+left/(TILE*2)*scale,oy+top/(TILE*2)*scale,Math.max(0,right-left)/(TILE*2)*scale,Math.max(0,bottom-top)/(TILE*2)*scale);
  }

  // ===== Low-power first-person maze drive: same logical roads and quest positions =====
  function chooseDriveHeading(x,y,preferred){
    var bestAngle=preferred,bestDist=-1;
    [0,Math.PI/2,Math.PI,-Math.PI/2].forEach(function(a){var d=rayHit(x,y,a,300).dist;
      if(d>bestDist){bestDist=d;bestAngle=a;}
    });
    return rayHit(x,y,preferred,300).dist<75?bestAngle:preferred;
  }
  function toggleMode(){
    if(!current)return;
    clearInteractionCue();
    gameMode=gameMode==='2d'?'drive':'2d';driveSpeed=0;pressed={};
    if(gameMode==='drive'){
      var dirs={right:0,down:Math.PI/2,left:Math.PI,up:-Math.PI/2};driveAngle=chooseDriveHeading(current.player.x,current.player.y,dirs[current.player.dir]||Math.PI/2);
    }else{
      var c=Math.cos(driveAngle),ss=Math.sin(driveAngle);current.player.dir=Math.abs(c)>Math.abs(ss)?(c>0?'right':'left'):(ss>0?'down':'up');fitCamera();
    }
    document.body.classList.toggle('drive-mode',gameMode==='drive');
    el('modeToggle').textContent=gameMode==='drive'?'🚶 返回 2D（V）':'🚗 切換駕駛（V）';
    el('drawerModeToggle').textContent=gameMode==='drive'?'🚶 返回 2D':'🚗 進入駕駛視角';
    el('driveDashboard').hidden=gameMode!=='drive';
    el('controlsFoot').innerHTML=gameMode==='drive'?'駕駛 <kbd>W</kbd> 油門 <kbd>S</kbd> 煞車 <kbd>A</kbd><kbd>D</kbd> 轉向　停車互動 <kbd>E</kbd>　切換 <kbd>V</kbd>':'移動 <kbd>↑</kbd><kbd>↓</kbd><kbd>←</kbd><kbd>→</kbd> 或 <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd>　互動 <kbd>E</kbd>　視角 <kbd>V</kbd>';
    notify(gameMode==='drive'?'已進入雙線道迷宮駕駛模式（W 加速，A/D 轉彎）':'已返回 2D 迷宮，位置與題目進度都保留。');
    canvas.focus({preventScroll:true});findNearby();
  }
  function updateDrive(dt){
    if(!current)return;
    var gas=!!(pressed.w||pressed.arrowup),brake=!!(pressed.s||pressed.arrowdown),left=!!(pressed.a||pressed.arrowleft),right=!!(pressed.d||pressed.arrowright);
    // Drive speed is in VIRTUAL units/sec. The same map movement is twelve
    // times longer in drive-world coordinates (without changing Q positions).
    if(gas)driveSpeed+=320*dt;
    if(brake)driveSpeed-=620*dt;
    if(!gas&&!brake)driveSpeed*=Math.exp(-1.35*dt);
    driveSpeed=clamp(driveSpeed,-135,DRIVE_TOP_SPEED);
    if(Math.abs(driveSpeed)<1.4)driveSpeed=0;
    var steer=(right?1:0)-(left?1:0),speedNorm=Math.abs(driveSpeed)/DRIVE_TOP_SPEED;
    // Agile low-speed turning and full steering at intersections. At a stop
    // the player can rotate, so a maze's right angles cannot trap the car.
    if(steer)driveAngle+=steer*(2.8-1.0*speedNorm)*dt*(driveSpeed < -5?-1:1);
    var p=current.player,step=driveSpeed*dt/DRIVE_SCALE,
        dx=Math.cos(driveAngle)*step,dy=Math.sin(driveAngle)*step;
    var moved=0;
    // Axis-separated collision sliding is more forgiving at corner entrances.
    if(canDriveStand(p.x+dx,p.y+dy)){p.x+=dx;p.y+=dy;moved=Math.hypot(dx,dy)}
    else{
      var mx=false,my=false;
      if(canDriveStand(p.x+dx,p.y)){p.x+=dx;mx=true}
      if(canDriveStand(p.x,p.y+dy)){p.y+=dy;my=true}
      if(mx||my){moved=Math.hypot(mx?dx:0,my?dy:0);driveSpeed*=.65}
      else driveSpeed=0;
    }
    driveDistance+=moved*DRIVE_SCALE;
    p.moving=Math.abs(driveSpeed)>8;
    p.walk=(p.walk||0)+dt*Math.abs(driveSpeed)/DRIVE_SCALE/16;
    el('speedValue').textContent=String(Math.round(Math.abs(driveSpeed)*.25));
    // The km/h scale and trip counter are internally consistent game-world
    // estimates rather than GPS / real-world dimensions.
    el('tripValue').textContent=(driveDistance/14400).toFixed(2);
  }
  function rayHit(ox,oy,angle,maxDist){
    // Lightweight DDA through the widened driving grid (14px subtiles).
    var road=current.driveRoad,unit=DRIVE_TILE,ux=Math.cos(angle),uy=Math.sin(angle),gx=ox/unit,gy=oy/unit;
    var cx=Math.floor(gx),cy=Math.floor(gy),sx=ux<0?-1:1,sy=uy<0?-1:1;
    var dx=Math.abs(ux)<1e-8?1e30:Math.abs(1/ux),dy=Math.abs(uy)<1e-8?1e30:Math.abs(1/uy);
    var nextX=ux<0?(gx-cx)*dx:(cx+1-gx)*dx,nextY=uy<0?(gy-cy)*dy:(cy+1-gy)*dy;
    var dist=0,side=0,hit=0;
    for(var iter=0;iter<road.w+road.h+6&&dist<maxDist;iter++){
      if(nextX<nextY){dist=nextX*unit;nextX+=dx;cx+=sx;side=0}
      else{dist=nextY*unit;nextY+=dy;cy+=sy;side=1}
      if(cx<0||cy<0||cx>=road.w||cy>=road.h||!road.bits[cy*road.w+cx]){hit=1;break}
    }
    return {dist:Math.min(dist,maxDist),hit:hit,side:side,x:cx,y:cy};
  }
  function lineVisible(ax,ay,bx,by){
    var vx=bx-ax,vy=by-ay,d=Math.hypot(vx,vy),steps=Math.ceil(d/14);
    for(var i=2;i<steps-2;i++){var t=i/steps;if(!driveRoadAt(ax+vx*t,ay+vy*t))return false}
    return true;
  }
  function drawMazeCeiling(g,w,h,horizon,time){
    // Continuous dark roof replaces all ocean/mountains/sky scenery. The
    // only navigable openings are the actual ray-cast corridors of the maze.
    var roof=g.createLinearGradient(0,0,0,horizon);
    roof.addColorStop(0,'#101923');roof.addColorStop(.68,'#192938');roof.addColorStop(1,'#2b3d4b');
    g.fillStyle=roof;g.fillRect(0,0,w,h);
    // Subtle horizontal ceiling bands; no sea or fragmented horizon.
    g.fillStyle='#33495b';g.fillRect(0,Math.max(0,horizon-4),w,4);
    g.fillStyle='#122331';g.fillRect(0,horizon,w,Math.max(0,h-horizon));
  }
  function drawRoadFloor(g,w,h,horizon,focal){
    // Project the road onto a simple flat asphalt floor (low-cost 2x2 pixels).
    var floorH=h-horizon;if(floorH<=0)return;
    var image=g.createImageData(w,floorH),arr=image.data,camH=175,
        cs=Math.cos(driveAngle),sn=Math.sin(driveAngle),rightX=-sn,rightY=cs;
    for(var yy=0;yy<floorH;yy+=2){
      var depth=camH*focal/(yy+1.3),half=depth*Math.tan(.67);
      for(var xx=0;xx<w;xx+=2){
        var sideways=(xx/w*2-1)*half;
        var wx=current.player.x+(cs*depth+rightX*sideways)/DRIVE_SCALE,
            wy=current.player.y+(sn*depth+rightY*sideways)/DRIVE_SCALE;
        var road=driveRoadAt(wx,wy),r,gr,b;
        if(road){
          // Uniform asphalt with only faint stones and highly legible markings.
          var noise=(Math.floor(wx/38)*13+Math.floor(wy/38)*17)&3;
          r=49+noise;gr=58+noise;b=68+noise;
          var horizontal=driveRoadAt(wx-56,wy)&&driveRoadAt(wx+56,wy),
              vertical=driveRoadAt(wx,wy-56)&&driveRoadAt(wx,wy+56);
          var mx=((wx%(2*TILE))+(2*TILE))%(2*TILE),
              my=((wy%(2*TILE))+(2*TILE))%(2*TILE);
          var dashX=(Math.floor(wx*DRIVE_SCALE/280)&1)===0,
              dashY=(Math.floor(wy*DRIVE_SCALE/280)&1)===0;
          if(horizontal&&!vertical&&Math.abs(my-TILE)<2.3&&dashX){r=232;gr=185;b=85}
          if(vertical&&!horizontal&&Math.abs(mx-TILE)<2.3&&dashY){r=232;gr=185;b=85}
          // Light shoulders stop at real junctions, never obscure entrances.
          var edge=(!driveRoadAt(wx+8,wy)||!driveRoadAt(wx-8,wy)||
                    !driveRoadAt(wx,wy+8)||!driveRoadAt(wx,wy-8));
          if(edge){r=126;gr=138;b=145}
        }else{r=26;gr=36;b=49}
        var shade=Math.min(.50,depth/19000),fogR=49,fogG=66,fogB=82;
        r=(r*(1-shade)+fogR*shade)|0;gr=(gr*(1-shade)+fogG*shade)|0;b=(b*(1-shade)+fogB*shade)|0;
        var offset=yy*w*4+xx*4;
        for(var ry=0;ry<2&&yy+ry<floorH;ry++)for(var rx=0;rx<2&&xx+rx<w;rx++){
          var at=offset+ry*w*4+rx*4;arr[at]=r;arr[at+1]=gr;arr[at+2]=b;arr[at+3]=255;
        }
      }
    }
    g.putImageData(image,0,horizon);
  }
  function drawWallRays(g,w,h,horizon,focal){
    // Tall, continuous maze walls replace the old short seaside rails. They
    // reveal junction openings because the raycast stops only on real walls.
    var dir=driveAngle,maxD=1350,columns=2;
    for(var x=0;x<w;x+=columns){
      var off=Math.atan((x+.5-w*.5)/focal),hit=rayHit(current.player.x,current.player.y,dir+off,maxD);
      if(!hit.hit)continue;
      var dist=Math.max(88,hit.dist*DRIVE_SCALE*Math.cos(off));
      var bottom=horizon+175*focal/dist,
          top=horizon-590*focal/dist,
          height=bottom-top;
      if(bottom<0||top>h)continue;
      var fog=Math.min(.72,Math.max(0,(dist-500)/12500));
      var base=hit.side?[69,91,112]:[87,111,133],fogColor=[43,61,79];
      var face=base.map(function(c,i){return Math.round(c*(1-fog)+fogColor[i]*fog)});
      // Very faint panel seams, never random color patches that mimic doors.
      var hitCoord=hit.side?current.player.x+Math.cos(dir+off)*hit.dist:
                              current.player.y+Math.sin(dir+off)*hit.dist;
      var seam=((hitCoord%42)+42)%42<1.5;
      var dark=seam?0.78:1;
      g.fillStyle='rgb('+Math.round(face[0]*dark)+','+Math.round(face[1]*dark)+','+Math.round(face[2]*dark)+')';
      g.fillRect(x,Math.max(0,top),columns+1,Math.min(h,bottom)-Math.max(0,top));
      // Bright continuous cap/trim lets a driver trace openings and corners.
      var capY=top+26*focal/dist;
      if(capY>=0&&capY<h){g.fillStyle=hit.side?'#83a8c0':'#b6d5e3';g.fillRect(x,capY,columns+1,Math.max(1,8*focal/dist))}
      var lowerY=horizon+83*focal/dist;
      if(lowerY>=0&&lowerY<h){g.fillStyle=hit.side?'#355469':'#47667a';g.fillRect(x,lowerY,columns+1,Math.max(1,9*focal/dist))}
      if(bottom>=0&&bottom<h){g.fillStyle='#192d3d';g.fillRect(x,bottom-2,columns+1,Math.max(2,6*focal/dist))}
    }
  }
  function drawRoadsideSigns(g,w,h,horizon,focal){
    var objects=current.stations.map(function(s,i){return {pos:worldCenter(s.x,s.y),label:'Q'+(i+1),ok:done[i],finish:false}});
    objects.push({pos:worldCenter(current.exit.x,current.exit.y),label:'FINISH',ok:done.every(Boolean),finish:true});
    var p=current.player,co=Math.cos(driveAngle),si=Math.sin(driveAngle);
    objects.forEach(function(ob){ob.depth=((ob.pos.x-p.x)*co+(ob.pos.y-p.y)*si)*DRIVE_SCALE});
    objects.sort(function(a,b){return b.depth-a.depth});
    objects.forEach(function(ob){
      if(ob.depth<120||ob.depth>17000||!lineVisible(p.x,p.y,ob.pos.x,ob.pos.y))return;
      var side=(-(ob.pos.x-p.x)*si+(ob.pos.y-p.y)*co)*DRIVE_SCALE;
      var sx=w*.5+side*focal/ob.depth,yy=horizon+175*focal/ob.depth,scale=focal/ob.depth;
      if(sx < -70||sx > w+70)return;
      var poleH=Math.min(h*.85,380*scale),signW=Math.min(w*.30,210*scale),signH=Math.min(h*.35,120*scale);
      if(signW<8)return;
      g.fillStyle='#27434a';g.fillRect(sx-2,yy-poleH*.94,4,poleH);
      g.fillStyle=ob.finish?'#8e81d2':ob.ok?'#38baa5':'#ffc459';g.strokeStyle='#26383e';g.lineWidth=Math.max(1,10*scale);
      var by=yy-poleH-signH*.8;g.fillRect(sx-signW/2,by,signW,signH);g.strokeRect(sx-signW/2,by,signW,signH);
      g.fillStyle='#182c34';g.font='900 '+Math.max(10,Math.min(33,90*scale))+'px system-ui';g.textAlign='center';g.textBaseline='middle';
      g.fillText(ob.ok&&!ob.finish?'✓':ob.label,sx,by+signH*.5);
    });
  }
  function drawCockpit(g,w,h,time){
    // 2D cockpit overlay; constant complexity independent of world geometry.
    var sway=Math.sin(time*9)*Math.min(1,Math.abs(driveSpeed)/145)*1.4,base=h*.88+sway;
    g.save();var grad=g.createLinearGradient(0,base,0,h);grad.addColorStop(0,'#243742');grad.addColorStop(.28,'#12242d');grad.addColorStop(1,'#071118');
    g.fillStyle=grad;g.beginPath();g.moveTo(0,h);g.lineTo(0,base+18);g.quadraticCurveTo(w*.5,base-25,w,base+18);g.lineTo(w,h);g.closePath();g.fill();
    g.strokeStyle='#15232c';g.lineWidth=9;g.beginPath();g.moveTo(3,0);g.lineTo(w*.07,h*.25);g.lineTo(w*.12,h*.79);g.stroke();g.beginPath();g.moveTo(w-3,0);g.lineTo(w*.93,h*.25);g.lineTo(w*.88,h*.79);g.stroke();
    // A cropped steering wheel on the left foreground.
    var cx=w*.29,cy=h*.965,rad=Math.min(w*.16,h*.18);g.lineWidth=Math.max(8,rad*.17);g.strokeStyle='#081014';g.beginPath();g.arc(cx,cy,rad,Math.PI,Math.PI*2);g.stroke();
    g.strokeStyle='#64737d';g.lineWidth=rad*.03;g.beginPath();g.arc(cx,cy,rad*.92,Math.PI*1.05,Math.PI*1.95);g.stroke();
    g.strokeStyle='#101e26';g.lineWidth=Math.max(12,rad*.18);g.beginPath();g.moveTo(cx,cy);g.lineTo(cx-rad*.66,cy-rad*.58);g.moveTo(cx,cy);g.lineTo(cx+rad*.66,cy-rad*.58);g.stroke();
    g.fillStyle='#1e353b';g.beginPath();g.arc(cx,cy,rad*.28,0,7);g.fill();
    g.fillStyle='#436271';g.fillRect(w*.57,base+6,w*.29,16);g.fillStyle='#89b8b7';g.fillRect(w*.59,base+11,w*.1,3);
    g.restore();
  }
  function renderDrive(time){
    if(!current||!dctx)return;
    var W=Math.min(720,Math.max(280,Math.round(viewport.w*.7)));var H=Math.max(180,Math.round(W*viewport.h/viewport.w));
    if(driveSurface.width!==W||driveSurface.height!==H){driveSurface.width=W;driveSurface.height=H}
    var horizon=Math.round(H*.49+Math.sin(time*8)*Math.min(2,Math.abs(driveSpeed)/170)),focal=W/(2*Math.tan(.67));
    drawMazeCeiling(dctx,W,H,horizon,time);
    drawRoadFloor(dctx,W,H,horizon,focal);
    drawWallRays(dctx,W,H,horizon,focal);
    drawRoadsideSigns(dctx,W,H,horizon,focal);
    drawCockpit(dctx,W,H,time);
    ctx.clearRect(0,0,viewport.w,viewport.h);ctx.imageSmoothingEnabled=true;ctx.drawImage(driveSurface,0,0,viewport.w,viewport.h);
    if(showMap)drawMinimap();
  }
  function frame(t){var dt=Math.min((t-lastFrame)/1000||.016,.045);lastFrame=t;updateMapBudget(t);update(dt);if(!pendingInteraction){if(gameMode==='2d'){render(t/1000)}else if(t-driveRenderAt>=32){driveRenderAt=t;renderDrive(t/1000)}}requestAnimationFrame(frame)}
  function showDialog(html){clearInteractionCue();modalOpen=true;pressed={};driveSpeed=0;el('dialog').innerHTML=html;el('veil').classList.add('show');el('dialog').focus()}
  function hideDialog(){clearInteractionCue();modalOpen=false;activeQuestion=-1;el('veil').classList.remove('show');el('dialog').innerHTML=''}
  function videoCard(url,isExplanation){return '<div class="videobox"><div><div class="video-title">'+(isExplanation?'🎬 English Explanation (optional)':'🎬 English Question Video')+'</div><small>影片在新的分頁開啟，返回此頁繼續作答。</small></div><a class="video-link" target="_blank" rel="noopener noreferrer" href="'+escapeHtml(url)+'">▶ 開啟 YouTube ↗</a></div>'}
  function openQuestion(index){if(!assignment||!QUESTIONS[index]||done[index])return;activeQuestion=index;var q=QUESTIONS[index];
    showDialog('<div class="modalhead"><span class="chip">ENGLISH QUESTION · Q'+(index+1)+' / '+MAX_QUESTS+'</span><button class="btn" id="dialogClose">✕ 返回迷宮</button></div><h2>'+escapeHtml(q.title||q.id)+'</h2><p class="modaltext">先在 YouTube 新分頁觀看題目影片，回到迷宮選擇一個答案。</p>'+videoCard(q.questionVideoUrl,false)+'<div class="question">'+escapeHtml(q.prompt||'')+'</div><div class="answers">'+q.options.map(function(c,i){return '<button class="answer" type="button" data-answer="'+String.fromCharCode(65+i)+'"><span class="letter">'+String.fromCharCode(65+i)+'</span>'+escapeHtml(c)+'</button>'}).join('')+'</div><p class="muted">選擇一個答案即可。答錯會清除全部通關狀態，重新產生較小的迷宮。</p>');
    el('dialogClose').addEventListener('click',hideDialog);
    Array.from(el('dialog').querySelectorAll('[data-answer]')).forEach(function(btn){btn.addEventListener('click',function(){chooseAnswer(index,btn.dataset.answer)})});
  }
  function chooseAnswer(index,choice){
    if(index!==activeQuestion||!QUESTIONS[index]||done[index])return;
    var q=QUESTIONS[index];
    if(!AssignmentValidator.acceptsAnswer(q,choice)){
      failures++;newRound(false);
      var sz=MAZE_SIZES[Math.min(failures,MAZE_SIZES.length-1)];
      showDialog('<span class="chip" style="background:#ff9ba7">WRONG ANSWER</span><h2>答錯了，整局重新挑戰</h2><p class="modaltext">所有題目通關紀錄已清空，老師視角已恢復為 30 秒。新的迷宮已產生，題目內容與答案不變。</p><div class="question">第 '+(failures+1)+' 輪地圖：'+sz[0]+' × '+sz[1]+' 邏輯格</div><div class="modalbuttons"><button class="btn primary" id="nextRound">開始下一輪 →</button></div>');
      el('nextRound').addEventListener('click',hideDialog);return;
    }
    done[index]=true;syncHUD();var all=done.every(Boolean);
    showDialog('<span class="chip" style="background:#6cecc2">CORRECT ANSWER ✓</span><h2>答對了！Q'+(index+1)+' 通過</h2><div class="question">'+escapeHtml(q.explanationText||'')+'</div><p class="modaltext">可以選擇觀看英文解答影片，也可以直接繼續探索。</p>'+videoCard(q.explanationVideoUrl,true)+'<div class="modalbuttons"><button class="btn primary" id="continueMaze">'+(all?'全部完成，前往紫色終點 →':'返回迷宮，繼續尋找題目 →')+'</button></div>');
    el('continueMaze').addEventListener('click',function(){hideDialog();notify(all?'全部答對了！現在可以前往紫色終點。':'Q'+(index+1)+' 通過！可繼續探索其他題目。')});
  }
  function finish(){if(!assignment||!done.every(Boolean)){notify('請先通過所有題目，終點才能解鎖。');return}
    showDialog('<span class="chip" style="background:#9fe4d4">ALL QUESTS COMPLETED</span><h2>🎉 全部題目通過！</h2><p class="modaltext">'+escapeHtml(assignment.unitId+' · '+assignment.title)+'</p><div class="question">本輪成功：第 '+(failures+1)+' 次挑戰<br>已通過：'+MAX_QUESTS+' / '+MAX_QUESTS+'</div><div class="modalbuttons"><a class="video-link" href="'+escapeHtml(FORM_URL)+'" target="_blank" rel="noopener noreferrer">開啟 Google Form ↗</a></div><div class="modalbuttons"><button class="btn primary" id="again">重新玩一次</button><button class="btn" id="closeFinish">返回迷宮</button></div>');
    el('again').addEventListener('click',function(){newRound(true)});el('closeFinish').addEventListener('click',hideDialog);
  }
  function interact(){
    if(modalOpen||pendingInteraction||assignmentPaused||!nearItem)return;
    if(gameMode==='drive'&&Math.abs(driveSpeed)>25){notify('請先減速停車，再按 E 開啟題目。');return;}
    if(nearItem.type==='question'){
      if(gameMode==='2d')presentInteraction(nearItem.index);else openQuestion(nearItem.index);
    }else finish();
  }
  function isTyping(elm){return elm&&['INPUT','TEXTAREA','SELECT'].includes(elm.tagName)}
  window.addEventListener('keydown',function(e){
    var key=e.key.toLowerCase();
    if(pendingInteraction&&key==='escape'){e.preventDefault();clearInteractionCue();return;}
    if(isTyping(document.activeElement)||assignmentPaused||!current)return;
    if(['arrowleft','arrowright','arrowup','arrowdown','w','a','s','d','e','v',' '].includes(key))e.preventDefault();
    if(el('sidePanel').classList.contains('open')){if(key==='escape')togglePanel(false);return;}
    if(pendingInteraction){if(key==='v')toggleMode();return;}
    if(modalOpen){
      if(key==='escape'){if(el('dialogClose'))hideDialog();else if(el('continueMaze'))hideDialog();}
      return;
    }
    if(key==='v'){toggleMode();return;}
    if(key==='e'||key===' '){if(!e.repeat)interact();}else pressed[key]=true;
  });
  window.addEventListener('keyup',function(e){pressed[e.key.toLowerCase()]=false});window.addEventListener('blur',function(){pressed={};driveSpeed=0;clearInteractionCue()});
  canvas.addEventListener('click',function(){if(gameMode==='2d')interact();canvas.focus()});
  function togglePanel(visible){
    if(visible)clearInteractionCue();
    var side=el('sidePanel');side.classList.toggle('open',visible);side.setAttribute('aria-hidden',String(!visible));
    el('panelScrim').classList.toggle('open',visible);el('panelToggle').setAttribute('aria-expanded',String(visible));
    pressed={};driveSpeed=0;if(visible){el('panelClose').focus()}else{canvas.focus({preventScroll:true})}
  }
  el('modeToggle').addEventListener('click',toggleMode);el('drawerModeToggle').addEventListener('click',function(){togglePanel(false);toggleMode()});
  el('atmosphereSelect').addEventListener('change',function(){setAtmosphere(this.value,true);canvas.focus({preventScroll:true});});
  el('drawerAtmosphereSelect').addEventListener('change',function(){setAtmosphere(this.value,true);});
  motionPreference.addEventListener('change',function(){if(motionPreference.matches&&pendingInteraction)revealPending(pendingInteraction);});
  el('zoomSelect').addEventListener('change',function(){
    var next=Number(this.value);if([1.5,1.75].indexOf(next)<0)return;
    gameZoom=next;fitCamera();notify('迷宮鏡頭已調整為 '+Math.round(gameZoom*100)+'%（網頁介面不變）');canvas.focus({preventScroll:true});
  });
  el('panelToggle').addEventListener('click',function(){togglePanel(!el('sidePanel').classList.contains('open'))});
  el('panelClose').addEventListener('click',function(){togglePanel(false)});
  el('panelScrim').addEventListener('click',function(){togglePanel(false)});
  el('resetBtn').addEventListener('click',function(){newRound(true)});
  el('drawerResetBtn').addEventListener('click',function(){newRound(true);togglePanel(false)});
  el('drawerMapToggle').addEventListener('click',function(){togglePanel(false);setMapVisible(!showMap)});
  el('mapToggle').addEventListener('click',function(){setMapVisible(!showMap)});
  el('touchInteract').addEventListener('click',interact);
  Array.from(document.querySelectorAll('[data-key]')).forEach(function(btn){var key=btn.dataset.key;var set=function(down,e){if(e)e.preventDefault();pressed[key]=down};btn.addEventListener('pointerdown',function(e){set(true,e);btn.setPointerCapture(e.pointerId)});['pointerup','pointercancel','lostpointercapture'].forEach(function(evt){btn.addEventListener(evt,function(e){set(false,e)})})});
  window.addEventListener('resize',sizeCanvas);
  document.addEventListener('visibilitychange',function(){if(document.hidden){pressed={};driveSpeed=0;clearInteractionCue()}mapLastTick=performance.now()});
  function resetAssignment(){
    // A selector, failed load or new selection cannot leave a previous unit playable.
    if(current&&gameMode==='drive')toggleMode();
    current=null;assignment=null;QUESTIONS=[];FORM_URL='';MAX_QUESTS=0;
    failures=0;done=[];pressed={};driveSpeed=0;driveDistance=0;driveTurn=0;
    driveAngle=Math.PI/2;driveRenderAt=0;camera.x=0;camera.y=0;nearItem=null;
    hideDialog();togglePanel(false);resetMapBudget();
    ctx.clearRect(0,0,viewport.w,viewport.h);
    clearTimeout(toastTimer);el('toast').classList.remove('show');
    el('unitLabel').textContent='單元';el('unitLabel').title='選擇單元';
    el('roundN').textContent='1';el('mazeSize').textContent='—';
    el('doneCount').textContent='0 / 0';el('failureCount').textContent='0';
    el('progressStrip').textContent='請選擇單元';el('questlist').replaceChildren();
    el('finalStatus').textContent='請先載入已發布單元。';
    el('interactTip').classList.remove('show');el('status').textContent='請選擇單元';
    el('tripValue').textContent='0.00';el('speedValue').textContent='0';
  }
  var loader=AssignmentLoader.create({
    hasAssignment:function(){return assignment!==null;},
    activeUnitId:function(){return assignment&&assignment.unitId;},
    onPause:function(){
      clearInteractionCue();
      if(!assignmentPaused)updateMapBudget(performance.now());
      assignmentPaused=true;pressed={};driveSpeed=0;
    },
    onResume:function(){assignmentPaused=false;pressed={};driveSpeed=0;mapLastTick=performance.now();},
    onReset:resetAssignment,onReady:function(unit){
    assignment=unit;QUESTIONS=unit.questions;FORM_URL=unit.googleFormUrl;MAX_QUESTS=QUESTIONS.length;
    el('unitLabel').textContent=unit.unitId;
    var unitTitle=document.createElement('span');unitTitle.className='unit-title';
    unitTitle.textContent=' · '+unit.title;el('unitLabel').appendChild(unitTitle);
    el('unitLabel').title=unit.unitId+' · '+unit.title+'（選擇單元）';
    newRound(true);
  }});
  el('unitLabel').addEventListener('click',loader.open);
  setAtmosphere(atmosphereMode,false);
  sizeCanvas();requestAnimationFrame(frame);loader.start();
})();
