# -*- coding: utf-8 -*-
"""
IndexNow 자동 색인 요청.
매일 KST 00:00에 GitHub Actions cron으로 실행.

흐름:
1. sitemap.xml fetch → URL 배열
2. day-of-year × 50 = 시작 인덱스 → 50개 슬라이스
3. IndexNow API POST (Bing/Yandex 등에 자동 전파)
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SITE = "wawacenter.kr"
INDEXNOW_KEY = "0ad0f5dc3cc44c6899ea15e76e773372"
KEY_LOCATION = f"https://{SITE}/{INDEXNOW_KEY}.txt"
SITEMAP_URL = f"https://{SITE}/sitemap.xml"
INDEXNOW_API = "https://www.bing.com/indexnow"  # Bing 직접 endpoint (더 안정적)
BATCH_SIZE = 50


def fetch_sitemap_urls() -> list[str]:
    req = urllib.request.Request(SITEMAP_URL, headers={"User-Agent": "wawa-indexnow/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", text)
    return urls


def daily_batch(urls: list[str], batch_size: int = BATCH_SIZE) -> tuple[list[str], int, int]:
    """day-of-year 기준 슬라이스. URL 다 돌면 wrap-around."""
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    day_of_year = now.timetuple().tm_yday  # 1~366
    total = len(urls)
    if total == 0:
        return [], 0, 0
    start = (day_of_year * batch_size) % total
    end = start + batch_size
    if end <= total:
        batch = urls[start:end]
    else:
        # wrap around
        batch = urls[start:] + urls[: end - total]
    return batch, start, day_of_year


def submit_indexnow(urls: list[str]) -> tuple[int, str]:
    body = {
        "host": SITE,
        "key": INDEXNOW_KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        INDEXNOW_API,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (compatible; wawa-indexnow/1.0)",
            "Host": "www.bing.com",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", errors="replace")[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")[:300]
    except Exception as e:
        return -1, str(e)


def main():
    print(f"[{datetime.now()}] IndexNow 자동 색인 요청 시작")
    print(f"  사이트: {SITE}")
    print(f"  Key Location: {KEY_LOCATION}")
    print()

    urls = fetch_sitemap_urls()
    print(f"  sitemap URL: {len(urls)}개")

    batch, start, day = daily_batch(urls)
    print(f"  오늘(day {day}): {start+1}~{start+len(batch)}번째 → {len(batch)}개 제출")
    print()

    for u in batch[:5]:
        print(f"    {u}")
    if len(batch) > 5:
        print(f"    ... 외 {len(batch) - 5}개")
    print()

    if not batch:
        print("  [skip] 제출할 URL 없음")
        return

    status, body = submit_indexnow(batch)
    print(f"  IndexNow API 응답: HTTP {status}")
    if body:
        print(f"  Body: {body}")

    if 200 <= status < 300:
        print(f"\n  ✅ 성공: {len(batch)}개 URL 색인 큐에 등록됨 (Bing/Yandex 등)")
        print("  📌 1~3일 내 색인 진행")
    elif status == 422:
        print("\n  ⚠️ 422: 일부 URL 무효 (정상 — 한국어 URL 인코딩 등)")
    else:
        print(f"\n  ❌ 실패: {status}")
        sys.exit(1)


if __name__ == "__main__":
    main()
