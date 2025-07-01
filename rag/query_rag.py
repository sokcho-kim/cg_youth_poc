#!/usr/bin/env python3
"""
RAG 응답 생성 스크립트 (ChromaDB 기반)
벡터 저장소를 사용하여 질의에 대한 답변을 생성
"""

import os
import json
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import tiktoken

class PolicyRAG:
    def __init__(self, 
                 vectorstore_dir: str = "rag",
                 chroma_db_path: str = "./chroma_db",
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 openai_api_key: Optional[str] = None):
        """
        정책 RAG 시스템 초기화
        
        Args:
            vectorstore_dir: 벡터 저장소 설정 디렉토리
            chroma_db_path: ChromaDB 데이터베이스 경로
            model_name: 임베딩 모델명
            openai_api_key: OpenAI API 키
        """
        self.vectorstore_dir = vectorstore_dir
        self.chroma_db_path = chroma_db_path
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
        # OpenAI 클라이언트 초기화
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None
            
        # ChromaDB 클라이언트 및 컬렉션 로드
        self.chroma_client = None
        self.collection = None
        self.config = {}
        self.load_vectorstore()
        
    def load_vectorstore(self):
        """ChromaDB 벡터 저장소를 로드합니다."""
        try:
            # ChromaDB 클라이언트 초기화
            if os.path.exists(self.chroma_db_path):
                self.chroma_client = chromadb.PersistentClient(
                    path=self.chroma_db_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                print(f"ChromaDB 클라이언트 로드 완료: {self.chroma_db_path}")
            else:
                print(f"ChromaDB 데이터베이스가 존재하지 않습니다: {self.chroma_db_path}")
                return
            
            # 컬렉션 로드
            collection_name = "seoul_youth_policies"
            try:
                self.collection = self.chroma_client.get_collection(collection_name)
                print(f"컬렉션 로드 완료: {collection_name}")
                print(f"저장된 문서 수: {self.collection.count()}")
            except Exception as e:
                print(f"컬렉션 로드 실패: {e}")
                return
            
            # 설정 로드
            config_path = os.path.join(self.vectorstore_dir, "vectorstore_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print("설정 로드 완료")
                
        except Exception as e:
            print(f"벡터 저장소 로드 중 오류 발생: {e}")
    
    def search_policies(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """쿼리와 유사한 정책을 검색합니다."""
        if self.collection is None:
            raise ValueError("ChromaDB 컬렉션이 로드되지 않았습니다.")
        
        try:
            # 쿼리 임베딩
            query_embedding = self.model.encode([query])
            
            # ChromaDB 검색
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=k
            )
            
            # 결과 변환
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i, (doc_id, distance, metadata, document) in enumerate(zip(
                    results['ids'][0], 
                    results['distances'][0], 
                    results['metadatas'][0], 
                    results['documents'][0]
                )):
                    result = {
                        'rank': i + 1,
                        'score': float(1 - distance),  # 거리를 유사도로 변환
                        'metadata': metadata,
                        'content': document
                    }
                    search_results.append(result)
            
            return search_results
            
        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
            return []
    
    def create_context(self, search_results: List[Dict[str, Any]]) -> str:
        """검색 결과를 컨텍스트로 변환합니다."""
        context_parts = []
        
        for result in search_results:
            metadata = result['metadata']
            context_parts.append(f"""
정책 {result['rank']}: {metadata['title']}
카테고리: {metadata['category']}
URL: {metadata['url']}
유사도 점수: {result['score']:.3f}
내용: {result['content'][:500]}...
""")
        
        return "\n".join(context_parts)
    
    def generate_response_with_openai(self, query: str, context: str) -> str:
        """OpenAI를 사용하여 응답을 생성합니다."""
        if not self.openai_client:
            return "OpenAI API 키가 설정되지 않았습니다."
        
        prompt = f"""
당신은 서울시 청년 정책 전문 상담사입니다. 
다음은 사용자의 질문과 관련된 정책 정보입니다:

사용자 질문: {query}

관련 정책 정보:
{context}

위 정보를 바탕으로 사용자의 질문에 친절하고 정확하게 답변해주세요.
답변은 한국어로 작성하고, 구체적인 정책명과 지원 내용을 포함해주세요.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 서울시 청년 정책 전문 상담사입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"응답 생성 중 오류가 발생했습니다: {e}"
    
    def generate_simple_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """간단한 응답을 생성합니다 (OpenAI 없이)."""
        if not search_results:
            return "관련된 정책을 찾을 수 없습니다."
        
        response_parts = [f"'{query}'와 관련된 정책을 찾았습니다:\n"]
        
        for result in search_results:
            metadata = result['metadata']
            response_parts.append(f"""
{result['rank']}. {metadata['title']}
   - 카테고리: {metadata['category']}
   - 관련도: {result['score']:.1%}
   - 자세한 정보: {metadata['url']}
""")
        
        response_parts.append("\n더 자세한 정보는 위 링크를 통해 확인하실 수 있습니다.")
        
        return "\n".join(response_parts)
    
    def query(self, question: str, use_openai: bool = True, k: int = 5) -> Dict[str, Any]:
        """질의응답을 처리합니다."""
        try:
            # 정책 검색
            search_results = self.search_policies(question, k)
            
            # 컨텍스트 생성
            context = self.create_context(search_results)
            
            # 응답 생성
            if use_openai and self.openai_client:
                answer = self.generate_response_with_openai(question, context)
            else:
                answer = self.generate_simple_response(question, search_results)
            
            return {
                'question': question,
                'answer': answer,
                'search_results': search_results,
                'context': context,
                'used_openai': use_openai and self.openai_client is not None
            }
            
        except Exception as e:
            return {
                'question': question,
                'answer': f"오류가 발생했습니다: {e}",
                'search_results': [],
                'context': "",
                'used_openai': False,
                'error': str(e)
            }

def main():
    """메인 실행 함수"""
    print("정책 RAG 시스템을 시작합니다...")
    
    # OpenAI API 키 확인
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    # RAG 시스템 초기화
    rag = PolicyRAG(openai_api_key=openai_api_key)
    
    # 테스트 질의
    test_questions = [
        "청년 일자리 지원 정책이 궁금해요",
        "주거 지원 정책은 어떤 것이 있나요?",
        "디지털 교육 프로그램에 대해 알려주세요"
    ]
    
    for question in test_questions:
        print(f"\n{'='*50}")
        print(f"질문: {question}")
        print(f"{'='*50}")
        
        result = rag.query(question, use_openai=bool(openai_api_key))
        
        print(f"답변: {result['answer']}")
        
        if result['search_results']:
            print(f"\n참고한 정책:")
            for sr in result['search_results'][:3]:
                print(f"  - {sr['metadata']['title']} (유사도: {sr['score']:.3f})")

if __name__ == "__main__":
    main() 