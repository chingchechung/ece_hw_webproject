// GENERATED read-only from lite-v1.0 student/js/game.js. Do not edit.
// Source SHA256: 03cd7fe5e60aec7d9cb47a799a8facfd73e4e3137602f5fd4edadb73b34ea564
export function generateLayout(w,h,seed){
if(![[25,19],[21,15],[17,13],[13,9]].some(s=>s[0]===w&&s[1]===h)||!Number.isInteger(seed)||seed<0||seed>4294967295)throw new Error('Invalid demo size or uint32 seed');
var Date={now:()=>seed},Math=Object.create(globalThis.Math);Math.random=()=>0;var MAX_QUESTS=5,seedCounter=0,TILE=28,DRIVE_TILE=14;
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

var result=generateMaze(w,h);buildDriveRoad(result);result.driveRoad.bits=Array.from(result.driveRoad.bits);return result;
}
