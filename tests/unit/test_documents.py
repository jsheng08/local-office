import hashlib
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.routers.documents import router
from scripts.make_demo_pack import pdf_bytes
from services.documents.chunk import chunk_paragraphs
from services.documents.extract import extract_pdf, number_paragraphs

ROOT = Path(__file__).resolve().parents[2]


class ExtractionTests(unittest.TestCase):
    def test_generated_pdf_roundtrip(self):
        for version, filename in ((1, '1_SPL_client_brief_v1.pdf'), (2, '2_SPL_client_brief_v2_CHANGED.pdf')):
            with self.subTest(version=version):
                source = (ROOT / 'data/demo' / ('requirements_v%d.md' % version)).read_text()
                expected = [p['id'] for p in chunk_paragraphs(source)]
                for data in (pdf_bytes(source), (ROOT / 'demo_uploads' / filename).read_bytes()):
                    text = extract_pdf(data)
                    self.assertEqual([p['id'] for p in chunk_paragraphs(text)], expected)
                    self.assertIn('Sinar Pantai Logistics', text)

    def test_numbering_and_existing_ids(self):
        self.assertEqual(number_paragraphs('First\nline\n\nSecond'),
                         ('§1. First\nline\n\n§2. Second', ['§1', '§2'], True))
        self.assertEqual(number_paragraphs('§8. Existing')[1:], (['§8'], False))

    def test_pdf_operators_escapes_octal_hex(self):
        stream = b'''BT (\\2471. Hello \\(world\\)) Tj 0 -14 Td [(more) -120 ( text)] TJ T* (line) ' 0 0 (quoted) " <656e64> Tj ET'''
        pdf = b'%PDF-1.4\n1 0 obj\n<< >>\nstream\n' + stream + b'\nendstream\nendobj'
        result = extract_pdf(pdf)
        self.assertIn('§1. Hello (world)\nmore text', result)
        self.assertIn('line\nquotedend', result)

    def test_deflate_limit(self):
        stream = zlib.compress(b' ' * 200)
        pdf = b'%PDF-1.4\n1 0 obj\n<< /Filter /FlateDecode >>\nstream\n' + stream + b'\nendstream\nendobj'
        with patch('services.documents.extract.LIMIT', 100):
            with self.assertRaises(ValueError): extract_pdf(pdf)


class UploadTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI(); app.include_router(router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        patcher = patch('apps.api.routers.documents.record')
        self.audit = patcher.start(); self.addCleanup(patcher.stop)
        patcher = patch('services.security.auth.audit.record')
        patcher.start(); self.addCleanup(patcher.stop)

    def upload(self, name, data, username='aisyah', project='PRJ-SPL'):
        return self.client.post('/api/projects/%s/documents' % project,
                                headers={'X-Demo-User': username}, files={'file': (name, data)})

    def test_text_upload_audit_hash_and_no_content(self):
        data = b'First paragraph\n\nSecond paragraph'
        response = self.upload('brief.txt', data)
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body['paragraph_ids'], ['§1', '§2'])
        self.assertEqual(body['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(body['meta'], {'calls': []})
        detail = self.audit.call_args.kwargs['detail']
        self.assertEqual(set(detail), {'filename', 'sha256', 'size', 'method'})
        self.assertNotIn('First paragraph', str(detail))

    def test_invalid_empty_and_oversize(self):
        for name, data, status in [('bad.txt', b'\xff', 422), ('bad.exe', b'hi', 415),
                                   ('empty.pdf', b'%PDF-1.4\n', 422), ('bad.png', b'wrong', 422)]:
            self.assertEqual(self.upload(name, data).status_code, status)
        with patch('apps.api.routers.documents.MAX_BYTES', 3):
            self.assertEqual(self.upload('big.txt', b'1234').status_code, 413)
        self.assertEqual(self.audit.call_count, 5)

    def test_large_upload_never_spools_to_disk(self):
        files = []
        def spool(*args, **kwargs):
            handle = tempfile.SpooledTemporaryFile(*args, **kwargs)
            files.append(handle)
            return handle
        with patch('starlette.formparsers.SpooledTemporaryFile', side_effect=spool):
            response = self.upload('large.txt', b'a' * (2 * 1024 * 1024))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(files), 1)
        self.assertFalse(files[0]._rolled)
        self.assertTrue(files[0].closed)

    def test_backend_access(self):
        self.assertEqual(self.upload('a.txt', b'hello', username='haziq').status_code, 403)
        self.assertEqual(self.upload('a.txt', b'hello', project='PRJ-KLN').status_code, 403)
        self.assertEqual(self.client.post('/api/projects/PRJ-SPL/documents', files={'file': ('a.txt', b'hi')}).status_code, 401)

    def test_board_project_check(self):
        with patch('apps.api.routers.documents.store.get_board', return_value=[]) as get:
            response = self.client.get('/api/projects/PRJ-SPL/board', headers={'X-Demo-User': 'aisyah'})
            self.assertEqual(response.json(), {'project_id': 'PRJ-SPL', 'board': []})
            denied = self.client.get('/api/projects/PRJ-KLN/board', headers={'X-Demo-User': 'aisyah'})
            self.assertEqual(denied.status_code, 403)
            get.assert_called_once_with('PRJ-SPL')
