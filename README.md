# Surak Festival Server

학교 축제용 포인트·대기열 관리 웹 서버입니다. Flask + SQLite 기반으로 동작하며 Tailwind/Bootstrap 스타일의 간단한 UI를 제공합니다.

## 실행 방법
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --host 0.0.0.0 --port 5000
```

## 주요 기능
- 학생: 학번+PIN 로그인, 보유 포인트/트랜잭션 조회
- 부스 관리자: 대기열 입력/증감, 학생 포인트 증감, 홍보 게시물 등록, 대표 이미지 업로드
- 슈퍼 관리자: 부스/관리자 생성, 전체/개별 포인트 지급, 트랜잭션 조회
- 게스트: 부스 홍보 페이지, 대기열, 랭킹 Top10 조회
- 랭킹 API: `/api/rankings` (5초 폴링 권장)

## 초기 데이터 등록
CSV 헤더 예시: `student_id,name,pin`
```bash
flask --app app load-students students.csv
flask --app app create-super-admin admin_id admin_password
```
