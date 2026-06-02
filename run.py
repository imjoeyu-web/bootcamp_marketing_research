"""
run.py
전체 파이프라인 실행 진입점

사용법:
  python run.py                    # 전체 실행
  python run.py --step hrdnet      # HRD-Net 수집만
  python run.py --step meta        # Meta 광고만
  python run.py --step landing     # 랜딩페이지만
  python run.py --step analyze     # AI 분석만
  python run.py --step report      # 리포트 생성만
"""

import argparse
import json
import yaml
import sys
from pathlib import Path
from datetime import datetime

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hrdnet_fetcher import run as run_hrdnet
from meta_ads_fetcher import run as run_meta
from landing_analyzer import run as run_landing
from youth_platform_scraper import run as run_youth
from ai_analyzer import run as run_ai
from report_generator import run as run_report


def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        example_path = Path(__file__).parent / "config.yaml.example"
        print(f"⚠️  config.yaml 없음. {example_path}를 복사해서 작성해주세요.")
        print("   cp config.yaml.example config.yaml")
        # 데모 모드로 실행
        with open(example_path) as f:
            return yaml.safe_load(f)
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_latest_data(data_type: str) -> any:
    """processed 디렉토리에서 가장 최근 데이터 로드"""
    processed_dir = Path(__file__).parent / "data" / "processed"
    pattern = f"*_{data_type}.json"
    files = sorted(processed_dir.glob(pattern), reverse=True)

    if not files:
        return None

    with open(files[0], encoding="utf-8") as f:
        return json.load(f)


def run_full_pipeline(config: dict):
    """전체 파이프라인 순서대로 실행"""
    print("\n🚀 부트캠프 인텔리전스 파이프라인 시작")
    print(f"   실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. HRD-Net 훈련과정 수집
    courses = run_hrdnet(config)

    # 2. Meta 광고 수집
    ads_data = run_meta(config)

    # 3. 랜딩페이지 분석
    landing_data = run_landing(config)

    # 4. 청년 플랫폼 교육 공고 수집 (요즘것들 / 링커리어 / 슈퍼루키)
    youth_posts = run_youth(max_pages=3)

    # 5. Claude AI 분석
    analysis = run_ai(
        courses=courses,
        landing_data=landing_data,
        youth_posts=youth_posts,
        config=config
    )

    # 6. 리포트 생성 + GitHub push
    report_path = run_report(
        courses=courses,
        ads_data=ads_data,
        youth_posts=youth_posts,
        analysis=analysis,
        config=config
    )

    print("\n" + "=" * 60)
    print("🎉 파이프라인 완료!")
    print(f"   리포트 위치: {report_path}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="부트캠프 경쟁사 인텔리전스 파이프라인")
    parser.add_argument(
        "--step",
        choices=["hrdnet", "meta", "landing", "youth", "analyze", "report"],
        help="특정 단계만 실행 (미지정시 전체 실행)"
    )
    args = parser.parse_args()
    config = load_config()

    if args.step is None:
        run_full_pipeline(config)

    elif args.step == "hrdnet":
        run_hrdnet(config)

    elif args.step == "meta":
        run_meta(config)

    elif args.step == "landing":
        run_landing(config)

    elif args.step == "youth":
        run_youth(max_pages=3)

    elif args.step == "analyze":
        courses = load_latest_data("hrdnet_courses") or []
        landing_data = load_latest_data("landing_pages") or []
        run_ai(courses=courses, landing_data=landing_data, config=config)

    elif args.step == "report":
        courses = load_latest_data("hrdnet_courses") or []
        ads_data = load_latest_data("meta_ads") or {}
        analysis = load_latest_data("ai_analysis") or {}
        run_report(courses=courses, ads_data=ads_data, analysis=analysis, config=config)


if __name__ == "__main__":
    main()
