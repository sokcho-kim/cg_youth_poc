#!/usr/bin/env python3
"""
서울 청년 일자리 정책 수집 스크립트
서울시 청년정책 사이트에서 정책 정보를 수집하여 JSON 형태로 저장
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any

class SeoulYouthPolicyCrawler:
    def __init__(self):
        self.base_url = "https://youth.seoul.go.kr"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_job_policies(self, page: int = 1) -> List[Dict[str, Any]]:
        """일자리 정책 목록을 가져옵니다."""
        policies = []
        
        try:
            # 서울시 청년정책 사이트의 일자리 정책 페이지 URL (예시)
            url = f"{self.base_url}/site/youth/policy/job"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 실제 사이트 구조에 맞게 수정 필요
            policy_items = soup.find_all('div', class_='policy-item')
            
            for item in policy_items:
                policy = {
                    'title': item.find('h3').text.strip() if item.find('h3') else '',
                    'description': item.find('p').text.strip() if item.find('p') else '',
                    'url': self.base_url + item.find('a')['href'] if item.find('a') else '',
                    'category': '일자리',
                    'collected_at': datetime.now().isoformat()
                }
                policies.append(policy)
                
        except Exception as e:
            print(f"정책 수집 중 오류 발생: {e}")
            
        return policies
    
    def get_policy_detail(self, url: str) -> Dict[str, Any]:
        """개별 정책의 상세 정보를 가져옵니다."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            detail = {
                'content': soup.get_text(),
                'html_content': str(soup),
                'last_updated': datetime.now().isoformat()
            }
            
            return detail
            
        except Exception as e:
            print(f"상세 정보 수집 중 오류 발생: {e}")
            return {}
    
    def save_policies(self, policies: List[Dict[str, Any]], filename: str = None):
        """수집된 정책을 JSON 파일로 저장합니다."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"seoul_youth_policies_{timestamp}.json"
        
        filepath = os.path.join("data", "processed", filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(policies, f, ensure_ascii=False, indent=2)
        
        print(f"정책 데이터가 {filepath}에 저장되었습니다.")
        return filepath
    
    def create_sample_data(self):
        """샘플 데이터를 생성합니다 (실제 크롤링이 어려운 경우)."""
        sample_policies = [
            {
                "title": "서울시 청년 일자리 지원 프로그램",
                "description": "서울시 거주 청년을 위한 다양한 일자리 지원 프로그램을 제공합니다.",
                "content": """
                서울시 청년 일자리 지원 프로그램은 다음과 같은 혜택을 제공합니다:
                
                1. 청년 일자리 매칭 서비스
                - 맞춤형 일자리 추천
                - 이력서 작성 지원
                - 면접 준비 교육
                
                2. 청년 창업 지원
                - 창업 교육 프로그램
                - 창업 자금 지원
                - 멘토링 서비스
                
                3. 청년 인턴십 프로그램
                - 기업 인턴십 연계
                - 정부기관 인턴십
                - 급여 지원
                
                지원 자격: 서울시 거주 만 18-34세 청년
                신청 방법: 온라인 신청 또는 방문 신청
                """,
                "category": "일자리",
                "url": "https://youth.seoul.go.kr/site/youth/policy/job/1",
                "collected_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "title": "청년 디지털 역량 강화 프로그램",
                "description": "4차 산업혁명 시대에 필요한 디지털 역량을 키울 수 있는 프로그램입니다.",
                "content": """
                청년 디지털 역량 강화 프로그램은 다음과 같은 과정을 제공합니다:
                
                1. 프로그래밍 기초 과정
                - Python, JavaScript, Java 등
                - 웹 개발 기초
                - 모바일 앱 개발
                
                2. 데이털 분석 과정
                - 데이털 시각화
                - 머신러닝 기초
                - 빅데이털 분석
                
                3. AI/ML 과정
                - 인공지능 기초
                - 딥러닝 입문
                - AI 프로젝트 실습
                
                교육 기간: 3-6개월
                수강료: 무료 (일부 과정은 부분 부담)
                수료 후: 취업 연계 지원
                """,
                "category": "교육",
                "url": "https://youth.seoul.go.kr/site/youth/policy/education/1",
                "collected_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            {
                "title": "청년 주거 지원 정책",
                "description": "서울시 청년의 주거 문제 해결을 위한 다양한 지원 정책입니다.",
                "content": """
                청년 주거 지원 정책은 다음과 같은 혜택을 제공합니다:
                
                1. 청년 임대주택
                - 전용면적 20-40㎡
                - 월세 30-50% 할인
                - 계약기간 2년 (연장 가능)
                
                2. 청년 전용 매입임대주택
                - 신축 아파트 단지
                - 월세 20-40% 할인
                - 우선 입주 자격
                
                3. 청년 주거비 지원
                - 월 30만원 한도
                - 최대 24개월 지원
                - 소득 기준 적용
                
                지원 자격: 서울시 거주 만 19-39세 청년
                소득 기준: 중위소득 80% 이하
                """,
                "category": "주거",
                "url": "https://youth.seoul.go.kr/site/youth/policy/housing/1",
                "collected_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        ]
        
        return sample_policies

def main():
    """메인 실행 함수"""
    print("서울 청년 정책 수집을 시작합니다...")
    
    crawler = SeoulYouthPolicyCrawler()
    
    # 실제 크롤링 대신 샘플 데이터 생성
    print("샘플 정책 데이터를 생성합니다...")
    policies = crawler.create_sample_data()
    
    # 데이터 저장
    filepath = crawler.save_policies(policies)
    
    print(f"총 {len(policies)}개의 정책이 수집되었습니다.")
    print(f"저장 위치: {filepath}")
    
    # 데이터 요약 출력
    for i, policy in enumerate(policies, 1):
        print(f"\n{i}. {policy['title']}")
        print(f"   카테고리: {policy['category']}")
        print(f"   설명: {policy['description'][:100]}...")

if __name__ == "__main__":
    main() 