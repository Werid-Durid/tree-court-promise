"""本地网站入口。启动：python -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8765。"""
import asyncio
import copy
import hashlib
import io
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .domain import replay, validate_and_apply
from .storage import Repository
from .stage import send_event

ROOT = Path(__file__).resolve().parents[2]
CATALOG = json.loads((ROOT / "data/curriculum/catalog.json").read_text(encoding="utf-8"))
CATALOG['characters']=json.loads((ROOT/'characters/profiles.json').read_text(encoding='utf-8'))['characters']
CATALOG['invitations']=json.loads((ROOT/'data/invitations.json').read_text(encoding='utf-8'))
POLICY = json.loads((ROOT / "data/teaching-policy.json").read_text(encoding="utf-8"))
RUNTIME = Path(os.environ.get("TREECOURT_RUNTIME", str(ROOT / "data/runtime")))
repo = Repository(RUNTIME / "treecourt.sqlite3")
def progress_epoch():
    p=RUNTIME/'progress-epoch.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'epoch':'initial'}
app = FastAPI(title="树庭之约 · 本地学习 API", version="0.1.0", docs_url=None, redoc_url=None)

# catalog 单次约 12.8MB，文本压缩通常能降到十分之一左右；小于 1KB 的响应不压。
app.add_middleware(GZipMiddleware, minimum_size=1024)

