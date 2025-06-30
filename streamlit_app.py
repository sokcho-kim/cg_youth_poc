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
    page_title="서울 청년 정책 AI 상담사",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None

if 'web_search_system' not in st.session_state:
    st.session_state.web_search_system = None

def initialize_systems():
    """RAG 시스템들을 초기화합니다."""
    try:
        # OpenAI API 키 확인
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_api_key:
            st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. 환경변수 OPENAI_API_KEY를 설정해주세요.")
        
        # 정책 RAG 시스템 초기화 (ChromaDB 사용)
        if st.session_state.rag_system is None:
            with st.spinner("정책 RAG 시스템을 로드하는 중..."):
                st.session_state.rag_system = PolicyRAG(
                    openai_api_key=openai_api_key,
                    chroma_db_path="./chroma_db"
                )
        
        # 웹 검색 RAG 시스템 초기화
        if st.session_state.web_search_system is None:
            with st.spinner("웹 검색 시스템을 로드하는 중..."):
                st.session_state.web_search_system = WebSearchRAG(openai_api_key=openai_api_key)
                
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

def main():
    """메인 앱 함수"""
    st.title("🏙️ 서울 청년 정책 AI 상담사")
    st.markdown("---")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 시스템 초기화
        if st.button("🔄 시스템 초기화"):
            initialize_systems()
        
        # 검색 옵션
        st.subheader("검색 옵션")
        use_rag = st.checkbox("정책 데이터베이스 검색 (ChromaDB)", value=True)
        use_web_search = st.checkbox("웹 검색", value=False)
        
        # OpenAI 사용 여부
        openai_available = bool(os.getenv('OPENAI_API_KEY'))
        if openai_available:
            st.success("✅ OpenAI API 사용 가능")
        else:
            st.warning("⚠️ OpenAI API 키가 없습니다")
        
        # ChromaDB 상태 확인
        chroma_db_exists = os.path.exists("./chroma_db")
        if chroma_db_exists:
            st.success("✅ ChromaDB 데이터베이스 존재")
        else:
            st.warning("⚠️ ChromaDB 데이터베이스가 없습니다")
            st.info("먼저 벡터 저장소를 구축해주세요: python rag/build_vectorstore.py")
        
        # 통계 정보
        st.subheader("📊 통계")
        st.write(f"채팅 기록: {len(st.session_state.chat_history)}개")
        
        # 샘플 질문
        st.subheader("💡 샘플 질문")
        sample_questions = [
            "청년 일자리 지원 정책이 궁금해요",
            "주거 지원 정책은 어떤 것이 있나요?",
            "디지털 교육 프로그램에 대해 알려주세요",
            "청년 창업 지원 정책을 알고 싶어요"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{question}"):
                st.session_state.user_input = question
    
    # 메인 채팅 인터페이스
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 정책 상담")
        
        # 채팅 히스토리 표시
        for message in st.session_state.chat_history:
            display_chat_message(message, is_user=message['role'] == 'user')
        
        # 사용자 입력
        user_input = st.chat_input("정책에 대해 궁금한 점을 물어보세요...")
        
        if user_input:
            # 사용자 메시지 추가
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            })
            
            # 응답 생성
            responses = process_query(user_input, use_rag, use_web_search)
            
            # 응답 메시지 추가
            for response in responses:
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"[{response['type']}] {response['content']}",
                    'search_results': response['search_results'],
                    'timestamp': datetime.now().isoformat()
                })
            
            # 페이지 새로고침
            st.rerun()
    
    with col2:
        st.subheader("📋 응답 비교")
        
        if len(st.session_state.chat_history) >= 2:
            # 마지막 응답들 표시
            recent_responses = [msg for msg in st.session_state.chat_history[-3:] 
                              if msg['role'] == 'assistant']
            
            for i, response in enumerate(recent_responses):
                with st.expander(f"응답 {i+1}", expanded=True):
                    st.write(response['content'])
                    
                    if 'search_results' in response and response['search_results']:
                        st.write("**참고 정보:**")
                        for result in response['search_results'][:2]:
                            if 'metadata' in result:
                                st.write(f"• {result['metadata']['title']}")
                            else:
                                st.write(f"• {result['title']}")
    
    # 하단 정보
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**정책 RAG (ChromaDB)**: 수집된 정책 데이터베이스에서 관련 정보 검색")
    
    with col2:
        st.info("**웹 검색**: 최신 웹 정보를 검색하여 답변 생성")
    
    with col3:
        st.info("**AI 요약**: GPT를 사용하여 자연스러운 답변 생성")

if __name__ == "__main__":
    # 시스템 초기화
    if initialize_systems():
        main()
    else:
        st.error("시스템 초기화에 실패했습니다. 설정을 확인해주세요.") 