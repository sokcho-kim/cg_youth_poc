import requests
from bs4 import BeautifulSoup
import json
import os

BASE_VIEW_URL = "https://youth.seoul.go.kr/infoData/plcyInfo/view.do"
SAVE_PATH = "data/processed"
os.makedirs(SAVE_PATH, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def parse_detail(policy_id):
    res = requests.get(BASE_VIEW_URL, params={"plcyBizId": policy_id}, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    # 제목 추출
    title = soup.select_one(".policy-detail .title")
    title = title.text.strip() if title else ""

    data = {
        "title": title,
        "plcyBizId": policy_id,
        "tags": ["일자리"],
        "page_url": f"{BASE_VIEW_URL}?plcyBizId={policy_id}"
    }

    # 모든 테이블 찾기
    all_tables = soup.find_all("table", class_="form-table")
    
    for table in all_tables:
        # 테이블 제목 찾기
        prev_sibling = table.find_previous_sibling()
        table_title = ""
        if prev_sibling and prev_sibling.name == 'strong':
            table_title = prev_sibling.text.strip()
        
        rows = table.find_all("tr")
        
        for row in rows:
            th_elements = row.find_all("th")
            td_elements = row.find_all("td")
            
            for i, th in enumerate(th_elements):
                if i < len(td_elements):
                    label = th.text.strip()
                    td = td_elements[i]
                    value = td.text.strip().replace("\xa0", " ")
                    
                    # 사업개요 테이블
                    if "사업개요" in table_title:
                        if "정책 유형" in label:
                            data["policy_type"] = value
                        elif "주관 기관" in label:
                            data["agency"] = value
                        elif "정책 소개" in label:
                            data["introduction"] = value
                        elif "지원 내용" in label:
                            data["content"] = value
                        elif "사업운영기간" in label:
                            data["operation_period"] = value
                        elif "사업신청기간" in label:
                            if "~" in value:
                                parts = [v.strip() for v in value.split("~")]
                                if len(parts) >= 2:
                                    data["apply_start"] = parts[0]
                                    data["apply_end"] = parts[-1]  # 마지막 부분을 종료일로
                                else:
                                    data["apply_start"] = value
                                    data["apply_end"] = ""
                            else:
                                data["apply_start"] = value
                                data["apply_end"] = ""
                        elif "지원규모" in label:
                            data["support_scale"] = value
                        elif "관련 사이트" in label:
                            link = td.find("a")
                            if link and link.has_attr("href"):
                                data["related_site"] = link["href"]
                    
                    # 신청자격 테이블
                    elif "신청자격" in table_title:
                        if "연령" in label:
                            data["age_range"] = value
                        elif "학력" in label:
                            data["education"] = value
                        elif "전공요건" in label:
                            data["major_requirement"] = value
                        elif "취업상태" in label:
                            data["employment_status"] = value
                        elif "특화분야 요건" in label:
                            data["specialized_field"] = value
                        elif "추가단서 사항" in label:
                            data["additional_requirements"] = value
                        elif "참여제한 대상" in label:
                            data["excluded_targets"] = value
                    
                    # 신청방법 테이블
                    elif "신청방법" in table_title:
                        if "신청절차" in label:
                            data["application_procedure"] = value
                        elif "심사 및 발표" in label:
                            data["evaluation_announcement"] = value
                        elif "제출서류" in label:
                            data["required_documents"] = value
                        elif "신청 사이트" in label:
                            link = td.find("a")
                            if link and link.has_attr("href"):
                                data["application_site"] = link["href"]
                    
                    # 기타 테이블
                    elif "기타" in table_title:
                        if "기타사항" in label:
                            data["other_matters"] = value
                        elif "운영기관" in label:
                            data["operating_agency"] = value
                        elif "참고 사이트 Ⅰ" in label:
                            link = td.find("a")
                            if link and link.has_attr("href"):
                                data["reference_site_1"] = link["href"]
                        elif "참고 사이트 Ⅱ" in label:
                            link = td.find("a")
                            if link and link.has_attr("href"):
                                data["reference_site_2"] = link["href"]

    return data

def save_json(data):
    fname = os.path.join(SAVE_PATH, f"{data['plcyBizId']}.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
