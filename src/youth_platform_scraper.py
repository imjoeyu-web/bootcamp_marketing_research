"""
youth_platform_scraper.py
요즘것들 / 링커리어 / 슈퍼루키 / 새싹(SeSAC) 교육 공고 수집기

Playwright 기반 — JS 렌더링 및 IP 제한 사이트 전용
반드시 로컬에서 실행 (새싹은 서버 IP 차단, 나머지도 JS 렌더링 필요)

설치:
    pip install playwright beautifulsoup4
    playwright install chromium
"""

import json
import time
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("playwright 미설치. 실행: pip install playwright && playwright install chromium")
    exit(1)


# ─────────────────────────────────────────
# 공통 브라우저 설정
# ─────────────────────────────────────────

BROWSER_ARGS = ["--no-sandbox", "--disable-dev-shm-usage"]
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def make_page(browser):
    ctx = browser.new_context(user_agent=USER_AGENT)
    page = ctx.new_page()
    # 이미지/폰트 차단해서 속도 개선
    page.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf}", lambda r: r.abort())
    return page


# ─────────────────────────────────────────
# 1. 요즘것들
# ─────────────────────────────────────────

def scrape_allforyoung(page, max_pages: int = 5) -> list:
    """
    요즘것들 교육 섹션 공고 수집
    https://www.allforyoung.com/posts/education
    """
    results = []
    base_url = "https://www.allforyoung.com/posts/education"

    for page_num in range(1, max_pages + 1):
        url = f"{base_url}?page={page_num}"
        print(f"    📄 요즘것들 {page_num}페이지 수집 중...")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2500)  # JS 렌더링 대기

            # 공고 카드 선택자 탐색 (여러 패턴 시도)
            selectors = [
                "a[href*='/posts/education/']",
                "[class*='PostCard']",
                "[class*='post-card']",
                "[class*='ActivityCard']",
                "ul li a[href*='/posts/']",
            ]

            cards = []
            for sel in selectors:
                cards = page.query_selector_all(sel)
                if cards:
                    break

            if not cards:
                # 마지막 페이지 도달
                print(f"    ⏹  {page_num}페이지 카드 없음 — 수집 종료")
                break

            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    if not href.startswith("http"):
                        href = "https://www.allforyoung.com" + href

                    text = card.inner_text().strip()
                    lines = [l.strip() for l in text.splitlines() if l.strip()]

                    results.append({
                        "platform": "요즘것들",
                        "url": href,
                        "title": lines[0] if lines else "",
                        "description": " | ".join(lines[1:3]) if len(lines) > 1 else "",
                        "raw_text": text[:300],
                        "page": page_num,
                        "fetched_at": datetime.now().isoformat(),
                    })
                except Exception:
                    continue

            print(f"       → {len(cards)}개 공고 수집")
            time.sleep(1)

        except PWTimeout:
            print(f"    ⚠️  {page_num}페이지 타임아웃")
            break

    return results


# ─────────────────────────────────────────
# 2. 링커리어
# ─────────────────────────────────────────

def scrape_linkareer(page, max_pages: int = 5) -> list:
    """
    링커리어 교육/대외활동 공고 수집
    https://linkareer.com/list/activity?category=교육
    """
    results = []
    # 교육 카테고리 필터 URL
    urls_to_try = [
        "https://linkareer.com/list/activity?category=%EA%B5%90%EC%9C%A1",  # 교육
        "https://linkareer.com/list/activity",
    ]

    for page_num in range(1, max_pages + 1):
        url = f"{urls_to_try[0]}&page={page_num}"
        print(f"    📄 링커리어 {page_num}페이지 수집 중...")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)

            selectors = [
                "a[href*='/activity/']",
                "[class*='ActivityCard'] a",
                "[class*='activity-card'] a",
                "[class*='ListItem'] a",
                "ul[class*='list'] li a",
            ]

            cards = []
            for sel in selectors:
                cards = page.query_selector_all(sel)
                if cards:
                    break

            if not cards:
                print(f"    ⏹  {page_num}페이지 카드 없음 — 수집 종료")
                break

            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    if not href.startswith("http"):
                        href = "https://linkareer.com" + href
                    if "/activity/" not in href:
                        continue

                    text = card.inner_text().strip()
                    lines = [l.strip() for l in text.splitlines() if l.strip()]

                    # 링커리어 카드 구조: 제목 / 기관명 / 마감일 순서
                    results.append({
                        "platform": "링커리어",
                        "url": href,
                        "title": lines[0] if lines else "",
                        "org": lines[1] if len(lines) > 1 else "",
                        "deadline": next((l for l in lines if "~" in l or "마감" in l), ""),
                        "raw_text": text[:300],
                        "page": page_num,
                        "fetched_at": datetime.now().isoformat(),
                    })
                except Exception:
                    continue

            print(f"       → {len(cards)}개 공고 수집")
            time.sleep(1.5)

        except PWTimeout:
            print(f"    ⚠️  {page_num}페이지 타임아웃")
            break

    return results


