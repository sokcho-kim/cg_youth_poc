import requests
import json

# API 기본 URL
BASE_URL = "http://localhost:8000"

def test_health():
    """헬스 체크 테스트"""
    print("🔍 헬스 체크 테스트...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {response.json()}")
    print()

def test_search():
    """검색 API 테스트"""
    print("🔍 검색 API 테스트...")
    
    test_queries = [
        "30대 무직자 취업 지원",
        "청년 창업 지원",
        "학력 제한없는 일자리"
    ]
    
    for query in test_queries:
        print(f"쿼리: '{query}'")
        payload = {
            "query": query,
            "k": 3
        }
        
        response = requests.post(f"{BASE_URL}/search", json=payload)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"검색 결과 수: {data['total_count']}")
            for i, result in enumerate(data['results'], 1):
                print(f"  {i}. {result['title']}")
                print(f"     정책유형: {result['policy_type']}")
                print(f"     연령: {result['age_range']}")
        else:
            print(f"오류: {response.text}")
        print()

def test_answer():
    """답변 생성 API 테스트"""
    print("🤖 답변 생성 API 테스트...")
    
    test_queries = [
        "30대인 무직자인데 취업하고 싶어",
        "청년 창업하고 싶은데 지원받을 수 있어?",
        "학력이 낮아도 지원받을 수 있는 정책이 있을까?"
    ]
    
    for query in test_queries:
        print(f"질문: '{query}'")
        payload = {
            "query": query,
            "k": 3
        }
        
        response = requests.post(f"{BASE_URL}/answer", json=payload)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("답변:")
            print(data['answer'])
            print(f"신뢰도: {data['confidence']}")
            print(f"소스 수: {len(data['sources'])}")
        else:
            print(f"오류: {response.text}")
        print("="*50)

def test_policy_detail():
    """정책 상세 정보 API 테스트"""
    print("📋 정책 상세 정보 API 테스트...")
    
    # 실제 정책 ID 사용
    policy_id = "R2024112828265"
    
    response = requests.get(f"{BASE_URL}/policy/{policy_id}")
    print(f"상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"제목: {data.get('title', 'N/A')}")
        print(f"정책유형: {data.get('policy_type', 'N/A')}")
        print(f"주관기관: {data.get('agency', 'N/A')}")
    else:
        print(f"오류: {response.text}")
    print()

if __name__ == "__main__":
    print("🚀 FastAPI 테스트 시작...")
    print()
    
    try:
        test_health()
        test_search()
        test_answer()
        test_policy_detail()
        
        print("✅ 모든 테스트 완료!")
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인해주세요.")
        print("서버 실행 명령어: python api/main.py")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}") 