from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import json

app = FastAPI(
    title="청년정책 검색 API",
    description="서울시 청년정책 검색 및 AI 답변 생성 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용. 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
vectorstore = None
embedding_model = None
openai_client = None

class SearchRequest(BaseModel):
    query: str
    k: int = 5
    filters: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_count: int

class AnswerRequest(BaseModel):
    query: str
    user_context: Optional[str] = None
    k: int = 3

class AnswerResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float

def load_vectorstore():
    """벡터스토어 로드"""
    global vectorstore, embedding_model, openai_client
    
    try:
        # 임베딩 모델 로드
        embedding_model = HuggingFaceEmbeddings(model_name="BM-K/KoSimCSE-roberta")
        
        # 벡터스토어 로드
        vectorstore = Chroma(
            persist_directory="vectorstore",
            embedding_function=embedding_model
        )
        
        # OpenAI 클라이언트 초기화
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            try:
                from openai import OpenAI
                openai_client = OpenAI(api_key=openai_api_key)
                print("✅ OpenAI 클라이언트 초기화 완료")
            except ImportError:
                print("❌ openai 패키지가 설치되어 있지 않습니다. OpenAI 기능이 비활성화됩니다.")
        
        print("✅ 벡터스토어 로드 완료")
        print(f"✅ .env 경로: {dotenv_path}")
        print(f"✅ OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")
        return True
    except Exception as e:
        print(f"❌ 벡터스토어 로드 실패: {e}")
        return False

def generate_llm_answer(query: str, context_docs: List[Document]) -> str:
    """
    LLM을 사용하여 답변 생성
    OpenAI API 또는 템플릿 기반 답변 생성
    """
    if not context_docs:
        return "죄송합니다. 관련 정책을 찾을 수 없습니다."
    
    # OpenAI 클라이언트가 있으면 사용
    if openai_client:
        try:
            # 컨텍스트 생성
            context_parts = []
            for i, doc in enumerate(context_docs, 1):
                context_parts.append(f"""
정책 {i}: {doc.metadata.get('title', '제목 없음')}
주관기관: {doc.metadata.get('agency', '')}
연령: {doc.metadata.get('age_range', '')}
신청기간: {doc.metadata.get('apply_start', '')} ~ {doc.metadata.get('apply_end', '')}
지원내용: {doc.page_content[:300]}...
신청사이트: {doc.metadata.get('application_site', '')}
""")
            
            context = "\n".join(context_parts)
            
            # OpenAI API 호출 (GPT-4o-mini 사용)
            model_name = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "당신은 서울시 청년 정책 전문 상담사입니다. 사용자의 질문에 친절하고 정확하게 답변해주세요."},
                    {"role": "user", "content": f"질문: {query}\n\n관련 정책 정보:\n{context}\n\n위 정보를 바탕으로 답변해주세요."}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API 호출 실패: {e}")
            # 실패 시 템플릿 기반 답변으로 fallback
    
    # 템플릿 기반 답변 (fallback 또는 OpenAI 없을 때)
    policies = []
    for doc in context_docs:
        policy_info = {
            "title": doc.metadata.get("title", "제목 없음"),
            "agency": doc.metadata.get("agency", ""),
            "age_range": doc.metadata.get("age_range", ""),
            "policy_type": doc.metadata.get("policy_type", ""),
            "apply_period": f"{doc.metadata.get('apply_start', '')} ~ {doc.metadata.get('apply_end', '')}",
            "application_site": doc.metadata.get("application_site", ""),
            "summary": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        }
        policies.append(policy_info)
    
    answer_parts = []
    answer_parts.append(f"'{query}'에 대한 관련 정책을 찾았습니다:")
    answer_parts.append("")
    
    for i, policy in enumerate(policies, 1):
        answer_parts.append(f"📋 {i}. {policy['title']}")
        if policy['agency']:
            answer_parts.append(f"   주관기관: {policy['agency']}")
        if policy['age_range']:
            answer_parts.append(f"   연령: {policy['age_range']}")
        if policy['apply_period'] and policy['apply_period'] != " ~ ":
            answer_parts.append(f"   신청기간: {policy['apply_period']}")
        if policy['application_site']:
            answer_parts.append(f"   신청사이트: {policy['application_site']}")
        answer_parts.append(f"   요약: {policy['summary']}")
        answer_parts.append("")
    
    answer_parts.append("💡 더 자세한 정보는 각 정책의 신청사이트를 방문해보세요!")
    
    return "\n".join(answer_parts)

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 벡터스토어 로드"""
    if not load_vectorstore():
        raise Exception("벡터스토어 로드 실패")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "청년정책 검색 API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search",
            "answer": "/answer",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "vectorstore_loaded": vectorstore is not None
    }

@app.post("/search", response_model=SearchResponse)
async def search_policies(request: SearchRequest):
    """
    정책 검색 API
    
    Args:
        request: 검색 요청 (쿼리, 결과 수, 필터)
    
    Returns:
        검색 결과
    """
    if not vectorstore:
        raise HTTPException(status_code=500, detail="벡터스토어가 로드되지 않았습니다")
    
    try:
        # 검색 실행
        results = vectorstore.similarity_search(
            request.query, 
            k=request.k
        )
        
        # 결과 포맷팅
        formatted_results = []
        for doc in results:
            result = {
                "title": doc.metadata.get("title", ""),
                "policy_id": doc.metadata.get("policy_id", ""),
                "policy_type": doc.metadata.get("policy_type", ""),
                "agency": doc.metadata.get("agency", ""),
                "age_range": doc.metadata.get("age_range", ""),
                "education": doc.metadata.get("education", ""),
                "employment_status": doc.metadata.get("employment_status", ""),
                "apply_start": doc.metadata.get("apply_start", ""),
                "apply_end": doc.metadata.get("apply_end", ""),
                "support_scale": doc.metadata.get("support_scale", ""),
                "page_url": doc.metadata.get("page_url", ""),
                "application_site": doc.metadata.get("application_site", ""),
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
            }
            formatted_results.append(result)
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            total_count=len(formatted_results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")

@app.post("/answer", response_model=AnswerResponse)
async def generate_answer(request: AnswerRequest):
    """
    LLM 답변 생성 API
    
    Args:
        request: 답변 생성 요청 (쿼리, 사용자 컨텍스트, 검색 결과 수)
    
    Returns:
        AI 답변과 소스 정보
    """
    if not vectorstore:
        raise HTTPException(status_code=500, detail="벡터스토어가 로드되지 않았습니다")
    
    try:
        # 관련 정책 검색
        context_docs = vectorstore.similarity_search(
            request.query, 
            k=request.k
        )
        
        # LLM 답변 생성
        answer = generate_llm_answer(request.query, context_docs)
        
        # 소스 정보 정리
        sources = []
        for doc in context_docs:
            source = {
                "title": doc.metadata.get("title", ""),
                "policy_id": doc.metadata.get("policy_id", ""),
                "agency": doc.metadata.get("agency", ""),
                "page_url": doc.metadata.get("page_url", ""),
                "application_site": doc.metadata.get("application_site", ""),
                "relevance_score": 0.95  # 실제로는 유사도 점수 계산 필요
            }
            sources.append(source)
        
        return AnswerResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            confidence=0.9 if sources else 0.0
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답변 생성 중 오류 발생: {str(e)}")

@app.get("/policy/{policy_id}")
async def get_policy_detail(policy_id: str):
    """
    특정 정책 상세 정보 조회
    
    Args:
        policy_id: 정책 ID
    
    Returns:
        정책 상세 정보
    """
    try:
        # JSON 파일에서 정책 정보 로드
        policy_file = f"data/processed/{policy_id}.json"
        if not os.path.exists(policy_file):
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다")
        
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy_data = json.load(f)
        
        return policy_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 정보 로드 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 