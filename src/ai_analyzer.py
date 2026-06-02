"""
ai_analyzer.py
Gemini API로 수집된 랜딩페이지 / 광고 소재 자동 분류 및 인사이트 추출
모델: gemini-1.5-flash (무료 티어 지원)
"""

import json
import yaml
from datetime import datetime
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("google-genai 미설치. 실행: pip install google-genai")
    exit(1)


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def call_gemini(client, prompt: str, max_tokens: int = 2000) -> str:
    """Gemini API 호출 공통 함수"""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=0.2,
        )
    )
    return response.text


def parse_json(text: str) -> dict:
    """응답에서 JSON 추출"""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return json.loads(text.strip())


def analyze_landing_pages(landing_data: list, client) -> dict:
    """랜딩페이지 데이터 분석"""
    summary_input = []
    for comp in landing_data:
        comp_summary = {"name": comp["name"], "pages": []}
        for page in comp.get("pages", []):
            page_summary = {
                "url": page["url"],
                "title": page.get("page_title", ""),
                "meta": page.get("meta_description", ""),
                "keywords": page.get("detected_keywords", []),
                "headlines": page.get("elements", {}).get("headline", {}).get("found", [])[:3],
                "cta": page.get("elements", {}).get("cta_buttons", {}).get("found", [])[:3],
                "social_proof": page.get("elements", {}).get("social_proof", {}).get("found", [])[:3],
            }
            comp_summary["pages"].append(page_summary)
        summary_input.append(comp_summary)

    prompt = f"""다음은 AI 부트캠프 경쟁사들의 랜딩페이지 분석 데이터입니다.
아래 관점에서 분석하고 JSON으로만 응답해주세요. (```json 블록 포함)

데이터:
{json.dumps(summary_input, ensure_ascii=False, indent=2)}

분석 관점:
1. 각 경쟁사의 핵심 포지셔닝 메시지 (1줄 요약)
2. 주요 소구점 유형 (취업연계/국비/커리큘럼/커뮤니티/가격 등)
3. 타겟 페르소나 추정 (비전공자/전공자/재직자/취업준비생 등)
4. CTA 전략
5. 차별화 포인트
6. 데이톤 대비 공백/기회 포인트

JSON 형식:
```json
{{
  "analyzed_at": "ISO timestamp",
  "competitors": [
    {{
      "name": "기관명",
      "positioning": "핵심 포지셔닝 1줄",
      "appeal_types": ["소구점1", "소구점2"],
      "target_persona": ["타겟1", "타겟2"],
      "cta_strategy": "CTA 전략",
      "differentiators": ["차별점1", "차별점2"],
      "weakness": "약점 또는 공백"
    }}
  ],
  "market_gaps": ["공백1", "공백2"],
  "recommended_positioning": "데이톤 추천 포지셔닝 방향"
}}
```"""

    try:
        text = call_gemini(client, prompt, max_tokens=2000)
        return parse_json(text)
    except Exception as e:
        print(f"  ⚠️  랜딩페이지 분석 실패: {e}")
        return {"error": str(e)}


def analyze_youth_posts(posts: list, client) -> dict:
    """청년 플랫폼 공고 분석 — 광고 소재 패턴 추출"""
    if not posts:
        return {"message": "수집된 플랫폼 공고 없음"}

    by_platform = {}
    for p in posts:
        platform = p.get("platform", "기타")
        by_platform.setdefault(platform, []).append(p)

    summary = []
    for platform, items in by_platform.items():
        titles = [i.get("title", "") for i in items[:30] if i.get("title")]
        summary.append(f"[{platform}] {len(items)}건\n" + "\n".join(f"- {t}" for t in titles))

    prompt = f"""다음은 청년 취업 플랫폼(요즘것들/링커리어/슈퍼루키/새싹)에서 수집한 AI/부트캠프 교육 공고 제목 목록입니다.

{chr(10).join(summary)}

아래를 JSON으로만 분석해주세요. (```json 블록 포함)

```json
{{
  "hook_patterns": ["자주 쓰이는 후킹 문구 패턴1", "패턴2"],
  "platform_orgs": {{"플랫폼명": ["주요기관1", "기관2"]}},
  "title_strategies": ["제목 작성 전략1", "전략2"],
  "dayton_copy_suggestions": ["데이톤 카피 제안1", "제안2", "제안3"]
}}
```"""

    try:
        text = call_gemini(client, prompt, max_tokens=1000)
        return parse_json(text)
    except Exception as e:
        return {"error": str(e)}


