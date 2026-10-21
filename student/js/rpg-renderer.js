/* Original Canvas pixel artwork for the engineering lab. No game-state writes.
 * Atlases are built once; one static scene is retained for the current maze.
 * All dimensions are world pixels. Collision/topology belong to game.js.
 */
(function(root){
  'use strict';
  function canvas(w,h){var c=document.createElement('canvas');c.width=w;c.height=h;return c;}
  function rect(g,x,y,w,h,color){g.fillStyle=color;g.fillRect(x,y,w,h);}
  var directionRows={down:0,left:1,right:2,up:3};
  var atmospheres={
    off:{shade:0,radius:0,scale:0,reveal:0},
    normal:{shade:.33,radius:190,scale:1.1,prepare:.04,slashEnd:.34,impactStart:.26,impactEnd:.42,reveal:.46},
    strong:{shade:.5,radius:150,scale:1.5,prepare:.08,slashEnd:.45,impactStart:.3,impactEnd:.5,reveal:.6}
  };
  var ink='#253e50',teal='#217f83',mint='#85d5b2',gold='#f1bd62';
  var glyphs={Q:['111','101','101','111','001'],1:['010','110','010','010','111'],
    2:['110','001','010','100','111'],3:['110','001','010','001','110'],
    4:['101','101','111','001','001'],5:['111','100','110','001','110'],
    E:['111','100','110','100','111'],X:['101','101','010','101','101'],
    I:['111','010','010','010','111'],T:['111','010','010','010','010'],
    L:['100','100','100','100','111'],A:['010','101','111','101','101'],
    B:['110','101','110','101','110']};
  function lettering(g,text,x,y,color,scale){
    for(var n=0;n<text.length;n++){
      var rows=glyphs[text[n]];
      if(rows)for(var r=0;r<5;r++)for(var col=0;col<3;col++)if(rows[r][col]==='1')rect(g,x+(n*4+col)*scale,y+r*scale,scale,scale,color);
    }
  }
  function makeCharacterAtlas(){
    var atlas=canvas(32*6,40*4),g=atlas.getContext('2d');
    var hair='#293d50',hairLight='#4a6070',skin='#e7b48b',skinShade='#bf8569',coat='#f4f0df',coatShade='#a9c5c1';
    for(var direction=0;direction<4;direction++)for(var frame=0;frame<6;frame++){
      g.save();g.translate(frame*32,direction*40);
      var walking=frame>=2,phase=walking?frame-2:0;
      var stride=walking?(phase===0?2:phase===2?-2:0):0;
      var bob=walking&&(phase===1||phase===3)?1:0;
      var side=direction===1||direction===2,flip=direction===1;
      if(flip){g.translate(32,0);g.scale(-1,1);}
      // Soft stepped ground shadow; the sprite's centre remains at the same feet.
      rect(g,8,35,17,2,'#6c8e8380');rect(g,6,36,21,2,'#6c8e8340');
      // Two independently stepping shoes and trouser legs.
      rect(g,10,27,5,8+stride,ink);rect(g,17,27,5,8-stride,ink);
      rect(g,11,28,3,5+stride,'#40586d');rect(g,18,28,3,5-stride,'#40586d');
      rect(g,9,34+stride,7,3,ink);rect(g,17,34-stride,7,3,ink);
      rect(g,10,36+stride,6,1,'#88a8a8');rect(g,18,36-stride,6,1,'#88a8a8');
      g.translate(0,bob);
      // Shirt, open lab jacket, sleeves and hands.
      rect(g,9,16,14,14,ink);rect(g,7,18,4,10,ink);rect(g,22,18,4,10,ink);
      rect(g,10,17,12,11,teal);rect(g,10,18,4,11,coat);rect(g,19,18,4,11,coatShade);
      rect(g,10,28,13,2,coatShade);rect(g,8,19+stride/2,3,7,coatShade);
      rect(g,23,19-stride/2,2,7,coat);rect(g,8,26+stride/2,3,3,skinShade);rect(g,23,26-stride/2,3,3,skin);
      rect(g,11,17,3,2,'#ffffff');rect(g,19,17,3,2,'#dae2d4');
      // Face and sculpted hair, not a recoloured stock sprite.
      rect(g,10,4,13,13,ink);rect(g,9,7,15,7,hair);rect(g,11,8,11,8,skinShade);
      rect(g,11,8,10,7,skin);rect(g,11,4,11,4,hair);rect(g,10,6,13,3,hair);
      rect(g,12,4,7,1,hairLight);rect(g,17,2,4,2,hair);rect(g,18,2,2,1,hairLight);rect(g,10,8,2,4,hair);rect(g,21,7,2,5,hair);
      if(direction===3){
        rect(g,10,5,13,10,hair);rect(g,12,5,8,2,hairLight);rect(g,11,14,10,2,skinShade);
        // Ochre instrument bag identifies the back direction immediately.
        rect(g,11,18,11,11,ink);rect(g,12,19,9,9,'#c78a51');rect(g,13,19,7,3,'#e8b46d');
        rect(g,14,24,5,3,'#a56b43');rect(g,11,18,2,10,'#f2c783');rect(g,15,24,3,1,'#f6ddb3');
      }else if(side){
        rect(g,9,7,6,10,hair);rect(g,10,6,8,3,hairLight);rect(g,20,10,3,4,skin);
        rect(g,20,10,1,2,ink);rect(g,22,12,2,2,skin);rect(g,19,15,3,1,skinShade);
        rect(g,10,19,5,10,'#c78a51');rect(g,10,18,2,11,'#e8b46d');
        rect(g,19,20,3,5,coat);rect(g,20,25,3,3,skin);rect(g,19,20,2,1,'#ffffff');
      }else{
        rect(g,11,8,3,2,hair);rect(g,16,8,5,1,hair);rect(g,12,11,2,2,ink);rect(g,18,11,2,2,ink);
        rect(g,11,13,1,1,skinShade);rect(g,20,12,1,2,'#f2cba7');
        rect(g,13,11,1,1,'#f9faf0');rect(g,19,11,1,1,'#f9faf0');rect(g,15,14,3,1,skinShade);
        rect(g,20,18,2,11,'#d59a58');rect(g,20,21,3,4,ink);rect(g,20,21,2,3,gold);
        rect(g,11,22,3,1,coatShade);rect(g,17,23,1,4,'#b0d4cd');
      }
      // The second idle frame only lifts the collar seam: no head/foot jitter.
      if(frame===1)rect(g,14,18,5,1,direction===3?'#f0c580':'#75b9b2');
      g.restore();
    }
    return atlas;
  }
  function makeTiles(tile){
    var atlas=canvas(tile*16,tile*2),g=atlas.getContext('2d');
    // Four restrained 56px floor quadrants, plus subtle surface variants.
    for(var i=0;i<8;i++){
      var x=i*tile;rect(g,x,0,tile,tile,i%2?'#c8d5c8':'#cbd8cc');
      if(i%2===0)rect(g,x,0,1,tile,'#b6c9be');
      if((i>>1)%2===0)rect(g,x,0,tile,1,'#b6c9be');
      rect(g,x+5+(i*3)%12,7+(i*7)%13,2,1,'#bfd0c4');
      rect(g,x+8+(i*5)%13,5+(i*3)%14,1,1,'#dfE6d8');
    }
    // N/E/S/W edge masks connect adjacent wall tops without false seams.
    for(var mask=0;mask<16;mask++){
      var px=mask*tile,py=tile;
      rect(g,px,py,tile,tile,'#87a7ad');
      if(mask&1){rect(g,px,py,tile,2,'#314e63');rect(g,px+1,py+2,tile-2,2,'#c0d4cd');}
      if(mask&2){rect(g,px+tile-3,py,3,tile,'#365b70');rect(g,px+tile-4,py+2,1,tile-3,'#aec7c5');}
      if(mask&4){
        rect(g,px,py+tile-11,tile,11,'#375d73');rect(g,px,py+tile-11,tile,2,'#c0d4cd');
        rect(g,px+1,py+tile-8,tile-2,4,'#567b8c');rect(g,px,py+tile-2,tile,2,ink);
      }
      if(mask&8){rect(g,px,py,2,tile,ink);rect(g,px+2,py+2,2,tile-3,'#b6ccc6');}
      // Recessed wall channel remains within the non-walkable tile.
      if(mask&4){rect(g,px+6,py+tile-6,8,1,'#7598a4');rect(g,px+7,py+tile-5,2,1,'#426c80');}
    }
    return atlas;
  }
  function makeStation(index,complete){
    var c=canvas(52,64),g=c.getContext('2d');
    // Grounding, steel legs and warm lab worktop.
    rect(g,6,52,40,5,'#6d96835c');rect(g,8,44,5,10,ink);rect(g,39,44,5,10,ink);
    rect(g,3,39,46,8,ink);rect(g,4,38,44,6,'#c58d58');rect(g,5,37,42,4,'#f0c38b');
    rect(g,8,45,36,2,'#916b4e');rect(g,10,46,3,5,'#63858a');rect(g,39,46,3,5,'#63858a');
    // Oscilloscope display, small instrument and keyboard (no answer content).
    rect(g,10,13,30,25,ink);rect(g,12,15,26,20,'#577f8c');rect(g,13,16,24,17,'#183e51');
    rect(g,15,18,20,1,'#366374');rect(g,15,22,20,1,'#366374');rect(g,15,27,20,1,'#366374');
    for(var x=17;x<35;x+=5)rect(g,x,18,1,12,'#2c5668');
    if(complete){
      rect(g,19,25,3,3,mint);rect(g,22,27,3,3,mint);rect(g,25,24,3,4,mint);rect(g,28,21,3,4,mint);
    }else{
      rect(g,15,26,5,2,'#80d7cd');rect(g,19,22,2,5,'#80d7cd');rect(g,21,21,4,2,'#80d7cd');
      rect(g,24,22,2,5,'#80d7cd');rect(g,26,26,4,2,'#80d7cd');rect(g,29,23,5,2,'#80d7cd');
    }
    rect(g,22,36,6,3,ink);rect(g,16,38,18,2,'#72938e');rect(g,13,41,23,3,'#637781');
    rect(g,15,41,18,1,'#d6dfcf');rect(g,39,33,7,6,'#345a70');rect(g,40,34,5,3,complete?mint:gold);
    rect(g,40,41,4,2,'#91664e');
    // Keep Q identity visible in both states; colour and icon both signal passing.
    rect(g,13,0,26,16,ink);rect(g,15,2,22,12,complete?'#82c9a6':gold);
    lettering(g,'Q'+(index+1),19,3,ink,2);
    return c;
  }
  function makeExit(unlocked){
    var c=canvas(56,68),g=c.getContext('2d');
    rect(g,4,57,48,5,'#78918460');rect(g,6,12,44,46,ink);rect(g,9,13,38,42,'#8a82ae');
    rect(g,12,16,32,37,'#203f55');
    rect(g,14,17,28,34,unlocked?'#b5a7d2':'#778c98');
    rect(g,16,19,11,30,unlocked?'#655d8c':'#536977');rect(g,29,19,11,30,unlocked?'#766fa2':'#536977');
    rect(g,15,20,10,1,'#bcd0cf');rect(g,30,20,9,1,'#bcd0cf');
    rect(g,24,34,2,5,unlocked?mint:gold);rect(g,30,34,2,5,unlocked?mint:gold);
    if(unlocked){
      rect(g,23,24,12,13,'#263f58');
      var arrow=['00100','00010','11111','00010','00100'];
      for(var ay=0;ay<5;ay++)for(var ax=0;ax<5;ax++)if(arrow[ay][ax]==='1')rect(g,23+ax*2,25+ay*2,2,2,mint);
    }else{
      rect(g,24,27,8,4,gold);rect(g,22,30,12,9,gold);rect(g,24,26,2,7,gold);rect(g,30,26,2,7,gold);
      rect(g,26,32,4,3,ink);rect(g,27,34,2,3,ink);
    }
    rect(g,7,52,42,5,'#8fa7a8');rect(g,10,52,36,2,'#d3ddd0');
    rect(g,10,0,36,16,ink);rect(g,12,2,32,12,unlocked?'#c0a9df':'#c7badb');lettering(g,'EXIT',13,3,ink,2);
    rect(g,7,17,3,29,unlocked?'#7fd1af':'#a6b7b9');rect(g,46,17,3,29,unlocked?'#7fd1af':'#a6b7b9');
    return c;
  }
  function makeLightOpening(){
    var c=canvas(256,256),g=c.getContext('2d');
    var gradient=g.createRadialGradient(128,128,0,128,128,128);
    gradient.addColorStop(0,'#000');gradient.addColorStop(.3,'#000');
    gradient.addColorStop(.68,'#0008');gradient.addColorStop(1,'#0000');
    g.fillStyle=gradient;g.fillRect(0,0,256,256);return c;
  }
  function makeActivationGlow(){
    var c=canvas(96,96),g=c.getContext('2d');
    var gradient=g.createRadialGradient(48,48,5,48,48,46);
    gradient.addColorStop(0,'#b6f4da99');gradient.addColorStop(.45,'#8de3d34d');gradient.addColorStop(1,'#8de3d300');
    g.fillStyle=gradient;g.fillRect(0,0,96,96);return c;
  }
  function makeSwipeAtlas(){
    var c=canvas(96*8,96),g=c.getContext('2d');
    var points=[[3,-16],[9,-14],[15,-10],[19,-5],[20,1],[18,8],[13,13],[6,16]];
    function ribbon(first,last,offset,alpha){
      g.save();g.globalAlpha=alpha;
      for(var i=first;i<last;i++){
        var a=points[i],b=points[i+1],steps=Math.max(Math.abs(b[0]-a[0]),Math.abs(b[1]-a[1]));
        for(var n=0;n<=steps;n++){
          var x=Math.round(a[0]+(b[0]-a[0])*n/steps)*2+offset,y=Math.round(a[1]+(b[1]-a[1])*n/steps)*2;
          rect(g,x-4,y-4,9,9,'#76e7e7a0');rect(g,x-1,y-1,3,3,'#f4fff5');
        }
      }
      g.restore();
    }
    for(var frame=0;frame<8;frame++){
      g.save();g.translate(frame*96+48,48);
      var first=Math.max(0,frame-3),last=Math.min(7,2+frame*2);
      // Cached short trailing ribbon, followed by the bright sweeping front.
      ribbon(Math.max(0,first-1),Math.max(1,last-1),-6,.22);
      ribbon(first,last,0,1);
      var tip=points[last];rect(g,tip[0]*2-1,tip[1]*2-1,3,3,'#ffe5a3');g.restore();
    }
    return c;
  }
  function create(tile){
    tile=tile||28;
    var characters=makeCharacterAtlas(),tiles=makeTiles(tile),stations=[[],[]],exits=[makeExit(false),makeExit(true)];
    for(var state=0;state<2;state++)for(var q=0;q<5;q++)stations[state][q]=makeStation(q,!!state);
    var opening=makeLightOpening(),glow=makeActivationGlow(),swipes=makeSwipeAtlas();
    var light=canvas(1,1),lightX=null,lightY=null,lightRadius=null,lightMode='',interaction=null,atmosphere='strong';
    var reducedMotion=root.matchMedia('(prefers-reduced-motion: reduce)');
    var scene=null,sceneMaze=null;
    function prepare(maze){
      if(sceneMaze===maze)return;
      if(interaction&&interaction.maze!==maze)interaction=null;
      sceneMaze=maze;scene=canvas(maze.grid[0].length*tile,maze.grid.length*tile);
      var g=scene.getContext('2d');g.imageSmoothingEnabled=false;
      for(var y=0;y<maze.grid.length;y++)for(var x=0;x<maze.grid[0].length;x++){
        var px=x*tile,py=y*tile;
        if(maze.grid[y][x]){
          var mask=(maze.grid[y-1]&&maze.grid[y-1][x]===0?1:0)|(maze.grid[y][x+1]===0?2:0)|
            (maze.grid[y+1]&&maze.grid[y+1][x]===0?4:0)|(maze.grid[y][x-1]===0?8:0);
          g.drawImage(tiles,mask*tile,tile,tile,tile,px,py,tile,tile);
          // Sparse technical wall plates/lights, never placed on traversable cells.
          if((mask&4)&&(x*11+y*19)%13===0){
            rect(g,px+8,py+5,13,6,ink);rect(g,px+9,py+6,11,3,'#cae1c8');rect(g,px+10,py+10,9,1,'#507e88');
          }
        }else{
          var variant=(x%2)+2*(y%2)+4*((x*13+y*7)%9===0?1:0);
          g.drawImage(tiles,variant*tile,0,tile,tile,px,py,tile,tile);
          if(maze.grid[y-1]&&maze.grid[y-1][x])rect(g,px,py,tile,3,'#9bb6aa');
          if(maze.grid[y][x-1])rect(g,px,py,2,tile,'#adc1b3');
        }
      }
      // Painted welcome mat at the original start; no extra decorative obstacles.
      var sx=tile*3,sy=tile*3;
      rect(g,sx-22,sy-19,44,38,'#a2bdb1');rect(g,sx-20,sy-17,40,34,'#d9e1d0');
      rect(g,sx-18,sy-15,36,30,'#b7cfc0');lettering(g,'LAB',sx-10,sy-9,teal,2);
      rect(g,sx-10,sy+5,20,2,'#7ea89d');
    }
    function drawCharacter(g,player,time){
      var row=directionRows[player.dir]||0;
      var frame=player.moving?2+(Math.floor((player.walk||0)*.8)%4):(Math.floor(time*.8)%2);
      g.drawImage(characters,frame*32,row*40,32,40,Math.round(player.x-16),Math.round(player.y-27),32,40);
    }
    function drawStation(g,x,y,index,complete,time,near){
      if(atmosphere!=='off'&&near&&!complete){
        g.save();g.globalAlpha=.4+(reducedMotion.matches?0:.12*Math.sin(time*3));g.drawImage(glow,x-48,y-44);g.restore();
      }
      if(near){
        rect(g,x-26,y+18,52,2,'#318b89');rect(g,x-26,y+14,2,5,'#318b89');rect(g,x+24,y+14,2,5,'#318b89');
      }
      g.drawImage(stations[complete?1:0][index],x-26,y-42);
      if(!complete){
        var pulse=Math.floor(time*2+index)%2;rect(g,x+14,y-7,3,2,pulse?'#fff0b6':gold);
      }
      if(near){rect(g,x+16,y-42,12,12,ink);lettering(g,'E',x+19,y-39,'#eff4df',1);}
    }
    function drawExit(g,x,y,unlocked,time,near){
      if(atmosphere!=='off'&&unlocked){
        g.save();g.globalAlpha=.5+(reducedMotion.matches?0:.12*Math.sin(time*2));
        g.drawImage(glow,x-48,y-44);g.restore();
      }
      g.drawImage(exits[unlocked?1:0],x-28,y-43);
      if(unlocked){rect(g,x-18,y+13,36,2,Math.floor(time*2)%2?'#bbefd0':mint);}
      if(near){rect(g,x+19,y-43,12,12,ink);lettering(g,'E',x+23,y-40,'#eff4df',1);}
    }
    function drawFocusLight(g,player,viewX,viewY,zoom,viewport,dpr,mapOpen){
      var settings=atmospheres[atmosphere];if(!settings.shade)return;
      // Quarter-resolution soft overlay; cached gradient and one small buffer.
      // Rebuild only when the light moves by a CSS pixel, zoom or viewport changes.
      var w=Math.ceil(viewport.w/4),h=Math.ceil(viewport.h/4);
      var cx=Math.round(player.x*zoom-viewX),cy=Math.round((player.y-8)*zoom-viewY);
      var radius=Math.max(112*zoom,Math.min(settings.radius*zoom,Math.min(viewport.w,viewport.h)*.8));
      if(light.width!==w||light.height!==h||lightX!==cx||lightY!==cy||lightRadius!==radius||lightMode!==atmosphere){
        if(light.width!==w||light.height!==h){light.width=w;light.height=h;}
        var lg=light.getContext('2d');lg.clearRect(0,0,w,h);
        rect(lg,0,0,w,h,'rgba(10,27,40,'+settings.shade+')');lg.globalCompositeOperation='destination-out';
        lg.drawImage(opening,(cx-radius)/4,(cy-radius)/4,radius/2,radius/2);
        lg.globalCompositeOperation='source-over';lightX=cx;lightY=cy;lightRadius=radius;lightMode=atmosphere;
      }
      g.save();g.setTransform(dpr,0,0,dpr,0,0);g.imageSmoothingEnabled=true;
      g.globalAlpha=mapOpen ? .35 : 1;g.drawImage(light,0,0,w*4,h*4);g.restore();
    }
    function beginInteraction(maze,index,time){
      var settings=atmospheres[atmosphere];
      if(reducedMotion.matches||!settings.reveal)return 0;
      interaction={maze:maze,index:index,x:maze.player.x,y:maze.player.y,dir:maze.player.dir,start:time,settings:settings};
      return settings.reveal;
    }
    function clearInteraction(){interaction=null;}
    function setAtmosphere(value){
      if(!Object.prototype.hasOwnProperty.call(atmospheres,value))return false;
      atmosphere=value;clearInteraction();return true;
    }
    function drawInteraction(g,maze,time){
      if(!interaction||interaction.maze!==maze)return;
      if(reducedMotion.matches){interaction=null;return;}
      var age=time-interaction.start,settings=interaction.settings;
      if(age>=settings.reveal){interaction=null;return;}
      if(age<0)return;
      var s=maze.stations[interaction.index],sx=(s.x*2+1)*tile,sy=(s.y*2+1)*tile;
      if(age>=settings.impactStart&&age<settings.impactEnd){
        var impact=Math.sin(Math.PI*(age-settings.impactStart)/(settings.impactEnd-settings.impactStart));
        g.save();g.globalAlpha=impact*.9;g.beginPath();g.rect(sx-28,sy-25,56,45);g.clip();
        g.drawImage(glow,sx-48,sy-44);g.strokeStyle='#f4fff5';g.lineWidth=2;g.strokeRect(sx-14,sy-25,28,17);g.restore();
      }
      if(age>=settings.slashEnd)return;
      var phase=Math.max(0,(age-settings.prepare)/(settings.slashEnd-settings.prepare));
      var frame=Math.min(7,Math.floor(phase*8)),size=96*settings.scale;
      g.save();g.globalAlpha=age<settings.prepare ? .65 : 1-phase*.45;
      // Preserve the station's opaque question sign for every facing direction.
      g.beginPath();g.rect(interaction.x-90,interaction.y-97,180,180);g.rect(sx-13,sy-42,26,16);g.clip('evenodd');
      g.translate(Math.round(interaction.x),Math.round(interaction.y-7));
      g.rotate(({right:0,down:Math.PI/2,left:Math.PI,up:-Math.PI/2})[interaction.dir]||0);
      g.drawImage(swipes,frame*96,0,96,96,-size/2,-size/2,size,size);g.restore();
    }
    function render(g,maze,passed,camera,zoom,viewport,time,near,mapOpen){
      prepare(maze);
      g.clearRect(0,0,viewport.w,viewport.h);rect(g,0,0,viewport.w,viewport.h,'#8fa9a2');
      g.save();g.imageSmoothingEnabled=false;
      // Snap the view translation to device pixels without modifying the camera.
      var dpr=g.getTransform().a;
      var viewX=Math.round(camera.x*zoom*dpr)/dpr,viewY=Math.round(camera.y*zoom*dpr)/dpr;
      g.scale(zoom,zoom);g.translate(-viewX/zoom,-viewY/zoom);
      var sx=Math.max(0,Math.floor(camera.x)-1),sy=Math.max(0,Math.floor(camera.y)-1);
      var sw=Math.min(scene.width,Math.ceil(camera.x+viewport.w/zoom)+1)-sx;
      var sh=Math.min(scene.height,Math.ceil(camera.y+viewport.h/zoom)+1)-sy;
      g.drawImage(scene,sx,sy,sw,sh,sx,sy,sw,sh);
      drawFocusLight(g,maze.player,viewX,viewY,zoom,viewport,dpr,mapOpen);
      var left=camera.x-55,right=camera.x+viewport.w/zoom+55,top=camera.y-70,bottom=camera.y+viewport.h/zoom+55;
      for(var i=0;i<maze.stations.length;i++){
        var s=maze.stations[i],x=(s.x*2+1)*tile,y=(s.y*2+1)*tile;
        if(x>=left&&x<=right&&y>=top&&y<=bottom)drawStation(g,x,y,i,passed[i],time,near&&near.type==='question'&&near.index===i);
      }
      var ex=(maze.exit.x*2+1)*tile,ey=(maze.exit.y*2+1)*tile;
      if(ex>=left&&ex<=right&&ey>=top&&ey<=bottom)drawExit(g,ex,ey,passed.every(Boolean),time,near&&near.type==='finish');
      drawCharacter(g,maze.player,time);drawInteraction(g,maze,time);g.restore();
    }
    return Object.freeze({render:render,drawCharacter:drawCharacter,drawStation:drawStation,drawExit:drawExit,
      beginInteraction:beginInteraction,clearInteraction:clearInteraction,setAtmosphere:setAtmosphere,
      getAtmosphere:function(){return atmosphere;}});
  }
  root.MazeRpgVisuals=Object.freeze({create:create});
}(globalThis));
