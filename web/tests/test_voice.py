"""验证角色音频接口、旧 MP3 兼容与路径边界，不加载推理模型。"""
import os,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
TEST_ROOT=Path(__file__).resolve().parents[1]/'.runtime'
TEST_ROOT.mkdir(exist_ok=True)
TEST_RUNTIME=tempfile.TemporaryDirectory(prefix='treecourt-voice-test-',dir=TEST_ROOT)
os.environ['TREECOURT_RUNTIME']=TEST_RUNTIME.name
from fastapi.testclient import TestClient
from web.backend import app as module
from voice.dialogue import collect_lines,text_hash

class VoiceTests(unittest.TestCase):
    def test_progress_reports_stopped_heartbeat_honestly(self):
        from web.backend.voice_index import generation
        with tempfile.TemporaryDirectory(prefix='treecourt-progress-',dir=TEST_ROOT) as folder:
            root=Path(folder);out=root/'data/voice/research';out.mkdir(parents=True)
            (out/'vocabulary-progress.json').write_text(json.dumps(dict(status='running',total_jobs=100,completed_jobs=7,updated_at='2020-01-01T00:00:00+00:00')),encoding='utf-8')
            result=generation(root);self.assertEqual(result['status'],'interrupted');self.assertEqual(result['completed_jobs'],7)

    def test_book_pronunciations_are_english_and_use_teacher_voice(self):
        lines=[x for x in collect_lines(module.CATALOG) if x['id'].startswith('pronounce-cet4core-')]
        self.assertEqual(len(lines),2327)
        for line in lines:
            self.assertEqual(line['language'],'English');self.assertEqual(line['character'],'anaxa')
            self.assertNotRegex(line['text'],r'[()/]')

    def test_resolver_rejects_wrong_character_stale_hash_and_missing_audio(self):
        from web.backend.voice_index import resolve
        with tempfile.TemporaryDirectory(prefix='treecourt-resolve-',dir=TEST_ROOT) as folder:
            root=Path(folder);out=root/'data/voice/generated';out.mkdir(parents=True)
            audio=out/'word-123.wav';audio.write_bytes(b'RIFF'+b'\0'*100)
            text='space';sha=text_hash(text)
            data={'clips':[dict(id='pronounce-test',character='anaxa',text=text,text_sha256=sha,synthetic=True,status='generated',file='data/voice/generated/word-123.wav',url='/voice/word-123.wav')]}
            (root/'data/voice/manifest.json').write_text(json.dumps(data),encoding='utf-8')
            self.assertTrue(resolve(root,'anaxa',sha)['ready'])
            self.assertFalse(resolve(root,'hyacine',sha)['ready'])
            self.assertFalse(resolve(root,'anaxa',text_hash('spaces'))['ready'])
            audio.unlink();self.assertFalse(resolve(root,'anaxa',sha)['ready'])

    def test_catalog_lines_have_distinct_ids_and_four_speakers(self):
        lines=collect_lines(module.CATALOG)
        self.assertEqual(len(lines),len({x['id'] for x in lines}))
        self.assertEqual({x['character'] for x in lines},{'anaxa','hyacine','castor','phainon'})
        self.assertTrue(any(x['id'].startswith('feedback-') for x in lines))
        self.assertTrue(all(x['text_sha256']==text_hash(x['text']) for x in lines))

    def test_wav_mp3_and_missing_file(self):
        with tempfile.TemporaryDirectory(prefix='treecourt-audio-',dir=TEST_ROOT) as folder:
            root=Path(folder);out=root/'data/voice/generated';out.mkdir(parents=True)
            (out/'intro-anaxa-123.wav').write_bytes(b'RIFF'+b'\0'*100)
            (out/'intro-anaxa.mp3').write_bytes(b'ID3'+b'\0'*100)
            with patch.object(module,'ROOT',root),TestClient(module.app) as client:
                r=client.get('/voice/intro-anaxa-123.wav')
                self.assertEqual(r.status_code,200);self.assertEqual(r.headers['content-type'],'audio/wav')
                self.assertEqual(client.get('/voice/intro-anaxa.mp3').status_code,200)
                self.assertEqual(client.get('/voice/missing.wav').status_code,404)
                self.assertEqual(client.get('/voice/bad%5Cpath.wav').status_code,404)
                self.assertEqual(client.get('/voice/'+('a'*161)+'.wav').status_code,404)
if __name__=='__main__':unittest.main()
