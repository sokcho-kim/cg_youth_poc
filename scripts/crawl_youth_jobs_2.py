from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re

BASE_LIST_URL = "https://youth.seoul.go.kr/infoData/plcyInfo/list.do"
BASE_VIEW_URL = "https://youth.seoul.go.kr/infoData/plcyInfo/view.do"

PARAMS = {
    "sc_plcyFldCd": "023010",  # 일자리 분야
    "orderBy": "regYmd desc"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

SAVE_PATH = "data/processed"
os.makedirs(SAVE_PATH, exist_ok=True)

def get_policy_ids_selenium(page=1):
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # 디버깅을 위해 주석 처리
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Windows 환경에서 ChromeDriver 경로 설정
    chrome_driver_path = r"C:\Users\sokch\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"
    service = Service(executable_path=chrome_driver_path)
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    url = f"{BASE_LIST_URL}?sc_plcyFldCd=023010&pageIndex={page}&orderBy=regYmd+desc"
    print(f"🔗 접속 URL: {url}")
    driver.get(url)
    
    # 페이지 로딩 대기
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".policy-list")))
        print("✅ 페이지 로딩 완료")
    except:
        print("❌ 페이지 로딩 실패")
        # HTML 저장해서 디버깅
        with open(f"debug_page_{page}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"📄 HTML 저장됨: debug_page_{page}.html")
    
    time.sleep(3)

    # 정책 목록에서 ID 추출
    print("🔍 정책 목록에서 ID 추출 중...")
    
    # 서울시 정책 목록
    seoul_policies = driver.find_elements(By.CSS_SELECTOR, ".policy-list li a[onclick*='goView']")
    print(f"   - 서울시 정책 수: {len(seoul_policies)}")
    
    ids = []
    for policy in seoul_policies:
        try:
            onclick = policy.get_attribute("onclick")
            if onclick:
                match = re.search(r"goView\('([^']+)'\)", onclick)
                if match:
                    policy_id = match.group(1)
                    ids.append(policy_id)
                    print(f"   ✅ 서울시 정책 ID 찾음: {policy_id}")
        except Exception as e:
            print(f"   ❌ 정책 처리 오류: {e}")
    
    # 중복 제거
    ids = list(set(ids))
    print(f"🔹 총 고유 ID 수: {len(ids)}")
    
    driver.quit()
    return ids

def parse_detail(policy_id):
    res = requests.get(BASE_VIEW_URL, params={"plcyBizId": policy_id}, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    title = soup.select_one(".policy-title h3")
    title = title.text.strip() if title else ""

    info_table = soup.select(".table-wrap table tr")
    data = {
        "title": title,
        "plcyBizId": policy_id,
        "tags": ["일자리"],
        "page_url": f"{BASE_VIEW_URL}?plcyBizId={policy_id}"
    }
    
    for row in info_table:
        th = row.select_one("th")
        td = row.select_one("td")
        if not th or not td:
            continue
        label = th.text.strip()
        value = td.text.strip().replace("\xa0", " ")

        if "신청기간" in label:
            if "~" in value:
                data["apply_start"], data["apply_end"] = [v.strip() for v in value.split("~")]
            else:
                data["apply_start"] = value
                data["apply_end"] = ""
        elif "지원대상" in label:
            data["target"] = value
        elif "주관기관" in label or "담당기관" in label:
            data["agency"] = value
        elif "첨부" in label:
            file_link = td.select_one("a")
            if file_link and file_link.has_attr("href"):
                data["file_url"] = "https://youth.seoul.go.kr" + str(file_link["href"])
        elif "지원내용" in label:
            data["content"] = value

    return data

def save_json(data):
    fname = os.path.join(SAVE_PATH, f"{data['plcyBizId']}.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    all_ids = []
    max_pages = 1  # 디버깅을 위해 1페이지만 시도
    
    for page in range(1, max_pages + 1):
        print(f"📄 {page}페이지 정책ID 수집 중...")
        ids = get_policy_ids_selenium(page)
        print(f"🔹 수집된 ID 수: {len(ids)}")
        if not ids:
            print("❌ ID를 찾을 수 없습니다. HTML 파일을 확인해주세요.")
            break
        all_ids.extend(ids)
        time.sleep(1)

    if all_ids:
        print(f"🔎 총 {len(all_ids)}건 수집 시작...")
        for pid in all_ids:
            print(f"▶ {pid} 수집 중...")
            try:
                detail = parse_detail(pid)
                save_json(detail)
                print(f"✅ 저장 완료: {detail['title']}")
            except Exception as e:
                print(f"❌ 에러 발생: {e}")
            time.sleep(1)
    else:
        print("❌ 수집할 ID가 없습니다.")