# 目录与策略在进程启动后不再变化：预序列化一次，并带上 ETag，浏览器二次进入只回 304。
CATALOG_BODY = json.dumps({"catalog": CATALOG, "policy": POLICY}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
CATALOG_ETAG = '"' + hashlib.sha256(CATALOG_BODY).hexdigest()[:16] + '"'


@app.middleware("http")
async def local_boundary(request: Request, call_next):
    """仅允许本机来源，防止其他网站借本地接口写入数据。"""
    host = request.headers.get("host", "").split(":")[0]
    origin = request.headers.get("origin")
    if host not in ("127.0.0.1", "localhost", "testserver"):
        return JSONResponse({"detail": "默认只接受本机连接"}, status_code=403)
    if origin and origin not in ("http://127.0.0.1:8765", "http://localhost:8765", f"http://{request.headers.get('host')}"):
        return JSONResponse({"detail": "来源不受信任"}, status_code=403)
    if request.method not in ('GET','HEAD','OPTIONS') and request.url.path.startswith('/api/'):
        epoch=progress_epoch()['epoch']
        if epoch!='initial' and request.headers.get('X-Treecourt-Epoch')!=epoch:
            return JSONResponse({'detail':'progress_reset','epoch':epoch},status_code=409)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self' blob:; connect-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    if request.url.path.startswith("/api/"):
        # catalog 是只读的静态目录，允许带 ETag 让二次进入只回 304；其余 /api 仍禁止缓存。
        response.headers["Cache-Control"] = "no-cache" if request.url.path == "/api/catalog" else "no-store"
    elif request.url.path.startswith(("/models/", "/art/")):
        # 角色模型和立绘是只读静态资源，且单个模型 30-48MB：不缓存等于每次进教室重下上百 MB。
        response.headers["Cache-Control"] = "public, max-age=604800"
    elif request.url.path.startswith("/static/") and request.url.path.endswith((".js",".css")):
        response.headers["Cache-Control"] = "no-cache"
    return response


def profile(authorization: str = Header(default="")):
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme != "Bearer":
            raise ValueError()
        return str(UUID(token))
    except (ValueError, AttributeError):
        raise HTTPException(401, "缺少本地学习档案标识")


from .exams import install_exams
install_exams(app, ROOT, RUNTIME, profile)
from .network_handout import install_network_handout
install_network_handout(app, ROOT)
from .textbook_sources import install_textbook_sources
install_textbook_sources(app, ROOT)
from .vocabulary import install_vocabulary
install_vocabulary(app, ROOT)


class Event(BaseModel):
    event_id: str
    type: str = Field(max_length=40)
    at: str = Field(max_length=50)
    payload: dict


class EventBatch(BaseModel):
    events: list[Event] = Field(max_length=500)


@app.get("/api/health")
def health():
    return {"ok": True, "version": "0.2.0", "stage": {"connected": False, "mode": "web3d", "reason": "浏览器使用真实 GLB；UE 执行状态以舞台事件回执为准"}}


@app.get("/api/catalog")
def catalog(request: Request):
    headers = {"ETag": CATALOG_ETAG, "Cache-Control": "no-cache"}
    if request.headers.get("if-none-match") == CATALOG_ETAG:
        return Response(status_code=304, headers=headers)
    return Response(content=CATALOG_BODY, media_type="application/json", headers=headers)


from .companion_media import install_companion_media
install_companion_media(app, ROOT)


@app.get('/api/progress-epoch')
def epoch_status():
    return progress_epoch()

@app.get('/outing-assets/{asset}')
def outing_asset(asset:str):
    if asset not in {s+ext for s in ('grove','courtyard','terrace','wheat') for ext in ('.glb','.json')}:
        raise HTTPException(404,'未知邀约场景')
    path=ROOT/'blender/build/outings'/asset
    if not path.is_file():raise HTTPException(404,'邀约场景尚未构建')
    return FileResponse(path)


@app.get("/api/user")
def user(pid: str = Depends(profile)):
    with repo.connect() as db:
        events = repo.events(db, pid)
    return {"events": events, "state": replay(events, CATALOG, POLICY)}


@app.post("/api/events")
def append_events(batch: EventBatch, pid: str = Depends(profile)):
    accepted, rejected = [], []
    with repo.connect() as db:
        # 在同一写事务中校验和入库，防止并发提交重复加分。
        db.execute("BEGIN IMMEDIATE")
        existing = repo.events(db, pid)
        known = {e["event_id"] for e in existing}
        state = replay(existing, CATALOG, POLICY)
        for model in batch.events:
            event = model.model_dump()
            eid = event["event_id"]
            if eid in known:
                accepted.append(eid)
                continue
            candidate = copy.deepcopy(state)
            try:
                if len(json.dumps(event, ensure_ascii=False)) > 8192:
                    raise ValueError("事件过大")
                validate_and_apply(candidate, event, CATALOG, POLICY)
            except (ValueError, KeyError, StopIteration, TypeError, AttributeError) as exc:
                rejected.append({"event_id": eid, "reason": str(exc) or "事件字段无效"})
                continue
            db.execute("INSERT INTO events(profile,event_id,body) VALUES (?,?,?)",
                       (pid, eid, json.dumps(event, ensure_ascii=False)))
            state = candidate
            known.add(eid)
            accepted.append(eid)
        events = repo.events(db, pid)
    return {"accepted": accepted, "rejected": rejected, "events": events, "state": state}


@app.get("/api/recommendations")
def recommendations(pid: str = Depends(profile)):
    """阶段一基线推荐；自适应引擎将在阶段五替换此策略。"""
    with repo.connect() as db:
        state = replay(repo.events(db, pid), CATALOG, POLICY)
    review = [point_id for point_id, items in state["attempts"].items() if not items[-1]["correct"]]
    return {"strategy": "baseline-v1", "adaptive": False, "daily_points": POLICY["default_daily_points"],
            "review_ids": review, "chapter_id": None,
            "message": "先照顾还不熟悉的词，再向前走。" if review else "自行选择板块与进度，也可以先做章节检测。"}


@app.get("/api/stats")
def stats(pid: str = Depends(profile)):
    with repo.connect() as db:
        state = replay(repo.events(db, pid), CATALOG, POLICY)
    now = datetime.now(timezone.utc)
    recent = [s for s in state["focus_sessions"] if datetime.fromisoformat(s["at"].replace("Z", "+00:00")) >= now - timedelta(days=7)]
    return {"study_ms": state["study_ms"], "completed": state["completed"],
            "weak_points": [k for k, v in state["attempts"].items() if not v[-1]["correct"]],
            "focus_sessions": state["focus_sessions"],
            "weekly_session_average_seconds": round(sum(s["seconds"] for s in recent) / len(recent)) if recent else None}


def extract_material(content, suffix):
    if suffix != ".pdf":
        return content.decode("utf-8-sig"), "queued", "文本已提取，等待知识点编译与人工审核。"
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    if len(reader.pages) > 100:
        return "", "needs_split", "超过 100 页，请拆分后重新上传。"
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    if not text.strip():
        return "", "needs_ocr", "未提取到可用文本，可能是扫描件；阶段一不提供 OCR。"
    return text, "queued", "PDF 文本已提取，等待知识点编译与人工审核。"


@app.get("/api/materials")
def materials(pid: str = Depends(profile)):
    return {"materials": repo.materials(pid)}


@app.post("/api/materials", status_code=201)
async def upload(file: UploadFile = File(...), pid: str = Depends(profile)):
    name = (file.filename or "material").replace("\\", "/").split("/")[-1][:180]
    suffix = Path(name).suffix.lower()
    if suffix not in (".pdf", ".txt", ".md"):
        await file.close()
        raise HTTPException(415, "支持 PDF、UTF-8 文本和 Markdown")
    # 逐块检查上限，避免把超大上传一次性读入内存。
    content = bytearray()
    try:
        while chunk := await file.read(65536):
            content.extend(chunk)
            if len(content) > POLICY["max_upload_bytes"]:
                raise HTTPException(413, "资料不能超过 10 MB")
    finally:
        await file.close()
    if not content:
        raise HTTPException(400, "资料是空文件")
    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(400, "文件不是有效的 PDF")
    try:
        text, status, detail = await asyncio.to_thread(extract_material, bytes(content), suffix)
    except UnicodeError:
        raise HTTPException(400, "文本请保存为 UTF-8 编码")
    except Exception:
        text, status, detail = "", "parse_failed", "解析失败，请检查 PDF 是否损坏或加密。"
    if len(text) > 1000000:
        text, status, detail = "", "needs_split", "文本超过 100 万字符，请拆分资料。"
    mid = str(uuid4())
    folder = RUNTIME / "materials" / mid
    folder.mkdir(parents=True)
    (folder / f"source{suffix}").write_bytes(content)
    (folder / "extracted.txt").write_text(text, encoding="utf-8")
    created_at = datetime.now(timezone.utc).isoformat()
    with repo.connect() as db:
        db.execute("INSERT INTO materials VALUES (?,?,?,?,?,?)", (mid, pid, name, status, detail, created_at))
    return {"id": mid, "name": name, "status": status, "detail": detail,
            "created_at": created_at, "characters_extracted": len(text)}


@app.get("/api/materials/{material_id}/text")
def material_text(material_id: str, pid: str = Depends(profile)):
    material = next((m for m in repo.materials(pid) if m["id"] == material_id), None)
    if material is None:
        raise HTTPException(404, "资料不存在")
    return {"material": material, "text": (RUNTIME / "materials" / material_id / "extracted.txt").read_text(encoding="utf-8")}


@app.post("/api/stage/events")
def stage_event(event: dict, pid: str = Depends(profile)):
    if event.get("type") not in ("dialogue", "feedback", "focus", "classroom"):
        raise HTTPException(400, "未知舞台事件")
    return send_event(event,CATALOG)


@app.get("/api/references")
def references():
    path=ROOT/"data/references/sources.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"sources":[]}


@app.get("/api/playlist")
def playlist():
    path = ROOT / "data/playlist.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"title": "树庭自习室 · 歌单", "tracks": []}


@app.get("/api/voice-status")
def voice_status(include_clips:bool=True):
    path=ROOT/"data/voice/manifest.json"
    result=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"official_clone":False,"clips":[]}
    from voice.dialogue import collect_lines
    expected=collect_lines(CATALOG);entries={c['id']:c for c in result.get('clips',[])}
    ready=sum(bool((e:=entries.get(x['id']))) and e.get('synthetic') and e.get('character')==x['character'] and e.get('text_sha256')==x['text_sha256'] and (ROOT/e.get('file','missing')).is_file() for x in expected)
    result['coverage']={'expected':len(expected),'generated':ready,'status':'ready' if ready==len(expected) else 'partial'}
    from .voice_index import generation
    result['generation']=generation(ROOT)
    if not include_clips:result.pop('clips',None)
    return result


