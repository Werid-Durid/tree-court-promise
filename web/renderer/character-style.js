import * as THREE from 'three';
import config from '../../blender/character_style.json';
import approved from '../../blender/materials/approved_npr.json';

export function materialClass(name){
 const n=name.replace(/\.\d+$/,'');
 if(n==='颜')return 'face';
 if(n.includes('肌')||n==='指甲')return 'skin';
 if(/^(白目|目|目光|齿)$/.test(n))return 'eye';
 if(n.includes('髪'))return 'hair';
 if(/金属|宝石|链|肩甲/.test(n))return 'metal';
 return 'cloth';
}

// 角色独立卡通明暗，避免教室强暖光把原皮肤图集染灰、洗白。
// 不改 Alpha、正反面或面片，保留上一次完整性修复。
export function styleCharacter(root,id,renderer){
 const seen=new Set(),caps=renderer?.capabilities.getMaxAnisotropy()||4;
 root.traverse(o=>{
  if(!o.isMesh)return;
  o.frustumCulled=false;
  for(const mat of(Array.isArray(o.material)?o.material:[o.material])){
   if(!mat||seen.has(mat))continue;seen.add(mat);
   if(mat.transparent)mat.depthWrite=false;
   if(mat.opacity<=.001)continue;
   const cls=materialClass(mat.name),p=config.classes[cls];
   const tint=(cls==='face'||cls==='skin')?config.characters[id].skin_tint:[1,1,1];
   mat.roughness=p.roughness;mat.metalness=0;mat.toneMapped=false;
   if(mat.map){mat.map.anisotropy=Math.min(8,caps);mat.map.colorSpace=THREE.SRGBColorSpace;mat.map.needsUpdate=true;}
   // 图集负责腮红、唇色和虹膜；只有很轻的暖色轮廓，避免塑料高光。
   mat.onBeforeCompile=shader=>{
    shader.uniforms.tcShadow={value:new THREE.Vector3(...p.shadow)};
    shader.uniforms.tcLight={value:new THREE.Vector3(...p.light)};
    shader.uniforms.tcTint={value:new THREE.Vector3(...tint)};
    shader.fragmentShader='uniform vec3 tcShadow;\nuniform vec3 tcLight;\nuniform vec3 tcTint;\n'+shader.fragmentShader;
    // 脸部与皮肤保留原图集血色，使用确认的三阶；边缘光仅加在衣料。
    const cloth=cls==='cloth'&&new RegExp(approved.cloth_name_pattern).test(mat.name);
    const npr=cls==='face'||cls==='skin'||cloth||cls==='hair';
    const rimCls=(approved.rim_classes||['cloth']).includes(cls);
    const rimMul=cls==='hair'?1.5:(cls==='face'||cls==='skin')?0.55:1.0;
    const rimPow=cls==='hair'?2.2:4.0;
    const rimLow=0.28,rimHigh=0.72;
    const warm=(cls==='face'||cls==='skin')?`vec3(1.05,0.94,0.86)`:`vec3(1.0)`;
    // 脸是平面，三阶明暗在脸上不显；用 UV 上缘加一层刘海投影，接近卡渲的硬脸影。
    const faceShadow=cls==='face'?`float tcBang=smoothstep(0.74,0.93,vMapUv.y);tcShade*=mix(1.0,0.58,tcBang);`:'';
    const vec=v=>`vec3(${v.map(x=>Number(x).toFixed(5)).join(',')})`;
    shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',`
     vec3 tcN=normalize(inverseTransformDirection(normal,viewMatrix));
     float tcBand=smoothstep(${p.low.toFixed(3)},${p.high.toFixed(3)},dot(tcN,normalize(vec3(-0.3,0.65,0.7))));
     vec3 tcShade=mix(tcShadow,tcLight,tcBand);
     ${npr?`float tcLightLevel=max(0.0,dot(tcN,normalize(vec3(-0.3,0.65,0.7))));
     tcShade=tcLightLevel<${approved.thresholds[0]}?${vec(approved.colors[0])}:(tcLightLevel<${approved.thresholds[1]}?${vec(approved.colors[1])}:${vec(approved.colors[2])});`:''}
     ${faceShadow}
     float tcFacing=clamp(dot(normal,normalize(vViewPosition)),0.0,1.0);
     float tcF0=pow((${approved.rim_ior}-1.0)/(${approved.rim_ior}+1.0),2.0);
     float tcFresnel=tcF0+(1.0-tcF0)*pow(1.0-tcFacing,${rimPow.toFixed(2)});
     outgoingLight=diffuseColor.rgb*${npr?'vec3(1.0)':'tcTint'}*tcShade*${warm}${rimCls?`+${vec(approved.rim_color)}*${rimMul.toFixed(2)}*smoothstep(${rimLow},${rimHigh},tcFresnel)`:''};
     #include <opaque_fragment>`);
   };
   mat.customProgramCacheKey=()=>`${approved.version}-${id}-${cls}`;
   mat.needsUpdate=true;
  }
 });
}
