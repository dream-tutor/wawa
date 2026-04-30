# 네이버 서치어드바이저 자동 색인 가이드

> ⚠️  비공식 자동화 — 본인 사이트 등록만 사용하세요.

## 1단계: 쿠키 추출 (1회)

1. 크롬에서 https://searchadvisor.naver.com 로그인
2. F12 (개발자도구) → **Network** 탭 클릭
3. F5로 페이지 새로고침
4. 요청 목록에서 아무 항목 클릭
5. 우측 **Headers** → Request Headers → `Cookie:` 값 전체 복사
   - `NID_AUT=...; NID_SES=...; NID_JKL=...; ...` 같은 긴 문자열

## 2단계: site-id 확인

1. 서치어드바이저에서 **wawacenter.kr** 클릭해서 사이트 페이지 진입
2. URL 보면: `searchadvisor.naver.com/console/board/{site_id}/...`
3. 그 site_id 복사

## 3단계: 실제 API endpoint 확인

`_naver_indexing.py`의 `NAVER_API_TEMPLATE`이 placeholder예요. 실제 endpoint를 찾아야 합니다.

1. 서치어드바이저 → **요청** → **웹페이지 수집** 메뉴
2. F12 → Network 탭 → Filter "request"
3. URL 입력 후 [확인] 클릭
4. Network 탭에서 새로 발생한 POST 요청 확인
5. 그 URL을 `_naver_indexing.py`의 `NAVER_API_TEMPLATE`에 넣기
6. Request Payload 형식도 확인하여 `submit_url` body 형식 맞추기

## 4단계: .env 파일 만들기

프로젝트 root (`C:\Users\goodj\Desktop\AI\와와(wawacenter.kr)`)에 `.env` 파일:

```
NAVER_COOKIE='NID_AUT=...; NID_SES=...; NID_JKL=...; ...전체쿠키복사붙여넣기'
NAVER_SITE_ID='실제-site-id'
```

⚠️  **이 파일은 .gitignore에 이미 포함됨** — 절대 git에 push되지 않음.

## 5단계: 로컬 테스트

```bash
py _naver_indexing.py
```

- 50개 URL 자동 등록
- 성공률 확인
- 실패 많으면 쿠키 갱신 또는 endpoint 재확인

## 6단계: GitHub Actions 자동화 (선택)

매일 자동 실행하려면:

1. GitHub repo → Settings → Secrets and variables → Actions
2. New repository secret 2개:
   - `NAVER_COOKIE`: 1단계에서 복사한 쿠키 값
   - `NAVER_SITE_ID`: 2단계 site-id
3. `.github/workflows/naver-indexing.yml` 활성화

## 유지보수

- **쿠키 만료**: 1~2주마다 다시 로그인 후 쿠키 갱신
- **endpoint 변경**: 네이버가 내부 API 바꾸면 다시 분석 필요
- **봇 감지**: 너무 빨리 연속 요청하면 IP 차단 가능 (스크립트는 2초 대기)

## 대안 (안전한 방법)

자동화 부담스러우면 **수동 5분 작업**:

```bash
py scripts/daily_indexing_queue.py
```

→ 출력된 50개 URL 복사 → 네이버 UI에 한 번에 붙여넣기. 10일이면 전체 완료.
