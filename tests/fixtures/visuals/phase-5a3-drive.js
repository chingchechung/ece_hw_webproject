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
