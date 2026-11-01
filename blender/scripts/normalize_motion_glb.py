"""glTF 以帧 1/24 秒为起点；归零采样时间，保持与 FBX 的 24 秒循环同步。"""
import json,struct
from pathlib import Path

def normalize(path,clip_name=None):
    path=Path(path);raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+size]);binary=bytearray(raw[28+size:])
    config=json.loads((Path(__file__).parent/'classroom_motion.json').read_text(encoding='utf-8'))
    renamed=False
    if len(doc.get('animations',[]))==1 and (clip_name or (path.stem in config['characters'] and doc['animations'][0]['name']=='Animation')):
        target=clip_name or config['characters'][path.stem]['clip']
        renamed=doc['animations'][0]['name']!=target;doc['animations'][0]['name']=target
    indices={s['input'] for a in doc.get('animations',[]) for s in a['samplers']}
    offset=min(doc['accessors'][i].get('min',[0])[0] for i in indices)
    if offset<=0 and not renamed:return
    for index in indices:
        a=doc['accessors'][index];assert a['componentType']==5126 and a['type']=='SCALAR'
        view=doc['bufferViews'][a['bufferView']];start=view.get('byteOffset',0)+a.get('byteOffset',0)
        step=view.get('byteStride',4)
        for n in range(a['count']):
            pos=start+n*step;v=struct.unpack_from('<f',binary,pos)[0]
            struct.pack_into('<f',binary,pos,max(0,v-offset))
        for k in ('min','max'):
            if k in a:a[k]=[max(0,v-offset) for v in a[k]]
    text=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();text+=b' '*((-len(text))%4)
    result=struct.pack('<III',0x46546C67,2,12+8+len(text)+8+len(binary))
    result+=struct.pack('<II',len(text),0x4E4F534A)+text+struct.pack('<II',len(binary),0x004E4942)+binary
    path.write_bytes(result)

if __name__=='__main__':
    for path in (Path(__file__).parent/'animated').glob('*.glb'):normalize(path)
