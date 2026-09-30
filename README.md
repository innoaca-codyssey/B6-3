# B6-3: 로그인이 되고 회원끼리 연결되는 웹 서비스 만들기

B6-2의 할 일 앱을 확장해 회원별 프로젝트와 할 일을 관리합니다. 로그인한 회원은 프로젝트 안에 할 일을 작성하고 완료/진행 중 상태를 변경합니다.

## 실행 방법

Python 3.10 이상을 사용합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8001
```

http://localhost:8001 을 엽니다. DB 파일은 프로젝트 루트의 task.db입니다. B6-2의 DB를 그대로 복사하지 않고 새 관계 스키마로 생성합니다.

## 테스트 계정

| ID | PW |
|---|---|
| demo | practice1234 |
| guest | practice1234 |

처음 실행할 때 테스트 회원을 DB에 생성합니다. 비밀번호는 무작위 salt를 사용하는 PBKDF2 해시로 저장합니다. 이 계정은 로컬 실습용입니다.

## 인증 방식

서버 DB 세션 방식을 사용합니다. 로그인 성공 시 무작위 세션 토큰을 HttpOnly, SameSite=Lax 쿠키에 발급하고 서버에는 토큰의 SHA-256 해시와 만료 시각을 저장합니다. 로그아웃하면 서버의 세션을 삭제합니다. 외부 서비스나 토큰 발급 계정은 필요하지 않습니다.

## 실행 환경

```bash
$ python3 --version
Python 3.14.7
```

B6-2의 소스와 고정된 패키지 버전을 기반으로 별도 제출 저장소에서 확장합니다.

## 패키지 설치

```bash
Resolved 18 packages in 58ms
Installed 18 packages in 76ms
 + annotated-doc==0.0.5
 + annotated-types==0.8.0
 + anyio==4.15.1
 + click==8.5.0
 + fastapi==0.142.2
 + h11==0.16.0
 + idna==3.20
 + jinja2==3.1.6
 + markupsafe==3.0.3
 + opentelemetry-api==1.45.0
 + pydantic==2.13.5
 + pydantic-core==2.46.5
 + python-multipart==0.0.32
 + sqlalchemy==2.1.1
 + starlette==1.7.0
 + typing-extensions==4.16.0
 + typing-inspection==0.4.4
 + uvicorn==0.54.0
```

B6-2와 같은 고정 버전의 허용 패키지를 설치했습니다. 인증 토큰 발급과 비밀번호 해시는 Python 표준 라이브러리를 사용합니다.

## 인증과 관계 검증

```bash
$ .venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -v
test_anonymous_and_wrong_password (testweb.WebTests.test_anonymous_and_wrong_password) ... ok
test_complete_workflow_relations_and_idempotent_state (testweb.WebTests.test_complete_workflow_relations_and_idempotent_state) ... ok
test_csrf_validation_missing_and_escaped_content (testweb.WebTests.test_csrf_validation_missing_and_escaped_content) ... ok
test_expired_session_and_project_cascade (testweb.WebTests.test_expired_session_and_project_cascade) ... ok
test_login_ui_cookie_and_hashed_storage (testweb.WebTests.test_login_ui_cookie_and_hashed_storage) ... ok
test_logout_revokes_replayed_cookie_and_session_rotation (testweb.WebTests.test_logout_revokes_replayed_cookie_and_session_rotation) ... ok
test_other_member_cannot_read_or_change (testweb.WebTests.test_other_member_cannot_read_or_change) ... ok
test_relations_persist_after_restart (testweb.WebTests.test_relations_persist_after_restart) ... ok

----------------------------------------------------------------------
Ran 8 tests in 2.967s

OK
```

비로그인 차단, 로그인 실패와 UI, 세션 해시 저장, 소유권, CSRF, 상태 변경, 세션 회전과 로그아웃 폐기, 만료, cascade 삭제와 서버 재시작 후 관계 저장을 검사했습니다. 세션 쿠키 값은 출력하지 않습니다.