# ─────────────────────────────────────────
# 3. 슈퍼루키
# ─────────────────────────────────────────

def scrape_superookie(page, max_pages: int = 5) -> list:
    """
    슈퍼루키 커리어 교육 공고 수집
    https://www.superookie.com/seminars
    """
    results = []

    for page_num in range(1, max_pages + 1):
        url = f"https://www.superookie.com/seminars?page={page_num}"
        print(f"    📄 슈퍼루키 {page_num}페이지 수집 중...")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2500)

            selectors = [
                "a[href*='/seminars/']",
                "[class*='seminar'] a",
                "[class*='SeminarCard'] a",
                "[class*='edu'] a",
                ".seminar-list li a",
            ]

            cards = []
            for sel in selectors:
                cards = page.query_selector_all(sel)
                if cards:
                    break

            if not cards:
                print(f"    ⏹  {page_num}페이지 카드 없음 — 수집 종료")
                break

            seen_hrefs = set()
            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    if not href.startswith("http"):
                        href = "https://www.superookie.com" + href
                    if "/seminars/" not in href or href in seen_hrefs:
                        continue
                    seen_hrefs.add(href)

                    text = card.inner_text().strip()
                    lines = [l.strip() for l in text.splitlines() if l.strip()]

                    results.append({
                        "platform": "슈퍼루키",
                        "url": href,
                        "title": lines[0] if lines else "",
                        "description": " | ".join(lines[1:3]) if len(lines) > 1 else "",
                        "raw_text": text[:300],
                        "page": page_num,
                        "fetched_at": datetime.now().isoformat(),
                    })
                except Exception:
                    continue

            print(f"       → {len(seen_hrefs)}개 공고 수집")
            time.sleep(1)

        except PWTimeout:
            print(f"    ⚠️  {page_num}페이지 타임아웃")
            break

    return results


# ─────────────────────────────────────────
# 공고 상세 페이지 수집 (선택)
# ─────────────────────────────────────────

def scrape_detail(page, item: dict) -> dict:
    """
    공고 상세페이지에서 본문 텍스트 추가 수집
    AI 분석 인풋 품질 향상용
    """
    try:
        page.goto(item["url"], wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)

        # 본문 영역 탐색
        body_selectors = [
            "article", "main", "[class*='content']",
            "[class*='detail']", "[class*='body']",
        ]
        body_text = ""
        for sel in body_selectors:
            el = page.query_selector(sel)
            if el:
                body_text = el.inner_text()[:1000]
                break

        item["detail_text"] = body_text
        item["detail_fetched"] = True

    except Exception as e:
        item["detail_text"] = ""
        item["detail_fetched"] = False

    return item


# ─────────────────────────────────────────
# 4. 새싹 (SeSAC)
# ─────────────────────────────────────────

