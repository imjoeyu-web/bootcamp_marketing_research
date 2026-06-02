"""
hrdnet_fetcher.py
고용24 Open API + 공공데이터포털로 AI 관련 훈련과정 목록 수집
"""

import requests
import json
import yaml
from datetime import datetime
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def fetch_hrdnet_courses(api_key: str, keywords: list, region: str = "") -> list:
    """
    고용24 훈련과정 검색 API 호출
    API 문서: https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do
    """
    base_url = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"
    all_courses = []

    for keyword in keywords:
        params = {
            "authKey": api_key,
            "returnType": "JSON",
            "outType": "1",          # 목록
            "pageNum": "1",
            "pageSize": "100",
            "srchTraArea1": region,  # 지역코드 (빈값=전국, '11'=서울)
            "srchNcs1": "",
            "srchTraGbn": "",        # 훈련구분 (빈값=전체)
            "srchTraStDt": "",       # 훈련시작일 (빈값=전체)
            "srchTraEndDt": "",
            "srchKeco1": "",
            "srchKeco2": "",
            "srchKeco3": "",
            "srchTrprDegr": "1",     # 훈련과정 등급
            "keyword": keyword,
        }

        try:
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            courses = data.get("srchList", [])
            for course in courses:
                course["_search_keyword"] = keyword
                course["_fetched_at"] = datetime.now().isoformat()
            all_courses.extend(courses)
            print(f"  ✅ '{keyword}' 검색: {len(courses)}개 과정 수집")

        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  '{keyword}' 검색 실패: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"  ⚠️  '{keyword}' 응답 파싱 실패: {e}")

    # 중복 제거 (trprId 기준)
    seen = set()
    unique_courses = []
    for c in all_courses:
        key = c.get("trprId", "")
        if key and key not in seen:
            seen.add(key)
            unique_courses.append(c)

    return unique_courses


def fetch_consortium_courses(api_key: str, keywords: list) -> list:
    """
    공공데이터포털 - 국가인적자원개발 컨소시엄 훈련과정 API
    https://www.data.go.kr/data/15037380/openapi.do
    """
    base_url = "https://apis.data.go.kr/B490007/nhrdc/nhrdc-trn-crse-list"
    all_courses = []

    for keyword in keywords:
        params = {
            "serviceKey": api_key,
            "pageNo": "1",
            "numOfRows": "100",
            "keyword": keyword,
            "dataType": "JSON",
        }

        try:
            resp = requests.get(base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(items, dict):
                items = [items]

            for item in items:
                item["_search_keyword"] = keyword
                item["_fetched_at"] = datetime.now().isoformat()
            all_courses.extend(items)
            print(f"  ✅ 컨소시엄 '{keyword}' 검색: {len(items)}개 과정")

        except Exception as e:
            print(f"  ⚠️  컨소시엄 '{keyword}' 검색 실패: {e}")

    return all_courses


def filter_ai_courses(courses: list) -> list:
    """AI/로봇 관련 과정만 필터링 + 경쟁사 매핑"""
    ai_keywords = ["AI", "인공지능", "머신러닝", "딥러닝", "에이전트", "로봇", "휴머노이드", "LLM", "GPT", "데이터"]

    filtered = []
    for c in courses:
        name = c.get("trprNm", "") or c.get("courseName", "") or ""
        desc = c.get("trprDsc", "") or c.get("courseDesc", "") or ""
        combined = (name + desc).upper()

        if any(kw.upper() in combined for kw in ai_keywords):
            filtered.append(c)

    return filtered


def save_courses(courses: list, output_dir: Path) -> Path:
    """수집된 과정 데이터를 JSON으로 저장"""
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = output_dir / f"{date_str}_hrdnet_courses.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    print(f"\n💾 저장 완료: {output_path} ({len(courses)}개 과정)")
    return output_path


def run(config: dict = None) -> list:
    """HRD-Net 수집 파이프라인 실행"""
    print("\n🔍 [1단계] HRD-Net 훈련과정 수집 시작")
    print("=" * 50)

    if config is None:
        config = load_config()

    api_key = config["api_keys"]["hrdnet"]
    data_key = config["api_keys"]["data_go_kr"]
    keywords = config["settings"]["target_keywords"]
    region = config["settings"].get("target_region", "")

    # API 키 미설정 시 데모 모드
    if api_key == "YOUR_HRDNET_API_KEY":
        print("  ⚠️  HRDNET_API_KEY 미설정 — 데모 데이터로 실행합니다")
        print("  📌 키 발급: https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do")
        courses = _get_demo_courses()
    else:
        # 고용24 API
        print(f"\n📡 고용24 API 수집 중... (키워드: {keywords})")
        courses = fetch_hrdnet_courses(api_key, keywords, region)

        # 컨소시엄 API
        if data_key != "YOUR_DATA_GO_KR_KEY":
            print(f"\n📡 컨소시엄 훈련과정 API 수집 중...")
            consortium = fetch_consortium_courses(data_key, keywords)
            courses.extend(consortium)

        # AI 관련 필터링
        courses = filter_ai_courses(courses)

    output_dir = Path(__file__).parent.parent / "data" / "processed"
    save_courses(courses, output_dir)

    print(f"\n✅ 총 {len(courses)}개 AI 관련 과정 수집 완료")
    return courses


def _get_demo_courses() -> list:
    """API 키 없을 때 구조 확인용 데모 데이터"""
    return [
        {
            "trprNm": "AI 에이전트 활용 실무 부트캠프",
            "traInstNm": "패스트캠퍼스",
            "trprDegr": "K-디지털 트레이닝",
            "traStartDate": "2026-07-01",
            "traEndDate": "2026-10-31",
            "trprCst": "0",
            "realTraStDt": "2026-07-01",
            "ncsCd": "20",
            "traArea1Nm": "서울",
            "yardMan": "30",
            "_search_keyword": "AI 에이전트",
            "_fetched_at": datetime.now().isoformat(),
        },
        {
            "trprNm": "비전공자를 위한 인공지능 서비스 기획",
            "traInstNm": "제로베이스",
            "trprDegr": "국민내일배움카드",
            "traStartDate": "2026-07-15",
            "traEndDate": "2026-09-30",
            "trprCst": "0",
            "traArea1Nm": "서울",
            "yardMan": "20",
            "_search_keyword": "인공지능",
            "_fetched_at": datetime.now().isoformat(),
        },
        {
            "trprNm": "생성AI 활용 데이터 분석 과정",
            "traInstNm": "멀티캠퍼스",
            "trprDegr": "K-디지털 트레이닝",
            "traStartDate": "2026-08-01",
            "traEndDate": "2026-11-30",
            "trprCst": "0",
            "traArea1Nm": "서울",
            "yardMan": "25",
            "_search_keyword": "AI",
            "_fetched_at": datetime.now().isoformat(),
        },
    ]


if __name__ == "__main__":
    run()
