"""可复现的开放四级教案。例句、情境、测验均为原创，不冒充课程逐字稿或真题。"""
import json,re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "data/curriculum/catalog.json"
catalog = json.loads(path.read_text(encoding="utf-8"))
# 保留旧 ID，使原有错题、进度与角色关系仍可回放。
catalog["points"] = [p for p in catalog["points"] if p["chapter"] == "cet4-01"]
old = list(catalog["points"])
chapters = [{
    "id": "cet4-01", "title": "词汇 · 日常行动", "module": "词汇",
    "subtitle": "先认词，再放回句子", "points": [p["id"] for p in old],
    "opening": "第一，别叫我那刻夏。第二，课程顺序由你决定，概念的边界却不能含糊。选一张词笺，我们从它在句子里做了什么开始。",
}]
# 每行：概念｜精炼释义｜记忆钩子｜例句｜译文｜课堂线索｜干扰线索｜迁移测验｜答案｜干扰项。
units = [
("vocabulary", "词汇", "词汇 · 构词与易混词", [
("predict","预测","pre- 表示在前，dict 与说有关：事先说出；预测仍需证据。","We cannot predict the result.","我们无法预测结果。","先于结果作出判断","结果发生后才回忆","The forecast helps us ___ tomorrow's weather.","predict","protect"),
("transport","运输；运送","trans- 跨越，port 与携带有关：把货物带到另一处。","Trucks transport food to the city.","卡车把食品运到城里。","把物品跨地搬运","把物品留在仓库","These ships ___ goods between ports.","transport","translate"),
("portable","便携的","port 与携带有关，-able 表示能够：能够随身带走。","This portable radio fits in my bag.","这台便携收音机能放进我的包里。","可以带走的小设备","固定在墙上的设备","A ___ charger is useful on a trip.","portable","permanent"),
("review","复习；回顾；审查","re- 再，view 看：再看一次，也可指审查；语境决定具体词义。","Review your notes after class.","课后复习笔记。","重新看一遍旧笔记","第一次发现陌生笔记","Please ___ the report before we publish it.","review","remove"),
("reduce","减少；降低","把水杯的刻度向下移：reduce 是降数量，不是清零。","We can reduce food waste.","我们可以减少食物浪费。","把原有用量调低","把用量不断增加","Better insulation can ___ energy use.","reduce","produce"),
("increase","增加；增长","把刻度往上移，与 reduce 对照记，不靠相似字形猜意思。","Exercise can increase your energy.","锻炼可以增强你的活力。","让数值向上变化","让数值向下变化","The number rose from ten to twenty: it ___.","increased","decreased"),
("affect","影响（动词）","Affect 是动作：天气影响旅程；effect 常作名词，指产生的效果。","Noise can affect concentration.","噪声会影响注意力。","噪声正在干扰学习","记录干扰产生的结果","Lack of sleep can ___ memory.","affect","effect"),
("effect","效果；影响（常用名词）","看见 an effect，先找一个结果；effect 也可作动词促成，不用绝对规则。","The new rule had a positive effect.","新规则产生了积极影响。","措施带来的结果","正在影响他人的动作","What was the ___ of the change?","effect","affect"),
("economic","经济的；经济学的","economic 描述经济事务，economical 描述省钱省资源；研究经济不等于省钱。","The city faces economic challenges.","这座城市面临经济挑战。","城市的经济发展","一辆省油的小车","The report discusses ___ growth.","economic","economical"),
("economical","节约的；经济实惠的","economical 像管账的人：花得少、用得省。","This car is economical to run.","这辆车的使用成本低。","花费较少的使用方案","研究宏观经济的论文","Cycling is an ___ way to travel.","economical","economic"),
("adapt","适应；改编","adapt 联想调节适配器：改变自己以适合环境；adopt 是采用或收养。","Students adapt to a new routine.","学生适应新的日常安排。","调节自己适合新环境","把一种方案正式采用","It takes time to ___ to a new climate.","adapt","adopt"),
("adopt","采用；收养","adopt 联想把方法接到自己这边：正式采用；不要与 adapt 适应混用。","The school adopted a new method.","学校采用了一种新方法。","选定并采用一种办法","为适合新环境改变自己","The team decided to ___ her suggestion.","adopt","adapt"),
("space","空间；太空","把书桌之间留出的空处记成 space。课程用大房间面积作谐音联想；谐音只是提醒，发音仍按 /speɪs/。","Leave some space between the desks.","在课桌之间留些空间。","给桌椅之间留出空处","把每张桌子紧贴在一起","We need more ___ for the chairs.","space","speed"),
("spacious","宽敞的","space 是空间，spacious 描述空间宽敞：名词到形容词，分别记住拼写和发音 /ˈspeɪʃəs/。","The classroom is spacious.","教室很宽敞。","用形容词描述宽敞的教室","把空间这个名词直接当形容词","This ___ room can hold thirty students.","spacious","space"),
]),
("grammar","语法","语法 · 句子骨架",[
("主谓骨架","先找限定谓语，再找主语","句子像树：主谓是树干，修饰语是枝叶；先别被长枝条遮住。","The book on the desk belongs to Lin.","桌上的书属于林。","先认出 book—belongs","把 on the desk 当谓语","The student with two bags is waiting. 主语中心词是？","student","bags"),
("主谓一致","谓语与主语中心词一致","书包再多，背书包的人还是一个；介词短语中的复数不决定主句谓语。","The list of names is on the desk.","名单在桌上。","盯住 list 而不是 names","看到 names 就使用 are","The quality of these products ___ improving.","is","are"),
("被动语态","be + 过去分词，主语承受动作","把聚光灯从做事的人移到承受动作的对象；be 负责时态。","The room was cleaned yesterday.","房间昨天被打扫了。","房间接受打扫这个动作","房间主动打扫其他物品","The report ___ by Li yesterday.","was written","wrote"),
("现在完成时","have/has + 过去分词，联系现在","过去到现在的一座桥；明确结束的 yesterday 通常走一般过去时。","She has lived here for five years.","她已经在这里住了五年。","从过去延续到现在","只定位昨天完成的瞬间","I ___ here since 2020 and still live here.","have lived","lived"),
("定语从句","修饰名词，关系词连接从句","名词背后的身份标签：who 常指人，which 常指物；先找被修饰名词。","The student who won the prize smiled.","获奖的学生笑了。","给 student 加上身份说明","把 won 当整个句子的唯一谓语","The book ___ you lent me is useful.","which","who"),
("非谓语","非谓语不独自充当限定谓语","一个分句的谓语位置要先确定，其他动作再选不定式、动名词或分词结构。","Reading every day improves vocabulary.","每天阅读能增加词汇量。","把 Reading 当活动名称","让 Reading 与 improves 都独立作限定谓语","___ English every day helps me improve.","Practising","Practise"),
("比较结构","than 引出比较对象","比较像天平：两边要可比，不把城市的面积和一座城市本身相比较。","This room is larger than that one.","这个房间比那个大。","比较房间与房间","比较房间与人口","This route is ___ than the old one.","shorter","shortest"),
("条件与时态","真实将来条件从句常用一般现在时","条件门写 if，主句写结果：门未打开，但门上的时态通常不用 will。","If it rains, we will stay inside.","如果下雨，我们就待在室内。","if 门后用现在时说未来条件","每个未来意义都写 will","If she ___ early, we will begin at nine.","arrives","will arrive"),
]),
("listening","听力","听力 · 预判与信号",[
("预读选项","先识别选项的差异与问题方向","听前铺地图：地点、人物、数字、原因先分类，别把预判当答案。","Where will the speakers meet?","说话者将在哪里见面？","先标出三个地点的区别","未听录音就选熟悉地点","选项都是地点时，听前优先预判什么？","会面地点或事件发生地","说话者的年龄"),
("转折信号","but / however 后常出现重点变化","but 像路口转向灯：保留前文，再留意新方向；不能只听一个词。","I wanted to walk, but it began to rain, so I took a bus.","我想走路，但下雨了，所以坐了公交车。","跟住转折后的实际安排","只记最初想步行","实际采用了哪种交通方式？","bus","walking"),
("数字更正","区分原安排与最终安排","旧数字轻轻划掉，最终确认的数字另起一行。","The meeting was at nine, but it has been moved to ten.","会议原定九点，现改到十点。","把最终时间圈出来","听见第一个数字就停笔","会议现在几点开始？","ten","nine"),
("同义替换","听懂意思，不等原词重现","给同一个意思换外套：costly 和 expensive 可以在价格语境中对应。","The repair is too costly.","维修费用太高。","把 costly 连到 expensive","只找完全一样的拼写","这里 costly 最接近哪个意思？","expensive","convenient"),
("原因与结果","because / so 区分因果方向","因为是来路，所以是去处；不要把结果倒装成原因。","The road was closed, so we walked home.","道路封闭，因此我们步行回家。","从封路指向步行","从步行推断导致封路","他们为什么步行回家？","The road was closed.","They disliked buses."),
("建议表达","Why not…? 可表示建议","不是追问为什么不做，而是把可行办法推到你面前；结合语调和语境。","Why not ask the librarian?","何不问问图书管理员？","把问句听成行动建议","把它理解成图书馆已关闭","说话者建议做什么？","Ask the librarian.","Close the library."),
("新闻要素","抓住谁、何事、何时、何地及原因","新闻像简短事件卡：先写主事件，后补数字和细节。","A new library opened in the town on Monday.","镇上一座新图书馆于周一开放。","先记图书馆开放这个主事件","只记 Monday 而忽略事件","这则消息的主事件是什么？","A library opened.","A library closed."),
("精听复盘","先听再核对文本，按错因补练","听不出声音、词义不熟、逻辑没跟上，要分三格修补。","Could you turn it down a little?","你能把音量调低一点吗？","遮住文本先听，再定位漏听处","看着全文假装自己听懂","已认识单词却辨不出连读，优先练什么？","跟读并比较声音边界","只增加默写数量"),
]),
("reading","阅读","阅读 · 定位与证据",[
("定位词","专名、时间等可帮助定位，仍需读上下文","把稀有词当书签，不把书签当答案。","In 2022, the school opened a new laboratory.","2022年，学校开设了一个新实验室。","用 2022 定位，再读事件","只凭年份相同就选答案","定位到年份后应怎样继续？","读相邻句确认题干所问","立刻选择含年份的选项"),
("细节证据","答案需得到原文支持","证据像脚印：每个判断都要能回到原句。","Some students prefer studying alone.","有些学生喜欢独自学习。","保留 some 的范围","把 some 扩大为 all","原句支持哪个判断？","A number of students prefer studying alone.","All students prefer studying alone."),
("词义猜测","结合转折、例子和上下文推断","陌生词站在熟悉的邻居中间，先看邻居关系。","The room was tiny; only one desk fitted inside.","房间很小，里面只能放一张书桌。","用 only one desk 推断大小","用自己的喜好猜词义","tiny 在这里最接近？","small","bright"),
("段落主旨","区分中心观点与支撑例子","主题是树干，例子是枝叶；第一句有时是主题，仍需通读验证。","Regular exercise benefits health. Walking, for example, can improve fitness.","规律锻炼有益健康，例如步行能改善体能。","把 exercise benefits health 当中心","把 walking 当唯一主题","这段最合适的概括是？","Benefits of regular exercise","The history of walking"),
("推断边界","推断不得超出证据支持的范围","从一块石头跨到下一块，不能直接跳到河对岸。","The café was closed when Lin arrived at eight.","林八点到时咖啡馆关着。","只确认到达时未营业","推断咖啡馆永久倒闭","哪项得到原句直接支持？","It was closed at eight.","It never opens."),
("长篇匹配","用信息组合匹配段落，警惕仅同词","两把钥匙一起开门：主题词和事实关系都对得上。","The paragraph explains how volunteers train new members.","这一段解释志愿者如何培训新成员。","匹配培训活动与参与者","只匹配 volunteers 一个词","选择匹配段落时最可靠的是？","关键信息及关系都一致","有同一个单词即可"),
("选词填空","先判断空格词性，再核对词义搭配","先给空格量尺寸，再挑能穿进去的词。","The team worked very carefully.","团队工作得非常仔细。","动词后看修饰方式的副词","只找看起来最长的词","She answered the question ___.","correctly","correct"),
("作者态度","依据措辞和论证，不代入个人观点","作者的语气从文本里找，不借自己的情绪替他发言。","The proposal is promising, although some risks remain.","这个提议有前景，不过仍有一些风险。","同时保留肯定与保留意见","把 promising 读成完全否定","作者的态度最接近？","Cautiously positive","Completely negative"),
]),
("translation","翻译","翻译 · 意群与重组",[
("意群拆分","先分信息单元，再组织英文","把长串珠子分段串好：谁做什么、时间地点、修饰说明。","Students read quietly in the library after class.","学生们课后在图书馆安静阅读。","先定主谓再添地点时间","逐字照搬中文次序","翻译长句时第一步更合适的是？","识别主干和信息层次","为每个汉字找一个英文词"),
("补足主语","英语完整陈述句通常需要主语和谓语","中文能省略的主语，英文要结合语境安置；祈使句等有例外。","It is important to protect the environment.","保护环境很重要。","用 It 承接后置的不定式","删掉主语只留 is important","哪句是完整自然的陈述？","It is useful to review regularly.","Is useful to review regularly."),
("时态线索","依据时间与语境选择时态","时间词是路标：昨天向过去，近年来常联系现在，不机械一词一时态。","The town built a bridge last year.","这个镇去年修建了一座桥。","根据 last year 使用过去式","只要中文没有了就用现在时","该句哪个形式合适？ The town ___ a bridge last year.","built","builds"),
("数量表达","hundred / thousand 具体数后通常不加 s","确数排整队：three hundred；概数成群：hundreds of。","Three hundred students joined the activity.","三百名学生参加了活动。","具体数后用 hundred","看到人数多就给 hundred 加 s","三千本书的自然表达是？","three thousand books","three thousands books"),
("名词搭配","以自然搭配表达，不拼凑孤立词义","词语也有固定同桌：make progress，不能按中文造 do progress。","We have made progress in saving energy.","我们在节能方面取得了进展。","把 make 与 progress 连起来","逐字把做进步译成 do progress","取得进步的自然搭配是？","make progress","do progress"),
("文化词解释","缺乏直译时用准确简短的解释","给陌生读者一张说明卡：保留核心文化信息，避免生造词。","The Dragon Boat Festival is a traditional Chinese festival.","端午节是中国传统节日。","名称配简短解释","不确定时编造夸张历史","首次介绍文化节日时可采用什么方式？","常用译名加必要解释","任意创造拼写"),
("主动被动选择","根据信息重点和英语习惯调整语态","灯光照在桥上时，可以说桥被建成；不是每个中文被字都必须照搬。","The bridge was completed in 2019.","这座桥于2019年建成。","强调 bridge 并用被动结构","让 bridge 主动完成自己","哪句适合强调桥的建成？","The bridge was completed in 2019.","The bridge completed in 2019."),
("检查清单","检查漏译、时态、单复数、冠词与拼写","交稿前沿五个站点走一圈：意思、时间、数量、小词、拼写。","The museum attracts many visitors every year.","这座博物馆每年吸引许多游客。","核对 many 后的复数 visitors","只检查句子是否足够长","many 后哪个形式适合？","visitors","visitor"),
]),
("writing","写作","写作 · 观点与展开",[
("审题","明确任务、对象与文体","先看信封寄给谁，再决定怎样开口；书信与议论文不能混用格式。","Write an email inviting a classmate to a study group.","写邮件邀请同学参加学习小组。","抓住 email、invite、classmate","直接背一段任意议论文","这项写作任务的主要目的是什么？","邀请同学参加学习小组","向报社投诉交通"),
("主题句","一句话给出段落中心","先立路牌再举例，读者才知道往哪里走。","Regular reading helps students build vocabulary.","经常阅读有助于学生积累词汇。","先提出阅读的益处","先堆不相关的个人经历","哪个句子更适合作为阅读益处段的主题句？","Reading regularly improves vocabulary.","My bag is blue."),
("原因展开","观点后说明为什么","结论不是论证，给 because 后面装上可以解释的原因。","Reading helps because it exposes us to words in context.","阅读有帮助，因为它使我们在语境中接触词汇。","补充接触语境这一原因","反复写 reading is good","观点后最需要补充什么？","支持它的原因或证据","相同结论重复三遍"),
("例子支撑","用具体例子说明原因","例子像放大镜：把抽象益处变成一个可观察场景。","For example, a news article shows how common verbs are used.","例如，一篇新闻文章可以展示常见动词的用法。","举出新闻文章中的词语使用","举一个与阅读无关的球赛结果","哪种例子能支持语境学词？","在短文里观察同一个词的不同搭配","描述昨天的天气而不联系观点"),
("衔接关系","连接词必须与真实逻辑相符","连接词是路标，不是装饰；转折用 however，因果用 therefore。","The task was difficult. However, we finished it.","任务很难。不过，我们完成了。","承认困难后转向完成结果","把所有句子都用 therefore 连接","表达转折时更合适的是？","however","therefore"),
("改写","保留原意再改变表达方式","换衣服不换人：词语可以替换，范围、否定和因果不能偷换。","Many students find the library useful.","许多学生觉得图书馆有用。","保留 many 而非扩大为 every","把许多改成所有来显得有力","哪个改写保留原意？","The library is useful to many students.","Every student depends entirely on the library."),
("应用文语气","请求与邀请使用清楚得体的语气","把命令放软，但把时间、地点、行动说清楚。","Would you like to join our study group on Friday?","你愿意周五加入我们的学习小组吗？","礼貌邀请并交代时间","只写 You must come!","哪个更适合给同学发邀请？","Would you like to join us?","You must obey me."),
("修改复核","先修意思与结构，再修语言细节","先把房子搭稳，再擦窗：任务是否完成、段落是否连贯，最后逐句校对。","Good writing develops through revision.","好文章在修改中形成。","先看任务与逻辑再查小错误","只换几个长词就交稿","修改作文时更合理的顺序是？","内容与结构，再语法和拼写","先换生僻词，再忽略内容"),
])]
for module, label, title, rows in units:
    chapter_id = f"cet4-{module}"
    chapter = {"id": chapter_id, "title": title, "module": label, "subtitle": "概念 → 联想 → 迁移练习",
               "opening": f"今天讨论{label}。你可以从任何一处开始，也可以直接做检测。顺序不是理解的证据，能解释自己的选择才是。", "points": []}
    for i, (concept, summary, hook, en, zh, yes, no, question, answer, distractor) in enumerate(rows):
        pid = f"{chapter_id}-{i+1:02d}"
        peer = "castor" if i % 2 == 0 else "phainon"
        clues = [{"id": "clue-0", "text": yes, "correct": True, "type": "概念／场景"},
                 {"id": "clue-1", "text": no, "correct": False, "type": "边界辨析"}]
        if i % 2: clues.reverse()
        p = {"id": pid, "subject": "cet4", "chapter": chapter_id, "concept": concept, "summary": summary,
             "character": ["anaxa","hyacine","castor","phainon"][i % 4], "speaker": "anaxa",
             "prompt": f"看这句：{en} 我们讨论「{concept}」。别让熟悉的字面代替判断。你会沿哪条线索解释它？",
             "clues": clues, "feedback": {"matched": f"这次判断有依据。{hook}", "redirect": f"先停在概念的边界上。{hook} 再带着这条线索读一遍。"},
             "memoryHook": hook, "example": {"en": en, "zh": zh}, "difficulty": 1,
             "assistant_hint": f"风堇：不必一次记住所有细节。{hook} 先在这个例子里找到它。",
             "classmate": {"character": peer, "text": f"请留意：{summary}。" if peer == "castor" else f"我记成一个小动作：{yes}。下次遇见，先试这一步。"},
             "lesson_method": ["语境观察","联想钩子","边界辨析","迁移检测"],
             "review_status": "approved", "source": {"type":"original","note":"原创微课与练习；参考用户提供课程的板块组织，不是逐字摘录，也非历年真题。"},
             "source_refs": ["original-cet4-v2", "bili-course-2026"],
             "test": {"question": question, "choices": [answer, distractor] if i%2==0 else [distractor,answer], "answer": 0 if i%2==0 else 1, "explanation": hook}}
        if module == "vocabulary": p["quick_meaning"] = summary
        if module == "listening": p["listen_text"] = en
        catalog["points"].append(p); chapter["points"].append(pid)
    chapters.append(chapter)
for i, p in enumerate(old):
    p["quick_meaning"] = re.sub(r"\b(?:n|v|adj|adv)\.\s*", "", p["summary"].split(". ",1)[-1])
    other = re.sub(r"\b(?:n|v|adj|adv)\.\s*", "", old[(i+5) % len(old)]["summary"].split(". ",1)[-1])
    p["test"] = {"question": f"在新一轮回顾中，{p['concept']} 的核心意思是？",
                 "choices": [p["quick_meaning"], other] if i%2==0 else [other,p["quick_meaning"]], "answer": i%2, "explanation": p["memoryHook"]}
    p["prompt"] = f"从「{p['concept']}」开始。{p['example']['en']} 把它放回语境，再判断：哪条线索抓住了动作的本质？"
for ch in chapters:
    ch.update(status="available", knowledgeCount=len(ch["points"]), minutes=len(ch["points"])*2)
    ch["test_points"] = ch["points"]
catalog["version"] = 2
catalog["subjects"][0].update(chapters=chapters, description="词汇、语法、听力、阅读、翻译、写作 · 自由选择板块与进度")
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(f"Published {len(chapters)} chapters, {len(catalog['points'])} original knowledge points.")