def scrape_sesac(page, max_pages: int = 5) -> list:
    """
    새싹 오프라인 과정 목록 수집
    https://sesac.seoul.kr/sesac/course/offline/courseList.do
    - 로컬 브라우저에서 실행 시 정상 접근 가능
    - 서버 IP에서는 방화벽 차단 → 반드시 로컬 실행
    """
    results = []
    base_url = "https://sesac.seoul.kr/sesac/course/offline/courseList.do"

    for page_num in range(1, max_pages + 1):
        url = f"{base_url}?pageIndex={page_num}&searchRcrtStts=ing"  # 모집중만
        print(f"    📄 새싹 {page_num}페이지 수집 중...")

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)

            # 새싹 과정 카드 선택자
            selectors = [
                "a[href*='courseDetail']",
                "[class*='course'] a",
                "[class*='card'] a",
                "ul.list li a",
                ".course-list li a",
            ]

            cards = []
            for sel in selectors:
                cards = page.query_selector_all(sel)
                if cards:
                    break

            if not cards:
                print(f"    ⏹  {page_num}페이지 카드 없음 — 수집 종료")
                break

            seen = set()
            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    if not href.startswith("http"):
                        href = "https://sesac.seoul.kr" + href
                    if "courseDetail" not in href or href in seen:
                        continue
                    seen.add(href)

                    # crsSn 파라미터 추출
                    crs_sn = href.split("crsSn=")[-1].split("&")[0] if "crsSn=" in href else ""

                    text = card.inner_text().strip()
                    lines = [l.strip() for l in text.splitlines() if l.strip()]

                    # 새싹 카드 구조 파싱: 상태 / 캠퍼스 / 분야 / 모집기간
                    status = next((l for l in lines if "모집" in l), "")
                    campus = next((l for l in lines if "캠퍼스" in l or any(
                        gu in l for gu in ["강남","강동","강북","강서","관악","광진","구로","금천",
                                           "노원","도봉","동대문","동작","마포","서대문","서초",
                                           "성동","성북","송파","양천","영등포","용산","은평","종로","중구","중랑"]
                    )), "")
                    deadline = next((l for l in lines if "~" in l or "기간" in l), "")

                    results.append({
                        "platform": "새싹(SeSAC)",
                        "url": href,
                        "crs_sn": crs_sn,
                        "title": lines[0] if lines else "",
                        "status": status,
                        "campus": campus,
                        "deadline": deadline,
                        "raw_text": text[:300],
                        "page": page_num,
                        "fetched_at": datetime.now().isoformat(),
                    })
                except Exception:
                    continue

            print(f"       → {len(seen)}개 과정 수집")
            time.sleep(1)

        except PWTimeout:
            print(f"    ⚠️  {page_num}페이지 타임아웃")
            break

    return results


def scrape_sesac_detail(page, item: dict) -> dict:
    """
    새싹 과정 상세 페이지 수집
    - 과정명, 교육기관, 모집인원, 교육기간, 커리큘럼 요약
    """
    try:
        page.goto(item["url"], wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)

        # 상세 정보 블록 파싱
        detail = {}

        # 과정명
        for sel in ["h2", "h3", ".course-name", "[class*='title']"]:
            el = page.query_selector(sel)
            if el:
                detail["course_name"] = el.inner_text(strip=True)
                break

        # 주요 정보 (교육기관, 모집인원, 교육기간 등)
        info_text = ""
        for sel in ["dl", ".course-info", "[class*='info']", "table"]:
            els = page.query_selector_all(sel)
            for el in els[:3]:
                info_text += el.inner_text() + "\n"

        detail["info_text"] = info_text[:500]

        # 커리큘럼/소개
        for sel in [".curriculum", "[class*='curriculum']", ".intro", "[class*='intro']", "main p"]:
            el = page.query_selector(sel)
            if el:
                detail["curriculum_summary"] = el.inner_text()[:300]
                break

        item.update(detail)
        item["detail_fetched"] = True

    except Exception as e:
        item["detail_fetched"] = False

    return item


# ─────────────────────────────────────────
# 키워드 필터링
# ─────────────────────────────────────────

AI_KEYWORDS = [
    "AI", "인공지능", "머신러닝", "딥러닝", "에이전트", "LLM", "GPT",
    "생성AI", "데이터", "로봇", "휴머노이드", "파이썬", "Python",
    "부트캠프", "국비", "취업", "코딩", "개발",
]

