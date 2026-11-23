// Behavioral checks use an in-memory DOM, caches and network mocks; no real browser or remote writes.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const dir = path.resolve(__dirname, '../phonebook');
const config = JSON.parse(fs.readFileSync(path.join(__dirname, '../site-config.json'), 'utf8'));
const swCode = fs.readFileSync(path.join(__dirname, '../sw.js'), 'utf8');
const cachePrefix = swCode.match(/const CACHE_PREFIX = '([^']+)'/)[1];
const expectedCache = cachePrefix + swCode.match(/const CACHE = CACHE_PREFIX \+ '([^']+)'/)[1];
const appShell = JSON.parse(swCode.match(/const APP_SHELL = (\[[\s\S]*?\]);/)[1]);
const projectURL = relative => new URL(relative, config.base_url).href;
const app = fs.readFileSync(path.join(dir, 'app.js'), 'utf8');
const resourceFiles = fs.readdirSync(dir).filter(f => /^resources-\d+\.js$/.test(f)).sort();
const bundle = resourceFiles.map(f => fs.readFileSync(path.join(dir, f), 'utf8')).join('\n');
const results = [];
function record(name, run) { run(); results.push({name, passed:true}); }
class Element {
  constructor(id='') { this.id=id; this.innerHTML=''; this.textContent=''; this.value=''; this.disabled=false; this.hidden=false; this.listeners={}; this.dataset={}; }
  addEventListener(type, fn) { this.listeners[type]=fn; }
  focus() { this.focused=true; }
  querySelectorAll(selector) {
    if(selector!=='.tab') return [];
    return [...this.innerHTML.matchAll(/data-id="([^"]+)"/g)].map(m=>{const e=new Element();e.dataset.id=m[1];return e;});
  }
}
function load(protocol='file:', storageThrows=true, offlineCopy=false) {
  const ids = ['tabs','main','search','category','clearFilters','resultCount','printAll','totalResources','installApp','shareApp','installHelp','downloadHtml','offlineStatus','recoveryGuideLink'];
  const elements=Object.fromEntries(ids.map(id=>[id,new Element(id)]));
  const windowEvents={}, timers=[];
  let fetches=0, registrations=0, printed='';
  const context={
    console, URL, Blob, encodeURIComponent, setTimeout:fn=>{timers.push(fn);return timers.length;}, clearTimeout:()=>{},
    location:{protocol,hostname:'localhost'},
    localStorage:{getItem(){if(storageThrows) throw Error('Storage denied');return null;},setItem(){if(storageThrows) throw Error('Storage denied');}},
    document:{documentElement:{dataset:offlineCopy ? {offlineCopy:'true'} : {}},getElementById:id=>elements[id],querySelector:()=>null},
    navigator:{userAgent:'test'},
    fetch:()=>{fetches++;throw Error('No network permitted in file-mode boot test');}
  };
  context.window=context;
  context.innerWidth=1200;
  context.addEventListener=(event,fn)=>{windowEvents[event]=fn;};
  context.print=()=>{printed=elements.main.innerHTML;};
  context.scrollTo=()=>{};
  vm.createContext(context);
  vm.runInContext(bundle+'\n'+app,context);
  return {context,elements,windowEvents,timers,getFetches:()=>fetches,getPrinted:()=>printed};
}
const l=load();
record('All 58 entries boot in file: mode with localStorage throwing and no network',()=>{
  assert.equal(l.context.PHONEBOOK_RESOURCES.length,58);
  assert.match(l.elements.totalResources.textContent,/58 resources/);
  assert.match(l.elements.main.innerHTML,/START HERE/);
  assert.equal(l.getFetches(),0);
});
record('Zero results remove prior selected card and announce zero',()=>{
  l.elements.search.value='zz-no-such-program-821';
  l.elements.search.listeners.input();
  assert.match(l.elements.main.innerHTML,/No matching resources/);
  assert.doesNotMatch(l.elements.main.innerHTML,/<article/);
  assert.match(l.elements.resultCount.textContent,/0 of 58/);
  assert.equal(l.elements.clearFilters.disabled,false);
});
record('Clear filters restores all entries and focuses search',()=>{
  l.elements.clearFilters.listeners.click();
  assert.equal(l.elements.search.value,'');
  assert.equal(l.elements.category.value,'');
  assert.match(l.elements.resultCount.textContent,/58 of 58/);
  assert.equal(l.elements.search.focused,true);
});
record('Category selection cannot retain an unrelated previous card',()=>{
  l.elements.category.value='Food';
  l.elements.category.listeners.change();
  const matched=l.context.filtered();
  assert.ok(matched.length>0);
  assert.ok(matched.every(r=>r.category==='Food'));
  assert.ok(l.elements.main.innerHTML.includes(l.context.escapeHtml(matched[0].name)));
  assert.doesNotMatch(l.elements.main.innerHTML,/START HERE/);
  l.elements.clearFilters.listeners.click();
});
record('SMS-only contacts never receive tel links; call/text offers two actions',()=>{
  const sms=l.context.phonesHtml({phones:[{label:'Text support',number:'741741',mode:'sms',body:'HOME'}]});
  assert.match(sms,/href="sms:741741\?body=HOME"/);
  assert.doesNotMatch(sms,/tel:/);
  const both=l.context.phonesHtml({phones:[{label:'988 support',number:'988',mode:'calltext'}]});
  assert.match(both,/href="tel:988"/);
  assert.match(both,/href="sms:988"/);
  assert.equal((both.match(/class="phone"/g)||[]).length,2);
});
record('Print all includes every entry plus printable source URLs then restores browsing',()=>{
  l.elements.printAll.listeners.click();
  l.timers.shift()();
  const printed=l.getPrinted();
  assert.equal((printed.match(/class="card print-resource"/g)||[]).length,58);
  assert.match(printed,/class="print-url"/);
  assert.match(printed,/https:\/\/unitedwaymesacounty.org/);
  assert.equal((l.elements.main.innerHTML.match(/<article/g)||[]).length,1);
});
record('Home-screen installation does not falsely claim offline readiness',()=>{
  l.windowEvents.appinstalled();
  assert.match(l.elements.installHelp.textContent,/Wait for the Ready offline message/);
});
record('Storage-denied navigation remains functional',()=>{
  const saved=l.context.localStorage;
  // Re-render and instrument produced buttons to invoke the real event listener.
  const buttons=[];
  l.elements.tabs.querySelectorAll=()=>{const e=new Element();e.dataset.id='211';buttons.push(e);return [e];};
  l.context.renderTabs();
  buttons[0].listeners.click();
  assert.match(l.elements.main.innerHTML,/Western Colorado 211/);
});
record('Readiness rejects an older cache and requires the exact reviewed version',()=>{
  l.context.MessageChannel=class {
    constructor(){this.port1={close(){}};this.port2={peer:this.port1};}
  };
  l.context.navigator.serviceWorker={controller:null};
  const worker={postMessage(_message,ports){ports[0].peer.onmessage({data:{type:'OFFLINE_STATUS',cache:cachePrefix + 'old',ready:true}});}};
  l.context.checkOfflineReady({active:worker});
  assert.doesNotMatch(l.elements.offlineStatus.textContent,/^Ready offline:/);
  worker.postMessage=(_message,ports)=>ports[0].peer.onmessage({data:{type:'OFFLINE_STATUS',cache:expectedCache,ready:true}});
  l.context.checkOfflineReady({active:worker});
  assert.match(l.elements.offlineStatus.textContent,/^Ready offline:/);
  l.windowEvents.appinstalled();
  assert.match(l.elements.installHelp.textContent,/offline copy is ready/);
});
record('Standalone HTML served over HTTPS stays self-contained and uses public companion links',()=>{
  const copy=load('https:',true,true);
  assert.equal(copy.getFetches(),0);
  assert.match(copy.elements.offlineStatus.textContent,/Saved offline copy/);
  assert.equal(copy.elements.recoveryGuideLink.href,projectURL('recovery/'));
  assert.equal(copy.context.PHONEBOOK_RESOURCES.length,58);
});
// Exercise the exact service-worker event handlers against in-memory caches.
(async()=>{
  const events={}, stores=new Map(), deleted=[], cacheName=expectedCache;
  let skipped=0,claimed=0,networkCalls=0;
  const cache={
    async addAll(requests){for(const r of requests) stores.set(r.url,{ok:true,marker:r.url,clone(){return this;}});},
    async match(key){return stores.get(typeof key==='string'?key:key.url);},
    async put(key,response){stores.set(key,response);}
  };
  const ctx={URL,Request,console,caches:{async open(){return cache;},async keys(){return ['unrelated-game-cache',cachePrefix + 'old',cacheName];},async delete(key){deleted.push(key);return true;}},
    self:{location:{href:projectURL('sw.js')},addEventListener:(name,fn)=>events[name]=fn,async skipWaiting(){skipped++;},clients:{async claim(){claimed++;}}},
    fetch:async()=>{networkCalls++;throw Error('offline');}
  };
  vm.createContext(ctx);vm.runInContext(swCode,ctx);
  let pending; const waitEvent={waitUntil:p=>pending=p};
  events.install(waitEvent);await pending;
  assert.equal(stores.size,new Set(appShell.map(projectURL)).size);assert.equal(skipped,1);
  results.push({name:'SW install atomically caches all configured shell URLs before skipWaiting',passed:true});
  events.activate(waitEvent);await pending;
  assert.deepEqual(deleted,[cachePrefix + 'old']);assert.equal(claimed,1);
  results.push({name:'SW activation cleans only its own older caches, preserving game cache',passed:true});
  let reply;
  const msg={data:{type:'CHECK_OFFLINE_READY'},ports:[{postMessage:r=>reply=r}],waitUntil:p=>pending=p};
  events.message(msg);await pending;
  assert.equal(reply.ready,true);assert.equal(reply.cache,cacheName);
  stores.delete(projectURL('recovery/'));
  events.message(msg);await pending;assert.equal(reply.ready,false);
  results.push({name:'SW readiness is true only when every phonebook and recovery URL is cached',passed:true});
  let response;events.fetch({request:{method:'GET',url:projectURL('phonebook/index.html'),mode:'navigate'},respondWith:p=>response=p});
  assert.ok((await response).ok);assert.equal(networkCalls,1);
  results.push({name:'SW navigation falls back to saved phonebook while network is unavailable',passed:true});
  let intercepted=false;events.fetch({request:{method:'GET',url:new URL('/unrelated-game/index.html', config.base_url).href,mode:'navigate'},respondWith:()=>intercepted=true});assert.equal(intercepted,false);
  results.push({name:'SW does not intercept the root game or external URLs',passed:true});
  const download=load('https:');
  download.context.location={protocol:'https:',hostname:'example.test'};
  const cloneElements=Object.fromEntries(Object.keys(download.elements).map(id=>[id,new Element(id)]));
  cloneElements.downloadHtml.disabled=true;cloneElements.downloadHtml.textContent='Preparing download…';
  cloneElements.installApp.disabled=true;cloneElements.installApp.textContent='Installed';
  cloneElements.search.value='food';cloneElements.search.setAttribute=()=>{};
  let qrEmbedded=false, removedScripts=0, removedIcons=0, inlineScript, capturedBlob, anchorClicked=false;
  const cloneBody={appendChild(s){inlineScript=s;}};
  const clone={dataset:{},querySelector(q){if(q==='body')return cloneBody;if(q==='[data-share-qr]')return{replaceWith(){qrEmbedded=true;}};return cloneElements[q.slice(1)];},
    querySelectorAll(q){if(q==='script[src]')return resourceFiles.concat('app.js').map(()=>({remove(){removedScripts++;}}));if(q.startsWith('link'))return[{remove(){removedIcons++;}},{remove(){removedIcons++;}}];if(q==='#category option')return[{removeAttribute(){}}];return[];},
    get outerHTML(){return '<html data-offline-copy="'+this.dataset.offlineCopy+'"><body><script>'+inlineScript.textContent+'</script></body></html>';}
  };
  download.context.document.documentElement={cloneNode(){return clone;}};
  download.context.document.createElement=tag=>{
    if(tag==='span')return {innerHTML:'',querySelector(){return {classList:{add(){}},setAttribute(){}};}};
    if(tag==='script')return {textContent:''};
    if(tag==='a')return {click(){anchorClicked=true;},remove(){}};
    throw Error('Unexpected element '+tag);
  };
  download.context.document.body={appendChild(){}};
  download.context.URL={createObjectURL(blob){capturedBlob=blob;return 'blob:test';},revokeObjectURL(){}};
  download.context.fetch=async url=>({ok:true,text:async()=>fs.readFileSync(path.join(dir,url.replace('./','')),'utf8')});
  await download.context.makeSingleFileDownload();
  assert.equal(cloneElements.downloadHtml.disabled,false);assert.equal(cloneElements.downloadHtml.textContent,'Download offline HTML');
  assert.equal(cloneElements.installApp.disabled,false);assert.equal(cloneElements.installApp.textContent,'Offline copy help');
  assert.equal(cloneElements.installHelp.hidden,true);assert.equal(cloneElements.search.value,'');assert.equal(cloneElements.category.value,'');
  assert.equal(cloneElements.recoveryGuideLink.href,projectURL('recovery/'));
  assert.equal(removedScripts,13);assert.equal(removedIcons,2);assert.equal(qrEmbedded,true);assert.equal(anchorClicked,true);
  assert.match(await capturedBlob.text(),/<!doctype html>/);
  new vm.Script(inlineScript.textContent);
  results.push({name:'Actual hosted download routine resets transient UI, embeds QR and all 13 scripts, and keeps recovery URL usable (mocked DOM)',passed:true});
  console.log(JSON.stringify({passed:results.length,results},null,2));
})().catch(error=>{console.error(error);process.exitCode=1;});
