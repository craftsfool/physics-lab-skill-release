#!/usr/bin/env node
// Device registration and signed reads. Reference bodies are output only to task context.
import {generateKeyPairSync,createPrivateKey,createPublicKey,createHash,randomBytes,sign} from 'node:crypto';
import {readFile,mkdir,open,lstat,rename,unlink} from 'node:fs/promises';
import {homedir} from 'node:os';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export const defaultConfig=()=>process.env.PHYSICS_LAB_DEVICE_CONFIG||join(
  process.platform==='win32'?(process.env.APPDATA||join(homedir(),'AppData/Roaming')):(process.env.XDG_CONFIG_HOME||join(homedir(),'.config')),
  'physics-lab-report','device.json');
const hash=value=>createHash('sha256').update(value).digest('hex');
export function endpoint(value) {
  const url=new URL(value);
  if(url.protocol!=='https:'||url.pathname!=='/api/reference'||url.username||url.password||url.search||url.hash)
    throw new Error('Use an HTTPS /api/reference endpoint without credentials or query.');
  return url;
}
export function signedHeaders(config,path,body,now=Date.now()) {
  const time=String(now),nonce=randomBytes(32).toString('base64url');
  const message=Buffer.from(JSON.stringify(['physics-lab-device-v1','POST',path,config.public_key,time,nonce,hash(body)]));
  return {'Content-Type':'application/json','Accept':'application/json',
    'x-physics-device-time':time,'x-physics-device-nonce':nonce,
    'x-physics-device-signature':sign(null,message,createPrivateKey({key:Buffer.from(config.private_key,'base64url'),type:'pkcs8',format:'der'})).toString('base64url')};
}
export async function loadConfig(path) {
  const info=await lstat(path);
  if(!info.isFile()||info.isSymbolicLink())throw new Error('Device configuration must be a regular private file.');
  if(process.platform!=='win32'&&(info.mode&0o077))throw new Error('Device configuration must have permission 0600.');
  const config=JSON.parse(await readFile(path,'utf8'));
  const privateKey=createPrivateKey({key:Buffer.from(config.private_key,'base64url'),type:'pkcs8',format:'der'});
  const publicKey=createPublicKey(privateKey);
  if(config.schema_version!==1||publicKey.asymmetricKeyType!=='ed25519'||
    publicKey.export({type:'spki',format:'der'}).toString('base64url')!==config.public_key)throw new Error('Invalid device credentials.');
  endpoint(config.endpoint);
  return config;
}
async function writeConfig(path,config,exclusive=false) {
  await mkdir(dirname(path),{recursive:true,mode:0o700});
  if(exclusive){const stream=await open(path,'wx',0o600);try{await stream.writeFile(JSON.stringify(config)+'\n');}finally{await stream.close();}return;}
  const temporary=path+'.'+randomBytes(8).toString('hex')+'.tmp';
  try {
    const stream=await open(temporary,'wx',0o600);
    try {await stream.writeFile(JSON.stringify(config)+'\n');}finally{await stream.close();}
    if((await lstat(path)).isSymbolicLink())throw new Error('Refusing a symbolic device file.');
    await rename(temporary,path);
  }finally{await unlink(temporary).catch(()=>{});}
}
async function request(url,headers,body,fetcher=fetch,maxBytes=16000) {
  if(process.env.PHYSICS_LAB_DEPLOYMENT_BYPASS)headers['x-vercel-protection-bypass']=process.env.PHYSICS_LAB_DEPLOYMENT_BYPASS;
  const response=await fetcher(url,{method:'POST',headers,body,redirect:'error',signal:AbortSignal.timeout(20000)});
  if(!response.ok)throw new Error('Reference service returned HTTP '+response.status+'.');
  if(response.headers.get('content-type')?.split(';')[0]!=='application/json')throw new Error('Expected JSON response.');
  const reader=response.body.getReader();let size=0;const chunks=[];
  for(;;){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>maxBytes){await reader.cancel();throw new Error('Response too large.');}chunks.push(value);}
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}
export async function register(path,url,fetcher=fetch) {
  endpoint(url);let config;
  try {config=await loadConfig(path);}catch(error){
    if(error.code!=='ENOENT')throw error;
    const keys=generateKeyPairSync('ed25519');
    config={schema_version:1,endpoint:url,public_key:keys.publicKey.export({type:'spki',format:'der'}).toString('base64url'),
      private_key:keys.privateKey.export({type:'pkcs8',format:'der'}).toString('base64url')};
    await writeConfig(path,config,true);
  }
  if(config.endpoint!==url)throw new Error('Existing device belongs to another endpoint; do not overwrite it.');
  const target=new URL('/api/device/register',url),body=JSON.stringify({public_key:config.public_key});
  const data=await request(target,signedHeaders(config,target.pathname,body),body,fetcher);
  if(data.schema_version!==1||data.device_bound!==true||data.endpoint!==url||!/^plr_[A-Za-z0-9_-]{43}$/.test(data.token)||
    !Number.isSafeInteger(data.expires_at)||data.expires_at<=Date.now()||!/^device-[a-f0-9]{40}$/.test(data.device_id))throw new Error('Invalid registration response.');
  // Store only private authentication material, never reference-module responses.
  config={...config,token:data.token,expires_at:data.expires_at,device_id:data.device_id};
  await writeConfig(path,config);
  return {registered:true,expires_at:new Date(data.expires_at).toISOString(),credential_file:resolve(path)};
}
export async function fetchModule(path,query,fetcher=fetch) {
  if(!/^[a-z][a-z0-9-]{0,47}$/.test(query.experiment)||!['textbook','senior'].includes(query.library)||
    !['purpose','theory','instruments','procedure','data_processing','uncertainty','questions','discussion'].includes(query.topic))throw new Error('Invalid reference query.');
  const config=await loadConfig(path);
  if(!/^plr_[A-Za-z0-9_-]{43}$/.test(config.token||'')||config.expires_at<=Date.now())throw new Error('Device credential is missing or expired.');
  const url=endpoint(config.endpoint),body=JSON.stringify(query);
  const headers={...signedHeaders(config,url.pathname,body),Authorization:'Bearer '+config.token};
  const data=await request(url,headers,body,fetcher);
  const fields=['schema_version','experiment','library','topic','version','summary','key_points','formulas','figures','sources','retrieved_at'];
  if(data.schema_version!==1||Object.keys(data).sort().join()!==fields.sort().join()||
    data.experiment!==query.experiment||data.library!==query.library||data.topic!==query.topic)throw new Error('Reference schema mismatch.');
  return data;
}
export async function previewChapter(path,experiment,fetcher=fetch) {
  if(!/^[a-z][a-z0-9-]{0,47}$/.test(experiment))throw new Error('Invalid experiment.');
  const config=await loadConfig(path);
  if(!/^plr_[A-Za-z0-9_-]{43}$/.test(config.token||'')||config.expires_at<=Date.now())throw new Error('Device credential is missing or expired.');
  const url=new URL('/api/chapter',config.endpoint),body=JSON.stringify({experiment});
  const data=await request(url,{...signedHeaders(config,url.pathname,body),Authorization:'Bearer '+config.token},body,fetcher);
  if(data.schema_version!==1||!/^\/api\/chapter-preview\?ticket=[A-Za-z0-9_-]{43}$/.test(data.preview_path)||
    !Number.isSafeInteger(data.expires_at)||data.expires_at<=Date.now()||!Number.isSafeInteger(data.pages)||typeof data.title!=='string')throw new Error('Invalid chapter preview response.');
  return {preview_url:new URL(data.preview_path,config.endpoint).href,title:data.title,pages:data.pages,expires_at:data.expires_at};
}
export async function main(argv) {
  const action=argv.shift(),args={};
  while(argv.length){const flag=argv.shift();if(!flag.startsWith('--')||!argv.length||args[flag]!==undefined)throw new Error('Invalid arguments.');args[flag]=argv.shift();}
  if(Object.keys(args).some(k=>!['--config','--endpoint','--experiment','--library','--topic'].includes(k)))throw new Error('Unknown option.');
  const path=args['--config']||defaultConfig();
  if(action==='status'){
    try {const value=await loadConfig(path);return {configured:Boolean(value.token),expired:Boolean(value.expires_at<=Date.now()),expires_at:value.expires_at||null};}
    catch(error){if(error.code==='ENOENT')return {configured:false};throw error;}
  }
  if(action==='register')return register(path,args['--endpoint']||'https://physics-lab-reference-api.vercel.app/api/reference');
  if(action==='fetch')return fetchModule(path,{experiment:args['--experiment'],library:args['--library'],topic:args['--topic']});
  if(action==='preview')return previewChapter(path,args['--experiment']);
  throw new Error('Use status, register, fetch or preview.');
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  main(process.argv.slice(2)).then(value=>process.stdout.write(JSON.stringify(value)+'\n')).catch(error=>{
    // Do not print request/response bodies, private keys, or native error details.
    const controlled=/^(Use |Invalid |Expected |Response |Reference |Device |Existing |Unknown |Refusing )/;
    process.stderr.write((controlled.test(error.message)?error.message:'Device operation failed; check configuration and network.')+'\n');process.exitCode=1;
  });
}
