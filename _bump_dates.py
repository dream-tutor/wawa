# -*- coding: utf-8 -*-
"""
모든 페이지에 "최종 업데이트" 날짜 표시 + 자동 갱신.

기능:
- 처음 실행: 모든 HTML의 footer 안에 <div class="page-updated"> 삽입
- 이후 실행: data-iso 값과 표시 텍스트를 오늘 날짜로 갱신
- 너무 자주 갱신되면 SEO에 안 좋으니 일주일 이상 지났을 때만 갱신
- sitemap.xml의 모든 <lastmod>도 동시 갱신
"""
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
TODAY_ISO = date.today().isoformat()
TODAY_DISPLAY = TODAY_ISO.replace("-", ".")

# 갱신 주기 (이 일수 이상 지난 페이지만 갱신)
MIN_DAYS = 7

UPDATED_DIV_TEMPLATE = '<div class="page-updated" data-iso="{iso}" style="font-size:11px;color:rgba(255,255,255,0.45);margin-top:8px;">📅 최종 업데이트: {display}</div>'


def find_pages():
    pages = []
    for html in ROOT.rglob("index.html"):
        if any(part.startswith(".") for part in html.relative_to(ROOT).parts):
            continue
        pages.append(html)
    return pages


def update_page(path: Path) -> str:
    """
    Returns:
      'added' — 처음 추가
      'bumped' — 날짜 갱신
      'fresh' — 최근 갱신됐으니 skip
      'no-footer' — footer 못 찾음
    """
    content = path.read_text(encoding="utf-8")
    if "</footer>" not in content:
        return "no-footer"

    # 기존 page-updated가 있는지
    m = re.search(r'<div class="page-updated"\s+data-iso="(\d{4}-\d{2}-\d{2})"[^>]*>[^<]*</div>', content)
    if m:
        # 이미 있음 — 일주일 이상 지났을 때만 갱신
        try:
            last = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            last = date(2000, 1, 1)
        if (date.today() - last).days < MIN_DAYS:
            return "fresh"
        new_div = UPDATED_DIV_TEMPLATE.format(iso=TODAY_ISO, display=TODAY_DISPLAY)
        new_content = content[:m.start()] + new_div + content[m.end():]
        path.write_text(new_content, encoding="utf-8")
        return "bumped"

    # 처음 추가 — </footer> 직전 삽입
    new_div = "  " + UPDATED_DIV_TEMPLATE.format(iso=TODAY_ISO, display=TODAY_DISPLAY) + "\n"
    new_content = content.replace("</footer>", new_div + "</footer>", 1)
    path.write_text(new_content, encoding="utf-8")
    return "added"


def update_sitemap_lastmod():
    """sitemap.xml의 모든 <lastmod>를 오늘 날짜로"""
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.exists():
        return 0
    content = sitemap.read_text(encoding="utf-8")
    new = re.sub(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", f"<lastmod>{TODAY_ISO}</lastmod>", content)
    if new != content:
        sitemap.write_text(new, encoding="utf-8")
        return 1
    return 0


def main():
    pages = find_pages()
    print(f"Found {len(pages)} pages")
    counts = {"added": 0, "bumped": 0, "fresh": 0, "no-footer": 0}
    for path in pages:
        status = update_page(path)
        counts[status] += 1
    for k, v in counts.items():
        print(f"  {k}: {v}")
    if update_sitemap_lastmod():
        print("  sitemap.xml lastmod 갱신됨")
    print(f"  Today: {TODAY_DISPLAY}")


if __name__ == "__main__":
    main()
