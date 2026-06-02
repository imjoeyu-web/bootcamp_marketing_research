"""
report_generator.py
수집/분석 데이터를 Markdown 주간 리포트로 생성하고 GitHub에 push
"""

import json
import yaml
import base64
import requests
from datetime import datetime
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def generate_report(courses: list, ads_data: dict, youth_posts: list, analysis: dict) -> str:
    """Markdown 리포트 생성"""
    now = datetime.now()
    date_str = now.strftime("%Y년 %m월 %d일")
    week_str = now.strftime("W%W")

    lines = [
        f"# 📊 부트캠프 경쟁사 모집/마케팅 동향 리포트",
        f"",
        f"> 생성일: {date_str} | 주차: {week_str}",
        f"> 자동 생성 by bootcamp-intelligence pipeline",
        f"",
        f"---",
        f"",
        f"## 목차",
        f"1. [시장 현황 요약](#1-시장-현황-요약)",
        f"2. [HRD-Net 훈련과정 동향](#2-hrd-net-훈련과정-동향)",
        f"3. [경쟁사 랜딩페이지 분석](#3-경쟁사-랜딩페이지-분석)",
        f"4. [청년 플랫폼 교육 공고 동향](#4-청년-플랫폼-교육-공고-동향)",
        f"5. [Meta 광고 소재 동향](#5-meta-광고-소재-동향)",
        f"6. [데이톤 기회 포인트](#6-데이톤-기회-포인트)",
        f"",
        f"---",
        f"",
    ]

    # 1. 시장 현황 요약
    lines += [
        f"## 1. 시장 현황 요약",
        f"",
    ]

    landing = analysis.get("landing_analysis", {})
    course_analysis = analysis.get("course_analysis", {})

    if "market_trend" in course_analysis:
        lines += [
            f"### 전반적 트렌드",
            f"{course_analysis.get('market_trend', '-')}",
            f"",
        ]

    if "recommended_positioning" in landing:
        lines += [
            f"### 데이톤 추천 포지셔닝",
            f"> **{landing.get('recommended_positioning', '-')}**",
            f"",
        ]

    # 2. HRD-Net 훈련과정 동향
    lines += [
        f"---",
        f"",
        f"## 2. HRD-Net 훈련과정 동향",
        f"",
        f"**수집 과정 수:** {len(courses)}개",
        f"",
    ]

    if "top_keywords" in course_analysis:
        kws = course_analysis["top_keywords"]
        lines += [
            f"### 주요 키워드 TOP {len(kws)}",
            f"",
            " ".join([f"`{kw}`" for kw in kws]),
            f"",
        ]

    if "org_count" in course_analysis and course_analysis["org_count"]:
        lines += [
            f"### 기관별 AI 과정 수",
            f"",
            f"| 기관 | 과정 수 |",
            f"|---|---|",
        ]
        for org, cnt in sorted(course_analysis["org_count"].items(), key=lambda x: -x[1]):
            lines.append(f"| {org} | {cnt} |")
        lines.append(f"")

    if courses:
        lines += [
            f"### 최근 수집된 과정 목록",
            f"",
            f"| 기관 | 과정명 | 지역 | 정원 |",
            f"|---|---|---|---|",
        ]
        for c in courses[:15]:
            org = c.get("traInstNm", "-")
            name = c.get("trprNm", "-")
            area = c.get("traArea1Nm", "-")
            cap = c.get("yardMan", "-")
            lines.append(f"| {org} | {name} | {area} | {cap} |")
        if len(courses) > 15:
            lines.append(f"| ... | *외 {len(courses)-15}개* | | |")
        lines.append(f"")

    # 3. 경쟁사 랜딩페이지 분석
    lines += [
        f"---",
        f"",
        f"## 3. 경쟁사 랜딩페이지 분석",
        f"",
    ]

    competitors_analysis = landing.get("competitors", [])
    for comp in competitors_analysis:
        name = comp.get("name", "")
        lines += [
            f"### 🏢 {name}",
            f"",
            f"**포지셔닝:** {comp.get('positioning', '-')}",
            f"",
            f"| 항목 | 내용 |",
            f"|---|---|",
            f"| 타겟 | {', '.join(comp.get('target_persona', []))} |",
            f"| 주요 소구점 | {', '.join(comp.get('appeal_types', []))} |",
            f"| CTA 전략 | {comp.get('cta_strategy', '-')} |",
            f"| 차별점 | {', '.join(comp.get('differentiators', []))} |",
            f"| 약점/공백 | {comp.get('weakness', '-')} |",
            f"",
        ]

    # 4. 청년 플랫폼 교육 공고 동향
    lines += [
        f"---",
        f"",
        f"## 4. 청년 플랫폼 교육 공고 동향",
        f"",
        f"**수집 공고 수:** {len(youth_posts)}건 (요즘것들 / 링커리어 / 슈퍼루키)",
        f"",
    ]

    youth_analysis = analysis.get("youth_platform_analysis", {})

    if "hook_patterns" in youth_analysis:
        lines += [f"### 자주 쓰이는 후킹 문구", f""]
        lines.append(" ".join([f"`{p}`" for p in youth_analysis["hook_patterns"]]))
        lines.append(f"")

    if "title_strategies" in youth_analysis:
        lines += [f"### 제목 작성 전략", f""]
        for s in youth_analysis["title_strategies"]:
            lines.append(f"- {s}")
        lines.append(f"")

    if "dayton_copy_suggestions" in youth_analysis:
        lines += [f"### 💡 데이톤 카피 제안", f""]
        for i, s in enumerate(youth_analysis["dayton_copy_suggestions"], 1):
            lines.append(f"{i}. **{s}**")
        lines.append(f"")

    if youth_posts:
        by_platform = {}
        for post in youth_posts:
            plat = post.get("platform", "기타")
            by_platform.setdefault(plat, []).append(post)

        lines += [f"### 플랫폼별 수집 공고 샘플", f""]
        for plat, posts in by_platform.items():
            lines += [f"**{plat}** ({len(posts)}건)"]
            for post in posts[:5]:
                title = post.get("title", "-")
                url = post.get("url", "")
                lines.append(f"- [{title}]({url})")
            lines.append(f"")

    # 5. Meta 광고 소재 동향
    lines += [
        f"---",
        f"",
        f"## 5. Meta 광고 소재 동향",
        f"",
    ]

    manual_links = []
    for name, ads in ads_data.items():
        if ads and ads[0].get("_status") == "manual_required":
            url = ads[0].get("_manual_url", "")
            manual_links.append(f"- [{name}]({url})")
        elif ads:
            lines += [f"### {name}", f"수집된 광고: {len(ads)}개", f""]

    if manual_links:
        lines += [
            f"### 수동 확인 필요 (Meta 광고 라이브러리)",
            f"",
        ] + manual_links + [f""]

    # 6. 데이톤 기회 포인트
    lines += [
        f"---",
        f"",
        f"## 6. 데이톤 기회 포인트",
        f"",
    ]

    market_gaps = landing.get("market_gaps", []) + course_analysis.get("empty_positions", [])
    if market_gaps:
        lines += [f"### 🎯 시장 공백 (아무도 안 하고 있는 포지션)", f""]
        for gap in market_gaps:
            lines.append(f"- {gap}")
        lines.append(f"")

    opportunities = course_analysis.get("dayton_opportunities", [])
    if opportunities:
        lines += [f"### 💡 데이톤 활용 기회", f""]
        for opp in opportunities:
            lines.append(f"- {opp}")
        lines.append(f"")

    lines += [
        f"---",
        f"",
        f"*자동 생성된 리포트입니다. 데이터 기준: {date_str}*",
    ]

    return "\n".join(lines)


