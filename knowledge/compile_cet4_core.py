"""以原 PDF 蓝色词头坐标为锚，合并高质量离线 OCR 与跨页释义。"""
import hashlib,json,re,sys,unicodedata
from pathlib import Path
from import_cet4_core_vocabulary import ROOT,BUILD,candidates,key,clean
def plain_meaning(raw):
 s=unicodedata.normalize('NFKC',raw)
 s=re.sub(r'/[^/]{1,85}/',' ',s)
 # 优先从明确词性后开始，避免把音标里的误识别汉字当作释义。
 pos=re.search(r'(?<![a-z])(?:adj|adv|prep|conj|pron|aux|num|vt|vi|v|n)\s*\.\s*',s,re.I)
 if pos:s=s[pos.end():]
 else:
  m=re.search('[\u4e00-\u9fff]',s)
  if m:s=s[max(0,m.start()-1) if m.start() and s[m.start()-1]=='(' else m.start():]
 s=re.sub(r'(?<![a-z])(?:adj|adv|prep|conj|pron|aux|num|vt|vi|v|n)\s*\.\s*','；',s,flags=re.I)
 s=re.sub(r'&\s*[；;]?', '', s)
 s=re.sub(r'\.{3,}', '……', s)
 return clean(s).strip(' /;；').replace(';','；').replace(',','，')
def spellings(word):
 variants={word};expanded={word}
 for _ in range(4):
  new=set()
  for x in expanded:
   m=re.search(r'\(([^()]+)\)',x)
   if m:new.update([x[:m.start()]+m[1]+x[m.end():],x[:m.start()]+x[m.end():]])
   else:new.add(x)
  if new==expanded:break
  expanded=new
 for x in expanded:
  bits=x.split('/');variants.add(bits[0])
  for alt in bits[1:]:variants.add(bits[0][:-len(alt[1:])]+alt[1:] if alt.startswith('-') else alt)
 return sorted(v for v in variants if v)
