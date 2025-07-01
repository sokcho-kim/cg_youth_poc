import requests
from bs4 import BeautifulSoup
import json

BASE_VIEW_URL = "https://youth.seoul.go.kr/infoData/plcyInfo/view.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

# 테스트할 정책 ID
test_id = "R2024112828265"

# 상세 페이지 요청
res = requests.get(BASE_VIEW_URL, params={"plcyBizId": test_id}, headers=HEADERS)
print(f"🔗 요청 URL: {res.url}")
print(f"📊 상태 코드: {res.status_code}")

# HTML 저장
with open("detail_full_debug.html", "w", encoding="utf-8") as f:
    f.write(res.text)
print("📄 HTML 저장됨: detail_full_debug.html")

# 파싱 시도
soup = BeautifulSoup(res.text, "html.parser")

# 모든 테이블 찾기
all_tables = soup.find_all("table")
print(f"📌 총 테이블 수: {len(all_tables)}")

# 각 테이블 분석
for i, table in enumerate(all_tables):
    print(f"\n🔍 테이블 {i+1}:")
    print(f"   클래스: {table.get('class', '없음')}")
    
    # 테이블 제목 찾기
    prev_sibling = table.find_previous_sibling()
    if prev_sibling and prev_sibling.name == 'strong':
        print(f"   제목: {prev_sibling.text.strip()}")
    
    # 테이블 내용 분석
    rows = table.find_all("tr")
    print(f"   행 수: {len(rows)}")
    
    # 첫 몇 행의 내용 확인
    for j, row in enumerate(rows[:3]):
        th_elements = row.find_all("th")
        td_elements = row.find_all("td")
        print(f"     행 {j+1}: th={len(th_elements)}, td={len(td_elements)}")
        
        for k, th in enumerate(th_elements):
            if k < len(td_elements):
                label = th.text.strip()
                value = td_elements[k].text.strip()[:50]
                print(f"       {label}: {value}...")

# 특정 섹션 찾기
sections = soup.find_all("div", class_="mt30")
print(f"\n📌 mt30 섹션 수: {len(sections)}")

for i, section in enumerate(sections):
    print(f"\n🔍 섹션 {i+1}:")
    strong = section.find("strong")
    if strong:
        print(f"   제목: {strong.text.strip()}")
    
    table = section.find("table")
    if table:
        rows = table.find_all("tr")
        print(f"   테이블 행 수: {len(rows)}")

# 기타 정보 찾기
print(f"\n🔍 기타 정보:")
print(f"   제목: {soup.select_one('.policy-detail .title')}")
print(f"   사업개요 테이블: {len(soup.select('.policy-detail .form-table'))}")
print(f"   신청방법 테이블: {len(soup.select('.policy-detail .mt30 .form-table'))}") 