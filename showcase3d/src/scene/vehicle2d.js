// Original procedural arcade car. Artwork faces +X; heading uses Lite's +Y-down axis.
export function createVehicleSprite() {
  const canvas = Object.assign(document.createElement('canvas'),{width:144,height:96});
  const c = canvas.getContext('2d'); c.scale(2,2); c.translate(36,24);
  c.fillStyle='#041c2b70';c.beginPath();c.ellipse(2,3,31,18,0,0,Math.PI*2);c.fill();
  c.fillStyle='#101b26';
  for(const x of [-17,15])for(const y of [-17,11]){c.beginPath();c.roundRect(x-5,y,11,6,2);c.fill();}
  const body=c.createLinearGradient(0,-14,0,14);body.addColorStop(0,'#8eeeff');body.addColorStop(.4,'#25badf');body.addColorStop(1,'#1177ae');
  c.fillStyle=body;c.strokeStyle='#053d60';c.lineWidth=1.6;c.beginPath();c.roundRect(-28,-14,56,28,7);c.fill();c.stroke();
  c.fillStyle='#075a88';c.beginPath();c.roundRect(-12,-11,27,22,5);c.fill();
  c.fillStyle='#bdeeff';c.beginPath();c.moveTo(9,-10);c.lineTo(16,-8);c.lineTo(16,8);c.lineTo(9,10);c.closePath();c.fill();
  c.fillStyle='#183d5b';c.fillRect(-18,-8,7,16);
  c.fillStyle='#78d7ed';c.fillRect(-8,-8,14,16);c.fillStyle='#e1faff';c.fillRect(19,-2,6,4);
  c.strokeStyle='#afefff';c.lineWidth=1;c.strokeRect(-7,-7,12,14);
  c.fillStyle='#fff3be';for(const y of [-10,6])c.fillRect(25,y,4,4);
  c.fillStyle='#ff5b77';for(const y of [-10,6])c.fillRect(-29,y,3,4);
  c.fillStyle='#c5eaf0';c.fillRect(-26,-7,2,14);c.fillStyle='#0d3452';c.fillRect(29,-7,2,14);
  return canvas;
}
export function drawVehicle(ctx,sprite,position,heading,full=false) {
  const width=full?34:46,height=width*2/3;
  ctx.save();ctx.translate(position.x,position.y);ctx.rotate(heading);
  ctx.drawImage(sprite,-width/2,-height/2,width,height);ctx.restore();
}
