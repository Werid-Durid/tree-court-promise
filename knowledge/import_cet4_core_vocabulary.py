"""按蓝色词头和双栏坐标分割 PDF；本机 OCR，原页可追溯。"""
import difflib,hashlib,json,re,shutil,sys,unicodedata,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BUILD=ROOT/'knowledge/build/cet4-core-vocabulary'
sys.path.insert(0,str(ROOT/'web/.deps'))
import pymupdf,numpy as np
SOURCE=Path('D:/开发项目/《英语四级核心词》内文.pdf')
DOCX=ROOT/'四六级真题/《英语四级核心词》内文20250901.docx'
UNIT_START=[1,4,8,12,16,20,24,28,31,35]
def key(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).lower().replace('’',"'")
def candidates():
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 with zipfile.ZipFile(DOCX) as z:root=ET.fromstring(z.read('word/document.xml'))
 words={}
 for p in root.findall('.//w:p',ns):
  parts=[]
  for run in p.findall('w:r',ns):
   c=run.find('w:rPr/w:color',ns)
   if c is None:continue
   value=c.get('{'+ns['w']+'}val','')
   if len(value)==6 and int(value[4:6],16)>int(value[:2],16)+60:parts.extend(t.text or '' for t in run.findall('w:t',ns))
  word=''.join(parts).strip()
  if re.fullmatch(r"[A-Za-z][A-Za-z /()\-’']{0,35}",word) and word!='Unit':words[key(word)]=word
 return words
def clean(s):
 s=unicodedata.normalize('NFKC',s)
 s=re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])','',s)
 return re.sub(r'\s+',' ',s).strip()
def build():
 canonical=candidates();ocr={r['page']:r for r in json.loads((BUILD/'ocr.json').read_text(encoding='utf-8-sig'))}
 entries=[];review=[]
 with pymupdf.open(SOURCE) as doc:
  for n,page in enumerate(doc,1):
   pix=page.get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),alpha=False);arr=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
   red,green,blue=[arr[:,:,i].astype(np.int16) for i in range(3)]
   mask=(blue>140)&(green>75)&(blue>red+65)&(green>red+35)
   w,h=pix.width,pix.height;unit=max(i+1 for i,start in enumerate(UNIT_START) if n>=start)
   for col,(left,right) in enumerate([(int(w*.06),int(w*.475)),(int(w*.505),int(w*.95))]):
    ys=np.flatnonzero(mask[100:h-110,left:right].sum(axis=1)>3)+100
    groups=[]
    for y in ys:
     if not groups or y-groups[-1][-1]>7:groups.append([int(y)])
     else:groups[-1].append(int(y))
    heads=[]
    for g in groups:
     if g[-1]-g[0]<5:continue
     y0,y1=g[0],g[-1]+1;xx=np.flatnonzero(mask[y0:y1,left:right].sum(axis=0)>0)+left
     if not len(xx):continue
     x0,x1=int(xx.min()),int(xx.max())+1
     if x0>left+w*.13:continue
     words=[]
     for line in ocr[n]['lines']:
      for word in line['words']:
       cx=word['x']+word['w']/2;cy=word['y']+word['h']/2
       if x0-10<=cx<=x1+10 and y0-8<=cy<=y1+8:words.append(word)
     raw=''.join(x['text'] for x in sorted(words,key=lambda x:(x['y']//15,x['x'])))
     raw=re.sub(r'[^A-Za-z /()\-’\']','',raw).strip()
     k=key(raw);matches=difflib.get_close_matches(k,canonical.keys(),n=2,cutoff=.5) if k else []
     score=difflib.SequenceMatcher(None,k,matches[0]).ratio() if matches else 0
     exact=k in canonical;chosen=canonical[k] if exact else canonical[matches[0]] if score>=.7 else raw
     second=difflib.SequenceMatcher(None,k,matches[1]).ratio() if len(matches)>1 else 0
     uncertain=not exact and (score<.78 or score-second<.07)
     heads.append(dict(word=chosen,raw_headword=raw,y=y0,bbox=[x0,y0,x1,y1],spelling_score=round(score if not exact else 1,3),review_required=uncertain))
    for i,head in enumerate(heads):
     stop=heads[i+1]['y']-5 if i+1<len(heads) else h-120
     start=head['y']-7;segments=[]
     for line in ocr[n]['lines']:
      words=[x for x in line['words'] if left<=x['x']+x['w']/2<right and start<=x['y']+x['h']/2<stop and x['x']>=left+w*.095]
      words=[x for x in words if not (head['bbox'][0]-8<=x['x']+x['w']/2<=head['bbox'][2]+8 and head['bbox'][1]-8<=x['y']+x['h']/2<=head['bbox'][3]+8)]
      if words:segments.append((min(x['y'] for x in words),' '.join(x['text'] for x in words)))
     raw=clean(' '.join(t for _,t in sorted(segments)))
     chinese=re.search('[\u4e00-\u9fff]',raw)
     meaning=raw[chinese.start():] if chinese else ''
     meaning=re.sub(r'\b(?:adj|adv|prep|conj|pron|aux|num|vi|vt|v|n)\s*\.?\s*(?=[\u4e00-\u9fff(;；])','',meaning,flags=re.I)
     meaning=clean(meaning).strip(' /;；')
     entry=dict(id='cet4core-'+hashlib.sha256(f'{n}:{col}:{head["y"]}:{head["word"]}'.encode()).hexdigest()[:16],word=head['word'],meaning=meaning,unit=unit,page=n,column=col+1,source_bbox=head['bbox'],raw_ocr=raw,raw_headword=head['raw_headword'],spelling_score=head['spelling_score'],review_status='needs_review' if head['review_required'] or not meaning or not re.search('[A-Za-z]',head['word']) else 'ocr_cross_checked')
     entries.append(entry)
     if entry['review_status']=='needs_review':review.append(entry)
 digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest();asset=ROOT/'data/vocabulary/cet4-core-source.pdf';asset.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SOURCE,asset)
 result=dict(version=1,title='英语四级核心词',source={'file':str(asset.relative_to(ROOT)),'sha256':digest,'pages':38,'type':'user_pdf','extraction':'本机中文OCR+蓝色词头双栏定位；同名DOCX仅作拼写交叉核对；未逐词人工审定'},units=[{'id':i+1,'title':f'Unit {i+1}','start_page':p,'end_page':UNIT_START[i+1]-1 if i+1<len(UNIT_START) else 38,'count':sum(e['unit']==i+1 for e in entries)} for i,p in enumerate(UNIT_START)],entries=entries)
 for name,value in [('data/vocabulary/cet4-core.json',result),('knowledge/build/cet4-core-vocabulary/review.json',review)]:
  (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'entries':len(entries),'review':len(review),'units':result['units'],'samples':entries[:3]},ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');build()
