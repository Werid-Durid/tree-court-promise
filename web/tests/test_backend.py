"""在临时 SQLite 中验证关键学习规则、持久化和文件访问边界。"""
import io
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

TEST_RUNTIME = Path(__file__).resolve().parents[1] / ".runtime"
TEST_RUNTIME.mkdir(exist_ok=True)
TEMP = tempfile.TemporaryDirectory(prefix="treecourt-test-", dir=TEST_RUNTIME)
os.environ["TREECOURT_RUNTIME"] = TEMP.name
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from web.backend.app import app, CATALOG, POLICY, repo
from web.backend.domain import initial_state, validate_and_apply


def event(kind, payload):
    return {"event_id": str(uuid4()), "at": datetime.now(timezone.utc).isoformat(), "type": kind, "payload": payload}


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"Authorization": f"Bearer {uuid4()}"}

    def tearDown(self):
        self.client.close()

    def post(self, events):
        r = self.client.post("/api/events", json={"events": events}, headers=self.headers)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def attempt(self, point, match=True):
        clue = next(c for c in point["clues"] if c["correct"] == match)
        return event("attempt", {"point_id": point["id"], "clue_id": clue["id"], "response_ms": 1234, "study_ms": 1500})

    def test_full_chapter_and_idempotence(self):
        events = [self.attempt(p) for p in CATALOG["points"] if p["chapter"] == "cet4-01"]
        events.append(event("chapter_complete", {"chapter_id": "cet4-01"}))
        result = self.post(events)
        self.assertEqual(result["rejected"], [])
        self.assertEqual(result["state"]["completed"], ["cet4-01"])
        self.assertEqual(result["state"]["affection"], {c["id"]: 0 for c in CATALOG["characters"]})
        again = self.post(events)
        self.assertEqual(len(again["events"]), 13)
        self.assertEqual(again["state"], result["state"])
        # 独立仓储连接读取，证明不是仅驻留于 API 进程的内存状态。
        with repo.connect() as db:
            self.assertEqual(len(repo.events(db, self.headers["Authorization"].split()[1])), 13)

    def test_wrong_answer_and_review_never_farm_affection(self):
        p = CATALOG["points"][0]
        result = self.post([self.attempt(p, False), self.attempt(p), self.attempt(p)])
        self.assertEqual(result["state"]["affection"]["anaxa"], 0)
        self.assertEqual(len(result["state"]["attempts"][p["id"]]), 3)
        stats = self.client.get("/api/stats", headers=self.headers).json()
        self.assertEqual(stats["weak_points"], [])

    def test_invalid_events_do_not_corrupt_batch(self):
        invalid = event("attempt", {"point_id": "unknown", "clue_id": "clue-0", "response_ms": 1})
        complete = event("chapter_complete", {"chapter_id": "cet4-01"})
        romance = event("relationship", {"character": "anaxa", "choice": "romance"})
        result = self.post([invalid, complete, romance, self.attempt(CATALOG["points"][0])])
        self.assertEqual(len(result["rejected"]), 3)
        self.assertEqual(result["state"]["affection"]["anaxa"], 0)
        self.assertEqual(result["state"]["relationships"]["anaxa"], "partner")

    def test_friend_and_romance_choices_are_separate_from_learning(self):
        for choice in ("friend", "romance"):
            state = initial_state(CATALOG)
            state["affection"]["anaxa"] = 85
            state["completed"] = ["cet4-01"]
            validate_and_apply(state, event("relationship", {"character": "anaxa", "choice": choice}), CATALOG, POLICY)
            self.assertEqual(state["relationships"]["anaxa"], choice)
            self.assertEqual(state["affection"]["anaxa"], 85)
            self.assertEqual(state["completed"], ["cet4-01"])
            with self.assertRaises(ValueError):
                validate_and_apply(state, event("relationship", {"character": "anaxa", "choice": "romance"}), CATALOG, POLICY)

    def test_profile_isolation_and_authentication(self):
        self.post([self.attempt(CATALOG["points"][0])])
        other = {"Authorization": f"Bearer {uuid4()}"}
        self.assertEqual(self.client.get("/api/user", headers=other).json()["events"], [])
        self.assertEqual(self.client.get("/api/user").status_code, 401)
        self.assertEqual(self.client.post("/api/events", json={"events": []}, headers={**self.headers, "Origin": "https://untrusted.example"}).status_code, 403)

    def test_upload_queue_and_no_automatic_publishing(self):
        r = self.client.post("/api/materials", headers=self.headers, files={"file": ("../../lesson.md", "# 极限\n这是资料。".encode(), "text/markdown")})
        self.assertEqual(r.status_code, 201, r.text)
        material = r.json()
        self.assertEqual(material["name"], "lesson.md")
        self.assertEqual(material["status"], "queued")
        text = self.client.get(f"/api/materials/{material['id']}/text", headers=self.headers)
        self.assertIn("这是资料", text.json()["text"])
        self.assertEqual(self.client.get(f"/api/materials/{material['id']}/text", headers={"Authorization": f"Bearer {uuid4()}"}).status_code, 404)
        self.assertEqual(self.client.post("/api/materials", headers=self.headers, files={"file": ("x.exe", b"data")}).status_code, 415)
        self.assertEqual(self.client.post("/api/materials", headers=self.headers, files={"file": ("fake.pdf", b"not pdf")}).status_code, 400)

    def test_pdf_without_text_requires_ocr(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        buffer = io.BytesIO()
        writer.write(buffer)
        r = self.client.post("/api/materials", headers=self.headers, files={"file": ("scan.pdf", buffer.getvalue(), "application/pdf")})
        self.assertEqual(r.json()["status"], "needs_ocr")

    def test_focus_and_recommendation_placeholder(self):
        self.post([event("focus_session", {"seconds": 180, "interruptions": 2}), self.attempt(CATALOG["points"][0], False)])
        stats = self.client.get("/api/stats", headers=self.headers).json()
        self.assertEqual(stats["weekly_session_average_seconds"], 180)
        self.assertEqual(stats["study_ms"], 181500)
        recommendation = self.client.get("/api/recommendations", headers=self.headers).json()
        self.assertFalse(recommendation["adaptive"])
        self.assertEqual(recommendation["review_ids"], ["cet4-01-01"])

    def test_static_paths_and_stage_do_not_claim_execution(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/docs").status_code, 200)
        self.assertEqual(self.client.get("/data/runtime/treecourt.sqlite3").status_code, 404)
        image = self.client.get("/art/bg_dawn.jpg?asset_name=../data/teaching-policy.json")
        self.assertEqual(image.headers["content-type"], "image/jpeg")
        stage = self.client.post("/api/stage/events", headers=self.headers, json={"type": "dialogue"}).json()
        self.assertFalse(stage["executed"])

    def test_curriculum_has_hooks_and_one_unambiguous_clue(self):
        self.assertEqual(len([c for c in CATALOG["subjects"][0]["chapters"] if not c.get("vocabulary_unit")]), 10)
        self.assertEqual({c["module"] for c in CATALOG["subjects"][0]["chapters"]}, {"词汇","语法","听力","阅读","翻译","写作","核心词汇课堂"})
        self.assertEqual({p["character"] for p in CATALOG["points"]}, {c["id"] for c in CATALOG["characters"]})
        for point in CATALOG["points"]:
            self.assertEqual(sum(c["correct"] for c in point["clues"]), 1)
            self.assertTrue(point["memoryHook"] and point["feedback"]["matched"] and point["feedback"]["redirect"])

    def test_3d_asset_boundary_and_teaching_roles(self):
        self.assertEqual(self.client.get("/models/unknown.glb").status_code,404)
        response=self.client.get("/models/anaxa.glb",headers={"Range":"bytes=0-3"})
        self.assertEqual(response.status_code,206)
        self.assertEqual(response.content,b"glTF")
        for point in CATALOG["points"]:
            self.assertEqual(point["speaker"],"anaxa")
            self.assertEqual(point.get('assistant_speaker','hyacine'),'hyacine')
            self.assertTrue(point['assistant_hint'].strip())
            self.assertIn(point["classmate"]["character"],("castor","phainon"))
        self.assertFalse(self.client.get("/api/voice-status").json()["official_clone"])


if __name__ == "__main__":
    unittest.main()
