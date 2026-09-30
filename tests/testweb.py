import hashlib
import http.cookiejar
from contextlib import closing
import os
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    def __init__(self, url):
        self.url = url
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(), urllib.request.HTTPCookieProcessor(self.jar))

    def request(self, path, data=None, cookie=None):
        headers = {'Cookie': 'session=' + cookie} if cookie else {}
        request = urllib.request.Request(self.url + path, data=urllib.parse.urlencode(data).encode() if data is not None else None, headers=headers)
        try:
            response = self.opener.open(request, timeout=4)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.code, response.headers, response.read().decode()

    def login(self, username='demo'):
        response = self.request('/login', {'username': username, 'password': 'practice1234'})
        if response[0] != 303:
            raise AssertionError('login failed: ' + str(response[0]))
        return response

    def csrf(self):
        return re.search(r'name="csrf" value="([^"]+)"', self.request('/')[2])[1]

    def token(self):
        return next(cookie.value for cookie in self.jar if cookie.name == 'session')


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.db = Path(cls.temporary.name) / 'task.db'
        cls.log = open(Path(cls.temporary.name) / 'server.log', 'w+')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            cls.port = sock.getsockname()[1]
        cls.url = f'http://127.0.0.1:{cls.port}'
        cls.start()

    @classmethod
    def start(cls):
        environment = dict(os.environ, TASK_DB_URL='sqlite:///' + str(cls.db))
        cls.process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', str(cls.port)], cwd=Path(__file__).resolve().parent.parent, env=environment, stdout=cls.log, stderr=subprocess.STDOUT)
        client = Client(cls.url)
        for _ in range(150):
            try:
                if client.request('/')[0] == 200:
                    return
            except OSError:
                if cls.process.poll() is not None:
                    break
            time.sleep(0.05)
        cls.process.terminate()
        cls.process.wait(timeout=5)
        cls.log.flush()
        cls.log.seek(0)
        raise RuntimeError(cls.log.read())

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)
        cls.log.close()
        cls.temporary.cleanup()

    def setUp(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('DELETE FROM auth_session')
            db.execute('DELETE FROM task')
            db.execute('DELETE FROM project')
        self.client = Client(self.url)

    def create(self, client=None):
        client = client or self.client
        client.login()
        csrf = client.csrf()
        status, headers, _ = client.request('/app/projects', {'name': '검증 프로젝트', 'csrf': csrf})
        self.assertEqual(status, 303)
        project = headers['Location']
        status, headers, _ = client.request(project + '/tasks', {'title': '첫 할 일', 'description': '내용', 'csrf': csrf})
        self.assertEqual(status, 303)
        return project, headers['Location'], csrf

    def test_anonymous_and_wrong_password(self):
        for path in ['/app/projects', '/app/projects/new', '/app/tasks', '/app/tasks/1', '/app/projects/1/tasks/new']:
            status, headers, _ = self.client.request(path)
            self.assertEqual(status, 303)
            self.assertEqual(headers['Location'], '/login')
        self.assertEqual(self.client.request('/app/projects', {'name': 'blocked'})[1]['Location'], '/login')
        status, _, body = self.client.request('/login', {'username': 'demo', 'password': 'wrong'})
        self.assertEqual(status, 400)
        self.assertIn('올바르지 않습니다', body)

    def test_login_ui_cookie_and_hashed_storage(self):
        self.assertNotIn('로그아웃', self.client.request('/')[2])
        _, headers, _ = self.client.login()
        cookie = headers['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=lax', cookie)
        self.assertIn('demo님 환영합니다', self.client.request('/')[2])
        with closing(sqlite3.connect(self.db)) as db, db:
            password = db.execute("SELECT password_hash FROM user WHERE username='demo'").fetchone()[0]
            stored = db.execute('SELECT token_hash FROM auth_session').fetchone()[0]
        self.assertTrue(password.startswith('pbkdf2_sha256$600000$'))
        self.assertNotEqual(password, 'practice1234')
        self.assertTrue(stored == hashlib.sha256(self.client.token().encode()).hexdigest())

    def test_complete_workflow_relations_and_idempotent_state(self):
        project, task, csrf = self.create()
        self.assertIn('진행 중', self.client.request(task)[2])
        self.assertIn('회원: demo', self.client.request(project)[2])
        self.assertIn('첫 할 일', self.client.request(project)[2])
        self.assertEqual(self.client.request(task + '/edit', {'title': '수정', 'description': '변경', 'csrf': csrf})[0], 303)
        for _ in range(2):
            self.assertEqual(self.client.request(task + '/state', {'completed': 'true', 'csrf': csrf})[0], 303)
        self.assertIn('<dd>완료</dd>', self.client.request(task)[2])
        self.assertEqual(self.client.request(task + '/state', {'completed': 'false', 'csrf': csrf})[0], 303)
        self.assertIn('<dd>진행 중</dd>', self.client.request(task)[2])

    def test_other_member_cannot_read_or_change(self):
        project, task, csrf = self.create()
        other = Client(self.url)
        other.login('guest')
        guest_csrf = other.csrf()
        for path in [project, task, task + '/edit']:
            self.assertEqual(other.request(path)[0], 404)
        self.assertEqual(other.request(task + '/state', {'completed': 'true', 'csrf': guest_csrf})[0], 404)
        self.assertEqual(other.request(project + '/delete', {'csrf': guest_csrf})[0], 404)
        self.assertNotIn('검증 프로젝트', other.request('/app/projects')[2])
        self.assertIn('<dd>진행 중</dd>', self.client.request(task)[2])

    def test_csrf_validation_missing_and_escaped_content(self):
        project, task, csrf = self.create()
        self.assertEqual(self.client.request(task + '/delete', {})[0], 403)
        self.assertEqual(self.client.request(task + '/state', {'completed': 'true', 'csrf': 'wrong'})[0], 403)
        self.assertEqual(self.client.request(task + '/state', {'completed': 'unknown', 'csrf': csrf})[0], 400)
        self.assertEqual(self.client.request('/app/tasks/9999')[0], 404)
        self.assertEqual(self.client.request(project + '/tasks', {'title': ' ', 'description': 'body', 'csrf': csrf})[0], 400)
        self.client.request(task + '/edit', {'title': '<script>bad</script>', 'description': 'safe', 'csrf': csrf})
        self.assertIn('&lt;script&gt;', self.client.request(task)[2])

    def test_logout_revokes_replayed_cookie_and_session_rotation(self):
        self.client.login()
        old = self.client.token()
        self.client.login()
        replay = Client(self.url)
        self.assertEqual(replay.request('/app/projects', cookie=old)[1]['Location'], '/login')
        current = self.client.token()
        self.assertEqual(self.client.request('/logout', {'csrf': self.client.csrf()})[0], 303)
        self.assertEqual(replay.request('/app/projects', cookie=current)[1]['Location'], '/login')

    def test_expired_session_and_project_cascade(self):
        project, task, csrf = self.create()
        self.assertEqual(self.client.request(project + '/delete', {'csrf': csrf})[0], 303)
        with closing(sqlite3.connect(self.db)) as db, db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM task').fetchone()[0], 0)
            db.execute("UPDATE auth_session SET expires_at='2000-01-01 00:00:00.000000'")
        self.assertEqual(self.client.request('/app/projects')[1]['Location'], '/login')

    def test_relations_persist_after_restart(self):
        project, task, csrf = self.create()
        self.process.terminate()
        self.process.wait(timeout=5)
        self.__class__.start()
        self.assertIn('첫 할 일', self.client.request(project)[2])
        self.assertIn('검증 프로젝트', self.client.request(task)[2])


if __name__ == '__main__':
    unittest.main()