def analyze_courses(courses: list, client) -> dict:
    """훈련과정 트렌드 분석"""
    if not courses:
        return {"message": "수집된 과정 데이터 없음"}

    course_names = [
        f"{c.get('traInstNm', c.get('platform', '?'))} — {c.get('trprNm', c.get('title', '?'))}"
        for c in courses[:50]
    ]

    prompt = f"""다음은 수집한 AI 관련 훈련과정 목록입니다.

{chr(10).join(course_names)}

아래를 JSON으로만 분석해주세요. (```json 블록 포함)

```json
{{
  "org_count": {{"기관명": 과정수}},
  "top_keywords": ["키워드1", "키워드2"],
  "market_trend": "현재 시장 주류 방향 요약",
  "empty_positions": ["공백 포지션1", "공백 포지션2"],
  "dayton_opportunities": ["기회1", "기회2"]
}}
```"""

    try:
        text = call_gemini(client, prompt, max_tokens=1000)
        return parse_json(text)
    except Exception as e:
        return {"error": str(e)}


def run(courses: list = None, landing_data: list = None, youth_posts: list = None, config: dict = None) -> dict:
    """Gemini AI 분석 파이프라인 실행"""
    print("\n🤖 [4단계] Gemini AI 분석 시작")
    print("=" * 50)

    if config is None:
        config = load_config()

    api_key = config["api_keys"]["gemini"]

    if api_key == "YOUR_GEMINI_API_KEY":
        print("  ⚠️  GEMINI_API_KEY 미설정 — 데모 분석 결과 반환")
        print("  📌 키 발급: https://aistudio.google.com/app/apikey")
        return _get_demo_analysis()

    # Gemini 클라이언트 초기화
    client = genai.Client(api_key=api_key)

    results = {"analyzed_at": datetime.now().isoformat()}

    if landing_data:
        print("  📊 랜딩페이지 분석 중...")
        results["landing_analysis"] = analyze_landing_pages(landing_data, client)
        print("  ✅ 완료")

    if youth_posts:
        print("  📊 청년 플랫폼 공고 패턴 분석 중...")
        results["youth_platform_analysis"] = analyze_youth_posts(youth_posts, client)
        print("  ✅ 완료")

    if courses:
        print("  📊 훈련과정 트렌드 분석 중...")
        results["course_analysis"] = analyze_courses(courses, client)
        print("  ✅ 완료")

    # 저장
    output_dir = Path(__file__).parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = output_dir / f"{date_str}_ai_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 분석 결과 저장: {output_path}")
    return results


def _get_demo_analysis() -> dict:
    return {
        "analyzed_at": datetime.now().isoformat(),
        "landing_analysis": {
            "competitors": [
                {
                    "name": "패스트캠퍼스",
                    "positioning": "실무 중심 프리미엄 AI 교육",
                    "appeal_types": ["커리큘럼 퀄리티", "강사진"],
                    "target_persona": ["전공자", "재직자"],
                    "cta_strategy": "무료 설명회 신청",
                    "differentiators": ["유명 강사진", "기업 파트너십"],
                    "weakness": "비전공자/입문자 배려 부족"
                },
                {
                    "name": "제로베이스",
                    "positioning": "취업 보장형 집중 부트캠프",
                    "appeal_types": ["취업연계", "포트폴리오"],
                    "target_persona": ["비전공자", "취업준비생"],
                    "cta_strategy": "지원하기 (경쟁 선발)",
                    "differentiators": ["높은 취업률 강조", "기수제 운영"],
                    "weakness": "수강료 부담, 국비지원 약함"
                },
            ],
            "market_gaps": [
                "AI 에이전트 + 휴머노이드 로봇 융합 과정 (없음)",
                "비전공 인문/사회계열 특화 AI 서비스 기획 과정",
                "정부지원 + 취업연계 동시 강조하는 AI 과정"
            ],
            "recommended_positioning": "국비지원 × 비전공자 × AI 에이전트 실무"
        },
        "course_analysis": {
            "top_keywords": ["AI", "인공지능", "데이터", "취업", "비전공자", "에이전트", "생성AI", "LLM"],
            "market_trend": "생성AI/LLM 활용 실무 과정 급증, 비전공자 대상 확대 추세",
            "empty_positions": [
                "AI 에이전트 + 물리 로봇 융합 운영 과정",
                "비전공자 대상 AI 서비스 기획/운영 특화"
            ],
            "dayton_opportunities": [
                "휴머노이드 로봇 운영 특화 (경쟁사 전무)",
                "고용노동부 지원 × 비전공 청년 특화 포지셔닝"
            ]
        }
    }


if __name__ == "__main__":
    run()
