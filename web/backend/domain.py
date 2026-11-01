"""学习事件与关系规则。服务器从事件重建状态，不接受客户端直接修改好感。"""
from datetime import datetime, timezone
from uuid import UUID


def initial_state(catalog):
    return {"affection": {c["id"]: 0 for c in catalog["characters"]},
            "relationships": {c["id"]: "partner" for c in catalog["characters"]},
            "attempts": {}, "completed": [], "academic_seen": [],
            "study_ms": 0, "focus_sessions": [], "assessments": {},
            "practice_days": {}, "practice_count": 0, "time_days": {}, "course_attempts": {}, "vocabulary_attempts": {},
            "affection_breakdown": {"tests": 0, "practice": 0, "time": 0},"outings":{},"bond_points":{},"bond_moments":{}}


def update_affection(state, policy):
    """三项贡献独立封顶；章节取历次最高分，避免重复提交测试无限加分。"""
    rules = policy["affection"]
    scores = [max(t["score"] for t in items) for items in state["assessments"].values() if items]
    parts = {
        "tests": min(rules["test_cap"], int(sum(scores) * rules["test_points_per_chapter"] / 100)),
        "practice": min(rules["practice_cap"], state["practice_count"] // rules["attempts_per_point"]),
        "time": min(rules["time_cap"], int(sum(min(v, rules["daily_credited_seconds"]) for v in state["time_days"].values()) // (rules["minutes_per_point"] * 60)))
    }
    state["affection_breakdown"] = parts
    # 四人共同参与同一课堂，因此共享学习贡献；关系选择仍分别保存。
    for char in state["affection"]:
        state["affection"][char] = min(policy["affection_max"], sum(parts.values()) + state.get('bond_points',{}).get(char,0))


def add_time(state, event, milliseconds):
    from datetime import timedelta
    state["study_ms"] += milliseconds
    # 固定北京时间日界，避免浏览器和服务端时区不同造成差异。
    day = datetime.fromisoformat(event["at"].replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=8))).date().isoformat()
    state["time_days"][day] = state["time_days"].get(day, 0) + milliseconds / 1000


def validate_and_apply(state, event, catalog, policy):
    """校验一个事件再变更状态；调用者在事务中保存，event_id 保证幂等。"""
    UUID(event["event_id"])
    date = datetime.fromisoformat(event["at"].replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("事件时间必须包含时区")
    if (date - datetime.now(timezone.utc)).total_seconds() > 86400:
        raise ValueError("事件时间超出范围")
    kind, payload = event["type"], event["payload"]
    points = {p["id"]: p for p in catalog["points"]}
    characters = state["affection"]
    if kind == "attempt":
        point = points[payload["point_id"]]
        clue = next(c for c in point["clues"] if c["id"] == payload["clue_id"])
        if point.get('interaction',{}).get('type') in {'structure_order','template_match','revision_match'}:
            from .skill_interactions import evaluate_interaction
            if evaluate_interaction(point['interaction'],payload.get('interaction_response')) != clue['correct']:
                raise ValueError('结构响应与线索结果不一致')
        response = payload["response_ms"]
        duration = payload.get("study_ms", response)
        if not (isinstance(response, int) and 0 <= response <= 900000
                and isinstance(duration, int) and 0 <= duration <= 900000):
            raise ValueError("学习时长超出范围")
        history = state["attempts"].setdefault(point["id"], [])
        from datetime import timedelta
        day = date.astimezone(timezone(timedelta(hours=8))).date().isoformat()
        bucket_id=point.get("vocabulary_lesson",{}).get("word_id",point["id"])
        key = f'{day}:{bucket_id}'
        count = state["practice_days"].get(key, 0)
        if response >= policy["affection"]["practice_min_response_ms"] and count < policy["affection"]["practice_per_point_per_day"]:
            state["practice_days"][key] = count + 1
            state["practice_count"] += 1
        history.append({"correct": clue["correct"], "clue_id": clue["id"],
                        "response_ms": response, "at": event["at"]})
        add_time(state, event, duration)
        update_affection(state, policy)
    elif kind == "vocabulary_attempt":
        from .vocabulary import grade
        bank=catalog['vocabulary_banks']['cet4'];entry=next(x for x in bank['entries'] if x['id']==payload['word_id'])
        response_ms=payload['response_ms']
        if type(response_ms) is not int or not 0<=response_ms<=900000:raise ValueError('作答时间超出范围')
        mode=payload['mode'];response=payload['response'];correct=grade(entry,mode,response)
        state['vocabulary_attempts'].setdefault(entry['id'],[]).append(dict(mode=mode,response=response,correct=correct,at=event['at'],response_ms=response_ms))
        from datetime import timedelta
        day=date.astimezone(timezone(timedelta(hours=8))).date().isoformat();key=f'{day}:{entry["id"]}';count=state['practice_days'].get(key,0)
        if response_ms>=policy['affection']['practice_min_response_ms'] and count<policy['affection']['practice_per_point_per_day']:
            state['practice_days'][key]=count+1;state['practice_count']+=1
        update_affection(state,policy)
    elif kind == "course_attempt":
        from .course_exercises import evaluate
        point=points[payload['point_id']]
        exercise=next(x for x in point.get('course',{}).get('exercises',[]) if x['id']==payload['exercise_id'])
        correct=evaluate(exercise,payload.get('response'))
        response_ms=payload['response_ms']
        if type(response_ms) is not int or not 0<=response_ms<=900000:raise ValueError('作答时间超出范围')
        key=f'{point["id"]}:{exercise["id"]}'
        state['course_attempts'].setdefault(key,[]).append(dict(response=payload['response'],correct=correct,response_ms=response_ms,at=event['at']))
        from datetime import timedelta
        day=date.astimezone(timezone(timedelta(hours=8))).date().isoformat()
        bucket=f'{day}:{point["id"]}';count=state['practice_days'].get(bucket,0)
        # 与同知识点原有练习共享每日上限，不能通过拆分练习无限增加好感。
        if response_ms>=policy['affection']['practice_min_response_ms'] and count<policy['affection']['practice_per_point_per_day']:
            state['practice_days'][bucket]=count+1;state['practice_count']+=1
        update_affection(state,policy)
    elif kind == "chapter_test":
        chapter = next(ch for s in catalog["subjects"] for ch in s["chapters"] if ch.get("id") == payload["chapter_id"])
        ids, answers = chapter["test_points"], payload["answers"]
        if not isinstance(answers, dict) or set(answers) != set(ids):
            raise ValueError("请提交本章完整检测，不接受客户端自报分数")
        for pid in ids:
            if type(answers[pid]) is not int or not 0 <= answers[pid] < len(points[pid]["test"]["choices"]):
                raise ValueError("检测选项无效")
        correct = sum(answers[pid] == points[pid]["test"]["answer"] for pid in ids)
        score = (correct * 100 + len(ids) // 2) // len(ids)
        state["assessments"].setdefault(chapter["id"], []).append({"score": score, "correct": correct, "total": len(ids), "at": event["at"]})
        if chapter["id"] not in state["completed"]:
            state["completed"].append(chapter["id"])
        update_affection(state, policy)
    elif kind == "study_tick":
        seconds = payload["seconds"]
        if type(seconds) is not int or not 1 <= seconds <= 60:
            raise ValueError("课堂计时片段须为 1–60 秒")
        add_time(state, event, seconds * 1000)
        update_affection(state, policy)
    elif kind == "chapter_complete":
        chapter_id = payload["chapter_id"]
        chapter = next(ch for s in catalog["subjects"] for ch in s["chapters"] if ch.get("id") == chapter_id)
        if not all(state["attempts"].get(pid) for pid in chapter["points"]):
            raise ValueError("请先完成本章全部知识点")
        if chapter_id not in state["completed"]:
            state["completed"].append(chapter_id)
    elif kind == "relationship":
        char, choice = payload["character"], payload["choice"]
        if char not in characters or choice not in ("friend", "romance"):
            raise ValueError("未知关系选项")
        if state["relationships"][char] != "partner":
            raise ValueError("关系已经选择，不重复邀请")
        if characters[char] < policy["romance_threshold"] or not state["completed"]:
            raise ValueError("尚未达到关系剧情条件")
        state["relationships"][char] = choice
    elif kind == "academic_seen":
        char, threshold = payload["character"], payload["threshold"]
        if threshold not in policy["academic_thresholds"] or characters[char] < threshold:
            raise ValueError("学术支线尚未解锁")
        key = f"{char}:{threshold}"
        if key not in state["academic_seen"]:
            state["academic_seen"].append(key)
    elif kind == 'outing_choice':
        from .invitations import apply_outing
        apply_outing(state,payload,catalog)
    elif kind == "focus_session":
        seconds, interruptions = payload["seconds"], payload["interruptions"]
        if not (isinstance(seconds, int) and 1 <= seconds <= 14400
                and isinstance(interruptions, int) and 0 <= interruptions <= 1000):
            raise ValueError("专注记录超出范围")
        state["focus_sessions"].append({"seconds": seconds, "interruptions": interruptions, "at": event["at"]})
        add_time(state, event, seconds * 1000)
        update_affection(state, policy)
    else:
        raise ValueError("未知学习事件")


def replay(events, catalog, policy):
    state = initial_state(catalog)
    for event in events:
        # 仅兼容数据库已接受的旧版关系/回忆。新提交仍走完整阈值校验。
        if event["payload"].get("policy_version", 1) < 2 and event["type"] in ("relationship", "academic_seen"):
            p = event["payload"]
            if event["type"] == "relationship":
                state["relationships"][p["character"]] = p["choice"]
            else:
                key = f'{p["character"]}:{p["threshold"]}'
                if key not in state["academic_seen"]:
                    state["academic_seen"].append(key)
            continue
        validate_and_apply(state, event, catalog, policy)
    return state