def build():
 path=ROOT/'data/vocabulary/cet4-core.json';bank=json.loads(path.read_text(encoding='utf-8'));old=bank['entries'];canonical=candidates();new=[]
 for n in range(1,39):
  regions=json.loads((BUILD/f'rapid-{n}.json').read_text(encoding='utf-8'));w,h=1354,1885
  # 页图来自2.5倍渲染，按实际PNG头尺寸读取，避免硬编码纸张像素。
  import struct
  png=(BUILD/f'page-{n}.png').read_bytes();w,h=struct.unpack('>II',png[16:24])
  boxes=[]
  for poly,text,confidence in regions:
   xs=[p[0] for p in poly];ys=[p[1] for p in poly]
   boxes.append(dict(x=min(xs),y=min(ys),right=max(xs),bottom=max(ys),cx=sum(xs)/4,cy=sum(ys)/4,text=text,score=confidence))
  for col in (1,2):
   anchors=sorted([e for e in old if e['page']==n and e['column']==col],key=lambda e:e['source_bbox'][1]);left,right=(w*.06,w*.475) if col==1 else (w*.505,w*.95)
   if not anchors:continue
   first=anchors[0]['source_bbox'][1]
   leading=[b for b in boxes if b['x']>=left+w*.095 and left<=b['cx']<right and 110<b['cy']<first-10]
   if leading and re.search('[\u4e00-\u9fff]',''.join(b['text'] for b in leading)):
    previous=next((e for e in reversed(new) if e['page']==(n-1 if col==1 else n) and e['column']==(2 if col==1 else 1) and e['unit']==anchors[0]['unit']),None)
    if previous:
     text=plain_meaning(' '.join(b['text'] for b in sorted(leading,key=lambda b:(b['cy'],b['x']))))
     previous['meaning']=clean(previous['meaning']+'；'+text).replace(';','；');previous.setdefault('continuations',[]).append(dict(page=n,rect=[left,110,w*.49 if col==1 else w*.99,first-8]))
   for i,a in enumerate(anchors):
    x0,y0,x1,y1=a['source_bbox'];stop=anchors[i+1]['source_bbox'][1]-7 if i+1<len(anchors) else h-110
    head=[b for b in boxes if abs(b['cy']-(y0+y1)/2)<15 and x0-15<=b['x']<=x1 and b['cx']<=x1+15]
    if not head:head=[b for b in boxes if abs(b['cy']-(y0+y1)/2)<18 and abs(b['x']-x0)<18]
    raw=' '.join(b['text'] for b in sorted(head,key=lambda b:b['x']))
    raw=raw.strip('.,;：: ')
    if re.search('[\u4e00-\u9fff]',raw):
     prefixes=[v for k,v in canonical.items() if key(raw).startswith(k)];raw=max(prefixes,key=len) if prefixes else re.split(r'\s|/',raw)[0]
    word=canonical.get(key(raw),raw)
    confidence=min((b['score'] for b in head),default=0)
    definition=[b for b in boxes if left<=b['cx']<right and b['x']>=left+w*.095 and y0-8<=b['cy']<stop and b not in head]
    raw_def=' '.join(b['text'] for b in sorted(definition,key=lambda b:(round(b['cy']/12),b['x'])))
    meaning=plain_meaning(raw_def)
    valid=bool(re.fullmatch(r"[A-Za-z][A-Za-z /()\-’']{0,45}",word))
    flags=[]
    if not valid or confidence<.95:flags.append('headword_ocr')
    if not re.search('[\u4e00-\u9fff]',meaning):flags.append('meaning_missing')
    if any(b['score']<.78 for b in definition if re.search('[\u4e00-\u9fff]',b['text'])):flags.append('meaning_ocr')
    entry=dict(id='cet4core-'+hashlib.sha256(f'{n}:{col}:{y0}'.encode()).hexdigest()[:16],word=word or '待核对词头',meaning=meaning or '请查看本词原图',unit=a['unit'],page=n,column=col,source_bbox=a['source_bbox'],source_rect=[left,max(100,y0-9),w*.49 if col==1 else w*.99,stop],raw_headword=raw,raw_ocr=raw_def,spelling_score=round(confidence,4),review_status='needs_review' if flags else 'ocr_cross_checked' if key(word) in canonical else 'ocr_high_confidence',review_reasons=flags,accepted_spellings=spellings(word))
    new.append(entry)
 from cet4_vocabulary_corrections import CORRECTIONS
 order=json.loads((BUILD/'review-order.json').read_text(encoding='utf-8'));by={e['id']:e for e in new}
 for line in CORRECTIONS.strip().splitlines():
  index,word,meaning=line.split('|');e=by[order[int(index)-1]['id']];e.update(word=word,meaning=meaning,accepted_spellings=spellings(word),review_status='human_checked',review_reasons=[])
 for e in new:
  if e['word']=='marvel(I) ous':e.update(word='marvel(l)ous',accepted_spellings=spellings('marvel(l)ous'),review_status='spelling_corrected')
 # 人工核对全部续行：原书部分栏首残行与前词无关，不强行并入释义。
 continuation_meanings={
  'reverse':'逆转；彻底改变；撤销；相反的；反向的；后面的；逆转；后面；损失；倒挡',
  'form':'形式；表格；组成；（使）形成',
  'sail':'航行；开船；在……上航行；驾驶（船）；帆；航行',
  'progress':'进步；进展；进步，改进',
  'splash':'落水声；溅洒后留下的污渍；把（水、泥等）溅在……上',
  'constant':'不断的；重复的；固定的，不变的',
  'plot':'密谋；策划；故事情节；密谋',
  'hack':'劈，砍；非法侵入（他人计算机系统）',
  'qualify':'取得资格（或学历）；使合格；达标',
  'require':'需要；要求，规定',
  'ingredient':'成分；（尤指烹饪）材料；（成功的）因素，要素',
  'combine':'（使）结合；联合；兼备；集团，联合企业',
  'dim':'昏暗的；朦胧的；模糊的，不清楚的',
  'subsequent':'随后的；后来的；接下来的',
  'accident':'（交通）事故；意外遭遇；不测事件',
 }
 for e in new:
  if e['word'] in continuation_meanings:
   e['meaning']=continuation_meanings[e['word']]
   e['review_status']='human_checked'
  if e['word'] in ('splash','plot','require'):
   e.pop('continuations',None)
   e['source_note']='原PDF下一栏首有不属于本词的残行，未并入本词释义'
 bank['entries']=new
 for unit in bank['units']:unit['count']=sum(e['unit']==unit['id'] for e in new)
 bank['source']['extraction']='原PDF蓝色词头及双栏坐标定位，离线RapidOCR识别，Windows OCR与同名Word辅助交叉核对；保留原图，未逐词人工审定'
 path.write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf-8')
 review=[e for e in new if e['review_status']=='needs_review'];(BUILD/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'count':len(new),'review':len(review),'empty':sum(e['word']=='待核对词头' for e in new),'samples':new[:3]},ensure_ascii=False))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');build()
