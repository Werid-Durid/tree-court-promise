"""通过 UE 内置 Remote Control 调用固定黑板组件，不接受任意对象／函数路径。"""
import json
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[2]
URL="http://127.0.0.1:30010"


def send_event(event,catalog):
    report_path=ROOT/"ue5/reports/classroom-build.json"
    if not report_path.exists():
        return {"accepted":True,"executed":False,"mode":"web3d","reason":"UE 场景尚未构建"}
    report=json.loads(report_path.read_text(encoding="utf-8"))
    payload=event.get("payload",{})
    point=next((p for p in catalog["points"] if p["id"]==payload.get("point_id")),None)
    try:
        line=point['example']['en'] if point else ''
        if point and point.get('course',{}).get('source',{}).get('kind') in {'textbook','video_course'}:
            line=point['course']['board']
        if point and point.get('vocabulary_lesson'):
            v=point['vocabulary_lesson'];step=payload.get('lesson_step',0)
            line='Recall the meaning: connect a memory anchor.' if step==2 and event.get('type')!='feedback' else v['meaning']
            line+=f' | Unit {v["unit"]} / PDF {v["page"]}'
        with httpx.Client(timeout=1.2,trust_env=False) as client:
            health=client.get(URL+"/remote/info")
            health.raise_for_status()
            if point:
                # 新关卡由原地图另存，演员名称保持一致；只尝试两条受控地图路径。
                for map_name in ('L_StoryClassroom','L_Classroom'):
                    try:
                        for label,value in (("TC_LessonWord",point["concept"]),("TC_LessonLine",line)):
                            component=report["actors"][label]["component"].replace('L_Classroom.L_Classroom',f'{map_name}.{map_name}')
                            response=client.put(URL+"/remote/object/call",json={"objectPath":component,"functionName":"K2_SetText","parameters":{"Value":value},"generateTransaction":False})
                            response.raise_for_status()
                        break
                    except httpx.HTTPStatusError:
                        if map_name=='L_Classroom':raise
            else:
                return {"accepted":True,"executed":False,"connected":True,"mode":"ue5","reason":"当前事件仅更新网页模式，无 UE 动作映射"}
        return {"accepted":True,"executed":True,"connected":True,"mode":"ue5","reason":"UE 黑板已同步"}
    except (httpx.HTTPError,KeyError,ValueError):
        return {"accepted":True,"executed":False,"mode":"web3d","reason":"UE 未运行或未开放 Remote Control；浏览器 3D 可独立学习"}
