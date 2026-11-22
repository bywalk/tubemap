#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Expand DESTINATION_DICTIONARY in collector.py with granular landmarks across 6 continents.
"""

import re

NEW_LANDMARKS = {
    # === 1. 아시아: 도쿄 세부 ===
    "시부야": {"country": "일본", "city": "도쿄", "lat": 35.6580, "lng": 139.7016},
    "신주쿠": {"country": "일본", "city": "도쿄", "lat": 35.6938, "lng": 139.7034},
    "긴자": {"country": "일본", "city": "도쿄", "lat": 35.6719, "lng": 139.7640},
    "아사쿠사": {"country": "일본", "city": "도쿄", "lat": 35.7118, "lng": 139.7967},
    "롯폰기": {"country": "일본", "city": "도쿄", "lat": 35.6628, "lng": 139.7313},
    "아키하바라": {"country": "일본", "city": "도쿄", "lat": 35.6983, "lng": 139.7731},
    "오모테산도": {"country": "일본", "city": "도쿄", "lat": 35.6652, "lng": 139.7123},
    "하라주쿠": {"country": "일본", "city": "도쿄", "lat": 35.6702, "lng": 139.7027},
    "오다이바": {"country": "일본", "city": "도쿄", "lat": 35.6264, "lng": 139.7744},
    "도쿄타워": {"country": "일본", "city": "도쿄", "lat": 35.6586, "lng": 139.7454},
    "스카이트리": {"country": "일본", "city": "도쿄", "lat": 35.7100, "lng": 139.8107},
    "디즈니씨": {"country": "일본", "city": "도쿄", "lat": 35.6267, "lng": 139.8850},
    "디즈니랜드": {"country": "일본", "city": "도쿄", "lat": 35.6329, "lng": 139.8804},
    "츠키지": {"country": "일본", "city": "도쿄", "lat": 35.6655, "lng": 139.7707},
    "지유가오카": {"country": "일본", "city": "도쿄", "lat": 35.6074, "lng": 139.6687},
    "기치조지": {"country": "일본", "city": "도쿄", "lat": 35.7032, "lng": 139.5798},
    "이케부쿠로": {"country": "일본", "city": "도쿄", "lat": 35.7295, "lng": 139.7109},
    "우에노": {"country": "일본", "city": "도쿄", "lat": 35.7141, "lng": 139.7774},

    # === 1. 아시아: 오사카/교토/후쿠오카 세부 ===
    "도톤보리": {"country": "일본", "city": "오사카", "lat": 34.6687, "lng": 135.5013},
    "난바": {"country": "일본", "city": "오사카", "lat": 34.6629, "lng": 135.5005},
    "우메다": {"country": "일본", "city": "오사카", "lat": 34.7025, "lng": 135.4959},
    "신사이바시": {"country": "일본", "city": "오사카", "lat": 34.6750, "lng": 135.5004},
    "유니버셜스튜디오": {"country": "일본", "city": "오사카", "lat": 34.6654, "lng": 135.4323},
    "USJ": {"country": "일본", "city": "오사카", "lat": 34.6654, "lng": 135.4323},
    "오사카성": {"country": "일본", "city": "오사카", "lat": 34.6873, "lng": 135.5262},
    "기온": {"country": "일본", "city": "교토", "lat": 35.0037, "lng": 135.7772},
    "청수사": {"country": "일본", "city": "교토", "lat": 34.9949, "lng": 135.7850},
    "기요미즈데라": {"country": "일본", "city": "교토", "lat": 34.9949, "lng": 135.7850},
    "아라시야마": {"country": "일본", "city": "교토", "lat": 35.0166, "lng": 135.6713},
    "후시미이나리": {"country": "일본", "city": "교토", "lat": 34.9671, "lng": 135.7727},
    "텐진": {"country": "일본", "city": "후쿠오카", "lat": 33.5902, "lng": 130.4017},
    "하카타": {"country": "일본", "city": "후쿠오카", "lat": 33.5900, "lng": 130.4206},
    "나카스": {"country": "일본", "city": "후쿠오카", "lat": 33.5930, "lng": 130.4060},
    "모모치": {"country": "일본", "city": "후쿠오카", "lat": 33.5947, "lng": 130.3524},
    "다자이후": {"country": "일본", "city": "후쿠오카", "lat": 33.5215, "lng": 130.5349},

    # === 1. 아시아: 대만/홍콩 세부 ===
    "시먼딩": {"country": "대만", "city": "타이베이", "lat": 25.0422, "lng": 121.5081},
    "지우펀": {"country": "대만", "city": "지우펀", "lat": 25.1099, "lng": 121.8452},
    "스펀": {"country": "대만", "city": "스펀", "lat": 25.0428, "lng": 121.7766},
    "단수이": {"country": "대만", "city": "단수이", "lat": 25.1726, "lng": 121.4440},
    "융캉제": {"country": "대만", "city": "타이베이", "lat": 25.0312, "lng": 121.5298},
    "스린야시장": {"country": "대만", "city": "타이베이", "lat": 25.0877, "lng": 121.5244},
    "침사추이": {"country": "홍콩", "city": "홍콩", "lat": 22.2988, "lng": 114.1722},
    "빅토리아피크": {"country": "홍콩", "city": "홍콩", "lat": 22.2759, "lng": 114.1455},
    "몽콕": {"country": "홍콩", "city": "홍콩", "lat": 22.3193, "lng": 114.1694},

    # === 1. 아시아: 동남아 세부 ===
    "카오산로드": {"country": "태국", "city": "방콕", "lat": 13.7588, "lng": 100.4974},
    "아이콘시암": {"country": "태국", "city": "방콕", "lat": 13.7267, "lng": 100.5105},
    "짜뚜짝": {"country": "태국", "city": "방콕", "lat": 13.7999, "lng": 100.5501},
    "왓아룬": {"country": "태국", "city": "방콕", "lat": 13.7437, "lng": 100.4888},
    "님만해민": {"country": "태국", "city": "치앙마이", "lat": 18.7963, "lng": 98.9690},
    "미케비치": {"country": "베트남", "city": "다낭", "lat": 16.0592, "lng": 108.2464},
    "바나힐": {"country": "베트남", "city": "다낭", "lat": 15.9988, "lng": 107.9964},
    "한시장": {"country": "베트남", "city": "다낭", "lat": 16.0683, "lng": 108.2244},
    "안방비치": {"country": "베트남", "city": "호이안", "lat": 15.9142, "lng": 108.3375},
    "우붓": {"country": "인도네시아", "city": "발리", "lat": -8.5069, "lng": 115.2625},
    "짱구": {"country": "인도네시아", "city": "발리", "lat": -8.6500, "lng": 115.1389},
    "스미냑": {"country": "인도네시아", "city": "발리", "lat": -8.6913, "lng": 115.1682},
    "울루와투": {"country": "인도네시아", "city": "발리", "lat": -8.8291, "lng": 115.0849},
    "누사페니다": {"country": "인도네시아", "city": "발리", "lat": -8.7278, "lng": 115.5444},
    "알로나비치": {"country": "필리핀", "city": "보홀", "lat": 9.5492, "lng": 123.7744},
    "오슬롭": {"country": "필리핀", "city": "세부", "lat": 9.5167, "lng": 123.4333},

    # === 2. 유럽 세부 ===
    "에펠탑": {"country": "프랑스", "city": "파리", "lat": 48.8584, "lng": 2.2945},
    "루브르": {"country": "프랑스", "city": "파리", "lat": 48.8606, "lng": 2.3376},
    "몽마르트르": {"country": "프랑스", "city": "파리", "lat": 48.8867, "lng": 2.3431},
    "오르세": {"country": "프랑스", "city": "파리", "lat": 48.8599, "lng": 2.3265},
    "샹젤리제": {"country": "프랑스", "city": "파리", "lat": 48.8698, "lng": 2.3075},
    "개선문": {"country": "프랑스", "city": "파리", "lat": 48.8738, "lng": 2.2950},
    "베르사유": {"country": "프랑스", "city": "베르사유", "lat": 48.8049, "lng": 2.1204},
    "마레지구": {"country": "프랑스", "city": "파리", "lat": 48.8575, "lng": 2.3622},
    "빅벤": {"country": "영국", "city": "런던", "lat": 51.5007, "lng": -0.1246},
    "타워브릿지": {"country": "영국", "city": "런던", "lat": 51.5055, "lng": -0.0754},
    "런던아이": {"country": "영국", "city": "런던", "lat": 51.5033, "lng": -0.1195},
    "노팅힐": {"country": "영국", "city": "런던", "lat": 51.5091, "lng": -0.2069},
    "코벤트가든": {"country": "영국", "city": "런던", "lat": 51.5117, "lng": -0.1240},
    "콜로세움": {"country": "이탈리아", "city": "로마", "lat": 41.8902, "lng": 12.4922},
    "트레비분수": {"country": "이탈리아", "city": "로마", "lat": 41.9009, "lng": 12.4833},
    "바티칸": {"country": "이탈리아", "city": "바티칸", "lat": 41.9029, "lng": 12.4534},
    "판테온": {"country": "이탈리아", "city": "로마", "lat": 41.8986, "lng": 12.4769},
    "사그라다파밀리아": {"country": "스페인", "city": "바르셀로나", "lat": 41.4036, "lng": 2.1744},
    "구엘공원": {"country": "스페인", "city": "바르셀로나", "lat": 41.4145, "lng": 2.1527},
    "고딕지구": {"country": "스페인", "city": "바르셀로나", "lat": 41.3828, "lng": 2.1769},
    "보케리아": {"country": "스페인", "city": "바르셀로나", "lat": 41.3817, "lng": 2.1715},
    "인터라켄": {"country": "스위스", "city": "인터라켄", "lat": 46.6863, "lng": 7.8632},
    "그린델발트": {"country": "스위스", "city": "그린델발트", "lat": 46.6242, "lng": 8.0414},
    "융프라우": {"country": "스위스", "city": "융프라우", "lat": 46.5475, "lng": 7.9854},
    "체르마트": {"country": "스위스", "city": "체르마트", "lat": 45.9765, "lng": 7.7491},
    "마터호른": {"country": "스위스", "city": "체르마트", "lat": 45.9765, "lng": 7.6586},
    "루체른": {"country": "스위스", "city": "루체른", "lat": 47.0502, "lng": 8.3093},

    # === 3. 북아메리카 세부 ===
    "타임스퀘어": {"country": "미국", "city": "뉴욕", "lat": 40.7580, "lng": -73.9855},
    "센트럴파크": {"country": "미국", "city": "뉴욕", "lat": 40.7851, "lng": -73.9683},
    "브루클린": {"country": "미국", "city": "뉴욕", "lat": 40.6782, "lng": -73.9442},
    "덤보": {"country": "미국", "city": "뉴욕", "lat": 40.7033, "lng": -73.9892},
    "첼시마켓": {"country": "미국", "city": "뉴욕", "lat": 40.7424, "lng": -74.0061},
    "하이라인": {"country": "미국", "city": "뉴욕", "lat": 40.7480, "lng": -74.0048},
    "자유의여신상": {"country": "미국", "city": "뉴욕", "lat": 40.6892, "lng": -74.0445},
    "산타모니카": {"country": "미국", "city": "로스앤젤레스", "lat": 34.0195, "lng": -118.4912},
    "헐리우드": {"country": "미국", "city": "로스앤젤레스", "lat": 34.1016, "lng": -118.3268},
    "할리우드": {"country": "미국", "city": "로스앤젤레스", "lat": 34.1016, "lng": -118.3268},
    "베벌리힐스": {"country": "미국", "city": "로스앤젤레스", "lat": 34.0736, "lng": -118.4004},
    "베니스비치": {"country": "미국", "city": "로스앤젤레스", "lat": 33.9850, "lng": -118.4695},
    "그리피스": {"country": "미국", "city": "로스앤젤레스", "lat": 34.1184, "lng": -118.3004},
    "게티센터": {"country": "미국", "city": "로스앤젤레스", "lat": 34.0780, "lng": -118.4741},
    "금문교": {"country": "미국", "city": "샌프란시스코", "lat": 37.8199, "lng": -122.4783},
    "피어39": {"country": "미국", "city": "샌프란시스코", "lat": 37.8087, "lng": -122.4098},
    "와이키키": {"country": "미국", "city": "하와이", "lat": 21.2766, "lng": -157.8275},
    "호놀룰루": {"country": "미국", "city": "하와이", "lat": 21.3069, "lng": -157.8583},
    "하나우마베이": {"country": "미국", "city": "하와이", "lat": 21.2690, "lng": -157.6938},
    "오아후": {"country": "미국", "city": "하와이", "lat": 21.4389, "lng": -158.0001},
    "마우이": {"country": "미국", "city": "하와이", "lat": 20.7984, "lng": -156.3319},
    "레이크루이스": {"country": "캐나다", "city": "밴프", "lat": 51.4254, "lng": -116.1773},
    "모레인": {"country": "캐나다", "city": "밴프", "lat": 51.3217, "lng": -116.1860},
    "나이아가라": {"country": "캐나다", "city": "나이아가라", "lat": 43.0896, "lng": -79.0849},

    # === 4. 남아메리카 세부 ===
    "마추픽추": {"country": "페루", "city": "쿠스코", "lat": -13.1631, "lng": -72.5450},
    "쿠스코": {"country": "페루", "city": "쿠스코", "lat": -13.5319, "lng": -71.9675},
    "리마": {"country": "페루", "city": "리마", "lat": -12.0464, "lng": -77.0428},
    "와카치나": {"country": "페루", "city": "이카", "lat": -14.0875, "lng": -75.7633},
    "라파스": {"country": "볼리비아", "city": "라파스", "lat": -16.5000, "lng": -68.1500},
    "부에노스아이레스": {"country": "아르헨티나", "city": "부에노스아이레스", "lat": -34.6037, "lng": -58.3816},
    "이과수": {"country": "아르헨티나", "city": "푸에르토이과수", "lat": -25.6953, "lng": -54.4367},
    "엘칼라파테": {"country": "아르헨티나", "city": "엘칼라파테", "lat": -50.3379, "lng": -72.2648},
    "피츠로이": {"country": "아르헨티나", "city": "엘찰텐", "lat": -49.2713, "lng": -73.0431},
    "산티아고": {"country": "칠레", "city": "산티아고", "lat": -33.4489, "lng": -70.6693},
    "아타카마": {"country": "칠레", "city": "아타카마", "lat": -22.9087, "lng": -68.1997},
    "토레스델파이네": {"country": "칠레", "city": "파이네", "lat": -51.2532, "lng": -72.8814},
    "리우데자네이루": {"country": "브라질", "city": "리우데자네이루", "lat": -22.9068, "lng": -43.1729},
    "상파울루": {"country": "브라질", "city": "상파울루", "lat": -23.5505, "lng": -46.6333},

    # === 5. 오세아니아 세부 ===
    "오페라하우스": {"country": "호주", "city": "시드니", "lat": -33.8568, "lng": 151.2153},
    "본다이비치": {"country": "호주", "city": "시드니", "lat": -33.8915, "lng": 151.2767},
    "하버브릿지": {"country": "호주", "city": "시드니", "lat": -33.8523, "lng": 151.2108},
    "달링하버": {"country": "호주", "city": "시드니", "lat": -33.8749, "lng": 151.2009},
    "블루마운틴": {"country": "호주", "city": "카툼바", "lat": -33.7150, "lng": 150.3117},
    "써리힐즈": {"country": "호주", "city": "시드니", "lat": -33.8869, "lng": 151.2117},
    "그레이트오션로드": {"country": "호주", "city": "멜버른", "lat": -38.6806, "lng": 143.3911},
    "퀸스타운": {"country": "뉴질랜드", "city": "퀸스타운", "lat": -45.0312, "lng": 168.6626},
    "밀포드사운드": {"country": "뉴질랜드", "city": "밀포드사운드", "lat": -44.6716, "lng": 167.9256},
    "오클랜드": {"country": "뉴질랜드", "city": "오클랜드", "lat": -36.8485, "lng": 174.7633},
    "테카포": {"country": "뉴질랜드", "city": "테카포", "lat": -44.0047, "lng": 170.4771},
    "투몬": {"country": "미국", "city": "괌", "lat": 13.5137, "lng": 144.8051},
    "괌": {"country": "미국", "city": "괌", "lat": 13.4443, "lng": 144.7937},
    "사이판": {"country": "미국", "city": "사이판", "lat": 15.1850, "lng": 145.7467},

    # === 6. 아프리카 & 중동 세부 ===
    "탁심": {"country": "튀르키예", "city": "이스탄불", "lat": 41.0370, "lng": 28.9850},
    "괴레메": {"country": "튀르키예", "city": "카파도키아", "lat": 38.6431, "lng": 34.8289},
    "피라미드": {"country": "이집트", "city": "카이로", "lat": 29.9792, "lng": 31.1342},
    "스핑크스": {"country": "이집트", "city": "카이로", "lat": 29.9753, "lng": 31.1376},
    "블루홀": {"country": "이집트", "city": "다합", "lat": 28.5724, "lng": 34.5369},
    "아스완": {"country": "이집트", "city": "아스완", "lat": 24.0889, "lng": 32.8998},
    "두바이몰": {"country": "아랍에미리트", "city": "두바이", "lat": 25.1972, "lng": 55.2744},
    "버즈칼리파": {"country": "아랍에미리트", "city": "두바이", "lat": 25.1972, "lng": 55.2744},
    "버즈알아랍": {"country": "아랍에미리트", "city": "두바이", "lat": 25.1412, "lng": 55.1852},
    "팜주메이라": {"country": "아랍에미리트", "city": "두바이", "lat": 25.1124, "lng": 55.1390},
    "아부다비": {"country": "아랍에미리트", "city": "아부다비", "lat": 24.4539, "lng": 54.3773},
    "셰프샤우엔": {"country": "모로코", "city": "셰프샤우엔", "lat": 35.1716, "lng": -5.2697},
    "페스": {"country": "모로코", "city": "페스", "lat": 34.0181, "lng": -5.0078}
}

def update_collector():
    collector_path = "collector.py"
    with open(collector_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find DESTINATION_DICTIONARY = { ... }
    dict_start = content.find("DESTINATION_DICTIONARY = {")
    if dict_start == -1:
        print("Could not find DESTINATION_DICTIONARY")
        return

    # Format new landmark lines
    landmark_lines = []
    for k, v in NEW_LANDMARKS.items():
        # Check if already present
        if f'"{k}":' in content:
            continue
        line = f'    "{k}": {{"country": "{v["country"]}", "city": "{v["city"]}", "lat": {v["lat"]}, "lng": {v["lng"]}}},'
        landmark_lines.append(line)

    print(f"Adding {len(landmark_lines)} new granular landmarks to DESTINATION_DICTIONARY...")

    # Insert right after DESTINATION_DICTIONARY = {
    insert_pos = content.find("{", dict_start) + 1
    new_content = (
        content[:insert_pos] +
        "\n    # --- 전 세계 주요 랜드마크 & 세부 명소 (Granular Landmarks) ---\n" +
        "\n".join(landmark_lines) +
        "\n" +
        content[insert_pos:]
    )

    with open(collector_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ collector.py DESTINATION_DICTIONARY successfully expanded!")

if __name__ == "__main__":
    update_collector()
