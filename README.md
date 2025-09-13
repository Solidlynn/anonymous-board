# 사내 익명 게시판

소규모 팀을 위한 안전하고 자유로운 소통 공간입니다.

## 주요 기능

- **익명 게시판**: 닉네임으로 자유롭게 소통
- **실시간 업데이트**: WebSocket을 통한 실시간 알림
- **반응 시스템**: 게시글과 댓글에 좋아요/싫어요
- **댓글 시스템**: 자유로운 토론과 의견 교환
- **검색 기능**: 제목, 내용, 닉네임으로 검색
- **반응형 디자인**: 모바일과 데스크톱 모두 지원

## 기술 스택

- **Backend**: Django 5.2, Django Channels
- **Frontend**: Bootstrap 5, JavaScript
- **Database**: SQLite (개발), PostgreSQL (배포)
- **Real-time**: WebSocket, Redis
- **배포**: Railway, Heroku, 또는 VPS

## 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd anonymous_board
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. Redis 설치 및 실행
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows (WSL 또는 Docker 사용 권장)
```

### 5. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

### 6. 관리자 계정 생성 (선택사항)
```bash
python manage.py createsuperuser
```

### 7. 개발 서버 실행
```bash
python manage.py runserver
```

브라우저에서 `http://127.0.0.1:8000`으로 접속하세요.

## 배포

### Railway 배포
1. [Railway](https://railway.app)에 가입
2. GitHub 저장소 연결
3. Redis 애드온 추가
4. 환경변수 설정:
   - `SECRET_KEY`: Django 시크릿 키
   - `DEBUG`: False
   - `ALLOWED_HOSTS`: 도메인 설정

### Heroku 배포
1. [Heroku](https://heroku.com)에 가입
2. Heroku CLI 설치
3. Redis 애드온 추가
4. 환경변수 설정

### VPS 배포
1. Ubuntu/Debian 서버 준비
2. Nginx, Gunicorn, Redis 설치
3. SSL 인증서 설정 (Let's Encrypt)
4. 방화벽 설정

## 환경변수

프로덕션 환경에서는 다음 환경변수를 설정하세요:

```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://localhost:6379
```

## 보안 고려사항

- **익명성**: 개인정보는 수집하지 않음
- **세션 관리**: 로컬 스토리지 기반 익명 세션
- **CSRF 보호**: Django 기본 CSRF 토큰 사용
- **XSS 방지**: 템플릿 자동 이스케이프
- **SQL 인젝션 방지**: Django ORM 사용

## 사용법

### 게시글 작성
1. 메인 페이지에서 "글쓰기" 버튼 클릭
2. 제목, 내용, 닉네임(선택사항) 입력
3. "게시글 작성" 버튼 클릭

### 댓글 작성
1. 게시글 상세 페이지로 이동
2. 댓글 입력창에 내용 입력
3. 닉네임 입력 (선택사항)
4. "댓글 작성" 버튼 클릭

### 반응하기
1. 게시글 또는 댓글의 좋아요/싫어요 버튼 클릭
2. 실시간으로 반응 수가 업데이트됨

## 라이선스

MIT License

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 문의

프로젝트에 대한 문의나 버그 리포트는 GitHub Issues를 이용해주세요.
