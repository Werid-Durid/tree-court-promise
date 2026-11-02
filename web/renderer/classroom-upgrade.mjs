export const ROOM_SCALE=.55;
export const BOARD_WIDTH=5.2*.72;
export const BOARD_HEIGHT=2.1*.72;
export const BOARD_X=.65;
export const BOARD_Y=2.35;
const DOOR_SHIFT=-.315/ROOM_SCALE;
const DOOR_HEIGHT_SCALE=1.55;
const LECTERN_FORWARD=.35;
export const FRONT_X=.35;
export const BOARD_Z=-6.054*ROOM_SCALE;
export function characterPosition(id,p){return ({anaxa:[FRONT_X,.18,-3.13+LECTERN_FORWARD],hyacine:[2.65,.18,-2.65],castor:[FRONT_X-.85,0,-.68],phainon:[FRONT_X+.85,0,-.68]})[id]||compactPoint(p); }
export function compactPoint(p){return [p[0]*ROOM_SCALE,p[1],p[2]*ROOM_SCALE];}
export function compactLayout(l){l.player_start=compactPoint(l.player_start);l.bounds=l.bounds.map((v,i)=>i<2?v*ROOM_SCALE*.9:-6.4*ROOM_SCALE+(v+6.4)*ROOM_SCALE*.94);for(const c of [...l.colliders,...(l.walkable_surfaces||[])]){c.center=compactPoint(c.center);c.center[0]*=.9;c.center[2]=-6.4*ROOM_SCALE+(c.center[2]+6.4*ROOM_SCALE)*.94;c.size=[c.size[0]*ROOM_SCALE*.9,c.size[1],c.size[2]*ROOM_SCALE*.94];}for(const s of l.seats||[])for(const key of ['desk_center','seat_center'])if(s[key])s[key]=compactPoint(s[key]);}
export function hingedDoor(T,room){
 const parts=['Door_Panel','Door_Window','Door_Handle'].map(n=>room.getObjectByName(n)).filter(Boolean),panel=parts[0];if(!panel)return null;
 room.updateMatrixWorld(true);const box=new T.Box3().setFromObject(panel),pivot=new T.Group();pivot.position.copy(room.worldToLocal(new T.Vector3(box.min.x,box.min.y, (box.min.z+box.max.z)/2)));room.add(pivot);for(const p of parts)pivot.attach(p);let open=false;
 return {pivot,parts,get open(){return open;},toggle(){open=!open;},update(dt){pivot.rotation.y+=( (open?-Math.PI*.53:0)-pivot.rotation.y)*(1-Math.exp(-7*dt));}};
}
// Subtract a box from triangles, retaining interpolated UVs/normals and material groups.
export function cutOpening(T,mesh,box){
 mesh.updateWorldMatrix(true,false);const original=mesh.geometry,g=original.index?original.toNonIndexed():original.clone(),pos=g.attributes.position;const out={};for(const k of Object.keys(g.attributes))out[k]=[];const inverse=mesh.matrixWorld.clone().invert();
 const planes=[[0,box.min.x,1],[0,box.max.x,-1],[1,box.min.y,1],[1,box.max.y,-1],[2,box.min.z,1],[2,box.max.z,-1]];
 const mix=(a,b,t)=>({world:a.world.clone().lerp(b.world,t),attrs:Object.fromEntries(Object.keys(a.attrs).map(k=>[k,a.attrs[k].map((v,i)=>v+(b.attrs[k][i]-v)*t)]))});
 function clip(poly,axis,value,sign,inside){const result=[];for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length],da=(a.world.getComponent(axis)-value)*sign,db=(b.world.getComponent(axis)-value)*sign,ia=inside?da>=0:da<=0,ib=inside?db>=0:db<=0;if(ia)result.push(a);if(ia!==ib)result.push(mix(a,b,da/(da-db)));}return result;}
 const groups=g.groups.length?g.groups:[{start:0,count:pos.count,materialIndex:0}];const result=new T.BufferGeometry();
 for(const group of groups){const start=out.position.length/3;for(let i=group.start;i<group.start+group.count;i+=3){let poly=[0,1,2].map(j=>{const attrs={};for(const [k,a]of Object.entries(g.attributes))attrs[k]=Array.from({length:a.itemSize},(_,n)=>a.array[(i+j)*a.itemSize+n]);return {world:new T.Vector3(...attrs.position).applyMatrix4(mesh.matrixWorld),attrs};});const fragments=[];
 for(const [axis,value,sign]of planes){if(!poly.length)break;const outside=clip(poly,axis,value,sign,false);if(outside.length>=3)fragments.push(outside);poly=clip(poly,axis,value,sign,true);}
 for(const f of fragments)for(let j=1;j<f.length-1;j++)for(const v of [f[0],f[j],f[j+1]])for(const k of Object.keys(out)){const vals=k==='position'?v.world.clone().applyMatrix4(inverse).toArray():v.attrs[k];out[k].push(...vals);}
 }result.addGroup(start,out.position.length/3-start,group.materialIndex);}
 for(const [k,a]of Object.entries(g.attributes))result.setAttribute(k,new T.Float32BufferAttribute(out[k],a.itemSize,a.normalized));result.computeBoundingSphere();mesh.geometry=result;original.dispose();g.dispose();
}
export function upgradeRoom(T,room,layout){
 const doorWidth=1.25/(1.15*ROOM_SCALE),doorCenter=-4.7;
 for(const o of room.children){
  if(/^Door_/.test(o.name)){o.position.x=doorCenter+(o.position.x-doorCenter)*doorWidth+DOOR_SHIFT;o.scale.x*=doorWidth;o.position.y*=DOOR_HEIGHT_SCALE;o.scale.y*=DOOR_HEIGHT_SCALE;}
  if(/^Corridor_|^Sky_Backdrop$/.test(o.name)){o.position.x+=DOOR_SHIFT;if(o.name!=='Corridor_Floor'){o.position.y*=DOOR_HEIGHT_SCALE;o.scale.y*=DOOR_HEIGHT_SCALE;}}
  // Keep the corridor's front edges behind the classroom wall so they do not form a second frame.
  if(/^Corridor_(Ceil|WallL|WallR)$/.test(o.name)){o.position.z=(-10.46-6.5)/2;o.scale.z*=3.96/4.6;}
 }
 // A short fixed transom above the tall glazed door leaf.
 const panel=room.getObjectByName('Door_Panel');
 if(panel){const cx=doorCenter+DOOR_SHIFT,w=1.25/ROOM_SCALE,gw=1.03/ROOM_SCALE;
  const shape=new T.Shape();shape.moveTo(-w/2,0);shape.lineTo(w/2,0);shape.lineTo(w/2,2.92);shape.lineTo(-w/2,2.92);shape.closePath();
  const hole=new T.Path();hole.moveTo(-gw/2,.25);hole.lineTo(-gw/2,2.68);hole.lineTo(gw/2,2.68);hole.lineTo(gw/2,.25);hole.closePath();shape.holes.push(hole);
  panel.geometry.dispose();panel.geometry=new T.ExtrudeGeometry(shape,{depth:.06,bevelEnabled:false});panel.geometry.translate(0,0,-.03);panel.position.set(cx,0,-5.84);panel.scale.set(1,1,1);panel.rotation.set(0,0,0);
  const glass=room.getObjectByName('Door_Window');if(glass){glass.geometry.dispose();glass.geometry=new T.BoxGeometry(gw,2.43,.018);glass.scale.set(1,1,1);glass.rotation.set(0,0,0);glass.position.set(cx,1.465,-5.84);}
  const handle=room.getObjectByName('Door_Handle');if(handle)handle.position.set(cx+.56/ROOM_SCALE,1.35,-5.74);
  const transom=new T.Group();transom.name='Door_Transom';room.add(transom);
  function bar(name,size,pos,mat=panel.material){const m=new T.Mesh(new T.BoxGeometry(...size),mat);m.name=name;m.position.set(...pos);transom.add(m);}
  bar('Door_TransomRail',[w,.09,.08],[cx,2.965,-5.84]);
  bar('Door_TransomTop',[w,.09,.08],[cx,3.365,-5.84]);
  for(const side of [-1,1])bar('Door_TransomSide',[.08/ROOM_SCALE,.31,.08],[cx+side*.585/ROOM_SCALE,3.165,-5.84]);
  bar('Door_TransomGlass',[(1.09)/ROOM_SCALE,.31,.02],[cx,3.165,-5.84],new T.MeshBasicMaterial({color:0xc2e9f6}));
 }
 const originalBoard=new T.Box3(new T.Vector3(-3.65,.85,-6.38),new T.Vector3(3.65,3.9,-6.0));room.updateMatrixWorld(true);
 room.traverse(o=>{if(o.isMesh&&/^TC_Cine_(wood_light|wood_dark|sage_dark|gold|paper)$/.test(o.name)&&new T.Box3().setFromObject(o).intersectsBox(originalBoard))cutOpening(T,o,originalBoard);});
 const openingLeft=doorCenter+(-5.29-doorCenter)*doorWidth+DOOR_SHIFT,openingRight=doorCenter+(-4.11-doorCenter)*doorWidth+DOOR_SHIFT;
 const opening=new T.Box3(new T.Vector3(openingLeft,-.1,-6.65),new T.Vector3(openingRight,2.23*DOOR_HEIGHT_SCALE,-5.96));
 const railMaterial=room.getObjectByName('TC_Cine_gold')?.material;
 if(railMaterial){const rail=new T.Mesh(new T.BoxGeometry(7.3,.07,.06),railMaterial);rail.name='Wall_Dado_Repair';rail.position.set(0,1.32,-6.27);room.add(rail);}
 // Remove the plant beside the door without touching the window or other plants.
 const doorLeaves=new T.Box3(new T.Vector3(-7.6,-.01,-6.2),new T.Vector3(-6.1,1.6,-4.7));
 const doorPot=new T.Box3(new T.Vector3(-7.2,-.01,-5.8),new T.Vector3(-6.6,.5,-5.2));
 room.traverse(o=>{const box=o.name==='TC_Cine_leaf'?doorLeaves:o.name==='TC_Cine_paper'?doorPot:null;if(o.isMesh&&box&&new T.Box3().setFromObject(o).intersectsBox(box))cutOpening(T,o,box);});
 layout.colliders=layout.colliders.filter(c=>!(c.name==='Plant_Pot'&&c.center[0]<-6&&c.center[2]<-4));
 // Remove notebooks and pencils left at the deleted desks' former positions.
 const looseProps=new T.Box3(new T.Vector3(-4.2,.62,-.1),new T.Vector3(4.2,.72,2.2));
 room.traverse(o=>{if(o.isMesh&&/^TC_Cine_(paper|gold)$/.test(o.name)&&new T.Box3().setFromObject(o).intersectsBox(looseProps))cutOpening(T,o,looseProps);});
 // Remove the old merged platform above floor level, plus its separate pedestal.
 const oldStage=new T.Box3(new T.Vector3(-4.4,.005,-6.45),new T.Vector3(4.4,.22,-2.8));
 room.traverse(o=>{if(o.isMesh&&/^TC_Cine_/.test(o.name)&&new T.Box3().setFromObject(o).intersectsBox(oldStage))cutOpening(T,o,oldStage);});
 for(const o of [...room.children])if(/^(Podium_|Vent_|ChalkBox|CurvedBase)/.test(o.name)){o.removeFromParent();o.geometry?.dispose();}
 // Keep imported desk and stool assemblies at their original physical size.
 const desks=[];room.traverse(o=>{if(o.isMesh&&/^NEW_Desk/.test(o.name))desks.push(o);});
 for(const o of desks){const g=o.geometry.clone().applyMatrix4(o.matrixWorld),box=new T.Box3().setFromBufferAttribute(g.attributes.position),center=box.getCenter(new T.Vector3());g.translate(-center.x,0,-center.z);g.scale(1/ROOM_SCALE,1,1/ROOM_SCALE);const n=new T.Mesh(g,o.material);n.name=o.name;const column=/_(1|11)$/.test(o.name)?1:-1,row=/_(10|11)$/.test(o.name)?1:0;n.position.set((FRONT_X+column*(row?1.65:.85))/ROOM_SCALE,0,(-1.1+row*1.5)/ROOM_SCALE);o.removeFromParent();room.add(n);o.geometry.dispose();}
 // Tighten only the room shell; furniture and door retain their physical dimensions.
 room.updateMatrixWorld(true);room.traverse(o=>{if(o.isMesh&&/^TC_Cine_/.test(o.name)){const g=o.geometry.clone().applyMatrix4(o.matrixWorld),p=g.attributes.position;for(let i=0;i<p.count;i++){p.setX(i,p.getX(i)*.9);p.setZ(i,-6.4+(p.getZ(i)+6.4)*.94);}g.computeVertexNormals();g.computeBoundingSphere();o.geometry.dispose();o.geometry=g;o.position.set(0,0,0);o.quaternion.identity();o.scale.set(1,1,1);o.updateMatrix();}});
 room.updateMatrixWorld(true);room.traverse(o=>{if(o.isMesh&&/^TC_Cine_/.test(o.name)){const b=new T.Box3().setFromObject(o);if(b.intersectsBox(opening))cutOpening(T,o,opening);}});
 const door=hingedDoor(T,room);room.scale.set(ROOM_SCALE,1,ROOM_SCALE);compactLayout(layout);referenceFront(T,room,layout);
 // Old collision data predates the current four desks. Rebuild from the live meshes.
 layout.colliders=layout.colliders.filter(c=>!/Desk|Stool|Chair|Podium|Back_Wall/.test(c.name));room.updateMatrixWorld(true);room.traverse(o=>{if(o.isMesh&&/^(NEW_Desk|Podium_Body)/.test(o.name)){const b=new T.Box3().setFromObject(o),p=b.getCenter(new T.Vector3()),s=b.getSize(new T.Vector3());layout.colliders.push({name:o.name,center:p.toArray(),size:s.toArray()});}});
 // Keep the door approach clear while retaining the wall beside the opening.
 const z=-6.4*ROOM_SCALE;for(const [a,b]of [[-7.75*.9,openingLeft],[openingRight,7.75*.9]])layout.colliders.push({name:'DoorWall',center:[(a+b)/2*ROOM_SCALE,2.25,z],size:[(b-a)*ROOM_SCALE,4.5,.2]});
 return door;
}
function referenceFront(T,room,layout){
 const group=new T.Group();group.name='Reference_Front';group.position.x=FRONT_X/ROOM_SCALE;group.scale.set(1/ROOM_SCALE,1,1/ROOM_SCALE);room.add(group);
 const wood=new T.MeshStandardMaterial({color:0xaf6b2c,roughness:.75}),edge=new T.MeshStandardMaterial({color:0x754824,roughness:.78}),body=new T.MeshStandardMaterial({color:0xb99d95,roughness:.8}),top=new T.MeshStandardMaterial({color:0xd4c5ae,roughness:.75}),green=new T.MeshStandardMaterial({color:0x254e3b,roughness:1});
 function box(name,size,pos,mat,parent=group){const o=new T.Mesh(new T.BoxGeometry(...size),mat);o.name=name;o.position.set(...pos);parent.add(o);return o;}
 function rounded(name,w,d,h,z,r,mat){const shape=new T.Shape(),x=-w/2,y=-d/2;shape.moveTo(x+r,y);shape.lineTo(x+w-r,y);shape.quadraticCurveTo(x+w,y,x+w,y+r);shape.lineTo(x+w,y+d-r);shape.quadraticCurveTo(x+w,y+d,x+w-r,y+d);shape.lineTo(x+r,y+d);shape.quadraticCurveTo(x,y+d,x,y+d-r);shape.lineTo(x,y+r);shape.quadraticCurveTo(x,y,x+r,y);const g=new T.ExtrudeGeometry(shape,{depth:h,bevelEnabled:false,curveSegments:10});g.rotateX(-Math.PI/2);const o=new T.Mesh(g,mat);o.name=name;o.position.z=z;group.add(o);return o;}
 rounded('Reference_Rounded_Stage',5.5,1.6,.18,-2.65,.3,wood);

 const lectern=new T.Group();lectern.name='Reference_Lectern';lectern.position.z=LECTERN_FORWARD;group.add(lectern);
 box('Reference_Lectern_Body',[2.55,.72,.56],[0,.61,-2.65],body,lectern);
 box('Reference_Lectern_Top',[2.78,.09,.7],[0,1.015,-2.65],top,lectern);
 box('Reference_Lectern_Rim',[2.8,.035,.72],[0,1.073,-2.65],edge,lectern);
 box('Reference_Lectern_Base',[2.62,.065,.6],[0,.215,-2.65],edge,lectern);
 for(let i=0;i<4;i++)box('Reference_Lectern_Vent',[.32,.018,.009],[-.97,.78-i*.065,-2.365],edge,lectern);
 box('Reference_Chalk_Box',[.28,.14,.18],[-.8,1.16,-2.6],wood,lectern);
 const frame=new T.Group();frame.name='Reference_Board_Frame';frame.position.set(BOARD_X-FRONT_X,BOARD_Y-2.25,0);group.add(frame);
 box('Reference_Board_Backing',[BOARD_WIDTH+.05,BOARD_HEIGHT+.04,.09],[0,2.25,BOARD_Z-.065],green,frame);
 for(const x of [-1,1]){box('Reference_Board_OuterSide',[.14,BOARD_HEIGHT+.32,.14],[x*(BOARD_WIDTH/2+.12),2.25,BOARD_Z],edge,frame);box('Reference_Board_InnerSide',[.09,BOARD_HEIGHT+.13,.16],[x*(BOARD_WIDTH/2+.02),2.25,BOARD_Z+.015],wood,frame);}
 for(const side of [-1,1]){box('Reference_Board_OuterRail',[BOARD_WIDTH+.38,.14,.14],[0,2.25+side*(BOARD_HEIGHT/2+.09),BOARD_Z],edge,frame);box('Reference_Board_InnerRail',[BOARD_WIDTH+.12,.08,.16],[0,2.25+side*(BOARD_HEIGHT/2+.02),BOARD_Z+.015],wood,frame);}
 box('Reference_Chalk_Ledge',[BOARD_WIDTH+.32,.075,.24],[0,2.25-BOARD_HEIGHT/2-.095,BOARD_Z+.08],wood,frame);
 layout.player_start=[FRONT_X,1.65,2.55];layout.walkable_surfaces=[{center:[FRONT_X,.09,-2.65],size:[5.5,.18,1.6]}];layout.colliders.push({name:'Reference_Lectern',center:[FRONT_X,.65,-2.65+LECTERN_FORWARD],size:[2.8,.95,.72]});
}
export function skyTexture(T){const c=document.createElement('canvas');c.width=1024;c.height=512;const x=c.getContext('2d'),g=x.createLinearGradient(0,0,0,512);g.addColorStop(0,'#659bd4');g.addColorStop(.65,'#b9dcec');g.addColorStop(1,'#fce9cb');x.fillStyle=g;x.fillRect(0,0,1024,512);x.fillStyle='rgba(255,255,255,.8)';for(const [a,b,s]of [[160,140,1],[640,210,1.4],[900,95,.8]]){for(let i=0;i<6;i++){x.beginPath();x.ellipse(a+(i-2)*27*s,b+Math.sin(i*2)*12*s,50*s,19*s,0,0,Math.PI*2);x.fill();}}const t=new T.CanvasTexture(c);t.colorSpace=T.SRGBColorSpace;return t;}
export function addExterior(T,room){const sky=skyTexture(T);room.traverse(o=>{if(o.isMesh&&/Sky_Backdrop|TC_Cine_sky_warm|^Door_Window$|^Door_TransomGlass$/.test(o.name)){o.material=new T.MeshBasicMaterial({map:sky,side:T.DoubleSide});}});const mat=new T.MeshStandardMaterial({color:0xe1cbb0,roughness:.9});for(let i=0;i<7;i++){const seam=new T.Mesh(new T.BoxGeometry(2.48,.004,.018),mat);seam.position.set(-4.7+DOOR_SHIFT,.063,-6.1-i*.65);room.add(seam);}const light=new T.PointLight(0xffedcf,10,7,2);light.position.set(-4.7+DOOR_SHIFT,2.3,-7.5);room.add(light);}
