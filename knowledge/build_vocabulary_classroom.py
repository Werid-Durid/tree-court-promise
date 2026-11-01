"""将用户词库编译成可自由选学的课堂。稳定词条 ID 与原图页码不变。"""
import json,math,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREFIX='cet4-core-class-'

def build():
    path=ROOT/'data/curriculum/catalog.json'
    catalog=json.loads(path.read_text(encoding='utf-8'))
    bank=json.loads((ROOT/'data/vocabulary/cet4-core.json').read_text(encoding='utf-8'))
    subject=next(s for s in catalog['subjects'] if s['id']=='cet4')
    subject['chapters']=[c for c in subject['chapters'] if not c['id'].startswith(PREFIX)]
    catalog['points']=[p for p in catalog['points'] if not p.get('vocabulary_lesson')]
    generated=[]
    for unit in bank['units']:
        entries=[e for e in bank['entries'] if e['unit']==unit['id']]
        for offset in range(0,len(entries),16):
            group=entries[offset:offset+16];number=offset//16+1
            chapter=f'{PREFIX}u{unit["id"]:02d}-{number:02d}'
            ids=[]
            for index,e in enumerate(group):
                word,meaning=e['word'],e['meaning'];pid='class-'+e['id'];ids.append(pid)
                # 不为自动生成的内容编造词根或例句；完整释义始终取自指定词表。
                anchor=f'先看清 {word} 的拼写，再把“{meaning}”连到这个词上。遮住中文，复述一次；隔几个词再回来。'
                dialogues={
                    'anaxa':f'看黑板上的 {word}。本书给出的释义是：{meaning}。别把眼熟当成理解。先说出它的意思，再检验你能否独立想起。',
                    'hyacine':f'不着急。{anchor} 一次记不全，可以先记住其中一个义项，再慢慢补齐。',
                    'castor':f'{word}：{meaning}。先辨清义项，再回忆。',
                    'phainon':f'我们把 {word} 写在便笺正面，中文写在背面。先遮住背面讲一遍，再翻过来核对；下一轮我和你交换着抽查。',
                }
                distractors=[]
                for step in range(1,len(bank['entries'])):
                    other=bank['entries'][(bank['entries'].index(e)+step*17)%len(bank['entries'])]
                    if other['meaning']!=meaning and other['meaning'] not in distractors:distractors.append(other['meaning'])
                    if len(distractors)==2:break
                choices=[meaning]+distractors
                # 每词固定打乱，刷新不会变更答案索引，也不会所有题都排在第一项。
                shift=int(hashlib.sha256(e['id'].encode()).hexdigest()[:4],16)%3
                choices=choices[shift:]+choices[:shift]
                correct=choices.index(meaning)
                clues=[{'id':f'{pid}-anchor-{i}','text':f'用“{m}”作释义锚点，再回看词形','correct':i==correct,'type':'meaning_anchor'} for i,m in enumerate(choices)]
                p={'id':pid,'subject':'cet4','chapter':chapter,'concept':word,'summary':'先听讲解，再遮住释义回忆','quick_meaning':meaning,'character':'anaxa','speaker':'anaxa','difficulty':1,
                   'prompt':f'现在遮住释义。{word} 应当连向哪一个记忆锚点？指出你的线索，再与原书核对。',
                   'clues':clues,'memoryHook':anchor,
                   'feedback':{'matched':f'这条联系成立。{word}：{meaning}。{anchor}', 'redirect':f'这条联系需要重建。{word}：{meaning}。{anchor} 失误是回查的起点，不扣好感。'},
                   'example':{'en':word,'zh':meaning},'assistant_hint':dialogues['hyacine'],'dialogue':dialogues,
                   'classmate':{'character':'castor' if index%2==0 else 'phainon','text':dialogues['castor' if index%2==0 else 'phainon']},
                   'test':{'question':f'回忆 {word}，哪一条释义来自本书？','choices':choices,'answer':correct,'explanation':f'原书第 {e["page"]} 页：{word} — {meaning}。'+anchor},
                   'vocabulary_lesson':{'word_id':e['id'],'unit':e['unit'],'page':e['page'],'meaning':meaning,'source':'cet4-core-user-pdf','continuation_pages':[c['page'] for c in e.get('continuations',[])]}}
                generated.append(p)
            subject['chapters'].append({'id':chapter,'module':'核心词汇课堂','title':f'核心词汇 · Unit {unit["id"]} · 第 {number} 课','subtitle':f'原书第 {group[0]["page"]}–{group[-1]["page"]} 页 · {len(group)} 词 · 讲解、联想、回忆',
               'vocabulary_unit':unit['id'],'points':ids,'test_points':ids,
               'opening':f'第一，别叫我那刻夏。今天从 Unit {unit["id"]} 的这组词开始。风堇协助你建立记忆线索，两位同学和你互相抽查。理解不靠赶进度；你可以随时换课或回到某一个词。'})
    catalog['points']+=generated;catalog['version']=max(7,catalog.get('version',1))
    path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'words':len(generated),'lessons':sum(c['module']=='核心词汇课堂' for c in subject['chapters']),'units':len(bank['units'])}))

if __name__=='__main__':build()
