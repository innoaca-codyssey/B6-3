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
