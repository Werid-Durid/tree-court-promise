"""将实际查看范围写入资料索引；原创内容与课程摘取分开记录。"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];path=ROOT/'data/references/sources.json';data=json.loads(path.read_text(encoding='utf-8'))
items=[
 dict(id='original-cet4-v2',title='树庭四级开放微课 · 66 个知识点',status='original',note='六个板块、七个可选小章。例句、线索、迁移题和角色对白为本项目原创；不是完整课程逐字稿或历年真题。'),
 dict(id='bili-course-2026',title='2026年12月刘晓燕四级全程班（用户指定合集）',url='https://www.bilibili.com/video/BV1u8pb6REzY/',status='sample_verified',note='页面包含 54 集；已核实六类板块目录，抽查 Unit 1 约 07:27 的先认词再回语境方法、约 23:56 的 space/spacious 与房间面积联想。其余 64 个知识点为原创整理，未逐集提炼整套课程；上传者不视作已验证官方账号。'),
 dict(id='anaxa-gameplay-v2',title='那刻夏实机演示',url='https://www.bilibili.com/video/BV1fLGvzGEbQ/',status='sample_verified',note='用户指定动作参考。抽查角色展示及场内待机；课堂步态为本项目原骨架 IK 编排，并非官方动作提取。'),
 dict(id='anaxa-study-v2',title='那刻夏自习室 · LILI-D',url='https://www.bilibili.com/video/BV1jiN86ZEXU/',status='sample_verified',note='抽查约 10:07：暖色侧窗光、木质桌案、黑板、书本与稳定远景。用于课堂氛围方向；未复制作者音频与音乐。'),
 dict(id='mmd-anaxa-v2',title='疑心暗鬼 · 那刻夏 · 千月其一',url='https://www.bilibili.com/video/BV1HDvoBEEuv/',status='sample_verified',note='已查看页面借物表与播放画面：偏冷轮廓光、简化面部阴影、手势与视线配合。课堂采用克制表情，未移植舞蹈动作。'),
 dict(id='mmd-hyacine-v2',title='守护最好的风宝 · 我是酸梅我不酸',url='https://www.bilibili.com/video/BV17WjnzLEjo/',status='sample_verified',note='约 01:30 抽帧：柔亮肤色、清晰发色层次、披带随转身延迟。课堂采用较柔和眨眼与回应幅度；尚未加入披带动力学。'),
 dict(id='mmd-castor-v2',title='我的悲伤是水做的 · 吾辈是黑猫怪盗',url='https://www.bilibili.com/video/BV1Vr3qzgEmL/',status='sample_verified',note='约 00:32 抽帧：浅紫白配色、正面留白与收拢手势。课堂采用较低嘴型幅度和较慢眨眼，保持寡言同学角色。'),
 dict(id='mmd-phainon-v2',title='致卡厄斯兰那 · 留守人 · 蓝蝶梦AnnieWisteria',url='https://www.bilibili.com/video/BV1KytozoEXM/',status='sample_verified',note='约 02:09 抽帧及作者制作说明：暖色背景、清晰金属与布料区分；作者说明涉及逐帧修动作、物理烘焙、景深和音频口型。课堂仅参考表现原则，未复制模型改造、动作或视频片段。')]
ids={x['id'] for x in items};data['sources']=[x for x in data['sources'] if x['id'] not in ids]+items;data['checked_date']='2026-10-20'
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