def push_to_github(content: str, filename: str, config: dict) -> bool:
    """GitHub 레포에 리포트 파일 push"""
    token = config["api_keys"]["github_token"]
    repo = config["github"]["repo"]
    branch = config["github"].get("branch", "main")
    reports_path = config["github"].get("reports_path", "reports")

    if token == "YOUR_GITHUB_TOKEN":
        print("  ⚠️  GITHUB_TOKEN 미설정 — 로컬에만 저장")
        return False

    api_url = f"https://api.github.com/repos/{repo}/contents/{reports_path}/{filename}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 파일이 이미 있으면 SHA 필요
    existing_sha = None
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 200:
        existing_sha = resp.json().get("sha")

    payload = {
        "message": f"📊 리포트 자동 업데이트: {filename}",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    resp = requests.put(api_url, headers=headers, json=payload)
    if resp.status_code in (200, 201):
        print(f"  ✅ GitHub push 완료: {repo}/{reports_path}/{filename}")
        return True
    else:
        print(f"  ⚠️  GitHub push 실패: {resp.status_code} {resp.text[:200]}")
        return False


def save_local(content: str, filename: str) -> Path:
    """로컬 저장"""
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    output_path.write_text(content, encoding="utf-8")
    print(f"  💾 로컬 저장: {output_path}")
    return output_path


def run(courses: list = None, ads_data: dict = None, youth_posts: list = None, analysis: dict = None, config: dict = None) -> Path:
    """리포트 생성 파이프라인 실행"""
    print("\n📝 [5단계] 리포트 생성 시작")
    print("=" * 50)

    if config is None:
        config = load_config()

    courses = courses or []
    ads_data = ads_data or {}
    youth_posts = youth_posts or []
    analysis = analysis or {}

    report_content = generate_report(courses, ads_data, youth_posts, analysis)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{date_str}_bootcamp_intel_report.md"

    # 로컬 저장
    local_path = save_local(report_content, filename)

    # GitHub push
    push_to_github(report_content, filename, config)

    print(f"\n✅ 리포트 생성 완료: {filename}")
    return local_path


if __name__ == "__main__":
    run()
