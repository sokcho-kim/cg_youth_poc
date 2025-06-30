#!/usr/bin/env python3
"""
ChromaDB 벡터 저장소 구축 스크립트
수집된 정책 데이터를 임베딩하여 ChromaDB 벡터 저장소를 생성
"""

import json
import os
import uuid
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from datetime import datetime

class PolicyVectorStore:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        정책 벡터 저장소 초기화
        
        Args:
            model_name: 사용할 임베딩 모델명
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
        # ChromaDB 클라이언트 초기화
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 컬렉션 이름
        self.collection_name = "seoul_youth_policies"
        
        # 기존 컬렉션이 있으면 삭제하고 새로 생성
        try:
            self.chroma_client.delete_collection(self.collection_name)
        except:
            pass
        
        # 새 컬렉션 생성
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"description": "서울시 청년 정책 데이터베이스"}
        )
        
        print(f"ChromaDB 컬렉션 '{self.collection_name}'이 생성되었습니다.")
        
    def load_policies(self, data_dir: str = "data/processed"):
        """정책 데이터를 로드합니다."""
        policies = []
        
        if not os.path.exists(data_dir):
            print(f"데이터 디렉토리가 존재하지 않습니다: {data_dir}")
            return policies
            
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            policies.extend(data)
                        else:
                            policies.append(data)
                    print(f"로드된 파일: {filename}")
                except Exception as e:
                    print(f"파일 로드 중 오류 발생 {filename}: {e}")
        
        print(f"총 {len(policies)}개의 정책이 로드되었습니다.")
        return policies
    
    def prepare_documents(self, policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """정책 데이터를 문서 형태로 변환합니다."""
        documents = []
        
        for i, policy in enumerate(policies):
            # 제목과 설명을 결합하여 문서 생성
            title = policy.get('title', '')
            description = policy.get('description', '')
            content = policy.get('content', '')
            
            # 문서 텍스트 구성
            doc_text = f"제목: {title}\n설명: {description}\n내용: {content}"
            
            # 메타데이터 구성
            metadata = {
                'title': title,
                'category': policy.get('category', ''),
                'url': policy.get('url', ''),
                'collected_at': policy.get('collected_at', ''),
                'original_index': i
            }
            
            documents.append({
                'id': str(uuid.uuid4()),
                'text': doc_text,
                'metadata': metadata
            })
        
        return documents
    
    def create_embeddings(self, documents: List[Dict[str, Any]]) -> List[np.ndarray]:
        """문서들을 임베딩합니다."""
        print("문서 임베딩을 시작합니다...")
        
        texts = [doc['text'] for doc in documents]
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        print(f"임베딩 완료: {embeddings.shape}")
        return embeddings.tolist()
    
    def build_index(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]):
        """ChromaDB 인덱스를 구축합니다."""
        print("ChromaDB 인덱스를 구축합니다...")
        
        # 데이터 준비
        ids = [doc['id'] for doc in documents]
        texts = [doc['text'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]
        
        # ChromaDB에 데이터 추가
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"인덱스 구축 완료: {len(documents)}개의 문서가 저장되었습니다.")
    
    def save_vectorstore_info(self, save_dir: str = "rag"):
        """벡터 저장소 정보를 저장합니다."""
        os.makedirs(save_dir, exist_ok=True)
        
        # 설정 정보 저장
        config = {
            'model_name': self.model_name,
            'collection_name': self.collection_name,
            'database_type': 'ChromaDB',
            'created_at': datetime.now().isoformat()
        }
        
        config_path = os.path.join(save_dir, "vectorstore_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"벡터 저장소 정보가 저장되었습니다: {config_path}")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """쿼리와 유사한 정책을 검색합니다."""
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

def main():
    """메인 실행 함수"""
    print("정책 벡터 저장소 구축을 시작합니다...")
    
    # 벡터 저장소 초기화
    vectorstore = PolicyVectorStore()
    
    # 정책 데이터 로드
    policies = vectorstore.load_policies()
    
    if not policies:
        print("로드할 정책 데이터가 없습니다.")
        return
    
    # 문서 준비
    documents = vectorstore.prepare_documents(policies)
    
    # 임베딩 생성
    embeddings = vectorstore.create_embeddings(documents)
    
    # 인덱스 구축
    vectorstore.build_index(documents, embeddings)
    
    # 벡터 저장소 정보 저장
    vectorstore.save_vectorstore_info()
    
    # 테스트 검색
    print("\n=== 테스트 검색 ===")
    test_queries = [
        "청년 일자리 지원",
        "주거 지원 정책",
        "디지털 교육 프로그램"
    ]
    
    for query in test_queries:
        print(f"\n쿼리: '{query}'")
        results = vectorstore.search(query, k=3)
        
        for result in results:
            print(f"  {result['rank']}. {result['metadata']['title']} (유사도: {result['score']:.3f})")

if __name__ == "__main__":
    main() 