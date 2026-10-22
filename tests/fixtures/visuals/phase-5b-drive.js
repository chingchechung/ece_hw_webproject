  // Driving artwork owns only derived caches; authoritative roads/physics stay above.
  var driveArtwork=null;
  function prepareDriveArtwork(g,w,h){
    if(!driveArtwork)driveArtwork={road:null,marks:null,floor:null,depths:null,w:0,h:0,walls:[]};
    var art=driveArtwork,road=current.driveRoad;
    if(art.road!==road){
      art.road=road;art.marks=new Uint8Array(road.bits.length);
      function open(x,y){return x>=0&&y>=0&&x<road.w&&y<road.h&&road.bits[y*road.w+x]===1;}
      for(var y=0;y<road.h;y++)for(var x=0;x<road.w;x++)if(open(x,y)){
        // Shifting 56 map pixels is exactly four road subcells, so these
        // straight/junction flags match the original continuous floor probes.
        art.marks[y*road.w+x]=(open(x-4,y)&&open(x+4,y)?1:0)|(open(x,y-4)&&open(x,y+4)?2:0)|
          (!open(x-1,y)?4:0)|(!open(x+1,y)?8:0)|(!open(x,y-1)?16:0)|(!open(x,y+1)?32:0);
      }
      art.objects=null;
    }
    if(art.w!==w||art.h!==h){
      art.w=w;art.h=h;art.floor=g.createImageData(w,h);art.depths=new Float32Array(w);
      art.roof=g.createLinearGradient(0,0,0,h*.5);
      art.roof.addColorStop(0,'#142b3b');art.roof.addColorStop(.7,'#304e63');art.roof.addColorStop(1,'#607f8b');
      art.dash=g.createLinearGradient(0,h*.86,0,h);
      art.dash.addColorStop(0,'#314b59');art.dash.addColorStop(.16,'#142b38');art.dash.addColorStop(1,'#081923');
    }
    if(!art.walls.length)for(var side=0;side<2;side++){
      var colors=[];
      for(var fog=0;fog<64;fog++){
        var t=fog/63*.52,base=side?[111,142,155]:[149,174,183],air=[77,105,123];
        var rgb=base.map(function(c,i){return Math.round(c*(1-t)+air[i]*t);});
        function color(f){return 'rgb('+rgb.map(function(c){return Math.round(c*f);}).join(',')+')';}
        colors.push({face:color(1),upper:color(.89),seam:color(.79),base:color(.57),edge:color(1.08)});
      }
      art.walls.push(colors);
    }
  }
  function drawMazeCeiling(g,w,h,horizon,time){
    g.fillStyle=driveArtwork.roof;g.fillRect(0,0,w,h);
  }
  function drawRoadFloor(g,w,h,horizon,focal){
    // Project the road onto a simple flat asphalt floor (low-cost 2x2 pixels).
    var floorH=h-horizon;if(floorH<=0)return;
    var image=driveArtwork.floor,arr=image.data,camH=175,road=current.driveRoad,marks=driveArtwork.marks,
        cs=Math.cos(driveAngle),sn=Math.sin(driveAngle),rightX=-sn,rightY=cs;
    for(var yy=0;yy<floorH;yy+=2){
      var depth=camH*focal/(yy+1.3),half=depth*Math.tan(.67);
      for(var xx=0;xx<w;xx+=2){
        var sideways=(xx/w*2-1)*half;
        var wx=current.player.x+(cs*depth+rightX*sideways)/DRIVE_SCALE,
            wy=current.player.y+(sn*depth+rightY*sideways)/DRIVE_SCALE;
        var gx=Math.floor(wx/DRIVE_TILE),gy=Math.floor(wy/DRIVE_TILE),index=gy*road.w+gx,r,gr,b;
        if(gx>=0&&gy>=0&&gx<road.w&&gy<road.h&&road.bits[index]){
          var flags=marks[index],lx=wx-gx*DRIVE_TILE,ly=wy-gy*DRIVE_TILE;
          var detail=Math.max(0,1-depth/3500);
          var noise=(((Math.floor(wx/6)*13)^(Math.floor(wy/6)*17))&3)*detail;
          r=53+noise;gr=70+noise;b=83+noise;
          // Restrained world-anchored slab joints fade before subpixel distance.
          if(wx%28<.7||wy%28<.7){var joint=9*Math.max(0,1-depth*2/(focal*DRIVE_SCALE*1.2));r-=joint;gr-=joint;b-=joint*.8;}
          var horizontal=!!(flags&1),vertical=!!(flags&2);
          var mx=((wx%(2*TILE))+(2*TILE))%(2*TILE),
              my=((wy%(2*TILE))+(2*TILE))%(2*TILE);
          var dashX=(Math.floor(wx*DRIVE_SCALE/280)&1)===0,
              dashY=(Math.floor(wy*DRIVE_SCALE/280)&1)===0;
          if(horizontal&&!vertical&&Math.abs(my-TILE)<1.5&&dashX){r=219;gr=195;b=127}
          if(vertical&&!horizontal&&Math.abs(mx-TILE)<1.5&&dashY){r=219;gr=195;b=127}
          // Only actual collision boundaries receive a narrow shoulder/light.
          var edge=(flags&4&&lx<3)||(flags&8&&lx>11)||(flags&16&&ly<3)||(flags&32&&ly>11);
          if(edge){r=103;gr=146;b=159;
            if(((Math.floor((flags&12?wy:wx)/28))&1)===0){r=126;gr=199;b=202;}}
        }else{r=31;gr=49;b=63}
        var shade=Math.min(.55,depth/17000),fogR=76,fogG=101,fogB=119;
        r=(r*(1-shade)+fogR*shade)|0;gr=(gr*(1-shade)+fogG*shade)|0;b=(b*(1-shade)+fogB*shade)|0;
        var offset=yy*w*4+xx*4;
        for(var ry=0;ry<2&&yy+ry<floorH;ry++)for(var rx=0;rx<2&&xx+rx<w;rx++){
          var at=offset+ry*w*4+rx*4;arr[at]=r;arr[at+1]=gr;arr[at+2]=b;arr[at+3]=255;
        }
      }
    }
    g.putImageData(image,0,horizon,0,0,w,floorH);
  }
  function drawWallRays(g,w,h,horizon,focal){
    // Tall, continuous maze walls replace the old short seaside rails. They
    // reveal junction openings because the raycast stops only on real walls.
    var dir=driveAngle,maxD=1350,columns=2,depths=driveArtwork.depths;
    depths.fill(Infinity);
    for(var x=0;x<w;x+=columns){
      var off=Math.atan((x+.5-w*.5)/focal),hit=rayHit(current.player.x,current.player.y,dir+off,maxD);
      if(!hit.hit)continue;
      var dist=Math.max(88,hit.dist*DRIVE_SCALE*Math.cos(off));
      depths[x]=dist;if(x+1<w)depths[x+1]=dist;
      var bottom=horizon+175*focal/dist,
          top=horizon-590*focal/dist,
          height=bottom-top;
      if(bottom<0||top>h)continue;
      var fog=Math.min(63,Math.max(0,Math.floor((dist-500)/12500*63)));
      var face=driveArtwork.walls[hit.side][fog];
      // Very faint panel seams, never random color patches that mimic doors.
      var hitCoord=hit.side?current.player.x+Math.cos(dir+off)*hit.dist:
                              current.player.y+Math.sin(dir+off)*hit.dist;
      var seam=((hitCoord%56)+56)%56<1.2;
      g.fillStyle=seam?face.seam:face.face;
      g.fillRect(x,Math.max(0,top),columns+1,Math.min(h,bottom)-Math.max(0,top));
      var panelY=horizon-180*focal/dist;
      if(panelY>0){g.fillStyle=seam?face.seam:face.upper;g.fillRect(x,Math.max(0,top),columns+1,Math.min(h,panelY)-Math.max(0,top));}
      // Bright continuous cap/trim lets a driver trace openings and corners.
      var capY=top+26*focal/dist;
      if(capY>=0&&capY<h){g.fillStyle=face.edge;g.fillRect(x,capY,columns+1,Math.max(1,8*focal/dist))}
      var lightY=horizon-125*focal/dist;
      if(lightY>=0&&lightY<h){g.fillStyle=hit.side?'#6ea5b3':'#9bced2';g.fillRect(x,lightY,columns+1,Math.max(1,5*focal/dist));}
      var panelU=((hitCoord%56)+56)%56;
      if(panelU>24&&panelU<32&&dist<7000){
        var plateY=horizon-290*focal/dist,plateH=42*focal/dist;
        g.fillStyle=face.base;g.fillRect(x,plateY,columns+1,plateH);
        if(panelU<26){g.fillStyle='#8fc3ca';g.fillRect(x,plateY+plateH*.2,columns+1,plateH*.6);}
      }
      var lowerY=horizon+83*focal/dist;
      if(lowerY>=0&&lowerY<h){g.fillStyle=face.base;g.fillRect(x,lowerY,columns+1,Math.max(1,13*focal/dist))}
      if(bottom>=0&&bottom<h){g.fillStyle='#192d3d';g.fillRect(x,bottom-2,columns+1,Math.max(2,6*focal/dist))}
    }
  }
  function makeDriveCheckpoint(index,complete,finishPoint){
    var c=document.createElement('canvas');c.width=96;c.height=128;var g=c.getContext('2d');
    var accent=finishPoint?(complete?'#8de4c2':'#b4a0e6'):(complete?'#8de4c2':'#f2cd83');
    function box(x,y,w,h,color){g.fillStyle=color;g.fillRect(x,y,w,h);}
    g.fillStyle='#0d25384d';g.beginPath();g.ellipse(48,121,40,5,0,0,7);g.fill();
    if(finishPoint){
      box(5,20,12,104,'#233e50');box(79,20,12,104,'#233e50');
      box(8,24,4,96,accent);box(84,24,4,96,accent);
      box(8,8,80,34,'#183245');box(12,12,72,26,accent);
      g.fillStyle='#143144';g.font='bold 22px monospace';g.textAlign='center';g.fillText('EXIT',48,33);
      box(23,43,50,22,'#193448');g.strokeStyle=accent;g.lineWidth=3;g.beginPath();
      if(complete){g.moveTo(34,54);g.lineTo(61,54);g.moveTo(53,47);g.lineTo(62,54);g.lineTo(53,61);g.stroke();}
      else{g.strokeRect(43,46,10,9);box(39,52,18,10,accent);box(47,55,3,5,'#193448');}
      box(17,121,62,2,accent);
    }else{
      box(26,101,44,17,'#263e4b');box(20,116,56,6,'#6f96a2');
      box(19,41,58,65,'#203b4e');box(23,43,50,59,'#7396a3');box(26,47,44,51,'#142f41');
      box(28,51,40,27,'#0b2638');
      g.strokeStyle=complete?'#8de4c2':'#81dde3';g.lineWidth=2;g.beginPath();
      g.moveTo(30,66);g.lineTo(35,66);g.lineTo(39,57);g.lineTo(44,72);g.lineTo(49,62);g.lineTo(55,66);g.lineTo(65,66);g.stroke();
      box(29,84,25,3,'#597f8e');box(29,91,15,2,'#597f8e');box(18,50,3,42,accent);
      box(12,11,72,31,'#203b4e');box(16,15,64,23,accent);
      g.fillStyle='#163244';g.font='bold 24px monospace';g.textAlign='center';g.fillText('Q'+(index+1),48,35);
      g.fillStyle=accent;g.beginPath();g.arc(63,89,6,0,7);g.fill();
      if(complete){g.strokeStyle='#173448';g.lineWidth=2;g.beginPath();g.moveTo(59,89);g.lineTo(62,92);g.lineTo(67,86);g.stroke();}
      else box(61,87,4,4,'#173448');
    }
    return c;
  }
  function driveObjects(){
    var art=driveArtwork;if(art.objects)return art.objects;
    if(!art.checkpoints){
      art.checkpoints=[[],[]];
      for(var state=0;state<2;state++)for(var i=0;i<6;i++)art.checkpoints[state][i]=makeDriveCheckpoint(i,!!state,i===5);
    }
    art.objects=current.stations.map(function(station,index){
      var pos=worldCenter(station.x,station.y),best=null;
      [0,Math.PI/2,Math.PI,-Math.PI/2].forEach(function(angle){
        var distance=rayHit(pos.x,pos.y,angle,100).dist;
        if(!best||distance<best.distance)best={angle:angle,distance:distance};
      });
      // The visual pedestal sits toward an actual road edge. Its authoritative
      // station/eligibility position is unchanged and is never written here.
      var offset=Math.max(0,Math.min(18,best.distance-10));
      return {pos:{x:pos.x+Math.cos(best.angle)*offset,y:pos.y+Math.sin(best.angle)*offset},index:index,finish:false};
    });
    art.objects.push({pos:worldCenter(current.exit.x,current.exit.y),index:5,finish:true});
    return art.objects;
  }
  function projectDriveObject(ob,w,h,horizon,focal){
    var p=current.player,co=Math.cos(driveAngle),si=Math.sin(driveAngle);
    var dx=ob.pos.x-p.x,dy=ob.pos.y-p.y,depth=(dx*co+dy*si)*DRIVE_SCALE;
    if(depth<120||depth>17000||!lineVisible(p.x,p.y,ob.pos.x,ob.pos.y))return null;
    var side=(-dx*si+dy*co)*DRIVE_SCALE,sx=w*.5+side*focal/depth;
    var width=ob.finish?460:240,height=ob.finish?600:320;
    var scale=Math.min(focal/depth,w*(ob.finish ? .34 : .24)/width,h*.8/height);
    var pw=width*scale,ph=height*scale,base=horizon+175*focal/depth;
    if(pw<8||sx+pw*.8<0||sx-pw*.8>w)return null;
    return {x:sx-pw/2,y:base-ph,w:pw,h:ph,depth:depth,base:base};
  }
  function drawRoadsideSigns(g,w,h,horizon,focal,time){
    var objects=driveObjects().map(function(ob){return {object:ob,projection:projectDriveObject(ob,w,h,horizon,focal)};})
      .filter(function(item){return !!item.projection;}).sort(function(a,b){return b.projection.depth-a.projection.depth;});
    objects.forEach(function(item){
      var ob=item.object,p=item.projection,complete=ob.finish?done.every(Boolean):done[ob.index];
      // Column depth clipping prevents large nearby billboards bleeding through
      // corner walls even when their centre has a clear line of sight.
      g.save();g.beginPath();
      var start=Math.max(0,Math.floor(p.x)),end=Math.min(w,Math.ceil(p.x+p.w)),run=-1;
      for(var x=start;x<=end;x++){
        var visible=x<end&&driveArtwork.depths[x]>=p.depth-1;
        if(visible&&run<0)run=x;
        if(!visible&&run>=0){g.rect(run,0,x-run,h);run=-1;}
      }
      g.clip();g.imageSmoothingEnabled=true;
      g.drawImage(driveArtwork.checkpoints[complete?1:0][ob.index],p.x,p.y,p.w,p.h);
      if(!complete&&!ob.finish){
        var pulse=motionPreference.matches ? .5 : .5+.13*Math.sin(time*3);
        g.fillStyle='rgba(255,222,149,'+pulse+')';g.fillRect(p.x+p.w*.17,p.y+p.h*.39,Math.max(1,p.w*.025),p.h*.31);
      }
      g.restore();
    });
  }
  function drawCockpit(g,w,h,time){
    // 2D cockpit overlay; constant complexity independent of world geometry.
    var sway=motionPreference.matches?0:Math.sin(driveDistance*.012)*Math.min(.55,Math.abs(driveSpeed)/650),base=h*.90+sway;
    g.save();g.fillStyle=driveArtwork.dash;
    g.beginPath();g.moveTo(0,h);g.lineTo(0,base+12);g.quadraticCurveTo(w*.5,base-14,w,base+12);g.lineTo(w,h);g.closePath();g.fill();
    g.strokeStyle='#5b8290';g.lineWidth=1;g.stroke();
    // Slender pillars leave turning lanes visible at the edge of the windshield.
    g.strokeStyle='#102634';g.lineWidth=5;g.beginPath();g.moveTo(1,0);g.lineTo(w*.035,h*.32);g.lineTo(w*.065,h*.81);g.stroke();
    g.beginPath();g.moveTo(w-1,0);g.lineTo(w*.965,h*.32);g.lineTo(w*.935,h*.81);g.stroke();
    // A cropped steering wheel on the left foreground.
    var cx=w*.24,cy=h*.995,rad=Math.min(w*.13,h*.15);
    g.save();g.translate(cx,cy);
    var steering=(pressed.d||pressed.arrowright?1:0)-(pressed.a||pressed.arrowleft?1:0);
    if(!motionPreference.matches)g.rotate(steering*.16);
    cx=0;cy=0;g.lineWidth=Math.max(7,rad*.17);g.strokeStyle='#091a25';g.beginPath();g.arc(cx,cy,rad,Math.PI,Math.PI*2);g.stroke();
    g.strokeStyle='#64737d';g.lineWidth=rad*.03;g.beginPath();g.arc(cx,cy,rad*.92,Math.PI*1.05,Math.PI*1.95);g.stroke();
    g.strokeStyle='#101e26';g.lineWidth=Math.max(12,rad*.18);g.beginPath();g.moveTo(cx,cy);g.lineTo(cx-rad*.66,cy-rad*.58);g.moveTo(cx,cy);g.lineTo(cx+rad*.66,cy-rad*.58);g.stroke();
    g.fillStyle='#385968';g.beginPath();g.arc(cx,cy,rad*.28,0,7);g.fill();g.restore();
    var panelX=w*.58,panelY=base-18,panelW=w*.25;
    g.fillStyle='#0c2431';g.fillRect(panelX,panelY,panelW,Math.max(13,h*.065));
    g.fillStyle='#9fc3cc';g.font='bold '+Math.max(7,Math.round(w*.012))+'px monospace';g.textAlign='left';
    var gear=driveSpeed < -1?'R':driveSpeed>1?'D':'N';
    var gearLabel=gear==='R'?'R / REVERSE':gear==='D'?'D / DRIVE':'N / STOP';
    g.fillText(w<420?gear:gearLabel,panelX+6,panelY+10);
    var speed=Math.min(1,Math.abs(driveSpeed)/DRIVE_TOP_SPEED);
    g.fillStyle=driveSpeed<0?'#f2cd83':'#8de4c2';g.fillRect(panelX+panelW*.53,panelY+5,Math.max(1,panelW*.42*speed),3);
    g.restore();
  }
  function renderDrive(time){
    if(!current||!dctx)return;
    var W=Math.min(720,Math.max(280,Math.round(viewport.w*.7)));var H=Math.max(180,Math.round(W*viewport.h/viewport.w));
    if(driveSurface.width!==W||driveSurface.height!==H){driveSurface.width=W;driveSurface.height=H}
    prepareDriveArtwork(dctx,W,H);
    var bob=motionPreference.matches?0:Math.sin(driveDistance*.012)*Math.min(.65,Math.abs(driveSpeed)/650);
    var horizon=Math.round(H*.49+bob),focal=W/(2*Math.tan(.67));
    drawMazeCeiling(dctx,W,H,horizon,time);
    drawRoadFloor(dctx,W,H,horizon,focal);
    drawWallRays(dctx,W,H,horizon,focal);
    drawRoadsideSigns(dctx,W,H,horizon,focal,time);
    drawCockpit(dctx,W,H,time);
    ctx.clearRect(0,0,viewport.w,viewport.h);ctx.imageSmoothingEnabled=true;ctx.drawImage(driveSurface,0,0,viewport.w,viewport.h);
    if(showMap)drawMinimap();
  }
