/* Test-only graph/route measurements, without changing the active maze/player. */
window.gameplayTest.quality=function(seedCount) {
  const rows=[],originalSeed=window.__mazeSeed,originalCounter=seedCounter;
  function distances(m,start) {
    const dist=new Map([[start.x+','+start.y,0]]),queue=[start];
    for(let i=0;i<queue.length;i++) {
      const p=queue[i];
      for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
        const x=p.x+dx,y=p.y+dy,key=x+','+y;
        if(m.grid[y*2]?.[x*2]===0&&!dist.has(key)) {
          dist.set(key,dist.get(p.x+','+p.y)+1);queue.push({x,y});
        }
      }
    }
    return dist;
  }
  try {
    for(const [w,h] of MAZE_SIZES) {
      const tours=[],deadEnds=[],stationEnds=[],layouts=new Set(),labelled=new Set();
      for(let seed=1;seed<=seedCount;seed++) {
        window.__mazeSeed=seed*104729;seedCounter=0;
        const m=generateMaze(w,h);buildDriveRoad(m);
        const start={x:1,y:1},points=[start,...m.stations,m.exit];
        const all=points.map(p=>distances(m,p)),reachable=all[0].size;
        const keys=m.stations.map(p=>p.x+','+p.y);
        if(keys.length!==MAX_QUESTS||new Set(keys).size!==MAX_QUESTS)throw Error('station count/duplicates');
        if(keys.includes('1,1')||keys.includes((w-2)+','+(h-2)))throw Error('start/exit overlap');
        const zones=new Set(m.stations.map(p=>(p.y<h/2?0:2)+(p.x<w/2?0:1)));
        if(zones.size!==4)throw Error('missing quadrant');
        layouts.add([...keys].sort().join(';'));labelled.add(keys.join(';'));
        const degree=p=>[[1,0],[-1,0],[0,1],[0,-1]].filter(([dx,dy])=>m.grid[(p.y+dy)*2]?.[(p.x+dx)*2]===0).length;
        stationEnds.push(m.stations.filter(p=>degree(p)===1).length/MAX_QUESTS);
        let dead=0;
        const bits=m.driveRoad.bits,rw=m.driveRoad.w,rh=m.driveRoad.h;
        function stand(x,y) {
          for(const [dx,dy] of [[0,0],[-6,-6],[6,-6],[-6,6],[6,6],[-6,0],[6,0],[0,-6],[0,6]]) {
            const gx=Math.floor((x+dx)/14),gy=Math.floor((y+dy)/14);
            if(gx<0||gy<0||gx>=rw||gy>=rh||!bits[gy*rw+gx])throw Error('undrivable route centre');
          }
        }
        for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++)if(m.grid[y*2]?.[x*2]===0) {
          const p={x,y};if(degree(p)===1)dead++;
          const centre=worldCenter(x,y);stand(centre.x,centre.y);
          for(const [dx,dy] of [[1,0],[0,1]])if(m.grid[(y+dy)*2]?.[(x+dx)*2]===0) {
            for(let t=0;t<=56;t+=2)stand(centre.x+dx*t,centre.y+dy*t);
          }
        }
        deadEnds.push(dead/reachable);
        for(const p of points)if(!all[0].has(p.x+','+p.y))throw Error('unreachable target');
        // Exact shortest tour of at most five questions, then finish (<=120 orders).
        let best=Infinity;
        function visit(last,remaining,length) {
          if(!remaining.length) {
            best=Math.min(best,length+all[last].get(m.exit.x+','+m.exit.y));return;
          }
          for(const next of remaining)visit(next,remaining.filter(i=>i!==next),
            length+all[last].get(points[next].x+','+points[next].y));
        }
        visit(0,m.stations.map((_,i)=>i+1),0);
        if(best>2*(reachable-1))throw Error('excessive route length');
        tours.push(best);
      }
      const sorted=[...tours].sort((a,b)=>a-b),mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
      if(layouts.size<seedCount*.5||labelled.size<seedCount*.9)throw Error('insufficient position/label randomization '+JSON.stringify({w,h,positions:layouts.size,labelled:labelled.size}));
      if(mean(stationEnds)>.4)throw Error('too many dead-end question stations');
      rows.push({questions:MAX_QUESTS,width:w,height:h,seeds:seedCount,
        uniquePositions:layouts.size,uniqueLabelledLayouts:labelled.size,
        shortestTourSteps:{min:sorted[0],median:sorted[Math.floor(sorted.length/2)],p95:sorted[Math.floor(sorted.length*.95)],max:sorted.at(-1)},
        meanDeadEndCellFraction:mean(deadEnds),meanDeadEndStationFraction:mean(stationEnds)});
    }
  } finally {window.__mazeSeed=originalSeed;seedCounter=originalCounter;}
  return rows;
};
