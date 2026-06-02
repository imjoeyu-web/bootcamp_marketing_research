# 📊 Bootcamp Intelligence Pipeline

부트캠프 시장 경쟁사 모집/마케팅 동향 자동 수집 및 리포트 생성 시스템

## 구조

```
bootcamp-intelligence/
├── src/
│   ├── hrdnet_fetcher.py      # 고용24 API - 훈련과정 목록 수집
│   ├── meta_ads_fetcher.py    # Meta 광고 라이브러리 수집
│   ├── landing_analyzer.py   # 경쟁사 랜딩페이지 분석
│   ├── ai_analyzer.py        # Claude API - 소재 자동 분류/분석
│   └── report_generator.py   # Markdown 리포트 생성 + GitHub push
├── data/
│   ├── raw/                   # 수집된 원본 데이터
│   └── processed/             # 분석 완료 데이터
├── reports/                   # 생성된 주간 리포트
├── competitors.yaml           # 경쟁사 설정 파일
├── config.yaml                # API 키 등 설정
├── run.py                     # 전체 파이프라인 실행
└── requirements.txt
```

## 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 설정 파일 작성
cp config.yaml.example config.yaml
# config.yaml에 API 키 입력

# 3. 전체 파이프라인 실행
python run.py

# 4. 특정 단계만 실행
python run.py --step hrdnet       # 훈련과정 수집만
python run.py --step meta         # Meta 광고만
python run.py --step landing      # 랜딩페이지만
python run.py --step report       # 리포트 생성만
```

## 필요한 API 키

| 키 | 발급처 | 용도 |
|---|---|---|
| `HRDNET_API_KEY` | [고용24 Open API](https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do) | 훈련과정 목록 |
| `DATA_GO_KR_KEY` | [공공데이터포털](https://www.data.go.kr) | 컨소시엄 훈련과정 |
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com) | AI 분석 |
| `GITHUB_TOKEN` | GitHub Settings > Developer settings | 리포트 자동 push |

## 출력 예시

- `reports/YYYYMMDD_weekly_report.md` — 주간 경쟁사 동향 리포트
- `data/processed/YYYYMMDD_courses.json` — 훈련과정 데이터
- `data/processed/YYYYMMDD_meta_ads.json` — Meta 광고 소재 데이터
