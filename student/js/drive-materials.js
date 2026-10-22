/* Original procedural materials. Built once on first drive; no downloads. */
(function(root){
  'use strict';
  function create(){
    var seed=94721;
    function random(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;}
    function canvas(size){var c=document.createElement('canvas');c.width=c.height=size;return c;}
    function wrap(value,size){return ((value%size)+size)%size;}
    // Periodic, multi-scale fields avoid a visible border when the atlas wraps.
    function field(size){var a=new Float32Array(size*size);for(var i=0;i<a.length;i++)a[i]=random()*2-1;return a;}
    function smooth(a,size,u,v){
      var x=Math.floor(u),y=Math.floor(v),fx=u-x,fy=v-y;
      fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy);
      var x0=wrap(x,size),x1=(x0+1)%size,y0=wrap(y,size)*size,y1=((wrap(y,size)+1)%size)*size;
      return (a[y0+x0]*(1-fx)+a[y0+x1]*fx)*(1-fy)+(a[y1+x0]*(1-fx)+a[y1+x1]*fx)*fy;
    }
    var coarse=field(8),medium=field(32),floor=[],walls=[[],[]];
    var tone=new Float32Array(256*256);
    for(var y=0;y<256;y++)for(var x=0;x<256;x++){
      // Small aggregate over broad, low-contrast trowel/epoxy variation.
      tone[y*256+x]=smooth(coarse,8,x/32,y/32)*10+smooth(medium,32,x/8,y/8)*4+(random()-.5)*7;
    }
    floor.push(tone);
    for(var size=128;size>=1;size/=2){
      var previous=floor[floor.length-1],next=new Float32Array(size*size),stride=size*2;
      for(y=0;y<size;y++)for(x=0;x<size;x++){
        var at=y*2*stride+x*2;
        next[y*size+x]=(previous[at]+previous[at+1]+previous[at+stride]+previous[at+stride+1])*.25;
      }
      floor.push(next);
    }
    var surface=canvas(128),g=surface.getContext('2d'),image=g.createImageData(128,128);
    var brushed=field(128),broad=field(8);
    for(y=0;y<128;y++)for(x=0;x<128;x++){
      var u=x/128,v=y/128;
      var panel=smooth(broad,8,x/16,y/16)*3.5;
      var grain=brushed[y]*1.4+(random()-.5)*2.3;
      // Recessed gasket, bevel and continuous brushed face. No drawn openings.
      var row=y%64;
      var joint=x<2||row<1?-25:x<4||row<2?7:x>125||row>62?-8:0;
      var contact=-20*Math.pow(Math.max(0,(v-.85)/.15),2);
      var wear=(y>106&&x>12&&x<116)?Math.sin(x*.3+y*.1)*1.4:0;
      var value=panel+grain+joint+contact+wear+Math.cos(u*Math.PI)*2;
      // Tiny flush fasteners stay part of the material, never collision geometry.
      if((x===8||x===119)&&(row===7||row===56))value-=25;
      var offset=(y*128+x)*4;
      image.data[offset]=167+value;image.data[offset+1]=174+value;image.data[offset+2]=175+value;image.data[offset+3]=255;
    }
    g.putImageData(image,0,0);
    // Bake face lighting and mipmaps once; retain only the small RGBA arrays.
    for(var side=0;side<2;side++){
      var base=canvas(128),bg=base.getContext('2d');bg.drawImage(surface,0,0);
      if(side){bg.fillStyle='rgba(26,42,51,.20)';bg.fillRect(0,0,128,128);}
      walls[side].push(base);
      for(size=64;size>=1;size/=2){
        var mip=canvas(size);mip.getContext('2d').drawImage(walls[side][walls[side].length-1],0,0,size,size);walls[side].push(mip);
      }
    }
    walls=walls.map(function(row){return row.map(function(c){return {size:c.width,pixels:c.getContext('2d').getImageData(0,0,c.width,c.height).data};});});
    function bilinear(level,u,v){
      var size=256>>level,a=floor[level],scale=1/(1<<level),x=u*scale,y=v*scale;
      var rawX=Math.floor(x),rawY=Math.floor(y),mask=size-1;
      var ix=rawX&mask,iy=rawY&mask,fx=x-rawX,fy=y-rawY,nx=(ix+1)&mask,ny=(iy+1)&mask;
      return (a[iy*size+ix]*(1-fx)+a[iy*size+nx]*fx)*(1-fy)+(a[ny*size+ix]*(1-fx)+a[ny*size+nx]*fx)*fy;
    }
    function sampleFloor(x,y,level,blend){
      var a=bilinear(level,x*2,y*2);
      return blend>0?a+(bilinear(Math.min(8,level+1),x*2,y*2)-a)*blend:a;
    }
    return Object.freeze({floor:floor,walls:walls,sampleFloor:sampleFloor,
      bytes:floor.reduce(function(n,a){return n+a.byteLength;},0)+walls.reduce(function(n,row){return n+row.reduce(function(m,c){return m+c.pixels.byteLength;},0);},0)});
  }
  root.MazeDriveMaterials=Object.freeze({create:create,release:'5b1-1'});
}(globalThis));
