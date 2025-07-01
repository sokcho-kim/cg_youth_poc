# 서울시 청년정책 AI 상담사

이 프로젝트는 서울시 청년정책 데이터를 크롤링, 벡터화하여 ChromaDB에 저장하고, FastAPI 백엔드와 Streamlit 프론트엔드로 자연어 정책 검색 및 AI 답변을 제공합니다.

## 주요 기능
- 서울시 청년정책 데이터 크롤러 (Python)
- 정책 데이터 벡터화 (KoSimCSE 임베딩, ChromaDB)
- FastAPI 기반 검색/AI 답변 API
- OpenAI GPT 기반 자연어 답변 (API Key 필요)
- Streamlit 프론트엔드 (공공기관 스타일)
- .env 환경변수 관리 (API Key 등)

## 폴더 구조
```
cg_youth_poc/
├── api/                # FastAPI 백엔드
│   ├── main.py         # API 서버 (검색/답변)
│   └── ...
├── data/               # 정책 데이터 (크롤링 결과)
├── rag/                # 벡터화/임베딩 스크립트
├── scripts/            # 크롤러 등 유틸리티
├── streamlit_app.py    # Streamlit 프론트엔드
├── vectorstore/        # ChromaDB 벡터스토어
├── requirements.txt    # Python 패키지 목록
├── .env                # 환경변수 (API Key 등, git에 미포함)
└── README.md
```

## 설치 및 실행 방법

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. .env 파일 생성
프로젝트 루트에 `.env` 파일을 만들고 아래와 같이 입력:
```
OPENAI_API_KEY=sk-xxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

### 3. 정책 데이터 크롤링 및 벡터화
- 크롤러 실행: `python scripts/crawl_youth_jobs_2.py`
- 벡터화: `python rag/build_vectorstore.py`

### 4. FastAPI 서버 실행
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Streamlit 프론트엔드 실행
```bash
streamlit run streamlit_app.py
```

### 6. 웹에서 사용
- [http://localhost:8501](http://localhost:8501) 접속
- 자연어로 정책 검색 및 AI 답변 이용

## 참고/유의사항
- `.env` 파일은 반드시 git에 올리지 마세요! (API Key 유출 위험)
- ChromaDB 벡터스토어(`vectorstore/`)가 없으면 벡터화 스크립트부터 실행 필요
- 공식 정책 정보는 [서울시 청년포털](https://youth.seoul.go.kr/mainA.do) 참고

---

문의: [서울시 청년포털](https://youth.seoul.go.kr/mainA.do)