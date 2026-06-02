"""
meta_ads_fetcher.py
Meta 광고 라이브러리 API로 경쟁사 집행 중인 광고 소재 수집
공식 API: https://www.facebook.com/ads/library/api/
"""

import requests
import json
import yaml
from datetime import datetime
from pathlib import Path


def load_competitors():
    path = Path(__file__).parent.parent / "competitors.yaml"
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def fetch_ads_for_page(page_name: str, keywords: list = None) -> list:
    """
    Meta 광고 라이브러리 API 호출 (비로그인 공개 엔드포인트)
    - access_token 없이도 기본 조회 가능
    - 더 많은 데이터는 Meta 개발자 계정 토큰 필요
    """
    base_url = "https://graph.facebook.com/v19.0/ads_archive"

    # 기본 파라미터 (공개 접근)
    params = {
        "ad_type": "ALL",
        "ad_reached_countries": "['KR']",
        "search_page_ids": page_name,
        "fields": ",".join([
            "id",
            "ad_creation_time",
            "ad_creative_bodies",
            "ad_creative_link_captions",
            "ad_creative_link_descriptions",
            "ad_creative_link_titles",
            "ad_snapshot_url",
            "page_name",
            "impressions",
            "spend",
            "currency",
            "publisher_platforms",
        ]),
        "limit": "50",
    }

    if keywords:
        params["search_terms"] = " OR ".join(keywords)

    try:
        resp = requests.get(base_url, params=params, timeout=15)
        data = resp.json()

        if "error" in data:
            # 토큰 없이는 제한됨 → 수동 수집 가이드 반환
            return [{
                "_status": "manual_required",
                "_page": page_name,
                "_message": "Meta API는 액세스 토큰 필요. 아래 URL에서 수동 수집 가능",
                "_manual_url": f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&q={page_name}&search_type=page",
                "_fetched_at": datetime.now().isoformat(),
            }]

        ads = data.get("data", [])
        for ad in ads:
            ad["_page"] = page_name
            ad["_fetched_at"] = datetime.now().isoformat()

        return ads

    except Exception as e:
        print(f"  ⚠️  {page_name} 광고 수집 실패: {e}")
        return []


def fetch_all_competitor_ads(competitors: list, focus_keywords: list) -> dict:
    """전체 경쟁사 광고 수집"""
    result = {}

    for comp in competitors:
        name = comp["name"]
        page_id = comp.get("meta_page_id", "")

        if not page_id:
            print(f"  ⏭️  {name}: meta_page_id 없음, 건너뜀")
            continue

        print(f"  📡 {name} 광고 수집 중...")
        ads = fetch_ads_for_page(page_id, focus_keywords)
        result[name] = ads
        print(f"     → {len(ads)}개 광고 수집")

    return result


def generate_manual_collection_guide(competitors: list) -> str:
    """
    Meta API 토큰 없을 때 수동 수집용 URL 목록 생성
    → 이 URL들을 직접 브라우저에서 열어서 소재 확인
    """
    lines = ["# Meta 광고 라이브러리 수동 수집 가이드\n"]
    lines.append("아래 링크에서 각 경쟁사 광고를 직접 확인하세요.\n")
    lines.append("| 기관 | 광고 라이브러리 링크 |")
    lines.append("|---|---|")

    for comp in competitors:
        name = comp["name"]
        page_id = comp.get("meta_page_id", name)
        url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=KR&q={page_id}&search_type=page"
        lines.append(f"| {name} | [보러가기]({url}) |")

    return "\n".join(lines)


def save_ads(ads_data: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = output_dir / f"{date_str}_meta_ads.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ads_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 저장 완료: {output_path}")
    return output_path


def run(config: dict = None) -> dict:
    """Meta 광고 수집 파이프라인 실행"""
    print("\n📢 [2단계] Meta 광고 라이브러리 수집 시작")
    print("=" * 50)

    comp_data = load_competitors()
    competitors = comp_data["competitors"]
    focus_keywords = comp_data.get("focus_keywords", [])

    # 수동 수집 가이드 항상 생성
    guide = generate_manual_collection_guide(competitors)
    guide_path = Path(__file__).parent.parent / "data" / "raw" / "meta_ads_urls.md"
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text(guide, encoding="utf-8")
    print(f"  📋 수동 수집 URL 가이드 저장: {guide_path}")

    # API 자동 수집 시도
    ads_data = fetch_all_competitor_ads(competitors, focus_keywords)

    output_dir = Path(__file__).parent.parent / "data" / "processed"
    save_ads(ads_data, output_dir)

    # 자동 수집 실패한 것들 요약
    manual_needed = [
        name for name, ads in ads_data.items()
        if ads and ads[0].get("_status") == "manual_required"
    ]
    if manual_needed:
        print(f"\n  ℹ️  아래 기관은 수동 수집 필요:")
        for name in manual_needed:
            print(f"     - {name}")
        print(f"  → {guide_path} 참고")

    return ads_data


if __name__ == "__main__":
    run()
