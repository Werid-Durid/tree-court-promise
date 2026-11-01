// 服务端更换纪元后清空本应用存档；避免旧标签页把重置前的记录重新上传。
export function resetProgressStorage(storage,epoch,key='treecourt.web.v1'){
 if(storage.getItem(key+'.epoch')===JSON.stringify(epoch))return false;
 for(const k of Object.keys(storage))if(k===key||k.startsWith(key+'.'))storage.removeItem(k);
 storage.setItem(key+'.epoch',JSON.stringify(epoch));return true;
}
