import fs from "fs";
const files=["app.config.ts","app.config.js","app.json"]; const f=files.find(p=>fs.existsSync(p));
if(!f){ console.error("❌ No app config found."); process.exit(1); }
let t=fs.readFileSync(f,"utf8"); const isJson=f.endsWith(".json");
const bumpPatch=v=>{const a=(v||"1.0.0").split(".").map(n=>parseInt(n,10)); while(a.length<3)a.push(0); a[2]=(isFinite(a[2])?a[2]:0)+1; return `${a[0]}.${a[1]}.${a[2]}`;};
const bumpNum=(n,f=1)=>{const x=parseInt(String(n||"").replace(/[^0-9]/g,""),10); return isFinite(x)?x+1:f;};
let ch=[];
if(isJson){
  t=t.replace(/"version"\s*:\s*"([^"]+)"/,(m,v)=>{const nv=bumpPatch(v); ch.push(`version: ${v} -> ${nv}`); return `"version":"${nv}"`;});
  t=t.replace(/"buildNumber"\s*:\s*"([^"]+)"/,(m,v)=>{const nv=String(bumpNum(v,1)); ch.push(`ios.buildNumber: ${v} -> ${nv}`); return `"buildNumber":"${nv}"`;});
  t=t.replace(/"versionCode"\s*:\s*([0-9]+)/,(m,v)=>{const nv=bumpNum(v,1); ch.push(`android.versionCode: ${v} -> ${nv}`); return `"versionCode":${nv}`;});
}else{
  t=t.replace(/version\s*:\s*["'](\d+\.\d+\.\d+)["']/,(m,v)=>{const nv=bumpPatch(v); ch.push(`version: ${v} -> ${nv}`); return `version: "${nv}"`;});
  t=t.replace(/buildNumber\s*:\s*["']([^"']+)["']/,(m,v)=>{const nv=String(bumpNum(v,1)); ch.push(`ios.buildNumber: ${v} -> ${nv}`); return `buildNumber: "${nv}"`;});
  t=t.replace(/versionCode\s*:\s*([0-9]+)/,(m,v)=>{const nv=bumpNum(v,1); ch.push(`android.versionCode: ${v} -> ${nv}`); return `versionCode: ${nv}`;});
}
fs.writeFileSync(f,t,"utf8"); console.log("Updated:",f); for(const c of ch) console.log(" •",c);
