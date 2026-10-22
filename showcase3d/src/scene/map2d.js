import { LITE_ROAD_TILE } from '../gameplay/coordinates.js';
import { rectangles, wallRuns } from '../maze/layout.js';

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
export const MAP_ZOOMS = [125, 150, 175];
export function mapCamera(map, vehicle, width, height, zoom = 150, full = false) {
  const worldWidth = map.driveRoad.w * LITE_ROAD_TILE, worldHeight = map.driveRoad.h * LITE_ROAD_TILE;
  // Ordinary driving always shows a local area, even on the smallest maze/projector.
  // The timed fit-to-maze view is the only new complete gameplay map.
  const scale = full ? Math.min(Math.max(1,width-96)/worldWidth, Math.max(1,height-180)/worldHeight)
    : Math.max(.75, width/(worldWidth*.6), height/(worldHeight*.6)) * (MAP_ZOOMS.includes(zoom) ? zoom : 150)/100;
  const x = full ? worldWidth/2 : clamp(vehicle.x, width/(2*scale), worldWidth-width/(2*scale));
  const y = full ? worldHeight/2 : clamp(vehicle.y, height/(2*scale), worldHeight-height/(2*scale));
  return { x, y, scale, width, height, worldWidth, worldHeight, full };
}
export function projectMap(camera, position) {
  return { x: (position.x-camera.x)*camera.scale+camera.width/2, y: (position.y-camera.y)*camera.scale+camera.height/2 };
}
export function mapMarkers(attempt) {
  return [...attempt.checkpoints.map((c,i) => ({ id:c.id, position:{...c.position}, completed:attempt.completed[i], type:'checkpoint' })),
    { id:'EXIT', position:{...attempt.exit.position}, unlocked:attempt.completed.every(Boolean), type:'exit' }];
}

export class Map2D {
  constructor(canvas) {
    this.canvas = canvas; this.context = canvas.getContext('2d', { alpha:false });
    this.cache = document.createElement('canvas'); this.cacheContext = this.cache.getContext('2d', { alpha:false });
    this.builds = 0; this.draws = 0; this.samples = []; this.last = null;
  }
  setMap(map) {
    if (this.map === map) return;
    this.map = map;
    const {w,h,bits} = map.driveRoad, signature = `${w}x${h}:${bits.join('')}`;
    if (signature === this.signature) return;
    this.signature = signature; this.builds++;
    const unit = 4, ctx = this.cacheContext;
    this.cache.width = w*unit; this.cache.height = h*unit;
    ctx.fillStyle = '#17313e'; ctx.fillRect(0,0,this.cache.width,this.cache.height);
    ctx.fillStyle = '#a2b8bd';
    for (const r of rectangles(map)) ctx.fillRect(r.x*unit,r.z*unit,r.w*unit,r.d*unit);
    ctx.strokeStyle = '#53808a'; ctx.lineWidth = .6; ctx.beginPath();
    for (const r of wallRuns(map)) {
      if (r.direction%2===0) { ctx.moveTo(r.fixed*unit,r.start*unit);ctx.lineTo(r.fixed*unit,r.end*unit); }
      else {ctx.moveTo(r.start*unit,r.fixed*unit);ctx.lineTo(r.end*unit,r.fixed*unit);}
    }
    ctx.stroke();
  }
  render(map, attempt, {width,height,zoom=150,full=false}) {
    const started = performance.now(); this.setMap(map);
    width = Math.max(1,Math.round(width)); height = Math.max(1,Math.round(height));
    if (this.canvas.width!==width || this.canvas.height!==height) {this.canvas.width=width;this.canvas.height=height;}
    const ctx = this.context, camera = mapCamera(map,attempt.vehicle,width,height,zoom,full);
    ctx.setTransform(1,0,0,1,0,0); ctx.fillStyle='#102632';ctx.fillRect(0,0,width,height);
    ctx.imageSmoothingEnabled = false;
    const origin = projectMap(camera,{x:0,y:0});
    ctx.drawImage(this.cache,origin.x,origin.y,camera.worldWidth*camera.scale,camera.worldHeight*camera.scale);
    const markers = mapMarkers(attempt).map(marker => ({...marker,screen:projectMap(camera,marker.position)}));
    const player = projectMap(camera,attempt.vehicle);
    ctx.textAlign='center';ctx.textBaseline='middle';
    for (const m of markers) {
      const {x,y} = m.screen;
      if (x < -40 || y < -35 || x > width+40 || y > height+35) continue;
      ctx.save();ctx.translate(x,y);ctx.lineWidth=2;ctx.strokeStyle='#102632';
      if (m.type==='checkpoint') {
        ctx.fillStyle=m.completed?'#21694e':'#ffcc68';ctx.beginPath();
        if (m.completed) ctx.roundRect(-17,-13,34,26,4); else ctx.arc(0,0,18,0,Math.PI*2);
        ctx.fill();ctx.stroke();ctx.fillStyle=m.completed?'#ecfff5':'#162b36';
        ctx.font='bold 12px system-ui';ctx.fillText(m.completed?`${m.id} ✓`:m.id,0,0);
      } else {
        ctx.fillStyle=m.unlocked?'#21694e':'#713943';ctx.beginPath();ctx.roundRect(-28,-18,56,36,4);ctx.fill();ctx.stroke();
        ctx.fillStyle='#f1fff7';ctx.font='bold 11px system-ui';ctx.fillText('EXIT',0,-6);ctx.font='9px system-ui';ctx.fillText(m.unlocked?'OPEN':'LOCKED',0,8);
      }
      // Keep the identity readable when the correctly positioned vehicle covers a marker.
      if (Math.hypot(x-player.x,y-player.y)<35) {
        ctx.fillStyle='#102632';ctx.fillRect(-25,-40,50,20);ctx.fillStyle='#f1fff7';ctx.font='bold 11px system-ui';
        ctx.fillText(m.type==='exit'?'EXIT':m.completed?`${m.id} ✓`:m.id,0,-30);
      }
      ctx.restore();
    }
    ctx.save();ctx.translate(player.x,player.y);ctx.rotate(attempt.vehicle.heading);
    ctx.fillStyle='#e9fdff';ctx.strokeStyle='#074c6b';ctx.lineWidth=3;ctx.beginPath();
    ctx.moveTo(17,0);ctx.lineTo(-11,-10);ctx.lineTo(-6,0);ctx.lineTo(-11,10);ctx.closePath();ctx.fill();ctx.stroke();ctx.restore();
    const legendWidth = full?353:380, legendX = Math.max(12,width-legendWidth-12);
    ctx.fillStyle='#102632e8';ctx.fillRect(legendX,height-34,legendWidth,24);ctx.fillStyle='#dbecef';ctx.font='11px system-ui';ctx.textAlign='left';
    ctx.fillText(full?'FULL MAZE · amber: remaining · green ✓: completed':'LOCAL DRIVING · ▲ vehicle · amber: remaining · green ✓: completed',legendX+10,height-22);
    this.draws++;this.samples.push(performance.now()-started);if(this.samples.length>90)this.samples.shift();
    this.last={camera,markers,vehicle:{...attempt.vehicle,screen:player},cacheBuilds:this.builds,draws:this.draws,
      cacheBytes:this.cache.width*this.cache.height*4,canvasBytes:width*height*4,
      cpuPaintMeanMs:this.samples.reduce((a,b)=>a+b,0)/this.samples.length};
  }
  snapshot() { return this.last; }
}
