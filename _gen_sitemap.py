# -*- coding: utf-8 -*-
"""sitemap.xml 자동 생성 — 모든 페이지 포함

로컬·CI 모두에서 동작 (스크립트 위치 기준).
lastmod은 git log 기반으로 각 파일의 실제 마지막 변경일을 사용
(Naver Yeti 등 봇이 매일 동일 lastmod로 의심하는 문제 해결).
"""
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

# 스크립트 파일 위치 기준 (CI/GitHub Actions에서도 동작)
ROOT = str(Path(__file__).resolve().parent)
BASE = "https://wawacenter.kr"
TODAY = date.today().isoformat()


def _build_git_dates():
    """한 번의 git log 호출로 모든 파일의 마지막 변경일 dict 반환.

    CI 환경(fetch-depth: 1)에서는 일부 결과만 나올 수 있어 fallback 필요.
    """
    try:
        out = subprocess.check_output(
            ["git", "-c", "core.quotepath=false", "log", "--name-only",
             "--pretty=format:%cd", "--date=short", "--diff-filter=AM"],
            cwd=ROOT, encoding="utf-8", errors="replace", stderr=subprocess.DEVNULL,
        )
    except Exception:
        return {}
    dates = {}
    cur_date = None
    for line in out.split("\n"):
        line = line.strip()
        if not line: continue
        # 날짜 형식 (YYYY-MM-DD)
        if len(line) == 10 and line[4] == "-" and line[7] == "-":
            cur_date = line
        elif cur_date and line.endswith("index.html"):
            # 최신 날짜만 유지 (git log는 최신부터 출력)
            if line not in dates:
                dates[line] = cur_date
    return dates


GIT_DATES = _build_git_dates()


def get_lastmod(path):
    """path는 도메인 뒤 경로 (URL 인코딩 포함). git last-commit 날짜 반환."""
    from urllib.parse import unquote
    # URL 인코딩 디코딩 (한글 파일 경로 매칭용)
    rel = unquote(path).lstrip("/")
    file_rel = rel + "index.html" if rel.endswith("/") or rel == "" else rel + "/index.html"
    if file_rel in GIT_DATES:
        return GIT_DATES[file_rel]
    # fallback: 파일 mtime
    full = os.path.join(ROOT, file_rel)
    if os.path.isfile(full):
        return date.fromtimestamp(os.path.getmtime(full)).isoformat()
    return TODAY

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 결과 URL 모음
urls = []

def add(path, priority, changefreq):
    """path는 도메인 뒤 경로 (예: /seoul/mapo/), 끝에 슬래시 포함"""
    # 한글 등은 URL 인코딩
    encoded = quote(path, safe="/")
    urls.append((encoded, priority, changefreq))

# 1. 메인
add("/", "1.0", "weekly")

# 2~5. 시도/시군구/지점/동 페이지를 폴더 구조로 자동 발견
SKIP_DIRS = {".git", ".claude", ".netlify", "assets", "naver-ads", "__pycache__"}

for entry in sorted(os.listdir(ROOT)):
    full = os.path.join(ROOT, entry)
    if not os.path.isdir(full): continue
    if entry in SKIP_DIRS or entry.startswith(".") or entry.startswith("_"):
        continue

    # 시도 폴더 (예: seoul/) - index.html 있을 때만 추가
    region_index = os.path.join(full, "index.html")
    if os.path.isfile(region_index):
        add(f"/{entry}/", "0.8", "weekly")

    # 시군구 폴더는 항상 순회 (index.html 없어도 하위 페이지는 추가)
    for d2 in sorted(os.listdir(full)):
        full2 = os.path.join(full, d2)
        if not os.path.isdir(full2): continue
        d2_index = os.path.join(full2, "index.html")
        if os.path.isfile(d2_index):
            add(f"/{entry}/{d2}/", "0.7", "weekly")

        # 지점/동 페이지는 시군구 index 유무와 무관하게 추가
        for d3 in sorted(os.listdir(full2)):
            full3 = os.path.join(full2, d3)
            if not os.path.isdir(full3): continue
            d3_index = os.path.join(full3, "index.html")

            if d3 == "dong":
                for d4 in sorted(os.listdir(full3)):
                    full4 = os.path.join(full3, d4)
                    if not os.path.isdir(full4): continue
                    d4_index = os.path.join(full4, "index.html")
                    if os.path.isfile(d4_index):
                        add(f"/{entry}/{d2}/dong/{d4}/", "0.6", "monthly")
                    # 동×과목 페이지 (korean/english/math/science/social)
                    for d5 in sorted(os.listdir(full4)):
                        full5 = os.path.join(full4, d5)
                        if not os.path.isdir(full5): continue
                        if d5 not in ("korean", "english", "math", "science", "social"):
                            continue
                        d5_index = os.path.join(full5, "index.html")
                        if os.path.isfile(d5_index):
                            add(f"/{entry}/{d2}/dong/{d4}/{d5}/", "0.5", "monthly")
            elif d3 == "school":
                # 학교 페이지
                for d4 in sorted(os.listdir(full3)):
                    full4 = os.path.join(full3, d4)
                    if not os.path.isdir(full4): continue
                    d4_index = os.path.join(full4, "index.html")
                    if os.path.isfile(d4_index):
                        add(f"/{entry}/{d2}/school/{d4}/", "0.5", "monthly")
            elif os.path.isfile(d3_index):
                add(f"/{entry}/{d2}/{d3}/", "0.7", "weekly")

# XML 생성
lines = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url, prio, freq in urls:
    lines.append("  <url>")
    lines.append(f"    <loc>{BASE}{url}</loc>")
    lines.append(f"    <lastmod>{get_lastmod(url)}</lastmod>")
    lines.append(f"    <changefreq>{freq}</changefreq>")
    lines.append(f"    <priority>{prio}</priority>")
    lines.append("  </url>")
lines.append("</urlset>")

with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

# 통계 출력
counts = {"메인": 0, "시도": 0, "시군구": 0, "지점": 0, "동": 0, "동×과목": 0, "학교": 0}
for u, _, _ in urls:
    parts = [p for p in u.split("/") if p]
    if len(parts) == 0: counts["메인"] += 1
    elif len(parts) == 1: counts["시도"] += 1
    elif len(parts) == 2: counts["시군구"] += 1
    elif len(parts) == 3:
        if parts[2] == "school" or parts[2] == "dong":
            pass  # 이건 잘못된 패스, 무시
        else:
            counts["지점"] += 1
    elif len(parts) == 4 and parts[2] == "dong": counts["동"] += 1
    elif len(parts) == 4 and parts[2] == "school": counts["학교"] += 1
    elif len(parts) == 5 and parts[2] == "dong": counts["동×과목"] += 1

print(f"sitemap.xml 생성 완료: {len(urls)} URL")
for k, v in counts.items():
    print(f"  {k}: {v}")
