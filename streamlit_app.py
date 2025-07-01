#!/usr/bin/env python3
"""
서울 청년 정책 챗봇 UI 및 비교 평가 앱
Streamlit을 사용한 웹 인터페이스 (ChromaDB 기반)
"""

import streamlit as st
import os
import json
import sys
from datetime import datetime
from typing import Dict, Any, List
import requests
import time

# 프로젝트 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# RAG 모듈들 import
try:
    from rag.query_rag import PolicyRAG
    from web_search.query_duckduckgo import WebSearchRAG
except ImportError as e:
    st.error(f"모듈 import 오류: {e}")
    st.info("필요한 패키지들을 설치해주세요: pip install -r requirements.txt")

# 페이지 설정
st.set_page_config(
    page_title="서울시 청년정책 AI 상담사",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일 및 폰트
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
html, body, [class*="css"]  { font-family: 'Noto Sans KR', sans-serif; }
body { background: #fff; }
.main-header {
    background: linear-gradient(90deg, #e3f0ff 0%, #e0fff7 100%);
    color: #222b45;
    padding: 2.2rem 1rem 1.2rem 1rem;
    border-radius: 18px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 24px rgba(30,144,255,0.06);
    text-align: center;
    border: 1.5px solid #e0e7ef;
}
.policy-card {
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(30,144,255,0.07);
    padding: 1.5rem 1.2rem;
    margin-bottom: 1.5rem;
    border: 1.5px solid #e0e7ef;
}
.policy-title {
    color: #1e90ff;
    font-size: 1.18rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
}
.policy-title .icon {
    font-size: 1.3rem;
    margin-right: 0.5rem;
}
.policy-label {
    display: inline-block;
    background: #eaf6ff;
    color: #1e90ff;
    border-radius: 6px;
    padding: 0.2rem 0.7rem;
    font-size: 0.97rem;
    margin-right: 0.5rem;
    margin-bottom: 0.2rem;
    font-weight: 500;
}
.policy-content {
    margin-top: 0.7rem;
    font-size: 1.05rem;
    color: #222b45;
}
.stButton > button {
    background: linear-gradient(90deg, #1e90ff 0%, #00c3a5 100%);
    color: #fff;
    border: none;
    border-radius: 25px;
    padding: 0.7rem 2.2rem;
    font-weight: bold;
    font-size: 1.1rem;
    margin-top: 0.5rem;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #187bcd 0%, #009e82 100%);
}
.answer-box {
    background: #f4faff;
    border-left: 5px solid #1e90ff;
    border-radius: 12px;
    padding: 1.5rem 1.2rem;
    margin: 1.5rem 0;
    color: #222b45;
}
.source-item {
    background: #f0f8ff;
    border-radius: 7px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.97rem;
    color: #1e90ff;
}
.sidebar .sidebar-content {
    background: #f8fafc;
    color: #222b45;
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None

if 'web_search_system' not in st.session_state:
    st.session_state.web_search_system = None

# API 설정
API_BASE_URL = "http://localhost:8000"

def initialize_systems():
    """RAG 시스템들을 초기화합니다."""
    try:
        # 정책 RAG 시스템 초기화 (ChromaDB 사용)
        if st.session_state.rag_system is None:
            with st.spinner("정책 RAG 시스템을 로드하는 중..."):
                st.session_state.rag_system = PolicyRAG(
                    chroma_db_path="./chroma_db"
                )
        
        # 웹 검색 RAG 시스템 초기화
        if st.session_state.web_search_system is None:
            with st.spinner("웹 검색 시스템을 로드하는 중..."):
                st.session_state.web_search_system = WebSearchRAG()
                
        return True
        
    except Exception as e:
        st.error(f"시스템 초기화 중 오류 발생: {e}")
        return False

def display_chat_message(message: Dict[str, Any], is_user: bool = False):
    """채팅 메시지를 표시합니다."""
    if is_user:
        with st.chat_message("user"):
            st.write(message['content'])
    else:
        with st.chat_message("assistant"):
            st.write(message['content'])
            
            # 참고 정보 표시
            if 'search_results' in message and message['search_results']:
                with st.expander("참고한 정책/정보"):
                    for i, result in enumerate(message['search_results'][:3], 1):
                        if 'metadata' in result:
                            st.write(f"**{i}. {result['metadata']['title']}**")
                            st.write(f"카테고리: {result['metadata']['category']}")
                            st.write(f"유사도: {result['score']:.1%}")
                        else:
                            st.write(f"**{i}. {result['title']}**")
                            st.write(f"출처: {result['source']}")

def process_query(query: str, use_rag: bool = True, use_web_search: bool = False):
    """질의를 처리하고 응답을 생성합니다."""
    responses = []
    
    # 정책 RAG 응답
    if use_rag and st.session_state.rag_system:
        try:
            with st.spinner("정책 데이터베이스에서 검색 중..."):
                rag_result = st.session_state.rag_system.query(query, use_openai=True)
            
            responses.append({
                'type': '정책 RAG (ChromaDB)',
                'content': rag_result['answer'],
                'search_results': rag_result.get('search_results', []),
                'used_openai': rag_result.get('used_openai', False)
            })
        except Exception as e:
            st.error(f"정책 RAG 처리 중 오류: {e}")
    
    # 웹 검색 응답
    if use_web_search and st.session_state.web_search_system:
        try:
            with st.spinner("웹에서 최신 정보 검색 중..."):
                web_result = st.session_state.web_search_system.query(query, use_gpt=True)
            
            responses.append({
                'type': '웹 검색',
                'content': web_result['answer'],
                'search_results': web_result.get('search_results', []),
                'used_openai': web_result.get('used_gpt', False)
            })
        except Exception as e:
            st.error(f"웹 검색 처리 중 오류: {e}")
    
    return responses

def check_api_health() -> bool:
    """API 서버 상태 확인"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def search_policies(query: str, k: int = 5) -> Dict[str, Any]:
    """정책 검색"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/search",
            json={"query": query, "k": k}
        )
        return response.json()
    except Exception as e:
        st.error(f"검색 중 오류 발생: {e}")
        return {"results": [], "total_count": 0}

def generate_answer(query: str, k: int = 3) -> Dict[str, Any]:
    """AI 답변 생성"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/answer",
            json={"query": query, "k": k}
        )
        return response.json()
    except Exception as e:
        st.error(f"답변 생성 중 오류 발생: {e}")
        return {"answer": "죄송합니다. 답변을 생성할 수 없습니다.", "sources": []}

def display_policy_card(policy, index):
    st.markdown(f"""
    <div class="policy-card">
        <div class="policy-title"><span class="icon">📄</span>{index}. {policy.get('title', '제목 없음')}</div>
        <div>
            <span class="policy-label">주관기관</span> <span style="color:#222b45;">{policy.get('agency', '정보 없음')}</span>
            <span class="policy-label">연령</span> <span style="color:#00c3a5;">{policy.get('age_range', '정보 없음')}</span>
            <span class="policy-label">신청기간</span> <span style="color:#1e90ff;">{policy.get('apply_start', '')} ~ {policy.get('apply_end', '')}</span>
            <span class="policy-label">지원규모</span> <span style="color:#666;">{policy.get('support_scale', '정보 없음')}</span>
        </div>
        <div class="policy-content">
            {policy.get('content', '내용 없음')}
        </div>
        <div style="margin-top:0.7rem;">
            <span class="policy-label">신청사이트</span>
            <a href="{policy.get('application_site', '')}" target="_blank" style="color:#00c3a5; font-weight:600;">{policy.get('application_site', '정보 없음')}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    """메인 앱 함수"""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin-bottom:0.3rem; color:#1e90ff;">서울시 청년정책 AI 상담사</h1>
        <div style="font-size:1.15rem; color:#222b45;">자연어로 청년정책을 검색하고 AI가 답변해드립니다</div>
    </div>
    """, unsafe_allow_html=True)
    
    # API 상태 확인
    if not check_api_health():
        st.error("⚠️ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        st.info("API 서버 실행 방법: `python api/main.py`")
        return
    
    # 사이드바
    with st.sidebar:
        st.header("설정")
        
        # 검색 모드 선택
        search_mode = st.radio(
            "검색 모드",
            ["정책 검색", "AI 답변"],
            help="정책 검색: 관련 정책 목록만 표시\nAI 답변: AI가 정책 정보를 바탕으로 답변 생성"
        )
        
        # 검색 결과 수 설정
        if search_mode == "정책 검색":
            k_results = st.slider("결과 수", 1, 10, 5)
        else:
            k_results = st.slider("참고할 정책 수", 1, 5, 3)
        
        st.markdown("---")
        st.markdown("#### 사용 예시")
        st.markdown("""
- 청년 일자리 지원 정책이 궁금해요
- 주거 지원 정책은 어떤 것이 있나요?
- 디지털 교육 프로그램에 대해 알려주세요
- 창업 지원 정책을 찾고 있어요
        """)
    
    # 메인 컨텐츠
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 검색 입력
        query = st.text_input(
            "질문을 입력하세요",
            placeholder="예: 청년 일자리 지원 정책이 궁금해요",
            help="자연어로 질문하시면 됩니다"
        )
        
        # 검색 버튼
        search_button = st.button("검색하기", type="primary")
    
    with col2:
        st.markdown("### 📊 통계")
        # 여기에 통계 정보 추가 가능
    
    # 검색 실행
    if search_button and query:
        with st.spinner("검색 중..."):
            if search_mode == "정책 검색":
                results = search_policies(query, k_results)
                
                if results.get("total_count", 0) > 0:
                    st.success(f"{results['total_count']}개의 관련 정책을 찾았습니다!")
                    st.markdown("#### 정책 결과")
                    for i, policy in enumerate(results["results"], 1):
                        display_policy_card(policy, i)
                else:
                    st.warning("관련 정책을 찾을 수 없습니다. 다른 키워드로 검색해보세요.")
            
            else:
                answer_result = generate_answer(query, k_results)
                st.markdown(f"""
                <div class="answer-box">
                    <h3 style="color:#1e90ff;">AI 답변</h3>
                    <div style="font-size:1.08rem;">{answer_result.get('answer', '답변을 생성할 수 없습니다.')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 참고한 정책 표시
                sources = answer_result.get("sources", [])
                if sources:
                    st.markdown("#### 참고한 정책")
                    for i, source in enumerate(sources, 1):
                        st.markdown(f"""
                        <div class="source-item">
                            <b>{i}. {source.get('title', '제목 없음')}</b><br>
                            주관기관: {source.get('agency', '정보 없음')}<br>
                            <a href="{source.get('page_url', '')}" target="_blank">상세 정보 보기</a>
                        </div>
                        """, unsafe_allow_html=True)
    
    # 하단 정보
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📞 문의")
        st.markdown("서울시 청년정책 관련 문의")
    
    with col2:
        st.markdown("### 🔗 유용한 링크")
        st.markdown("[서울시 청년정책](https://youth.seoul.go.kr)")
    
    with col3:
        st.markdown("### ℹ️ 정보")
        st.markdown("AI 기반 청년정책 검색 시스템")

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; color:#888; font-size:0.95rem;">'
        '공식 정책 정보는 <a href="https://youth.seoul.go.kr/mainA.do" target="_blank" style="color:#1e90ff;">서울시 청년포털</a>에서 확인할 수 있습니다.'
        '</div>', unsafe_allow_html=True
    )

if __name__ == "__main__":
    # 시스템 초기화
    if initialize_systems():
        main()
    else:
        st.error("시스템 초기화에 실패했습니다. 설정을 확인해주세요.") 