@app.get('/api/course-voice-status')
def course_voice_status():
    from .voice_index import all_course_coverage
    return all_course_coverage(ROOT,CATALOG)


@app.get('/api/course-audio/{point_id}')
def course_audio(point_id:str):
    point=next((p for p in CATALOG['points'] if p['id']==point_id),None)
    if not point:raise HTTPException(404,'课程知识点不存在')
    from voice.course_audio import material_segments
    return {'segments':material_segments(point)}


@app.get('/api/vocabulary-voice-status')
def vocabulary_voice_status():
    from .voice_index import vocabulary_coverage
    return vocabulary_coverage(ROOT,CATALOG)


@app.get('/api/voice/resolve')
def resolve_voice(character:str,text_sha256:str):
    from .voice_index import resolve
    return resolve(ROOT,character,text_sha256)


@app.get("/models/{character}.glb")
def model(character: str, motion: str = "classroom"):
    if character not in {c["id"] for c in CATALOG["characters"]}:
        raise HTTPException(404,"未知模型")
    if motion not in {"classroom", "walk", "study"}:raise HTTPException(400,"未知动作")
    if motion == "walk":
        path=ROOT/"blender/walking"/f"{character}.glb"
        if not path.is_file():raise HTTPException(404,"行走动画尚未生成")
        return FileResponse(path,media_type="model/gltf-binary")
    if motion == "study":
        path=ROOT/"blender/study"/f"{character}.glb"
        if not path.is_file():raise HTTPException(404,"自习室动作尚未生成")
        return FileResponse(path,media_type="model/gltf-binary")
    animated=ROOT/"blender/animated"/f"{character}.glb"
    paired=ROOT/'blender/build/classroom-paired'
    if (paired/'published.json').is_file() and (paired/f'characters/{character}.glb').is_file():
        return FileResponse(paired/f'characters/{character}.glb',media_type='model/gltf-binary')
    ready=ROOT/"blender/animation-reports"/f"{character}.json"
    path=animated if animated.is_file() and ready.is_file() else ROOT/"blender/generated"/f"{character}.glb"
    if not path.exists():raise HTTPException(404,"派生模型尚未生成")
    return FileResponse(path,media_type="model/gltf-binary")


