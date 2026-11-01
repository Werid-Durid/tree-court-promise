// 完整课堂目录超过 localStorage 常见配额；教材缓存独立存入 IndexedDB，给学习事件留空间。
function access(mode,value){return new Promise(resolve=>{
 if(!globalThis.indexedDB){resolve(null);return;}
 const request=indexedDB.open('treecourt-curriculum-cache',1);
 request.onupgradeneeded=()=>request.result.createObjectStore('catalog');
 request.onerror=()=>resolve(null);
 request.onsuccess=()=>{const db=request.result,tx=db.transaction('catalog',mode),store=tx.objectStore('catalog');
  const op=mode==='readwrite'?store.put(value,'current'):store.get('current');let result=null;
  op.onsuccess=()=>{result=mode==='readwrite'?true:op.result;};
  tx.oncomplete=()=>{db.close();resolve(result);};tx.onerror=tx.onabort=()=>{db.close();resolve(null);};
 };
});}
export const saveCatalog=value=>access('readwrite',value);
export const loadCatalog=()=>access('readonly');
