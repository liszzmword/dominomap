#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import requests
import time
import json

API_KEY = "01807e413eceea1dee3a7c1b710e9d84"  # REST API 키

def get_coordinates(address):
    """Kakao REST API로 주소를 좌표로 변환"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {API_KEY}"}

    # 주소가 이미 "서울특별시"로 시작하면 그대로 사용
    if address.startswith('서울특별시'):
        params = {"query": address}
    else:
        params = {"query": f"서울특별시 {address}"}

    try:
        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        if result.get('documents'):
            doc = result['documents'][0]
            return float(doc['y']), float(doc['x'])  # lat, lng
        else:
            print(f"❌ 실패: {address}")
            return None, None
    except Exception as e:
        print(f"❌ 에러: {address} - {e}")
        return None, None

def process_csv(input_file, brand):
    """CSV 파일을 읽어서 좌표 추가"""
    stores = []

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)

        # 빈 줄 제거하고 헤더 찾기
        rows = [row for row in rows if row and any(cell.strip() for cell in row)]
        if not rows:
            return stores

        headers = rows[0]
        # BOM 제거
        headers = [h.replace('\ufeff', '').strip() for h in headers]

        # 헤더에 따라 컬럼 인덱스 결정
        if '지점명' in headers:
            # 새 파일 형식: 지점명,주소,전화번호,전화번호2,지점의특징,시군구
            name_idx = headers.index('지점명')
            address_idx = headers.index('주소')
            phone_idx = headers.index('전화번호')
            district_idx = headers.index('시군구')
        else:
            # 기존 파일 형식: 자치구,매장명,전화번호,주소 / 위치
            district_idx = headers.index('자치구')
            name_idx = headers.index('매장명')
            phone_idx = headers.index('전화번호')
            address_idx = headers.index('주소 / 위치')

        for row in rows[1:]:
            if len(row) <= max(name_idx, address_idx, phone_idx, district_idx):
                continue

            name = row[name_idx].strip()
            address = row[address_idx].strip()
            phone = row[phone_idx].strip()
            district = row[district_idx].strip()

            print(f"처리 중: {name}...")
            lat, lng = get_coordinates(address)

            if lat and lng:
                stores.append({
                    'district': district,
                    'name': name,
                    'phone': phone,
                    'address': address,
                    'lat': lat,
                    'lng': lng
                })
                print(f"✅ 성공: {name} ({lat}, {lng})")

            time.sleep(0.1)  # API 호출 제한 방지

    return stores

# 서브웨이 데이터 변환
print("=== 서브웨이 데이터 변환 시작 ===")
subway_stores = process_csv('subway.csv', 'subway')

# 도미노 데이터 변환
print("\n=== 도미노피자 데이터 변환 시작 ===")
domino_stores = process_csv('domino.csv', 'domino')

# JavaScript 코드 생성
print("\n=== JavaScript 코드 생성 ===")

def generate_js_array(stores, var_name):
    js = f"var {var_name} = [\n"
    for i, s in enumerate(stores):
        js += f'    {{district: "{s["district"]}", name: "{s["name"]}", phone: "{s["phone"]}", '
        js += f'address: "{s["address"]}", lat: {s["lat"]}, lng: {s["lng"]}}}'
        if i < len(stores) - 1:
            js += ','
        js += '\n'
    js += '];\n'
    return js

output = generate_js_array(subway_stores, 'subwayStores')
output += '\n'
output += generate_js_array(domino_stores, 'dominoStores')

# 파일로 저장
with open('stores_with_coords.js', 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\n✅ 완료!")
print(f"서브웨이: {len(subway_stores)}개")
print(f"도미노: {len(domino_stores)}개")
print(f"결과 파일: stores_with_coords.js")
