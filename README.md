# Bootcamp Marketing Research Pipeline

AI 부트캠프 경쟁사 모집/마케팅 동향을 자동 수집하고, Gemini AI로 분석해 리포트를 생성하는 파이프라인입니다.

---

## 파이프라인 구조

```
[1] HRD-Net 수집        고용24 API → 훈련과정 목록 (기관명/과정명/수강료/국비여부)
[2] Meta 광고 수집      Meta 광고 라이브러리 → 경쟁사 집행 광고 소재
[3] 랜딩페이지 분석     경쟁사 URL 크롤링 → 헤드라인/CTA/소셜증명 추출
[4] 청년 플랫폼 수집    요즘것들/링커리어/슈퍼루키/새싹 → 교육 공고 제목/후킹 문구
        ↓
[5] Gemini AI 분석      포지셔닝/소구점/타겟 페르소나/시장 공백 자동 분석
        ↓
[6] 리포트 생성         Markdown 리포트 생성 → GitHub 자동 push
```

## 분석 경쟁사

`competitors.yaml`에서 자유롭게 추가/수정 가능합니다.

| 기관 | 랜딩페이지 | Meta 광고 |
|------|-----------|-----------|
| 패스트캠퍼스 | O | O |
| 제로베이스 | O | O |
| 멀티캠퍼스 | O | O |
| 엘리스 | O | O |
| 스파르타코딩클럽 | O | O |
| 코드잇 | O | O |

## 디렉토리 구조

```
.
├── src/
│   ├── hrdnet_fetcher.py       # 고용24 API 훈련과정 수집
│   ├── meta_ads_fetcher.py     # Meta 광고 라이브러리 수집
│   ├── landing_analyzer.py     # 경쟁사 랜딩페이지 크롤링/분석
│   ├── youth_platform_scraper.py  # 청년 취업 플랫폼 공고 수집
│   ├── ai_analyzer.py          # Gemini AI 분석 (포지셔닝/공백/카피)
│   └── report_generator.py     # Markdown 리포트 생성 + GitHub push
├── data/
│   ├── raw/                    # 수집 원본 데이터
│   └── processed/              # AI 분석 완료 데이터 (JSON)
├── reports/                    # 생성된 리포트
├── competitors.yaml            # 경쟁사 설정
├── config.yaml.example         # 설정 파일 템플릿
├── run.py                      # 파이프라인 진입점
└── requirements.txt
```

## 시작하기

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 설정 파일 작성

```bash
cp config.yaml.example config.yaml
```

`config.yaml`을 열어 API 키를 입력합니다. (`.gitignore`에 등록되어 있어 커밋되지 않습니다)

### 3. 실행

```bash
# 전체 파이프라인 실행
python run.py

# 특정 단계만 실행
python run.py --step hrdnet      # HRD-Net 수집
python run.py --step meta        # Meta 광고 수집
python run.py --step landing     # 랜딩페이지 분석
python run.py --step youth       # 청년 플랫폼 공고 수집
python run.py --step analyze     # Gemini AI 분석
python run.py --step report      # 리포트 생성
```

> API 키 없이 실행하면 데모 분석 결과로 동작합니다.

## 필요한 API 키

| 키 | 발급처 | 용도 |
|---|---|---|
| `hrdnet` | [고용24 Open API](https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do) | 훈련과정 목록 수집 |
| `data_go_kr` | [공공데이터포털](https://www.data.go.kr) | 컨소시엄 훈련과정 수집 |
| `gemini` | [Google AI Studio](https://aistudio.google.com/app/apikey) | AI 분석 (무료 티어 지원) |
| `github_token` | GitHub Settings > Developer settings | 리포트 자동 push |

## AI 분석 항목

Gemini 2.0 Flash 모델이 아래 항목을 자동 분석합니다.

- **랜딩페이지 분석**: 핵심 포지셔닝, 소구점 유형, 타겟 페르소나, CTA 전략, 차별화 포인트
- **청년 플랫폼 공고 분석**: 후킹 문구 패턴, 제목 작성 전략, 카피 제안
- **훈련과정 트렌드 분석**: 기관별 과정 수, 주요 키워드, 시장 공백 포지션
- **시장 공백 도출**: 경쟁사 대비 부재한 포지션 및 기회 요인 추출

## 출력 결과

```
reports/
└── 20260602_bootcamp_intel_report.md   # 주간 경쟁사 동향 리포트

data/processed/
├── 20260602_hrdnet_courses.json        # 훈련과정 수집 데이터
├── 20260602_meta_ads.json              # Meta 광고 소재 데이터
├── 20260602_landing_pages.json         # 랜딩페이지 분석 데이터
└── 20260602_ai_analysis.json           # Gemini 분석 결과
```

## 기술 스택

| 분류 | 기술 |
|------|------|
| AI 분석 | Gemini 2.0 Flash (google-genai) |
| 데이터 수집 | Requests, BeautifulSoup4 |
| 공공 API | 고용24 HRD-Net, 공공데이터포털 |
| 설정 관리 | PyYAML |
| 리포트 배포 | GitHub API (자동 push) |
