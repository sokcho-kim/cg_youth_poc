import json
import os
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
import glob

class PolicyVectorizer:
    def __init__(self, embedding_model_name: str = "BM-K/KoSimCSE-roberta"):
        """
        정책 데이터를 벡터화하는 클래스
        
        Args:
            embedding_model_name: 임베딩 모델명 (기본값: KoSimCSE)
        """
        self.embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
        self.vectorstore = None
        
    def load_policy_data(self, data_dir: str = "data/processed") -> List[Dict]:
        """
        JSON 파일들에서 정책 데이터 로드
        
        Args:
            data_dir: 정책 JSON 파일들이 있는 디렉토리
            
        Returns:
            정책 데이터 리스트
        """
        policy_files = glob.glob(os.path.join(data_dir, "*.json"))
        policies = []
        
        for file_path in policy_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    policy = json.load(f)
                    policies.append(policy)
                print(f"✅ 로드됨: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"❌ 로드 실패: {file_path} - {e}")
                
        print(f"📊 총 {len(policies)}개 정책 로드 완료")
        return policies
    
    def create_policy_text(self, policy: Dict) -> str:
        """
        정책 데이터를 검색용 텍스트로 변환
        
        Args:
            policy: 정책 딕셔너리
            
        Returns:
            검색용 텍스트
        """
        text_parts = []
        
        # 제목 (가장 중요)
        if policy.get("title"):
            text_parts.append(f"제목: {policy['title']}")
        
        # 정책 소개
        if policy.get("introduction"):
            text_parts.append(f"정책 소개: {policy['introduction']}")
        
        # 지원 내용
        if policy.get("content"):
            text_parts.append(f"지원 내용: {policy['content']}")
        
        # 정책 유형
        if policy.get("policy_type"):
            text_parts.append(f"정책 유형: {policy['policy_type']}")
        
        # 주관 기관
        if policy.get("agency"):
            text_parts.append(f"주관 기관: {policy['agency']}")
        
        # 신청자격 (연령, 학력 등)
        if policy.get("age_range"):
            text_parts.append(f"연령: {policy['age_range']}")
        if policy.get("education"):
            text_parts.append(f"학력: {policy['education']}")
        if policy.get("employment_status"):
            text_parts.append(f"취업상태: {policy['employment_status']}")
        
        # 신청기간
        if policy.get("apply_start") and policy.get("apply_end"):
            text_parts.append(f"신청기간: {policy['apply_start']} ~ {policy['apply_end']}")
        
        # 지원규모
        if policy.get("support_scale"):
            text_parts.append(f"지원규모: {policy['support_scale']}")
        
        return "\n".join(text_parts)
    
    def create_metadata(self, policy: Dict) -> Dict:
        """
        정책 메타데이터 생성
        
        Args:
            policy: 정책 딕셔너리
            
        Returns:
            메타데이터 딕셔너리
        """
        metadata = {
            "policy_id": policy.get("plcyBizId", ""),
            "title": policy.get("title", ""),
            "policy_type": policy.get("policy_type", ""),
            "agency": policy.get("agency", ""),
            "age_range": policy.get("age_range", ""),
            "education": policy.get("education", ""),
            "employment_status": policy.get("employment_status", ""),
            "apply_start": policy.get("apply_start", ""),
            "apply_end": policy.get("apply_end", ""),
            "support_scale": policy.get("support_scale", ""),
            "page_url": policy.get("page_url", ""),
            "application_site": policy.get("application_site", "")
        }
        
        # 빈 값 제거
        metadata = {k: v for k, v in metadata.items() if v}
        return metadata
    
    def vectorize_policies(self, policies: List[Dict], persist_directory: str = "vectorstore"):
        """
        정책들을 벡터화하여 ChromaDB에 저장
        
        Args:
            policies: 정책 데이터 리스트
            persist_directory: 벡터스토어 저장 디렉토리
        """
        documents = []
        
        for policy in policies:
            # 정책 텍스트 생성
            text = self.create_policy_text(policy)
            if not text.strip():
                print(f"⚠️ 텍스트가 비어있음: {policy.get('plcyBizId', 'Unknown')}")
                continue
            
            # 메타데이터 생성
            metadata = self.create_metadata(policy)
            
            # Document 객체 생성
            doc = Document(
                page_content=text,
                metadata=metadata
            )
            documents.append(doc)
            
            print(f"📝 벡터화 준비: {policy.get('title', 'Unknown')[:30]}...")
        
        print(f"🔍 총 {len(documents)}개 문서 벡터화 시작...")
        
        # ChromaDB에 저장
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            persist_directory=persist_directory
        )
        
        # 저장
        self.vectorstore.persist()
        print(f"✅ 벡터스토어 저장 완료: {persist_directory}")
        
        return self.vectorstore
    
    def test_search(self, query: str, k: int = 3):
        """
        검색 테스트
        
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
        """
        if not self.vectorstore:
            print("❌ 벡터스토어가 로드되지 않았습니다.")
            return
        
        print(f"🔍 검색 쿼리: '{query}'")
        results = self.vectorstore.similarity_search(query, k=k)
        
        for i, doc in enumerate(results, 1):
            print(f"\n📋 결과 {i}:")
            print(f"   제목: {doc.metadata.get('title', 'N/A')}")
            print(f"   정책ID: {doc.metadata.get('policy_id', 'N/A')}")
            print(f"   정책유형: {doc.metadata.get('policy_type', 'N/A')}")
            print(f"   연령: {doc.metadata.get('age_range', 'N/A')}")
            print(f"   내용 일부: {doc.page_content[:100]}...")

def main():
    """메인 실행 함수"""
    print("🚀 정책 벡터화 시작...")
    
    # 벡터라이저 초기화
    vectorizer = PolicyVectorizer()
    
    # 정책 데이터 로드
    policies = vectorizer.load_policy_data()
    
    if not policies:
        print("❌ 로드할 정책 데이터가 없습니다.")
        return
    
    # 벡터화 및 저장
    vectorstore = vectorizer.vectorize_policies(policies)
    
    # 테스트 검색
    print("\n🧪 검색 테스트:")
    test_queries = [
        "30대 무직자 취업 지원",
        "청년 창업 지원",
        "학력 제한없는 일자리",
        "서울시 청년 정책"
    ]
    
    for query in test_queries:
        vectorizer.test_search(query)
        print("\n" + "="*50)

if __name__ == "__main__":
    main() 