def filter_relevant(items: list, keywords: list = None) -> tuple[list, list]:
    """AI/교육 관련 공고 필터링. (관련, 비관련) 튜플 반환"""
    kws = keywords or AI_KEYWORDS
    relevant, others = [], []
    for item in items:
        text = (item.get("title", "") + item.get("description", "") + item.get("raw_text", "")).upper()
        if any(k.upper() in text for k in kws):
            relevant.append(item)
        else:
            others.append(item)
    return relevant, others


# ─────────────────────────────────────────
# 저장
# ─────────────────────────────────────────

def save(data: list, label: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    path = output_dir / f"{date_str}_{label}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 저장: {path} ({len(data)}건)")
    return path


# ─────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────

def run(max_pages: int = 3, fetch_details: bool = False) -> list:
    """
    네 플랫폼 전체 수집 실행
    요즘것들 / 링커리어 / 슈퍼루키 / 새싹(SeSAC)

    Args:
        max_pages: 플랫폼당 최대 수집 페이지 수
        fetch_details: True면 공고 상세페이지도 추가 수집 (느림)

    Note:
        새싹은 로컬 IP에서만 접근 가능 (서버 방화벽).
        반드시 로컬에서 실행할 것.
    """
    print("\n🎯 [청년 플랫폼] 교육 공고 수집 시작")
    print("=" * 50)

    output_dir = Path(__file__).parent.parent / "data" / "processed"
    all_results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=BROWSER_ARGS,
        )

        # ── 요즘것들 ──
        print("\n  🟠 요즘것들 수집 시작")
        p = make_page(browser)
        afy = scrape_allforyoung(p, max_pages=max_pages)
        p.close()
        afy_rel, _ = filter_relevant(afy)
        print(f"  → 전체 {len(afy)}건 중 AI/교육 관련 {len(afy_rel)}건")
        all_results.extend(afy_rel)

        # ── 링커리어 ──
        print("\n  🔵 링커리어 수집 시작")
        p = make_page(browser)
        lk = scrape_linkareer(p, max_pages=max_pages)
        p.close()
        lk_rel, _ = filter_relevant(lk)
        print(f"  → 전체 {len(lk)}건 중 AI/교육 관련 {len(lk_rel)}건")
        all_results.extend(lk_rel)

        # ── 슈퍼루키 ──
        print("\n  🟢 슈퍼루키 수집 시작")
        p = make_page(browser)
        sr = scrape_superookie(p, max_pages=max_pages)
        p.close()
        sr_rel, _ = filter_relevant(sr)
        print(f"  → 전체 {len(sr)}건 중 AI/교육 관련 {len(sr_rel)}건")
        all_results.extend(sr_rel)

        # ── 새싹 ──
        print("\n  🌱 새싹(SeSAC) 수집 시작")
        p = make_page(browser)
        sesac = scrape_sesac(p, max_pages=max_pages)
        p.close()
        # 새싹은 모집중 과정만 가져오므로 전체 저장 (필터 없이)
        print(f"  → {len(sesac)}개 과정 수집")
        all_results.extend(sesac)

        # ── 상세 수집 (옵션) ──
        if fetch_details and all_results:
            print(f"\n  🔍 상세 페이지 추가 수집 ({len(all_results)}건)...")
            p = make_page(browser)
            updated = []
            for item in all_results:
                if item.get("platform") == "새싹(SeSAC)":
                    updated.append(scrape_sesac_detail(p, item))
                else:
                    updated.append(scrape_detail(p, item))
            all_results = updated
            p.close()

        browser.close()

    # 저장
    save(all_results, "youth_platform_posts", output_dir)

    print(f"\n✅ 총 {len(all_results)}건 수집 완료")
    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=3, help="플랫폼당 최대 페이지 수 (기본 3)")
    parser.add_argument("--details", action="store_true", help="상세 페이지 추가 수집")
    args = parser.parse_args()
    run(max_pages=args.pages, fetch_details=args.details)
