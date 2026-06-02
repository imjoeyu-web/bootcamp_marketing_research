"""
report_generator.py
마케팅/모집 전략 중심 주간 리포트 생성 + GitHub push
"""

import json
import yaml
import base64
import requests
from datetime import datetime
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_report(youth_posts: list, ads_data: dict, analysis: dict) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y년 %m월 %d일")
    week_str = now.strftime("W%W")

    copy_analysis = analysis.get("copy_analysis", {})
    landing_analysis = analysis.get("landing_analysis", {})
    copy_patterns = copy_analysis.get("copy_patterns", {})

    lines = [
        f"# 부트캠프 모집/마케팅 동향 리포트",
        f"",
        f"> 기준일: {date_str} | {week_str}주차",
        f"",
        f"---",
        f"",
        f"## 목차",
        f"1. [이번 주 수집 현황](#1-이번-주-수집-현황)",
        f"2. [공고 카피 패턴 분석](#2-공고-카피-패턴-분석)",
        f"3. [채널별 모집 전략](#3-채널별-모집-전략)",
        f"4. [랜딩페이지 마케팅 전략](#4-랜딩페이지-마케팅-전략)",
        f"5. [Meta 광고 소재 모니터링](#5-meta-광고-소재-모니터링)",
        f"6. [수집 공고 샘플](#6-수집-공고-샘플)",
        f"",
        f"---",
        f"",
    ]

    # 1. 수집 현황
    by_platform = {}
    for post in youth_posts:
        plat = post.get("platform", "기타")
        by_platform.setdefault(plat, []).append(post)

    lines += [
        f"## 1. 이번 주 수집 현황",
        f"",
        f"| 플랫폼 | 수집 공고 수 |",
        f"|---|---|",
    ]
    for plat, posts in by_platform.items():
        lines.append(f"| {plat} | {len(posts)}건 |")
    lines += [
        f"| **합계** | **{len(youth_posts)}건** |",
        f"",
    ]

    # 2. 카피 패턴 분석
    lines += [
        f"---",
        f"",
        f"## 2. 공고 카피 패턴 분석",
        f"",
    ]

    if copy_patterns.get("hook_phrases"):
        lines += [f"### 후킹 문구", f""]
        lines.append(" ".join([f"`{p}`" for p in copy_patterns["hook_phrases"]]))
        lines.append("")

    if copy_patterns.get("target_expressions"):
        lines += [f"### 타겟 명시 표현", f""]
        lines.append(" ".join([f"`{p}`" for p in copy_patterns["target_expressions"]]))
        lines.append("")

    if copy_patterns.get("benefit_expressions"):
        lines += [f"### 혜택 강조 표현", f""]
        lines.append(" ".join([f"`{p}`" for p in copy_patterns["benefit_expressions"]]))
        lines.append("")

    if copy_patterns.get("urgency_expressions"):
        lines += [f"### 긴박감 조성 표현", f""]
        lines.append(" ".join([f"`{p}`" for p in copy_patterns["urgency_expressions"]]))
        lines.append("")

    if copy_analysis.get("title_formulas"):
        lines += [f"### 효과적인 제목 공식", f""]
        for formula in copy_analysis["title_formulas"]:
            lines.append(f"- {formula}")
        lines.append("")

    if copy_analysis.get("cta_patterns"):
        lines += [f"### CTA 문구 패턴", f""]
        lines.append(" ".join([f"`{c}`" for c in copy_analysis["cta_patterns"]]))
        lines.append("")

    if copy_analysis.get("social_proof_types"):
        lines += [f"### 사회적 증거 활용 방식", f""]
        for sp in copy_analysis["social_proof_types"]:
            lines.append(f"- {sp}")
        lines.append("")

    if copy_analysis.get("recruitment_timing"):
        lines += [
            f"### 모집 타이밍 패턴",
            f"",
            f"{copy_analysis['recruitment_timing']}",
            f"",
        ]

    # 3. 채널별 전략
    lines += [
        f"---",
        f"",
        f"## 3. 채널별 모집 전략",
        f"",
    ]

    channel_strategy = copy_analysis.get("channel_strategy", {})
    if channel_strategy:
        lines += [
            f"| 채널 | 주요 전략/톤 |",
            f"|---|---|",
        ]
        for channel, strategy in channel_strategy.items():
            lines.append(f"| {channel} | {strategy} |")
        lines.append("")
    else:
        lines += [f"수집 데이터 부족 — 다음 주 업데이트 예정", f""]

    # 4. 랜딩페이지 마케팅 전략
    lines += [
        f"---",
        f"",
        f"## 4. 랜딩페이지 마케팅 전략",
        f"",
    ]

    if landing_analysis.get("lp_structure"):
        lines += [f"### 전형적인 LP 설득 구조", f"", f"{landing_analysis['lp_structure']}", f""]

    if landing_analysis.get("headline_patterns"):
        lines += [f"### 헤드카피 패턴", f""]
        for p in landing_analysis["headline_patterns"]:
            lines.append(f"- {p}")
        lines.append("")

    if landing_analysis.get("cta_strategy"):
        cta = landing_analysis["cta_strategy"]
        lines += [f"### CTA 전략", f""]
        if cta.get("common_ctas"):
            lines.append("**자주 쓰이는 CTA:** " + " / ".join([f"`{c}`" for c in cta["common_ctas"]]))
        if cta.get("placement"):
            lines.append(f"**배치 전략:** {cta['placement']}")
        lines.append("")

    if landing_analysis.get("social_proof_usage"):
        lines += [f"### 사회적 증거 활용", f""]
        for sp in landing_analysis["social_proof_usage"]:
            lines.append(f"- {sp}")
        lines.append("")

    if landing_analysis.get("benefit_framing"):
        lines += [f"### 혜택 프레이밍 방식", f""]
        for bf in landing_analysis["benefit_framing"]:
            lines.append(f"- {bf}")
        lines.append("")

    if landing_analysis.get("effective_elements"):
        lines += [f"### 효과적인 LP 요소", f""]
        for el in landing_analysis["effective_elements"]:
            lines.append(f"- {el}")
        lines.append("")

    # 5. Meta 광고
    lines += [
        f"---",
        f"",
        f"## 5. Meta 광고 소재 모니터링",
        f"",
    ]

    manual_links = []
    auto_collected = []
    for name, ads in ads_data.items():
        if not ads:
            continue
        if ads[0].get("_status") == "manual_required":
            url = ads[0].get("_manual_url", "")
            manual_links.append(f"| {name} | [광고 라이브러리 보기]({url}) |")
        else:
            auto_collected.append(f"| {name} | {len(ads)}개 |")

    if auto_collected:
        lines += [f"### 자동 수집", f"", f"| 채널 | 광고 수 |", f"|---|---|"]
        lines.extend(auto_collected)
        lines.append("")

    if manual_links:
        lines += [
            f"### 수동 확인 필요",
            f"",
            f"| 채널 | 링크 |",
            f"|---|---|",
        ]
        lines.extend(manual_links)
        lines.append("")

    # 6. 공고 샘플
    lines += [
        f"---",
        f"",
        f"## 6. 수집 공고 샘플",
        f"",
    ]

    for plat, posts in by_platform.items():
        lines += [f"### {plat}", f""]
        for post in posts[:8]:
            title = post.get("title", "-")
            url = post.get("url", "")
            deadline = post.get("deadline", "")
            deadline_str = f" `{deadline}`" if deadline else ""
            lines.append(f"- [{title}]({url}){deadline_str}")
        if len(posts) > 8:
            lines.append(f"- *외 {len(posts)-8}건*")
        lines.append("")

    lines += [
        f"---",
        f"",
        f"*자동 생성 리포트 | 기준일: {date_str}*",
    ]

    return "\n".join(lines)


def push_to_github(content: str, filename: str, config: dict) -> bool:
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

    existing_sha = None
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 200:
        existing_sha = resp.json().get("sha")

    payload = {
        "message": f"리포트 업데이트: {filename}",
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
        print(f"  ⚠️  GitHub push 실패: {resp.status_code}")
        return False


def save_local(content: str, filename: str) -> Path:
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text(content, encoding="utf-8")
    print(f"  💾 로컬 저장: {output_path}")
    return output_path


def run(courses: list = None, ads_data: dict = None, youth_posts: list = None,
        analysis: dict = None, config: dict = None) -> Path:
    print("\n📝 리포트 생성 시작")
    print("=" * 50)

    if config is None:
        config = load_config()

    youth_posts = youth_posts or []
    ads_data = ads_data or {}
    analysis = analysis or {}

    report_content = generate_report(youth_posts, ads_data, analysis)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{date_str}_marketing_report.md"

    local_path = save_local(report_content, filename)
    push_to_github(report_content, filename, config)

    print(f"\n✅ 리포트 생성 완료: {filename}")
    return local_path


if __name__ == "__main__":
    run()
