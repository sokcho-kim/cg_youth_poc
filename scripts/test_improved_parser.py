from detail_parser import parse_detail, save_json
import json

# 테스트할 정책 ID
test_id = "R2024112828265"

# 크롤링 시도
data = parse_detail(test_id)

# 결과 출력
print("📌 수집된 데이터:")
print(json.dumps(data, ensure_ascii=False, indent=2))

# 저장
save_json(data)
print(f"\n✅ 저장 완료: {data['plcyBizId']}.json") 