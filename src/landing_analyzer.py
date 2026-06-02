"""
landing_analyzer.py
경쟁사 랜딩페이지 핵심 요소 자동 추출
- 헤드카피 / 서브카피
- CTA 버튼 텍스트
- 사회적 증거 (수치, 후기, 언론)
- 커리큘럼 키워드
- 지원혜택 (국비, 취업연계 등)
"""

import requests
from bs4 import BeautifulSoup
import json
import yaml
from datetime import datetime
from pathlib import Path
import time


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# 분석할 LP 구조 요소 정의
LP_ELEMENTS = {
    "headline": {
        "selectors": ["h1", ".hero-title", ".main-title", "[class*='headline']", "[class*='hero'] h2"],
        "description": "메인 헤드카피"
    },
    "subheadline": {
        "selectors": ["h2", ".sub-title", "[class*='subtitle']", ".hero p", "[class*='hero'] p"],
        "description": "서브카피"
    },
    "cta_buttons": {
        "selectors": ["a.btn", "button", "[class*='cta']", "[class*='apply']", "[class*='register']"],
        "description": "CTA 버튼"
    },
    "social_proof": {
        "selectors": [
            "[class*='stat']", "[class*='number']", "[class*='review']",
            "[class*='testimonial']", "[class*='result']", "[class*='achievement']"
        ],
        "description": "사회적 증거 (수치/후기)"
    },
    "benefits": {
        "selectors": [
            "[class*='benefit']", "[class*='feature']", "[class*='curriculum']",
            "[class*='support']", "ul li", ".point"
        ],
        "description": "혜택/특징"
    },
}


def fetch_landing_page(url: str) -> BeautifulSoup | None:
    """랜딩페이지 HTML 가져오기"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"    ⚠️  페이지 로드 실패 ({url}): {e}")
        return None


def extract_elements(soup: BeautifulSoup, url: str) -> dict:
    """LP에서 핵심 요소 추출"""
    result = {
        "url": url,
        "fetched_at": datetime.now().isoformat(),
        "elements": {}
    }

    for element_name, config in LP_ELEMENTS.items():
        texts = []
        for selector in config["selectors"]:
            try:
                tags = soup.select(selector)[:5]  # 각 selector당 최대 5개
                for tag in tags:
                    text = tag.get_text(strip=True)
                    if text and len(text) > 2 and len(text) < 500:
                        if text not in texts:
                            texts.append(text)
            except Exception:
                continue

        result["elements"][element_name] = {
            "description": config["description"],
            "found": texts[:10]  # 최대 10개
        }

    # 페이지 타이틀
    result["page_title"] = soup.title.string.strip() if soup.title else ""

    # 메타 설명
    meta_desc = soup.find("meta", {"name": "description"})
    result["meta_description"] = meta_desc.get("content", "") if meta_desc else ""

    # 국비/취업 관련 키워드 감지
    full_text = soup.get_text()
    keywords_found = []
    check_keywords = [
        "국비", "무료", "취업연계", "취업률", "수강료 0원", "K-디지털",
        "비전공자", "포트폴리오", "1:1", "멘토링", "수강생 모집",
        "AI 에이전트", "인공지능", "휴머노이드", "로봇"
    ]
    for kw in check_keywords:
        if kw in full_text:
            keywords_found.append(kw)
    result["detected_keywords"] = keywords_found

    return result


def analyze_competitor(comp: dict) -> dict:
    """경쟁사 전체 랜딩페이지 분석"""
    name = comp["name"]
    urls = comp.get("landing_urls", [])
    pages = []

    for url in urls:
        print(f"    🔍 {url}")
        soup = fetch_landing_page(url)
        if soup:
            page_data = extract_elements(soup, url)
            pages.append(page_data)
        time.sleep(1)  # 서버 부담 방지

    return {
        "name": name,
        "analyzed_at": datetime.now().isoformat(),
        "pages": pages
    }


def save_landing_data(data: list, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = output_dir / f"{date_str}_landing_pages.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 저장 완료: {output_path}")
    return output_path


def run(config: dict = None) -> list:
    """랜딩페이지 분석 파이프라인 실행"""
    print("\n🌐 [3단계] 경쟁사 랜딩페이지 분석 시작")
    print("=" * 50)

    comp_data_path = Path(__file__).parent.parent / "competitors.yaml"
    with open(comp_data_path) as f:
        comp_data = yaml.safe_load(f)

    competitors = comp_data["competitors"]
    all_results = []

    for comp in competitors:
        print(f"\n  🏢 {comp['name']} 분석 중...")
        result = analyze_competitor(comp)
        all_results.append(result)

    output_dir = Path(__file__).parent.parent / "data" / "processed"
    save_landing_data(all_results, output_dir)

    print(f"\n✅ 총 {len(all_results)}개 기관 랜딩페이지 분석 완료")
    return all_results


if __name__ == "__main__":
    run()
