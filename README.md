# 서울 청년 정책 RAG 시스템

서울시 청년 정책을 생성형 AI를 활용하여 안내하는 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 🏗️ 프로젝트 구조

```
cg_youth_poc/
├── data/                        # 정책 정보 저장 폴더
│   ├── raw/                    # (옵션) 원본 HTML 저장용
│   └── processed/              # ✅ 수집된 JSON 저장 위치
│
├── scripts/                    # 💻 주요 수집 및 처리 스크립트
│   └── crawl_youth_jobs.py     # ▶ 일자리 정책 수집 스크립트
│
├── rag/                        # 🔍 RAG 구조 관련
│   ├── build_vectorstore.py    # → ChromaDB 벡터 저장소 구축
│   └── query_rag.py            # → RAG 응답 생성
│
├── web_search/                 # 🌐 DuckDuckGo 기반 검색 응답
│   └── query_duckduckgo.py     # → 검색 → GPT 요약 생성
│
├── streamlit_app.py            # ✅ 챗봇 UI 및 비교 평가 앱
├── requirements.txt            # 설치 목록
└── README.md                   # 프로젝트 개요
```

## 🚀 주요 기능

### 1. 정책 데이터 수집
- 서울시 청년정책 사이트에서 정책 정보 자동 수집
- JSON 형태로 구조화된 데이터 저장
- 샘플 데이터 제공 (실제 크롤링이 어려운 경우)

### 2. RAG 시스템 (ChromaDB 기반)
- **ChromaDB 벡터 저장소**: 정책 데이터의 의미적 검색
- **Sentence Transformers**: 한국어 텍스트 임베딩
- **OpenAI GPT**: 자연스러운 답변 생성

### 3. 웹 검색 통합
- **DuckDuckGo 검색**: 최신 웹 정보 수집
- **실시간 정보**: 최신 정책 동향 파악
- **GPT 요약**: 검색 결과의 자연어 요약

### 4. 웹 인터페이스
- **Streamlit 앱**: 직관적인 챗봇 인터페이스
- **실시간 상담**: 정책 질의응답
- **응답 비교**: RAG vs 웹 검색 결과 비교

## 📦 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 3. 데이터 수집
```bash
python scripts/crawl_youth_jobs.py
```

### 4. ChromaDB 벡터 저장소 구축
```bash
python rag/build_vectorstore.py
```

### 5. 웹 앱 실행
```bash
streamlit run streamlit_app.py
```

## 🔧 사용법

### 1. 정책 데이터 수집
```python
from scripts.crawl_youth_jobs import SeoulYouthPolicyCrawler

crawler = SeoulYouthPolicyCrawler()
policies = crawler.create_sample_data()  # 샘플 데이터 생성
crawler.save_policies(policies)
```

### 2. RAG 시스템 사용
```python
from rag.query_rag import PolicyRAG

rag = PolicyRAG(openai_api_key="your-key")
result = rag.query("청년 일자리 지원 정책이 궁금해요")
print(result['answer'])
```

### 3. 웹 검색 사용
```python
from web_search.query_duckduckgo import WebSearchRAG

web_rag = WebSearchRAG(openai_api_key="your-key")
result = web_rag.query("2024년 청년 정책")
print(result['answer'])
```

## 🎯 주요 특징

### 정확한 정보 제공
- 공식 정책 데이터베이스 기반
- 최신 웹 정보 통합
- 출처 명시 및 검증

### 사용자 친화적 인터페이스
- 직관적인 챗봇 UI
- 실시간 응답
- 응답 품질 비교 기능

### 확장 가능한 구조
- 모듈화된 설계
- 새로운 정책 카테고리 추가 용이
- 다양한 AI 모델 지원

## 📊 성능 최적화

### 벡터 검색 최적화
- ChromaDB 인덱스 사용으로 빠른 검색
- 코사인 유사도 기반 정확한 매칭
- 메타데이터 기반 필터링

### 응답 품질 향상
- 컨텍스트 기반 답변 생성
- 다중 소스 정보 통합
- 사용자 피드백 반영

## 🔍 기술 스택

- **백엔드**: Python 3.8+
- **웹 프레임워크**: Streamlit
- **벡터 데이터베이스**: ChromaDB
- **임베딩 모델**: Sentence Transformers
- **생성 모델**: OpenAI GPT-3.5/4
- **웹 검색**: DuckDuckGo Search
- **데이터 처리**: Pandas, NumPy

## 🔄 FAISS에서 ChromaDB로 마이그레이션

### 변경 사항
- **FAISS** → **ChromaDB**: 더 쉬운 설치 및 사용
- **파일 기반 저장** → **데이터베이스 기반 저장**
- **수동 메타데이터 관리** → **자동 메타데이터 관리**

### 장점
- Python 3.10+ 완전 지원
- macOS 호환성 문제 해결
- 더 간단한 API
- 자동 인덱싱 및 최적화

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.

---

**서울 청년 정책 RAG 시스템** - 청년들의 정책 정보 접근성을 높이는 AI 솔루션 🏙️✨