@app.get("/api/animation-status")
def animation_status(motion: str = "classroom"):
    """提供动作元数据与原站立身高，坐姿不能按变矮后的包围盒重新放大。"""
    if motion not in {"classroom", "walk", "study"}:
        raise HTTPException(400, "未知动作")
    if motion == "study":
        path = ROOT / "blender/study_motion.json"
        model_dir = ROOT / "blender/study"
        report_dir = ROOT / "blender/study/reports"
    else:
        path = ROOT / "blender/classroom_motion.json"
        model_dir = ROOT / "blender/animated"
        report_dir = ROOT / "blender/animation-reports"
        if motion == "walk":
            model_dir = ROOT / "blender/walking"
            report_dir = ROOT / "blender/walking/reports"
    paired = ROOT / 'blender/build/classroom-paired'
    if motion == 'classroom' and (paired / 'published.json').is_file():
        path = paired / 'motion.json'
    if not path.is_file():
        return {"characters": {}}
    config = json.loads(path.read_text(encoding="utf-8"))
    for cid, spec in config["characters"].items():
        report = report_dir / f"{cid}.json"
        spec["available"] = (model_dir / f"{cid}.glb").is_file() and report.is_file()
        if spec["available"]:
            spec.update(json.loads(report.read_text(encoding="utf-8")))
        if motion == "walk":
            spec.update(position=[-3 + list(config['characters']).index(cid) * 2, 0, 0], yaw=0)
    return config


