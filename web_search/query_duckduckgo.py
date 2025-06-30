#!/usr/bin/env python3
"""
DuckDuckGo 기반 검색 응답 스크립트
웹 검색을 통해 최신 정보를 수집하고 GPT로 요약 생성
"""

import os
import json
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
from openai import OpenAI
import time

class WebSearchRAG:
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        웹 검색 RAG 시스템 초기화
        
        Args:
            openai_api_key: OpenAI API 키
        """
        self.openai_client = None
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        
        self.ddgs = DDGS()
        
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """DuckDuckGo를 사용하여 웹 검색을 수행합니다."""
        try:
            # 한국어 검색을 위해 쿼리에 "서울 청년 정책" 추가
            search_query = f"{query} 서울 청년 정책"
            
            results = []
            search_results = self.ddgs.text(search_query, max_results=max_results)
            
            for result in search_results:
                results.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'snippet': result.get('body', ''),
                    'source': result.get('link', '').split('/')[2] if result.get('link') else ''
                })
            
            return results
            
        except Exception as e:
            print(f"웹 검색 중 오류 발생: {e}")
            return []
    
    def create_search_context(self, search_results: List[Dict[str, Any]]) -> str:
        """검색 결과를 컨텍스트로 변환합니다."""
        if not search_results:
            return "관련된 웹 검색 결과가 없습니다."
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"""
검색 결과 {i}:
제목: {result['title']}
출처: {result['source']}
링크: {result['link']}
내용: {result['snippet']}
""")
        
        return "\n".join(context_parts)
    
    def summarize_with_gpt(self, query: str, context: str) -> str:
        """GPT를 사용하여 검색 결과를 요약합니다."""
        if not self.openai_client:
            return "OpenAI API 키가 설정되지 않았습니다."
        
        prompt = f"""
당신은 서울시 청년 정책 전문가입니다.
다음은 사용자의 질문과 관련된 최신 웹 검색 결과입니다:

사용자 질문: {query}

웹 검색 결과:
{context}

위 검색 결과를 바탕으로 사용자의 질문에 대한 최신 정보를 포함한 답변을 생성해주세요.
답변은 다음을 포함해야 합니다:
1. 질문에 대한 직접적인 답변
2. 최신 정책 정보나 동향
3. 관련 웹사이트나 출처 정보
4. 추가 확인이 필요한 사항

답변은 한국어로 작성하고, 친절하고 정확하게 작성해주세요.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 서울시 청년 정책 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"요약 생성 중 오류가 발생했습니다: {e}"
    
    def create_simple_summary(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """간단한 요약을 생성합니다 (GPT 없이)."""
        if not search_results:
            return f"'{query}'에 대한 최신 정보를 찾을 수 없습니다."
        
        summary_parts = [f"'{query}'에 대한 최신 웹 검색 결과입니다:\n"]
        
        for i, result in enumerate(search_results, 1):
            summary_parts.append(f"""
{i}. {result['title']}
   출처: {result['source']}
   내용: {result['snippet'][:200]}...
   링크: {result['link']}
""")
        
        summary_parts.append("\n더 자세한 정보는 위 링크를 통해 확인하실 수 있습니다.")
        
        return "\n".join(summary_parts)
    
    def query(self, question: str, use_gpt: bool = True, max_results: int = 5) -> Dict[str, Any]:
        """웹 검색 기반 질의응답을 처리합니다."""
        try:
            # 웹 검색 수행
            search_results = self.search_web(question, max_results)
            
            # 컨텍스트 생성
            context = self.create_search_context(search_results)
            
            # 응답 생성
            if use_gpt and self.openai_client:
                answer = self.summarize_with_gpt(question, context)
            else:
                answer = self.create_simple_summary(question, search_results)
            
            return {
                'question': question,
                'answer': answer,
                'search_results': search_results,
                'context': context,
                'used_gpt': use_gpt and self.openai_client is not None,
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {
                'question': question,
                'answer': f"오류가 발생했습니다: {e}",
                'search_results': [],
                'context': "",
                'used_gpt': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def save_search_history(self, query_result: Dict[str, Any], filename: str = None):
        """검색 결과를 파일로 저장합니다."""
        if not filename:
            timestamp = int(query_result.get('timestamp', time.time()))
            filename = f"web_search_{timestamp}.json"
        
        filepath = os.path.join("data", "processed", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(query_result, f, ensure_ascii=False, indent=2)
        
        print(f"검색 결과가 {filepath}에 저장되었습니다.")

def main():
    """메인 실행 함수"""
    print("웹 검색 RAG 시스템을 시작합니다...")
    
    # OpenAI API 키 확인
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    # 웹 검색 RAG 시스템 초기화
    web_rag = WebSearchRAG(openai_api_key=openai_api_key)
    
    # 테스트 질의
    test_questions = [
        "2024년 서울시 청년 일자리 지원 정책",
        "청년 주거 지원 최신 정보",
        "서울시 청년 창업 지원 프로그램"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"질문: {question}")
        print(f"{'='*60}")
        
        result = web_rag.query(question, use_gpt=bool(openai_api_key))
        
        print(f"답변: {result['answer']}")
        
        if result['search_results']:
            print(f"\n참고한 웹 검색 결과:")
            for i, sr in enumerate(result['search_results'][:3], 1):
                print(f"  {i}. {sr['title']} ({sr['source']})")
        
        # 검색 결과 저장
        web_rag.save_search_history(result)

if __name__ == "__main__":
    main() 