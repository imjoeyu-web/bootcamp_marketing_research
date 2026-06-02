"""
ai_analyzer.py
Gemini API로 수집된 공고/랜딩페이지 데이터에서
마케팅/모집 전략 인사이트 추출
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
    with open(config_path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def call_gemini(client, prompt: str, max_tokens: int = 2000) -> str:
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
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return json.loads(text.strip())


def analyze_copy_patterns(posts: list, client) -> dict:
    """
    청년 플랫폼 공고에서 모집 카피/문구 패턴 분석
    - 어떤 표현이 자주 쓰이는가
    - 채널별로 어떻게 다른가
    - 효과적으로 보이는 CTA/후킹 문구는 무엇인가
    """
    if not posts:
        return {"message": "수집된 공고 없음"}

    by_platform = {}
    for p in posts:
        platform = p.get("platform", "기타")
        by_platform.setdefault(platform, []).append(p)

    platform_summary = []
    for platform, items in by_platform.items():
        entries = []
        for i in items[:40]:
            title = i.get("title", "")
            desc = i.get("description", "") or i.get("raw_text", "")[:100]
            entries.append(f"제목: {title}\n설명: {desc}")
        platform_summary.append(f"=== [{platform}] {len(items)}건 ===\n" + "\n---\n".join(entries))

    prompt = f"""다음은 부트캠프/교육과정 모집 공고 데이터입니다. 마케팅/모집 담당자 관점에서 분석해주세요.

{chr(10).join(platform_summary)}

아래 항목을 JSON으로만 응답해주세요. (```json 블록 포함)

```json
{{
  "copy_patterns": {{
    "hook_phrases": ["공고 제목에서 자주 쓰이는 후킹 문구 (예: 무료, 취업보장 등)"],
    "target_expressions": ["타겟을 명시하는 표현 (예: 비전공자 환영, 직장인 추천 등)"],
    "benefit_expressions": ["혜택 강조 표현 (예: 국비지원, 수료 후 취업연계 등)"],
    "urgency_expressions": ["긴박감 조성 표현 (예: 마감임박, 선착순 등)"]
  }},
  "channel_strategy": {{
    "요즘것들": "이 채널에서 주로 쓰이는 톤/전략",
    "링커리어": "이 채널에서 주로 쓰이는 톤/전략",
    "슈퍼루키": "이 채널에서 주로 쓰이는 톤/전략",
    "새싹(SeSAC)": "이 채널에서 주로 쓰이는 톤/전략"
  }},
  "cta_patterns": ["자주 쓰이는 CTA 문구 패턴"],
  "title_formulas": ["효과적으로 보이는 제목 공식 (예: [혜택] + 타겟 + 과정명)"],
  "social_proof_types": ["사회적 증거 활용 방식 (취업률, 수강생 수, 후기 등)"],
  "recruitment_timing": "모집 공고 마감 기간 패턴 (며칠 전 오픈, 얼마나 모집하는지 등)"
}}
```"""

    try:
        text = call_gemini(client, prompt, max_tokens=2000)
        return parse_json(text)
    except Exception as e:
        print(f"  ⚠️  카피 패턴 분석 실패: {e}")
        return {"error": str(e)}


def analyze_landing_marketing(landing_data: list, client) -> dict:
    """
    랜딩페이지에서 마케팅 전략 요소 추출
    - 어떤 구조로 설득하는가
    - CTA를 어디에 어떻게 배치하는가
    - 사회적 증거를 어떻게 활용하는가
    """
    summary_input = []
    for comp in landing_data:
        for page in comp.get("pages", []):
            if not page.get("elements"):
                continue
            summary_input.append({
                "org": comp["name"],
                "url": page["url"],
                "headline": page.get("elements", {}).get("headline", {}).get("found", [])[:3],
                "subheadline": page.get("elements", {}).get("subheadline", {}).get("found", [])[:3],
                "cta": page.get("elements", {}).get("cta_buttons", {}).get("found", [])[:5],
                "social_proof": page.get("elements", {}).get("social_proof", {}).get("found", [])[:5],
                "benefits": page.get("elements", {}).get("benefits", {}).get("found", [])[:5],
                "keywords": page.get("detected_keywords", []),
            })

    if not summary_input:
        return {"message": "수집된 랜딩페이지 데이터 없음"}

    prompt = f"""다음은 부트캠프 교육기관들의 랜딩페이지 마케팅 요소 데이터입니다.
수강생 모집 담당자 관점에서 '어떻게 홍보/모집하고 있는가'를 분석해주세요.

{json.dumps(summary_input, ensure_ascii=False, indent=2)}

JSON으로만 응답해주세요. (```json 블록 포함)