@app.get("/environment/{asset}")
def classroom_environment(asset: str):
    """环境只公开构建产物白名单，不允许从 URL 读取任意项目文件。"""
    if asset in {"study_room.glb", "study_room_layout.json"}:
        path = ROOT / "blender/build/study-room" / asset
        if not path.is_file():
            raise HTTPException(404, "自习室资源尚未生成")
        return FileResponse(path, media_type="application/json" if asset.endswith('.json') else "model/gltf-binary")
    if asset not in {"story_classroom.glb", "layout.json"}:
        raise HTTPException(404, "未知教室资源")
    # 新海诚风重建教室优先；未生成时回退旧教室，避免网页不可用。
    cine = ROOT / 'blender/build/cinematic-classroom'
    if (cine / asset).is_file():
        return FileResponse(cine / asset, media_type="application/json" if asset.endswith('.json') else "model/gltf-binary", headers={"Cache-Control": "no-store, max-age=0"})
    room=ROOT/'blender/build/classroom-paired'
    path=(room if (room/'published.json').is_file() else ROOT/'blender/classroom')/asset
    if not path.is_file():raise HTTPException(404,"教室资源尚未生成")
    return FileResponse(path,media_type="application/json" if asset.endswith('.json') else "model/gltf-binary")


@app.get("/voice/{clip}.mp3")
def voice(clip: str):
    if not clip.replace("-","").replace("_","").isalnum():
        raise HTTPException(404,"未知语音")
    path=ROOT/"data/voice/generated"/f"{clip}.mp3"
    if not path.is_file():raise HTTPException(404,"该语音尚未生成")
    return FileResponse(path,media_type="audio/mpeg")


@app.get("/voice/{clip}.wav")
def character_voice(clip: str):
    """角色合成音频仅从生成目录读取，保留原 MP3 兼容接口。"""
    if len(clip)>160 or not clip.replace("-","").replace("_","").isascii() or not clip.replace("-","").replace("_","").isalnum():
        raise HTTPException(404,"未知语音")
    path=ROOT/"data/voice/generated"/f"{clip}.wav"
    if not path.is_file():raise HTTPException(404,"该角色台词尚未生成")
    return FileResponse(path,media_type="audio/wav")


@app.get("/")
def index():
    return FileResponse(ROOT / "web/frontend/index.html")


@app.get("/docs", include_in_schema=False)
def api_docs():
    return FileResponse(ROOT / "web/frontend/api.html")


@app.get("/wallpaper", include_in_schema=False)
def wallpaper():
    return FileResponse(ROOT / "web/frontend/study-wallpaper.html")


app.mount("/static", StaticFiles(directory=ROOT / "web/frontend"), name="static")
# 仅公开现有图像目录，绝不把项目根目录或存档目录作为静态站点。
app.mount("/art/portraits", StaticFiles(directory=ROOT / "assets/portraits"), name="portraits")
def background_endpoint(asset_name):
    # 用闭包捕获白名单名称，不将文件路径暴露成可覆盖的查询参数。
    def background():
        return FileResponse(ROOT / "assets" / asset_name)
    return background


for name in ("bg_dawn.jpg", "bg_dusk.jpg", "bg_noon.jpg", "bg_night.jpg"):
    app.add_api_route(f"/art/{name}", background_endpoint(name), methods=["GET"], include_in_schema=False)