```json
{{
  "headline_patterns": ["헤드카피에서 자주 쓰이는 패턴/공식"],
  "lp_structure": "랜딩페이지 전반적인 설득 구조 (어떤 순서로 정보를 배치하는가)",
  "cta_strategy": {{
    "common_ctas": ["자주 쓰이는 CTA 문구"],
    "placement": "CTA 배치 전략"
  }},
  "social_proof_usage": ["사회적 증거 활용 방식과 구체적 예시"],
  "benefit_framing": ["혜택을 어떻게 표현하는가 (프레이밍 방식)"],
  "keyword_emphasis": ["강조되는 핵심 키워드"],
  "effective_elements": ["모집에 효과적으로 보이는 LP 요소들"]
}}
```"""

    try:
        text = call_gemini(client, prompt, max_tokens=2000)
        return parse_json(text)
    except Exception as e:
        print(f"  ⚠️  랜딩페이지 분석 실패: {e}")
        return {"error": str(e)}


def run(courses: list = None, landing_data: list = None, youth_posts: list = None, config: dict = None) -> dict:
    """마케팅 분석 파이프라인 실행"""
    print("\n🤖 [4단계] Gemini 마케팅 분석 시작")
    print("=" * 50)

    if config is None:
        config = load_config()

    api_key = config["api_keys"]["gemini"]

    if api_key == "YOUR_GEMINI_API_KEY":
        print("  ⚠️  GEMINI_API_KEY 미설정 — 데모 분석 결과 반환")
        print("  📌 키 발급: https://aistudio.google.com/app/apikey")
        return _get_demo_analysis()

    client = genai.Client(api_key=api_key)
    results = {"analyzed_at": datetime.now().isoformat()}

    # 청년 플랫폼 공고 카피 패턴 분석 (핵심)
    if youth_posts:
        print(f"  📊 공고 카피/문구 패턴 분석 중... ({len(youth_posts)}건)")
        results["copy_analysis"] = analyze_copy_patterns(youth_posts, client)
        print("  ✅ 완료")

    # 랜딩페이지 마케팅 전략 분석
    if landing_data:
        print("  📊 랜딩페이지 마케팅 전략 분석 중...")
        results["landing_analysis"] = analyze_landing_marketing(landing_data, client)
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
        "copy_analysis": {
            "copy_patterns": {
                "hook_phrases": ["무료", "국비지원", "취업보장", "100% 취업연계", "선착순 마감"],
                "target_expressions": ["비전공자 환영", "직장인 추천", "문과생 가능", "코딩 몰라도 OK"],
                "benefit_expressions": ["수료 후 취업연계", "포트폴리오 제공", "멘토 1:1 지원", "수강료 0원"],
                "urgency_expressions": ["마감임박", "잔여 OO석", "이번 기수 마지막", "선착순 OO명"]
            },
            "channel_strategy": {
                "요즘것들": "대학생/취준생 타겟. 감성적 카피보다 혜택 중심. 이미지 썸네일 비중 높음",
                "링커리어": "스펙/커리어 관심층. 수료 후 취업 연계 강조. 기업명 노출 효과적",
                "슈퍼루키": "신입/인턴 지원자층. 실무 포트폴리오 강조. 후기 중심",
                "새싹(SeSAC)": "서울시 공공 채널. 무료/국비 강조. 캠퍼스 위치 중요"
            },
            "cta_patterns": ["지금 신청하기", "무료 설명회 신청", "커리큘럼 보기", "상담 신청"],
            "title_formulas": [
                "[무료/국비] + 타겟 + 과정명",
                "타겟 + 혜택 + 과정명",
                "숫자(기간/취업률) + 과정 특징"
            ],
            "social_proof_types": ["취업률 OO%", "수강생 OOO명 돌파", "협력기업 OO개사", "수료생 후기"],
            "recruitment_timing": "개강 4~6주 전 오픈, 모집 기간 2~4주"
        },
        "landing_analysis": {
            "headline_patterns": ["숫자+성과 강조", "타겟 직접 호명", "before/after 구조"],
            "lp_structure": "헤드카피 → 사회적 증거 → 커리큘럼 → 혜택 → CTA → 수강생 후기 → 재CTA",
            "cta_strategy": {
                "common_ctas": ["무료 설명회 신청", "지원하기", "커리큘럼 받기"],
                "placement": "상단 고정 + 섹션마다 반복 배치"
            },
            "social_proof_usage": ["취업률 수치 히어로 섹션 배치", "협력기업 로고 나열", "수강생 후기 카드형"],
            "benefit_framing": ["비용 절감(국비) 먼저", "취업 결과 중심", "과정 특징은 후순위"],
            "keyword_emphasis": ["국비", "무료", "취업", "AI", "실무", "포트폴리오"],
            "effective_elements": ["수강생 후기 실명/사진", "협력기업 로고", "모집 마감 카운트다운"]
        }
    }


if __name__ == "__main__":
    run()
