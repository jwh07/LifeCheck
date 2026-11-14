"""
LifeCheck - CSV 데이터 저장 및 관리 모듈 (storage.py)
담당: 팀원 2 (파일 입출력 및 데이터 관리)

- data/items.csv 파일 자동 생성 및 관리
- 제품 정보의 등록(Create), 조회(Read), 수정(Update), 삭제(Delete) 처리
- UTF-8 with BOM(utf-8-sig) 인코딩 적용으로 엑셀 및 윈도우 환경 한글 깨짐 방지
"""

import os
import csv
from typing import List, Dict, Optional

# 데이터 저장 디렉토리 및 CSV 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_FILE_PATH = os.path.join(DATA_DIR, "items.csv")

CSV_HEADERS = ["id", "name", "category", "open_date", "period_months", "end_date"]


def init_storage() -> None:
    """
    저장소 디렉토리(data/) 및 CSV 파일(items.csv)이 존재하는지 확인하고,
    없으면 자동으로 디렉토리 생성 및 헤더가 포함된 빈 CSV 파일을 생성합니다.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def load_items() -> List[Dict]:
    """
    CSV 파일에서 모든 제품 정보를 읽어와 딕셔너리 리스트로 반환합니다.
    반환 형태:
    [
        {
            "id": 1,
            "name": "선크림",
            "category": "화장품",
            "open_date": "2026-10-01",
            "period_months": 6,
            "end_date": "2027-04-01"
        },
        ...
    ]
    """
    init_storage()
    items = []
    
    with open(CSV_FILE_PATH, mode="r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                item = {
                    "id": int(row["id"]),
                    "name": row["name"],
                    "category": row["category"],
                    "open_date": row["open_date"],
                    "period_months": int(row["period_months"]),
                    "end_date": row["end_date"]
                }
                items.append(item)
            except (ValueError, KeyError):
                # 손상되었거나 잘못된 행은 건너뜁니다.
                continue
    return items


def save_items(items: List[Dict]) -> None:
    """
    전체 제품 리스트를 CSV 파일에 덮어씁니다.
    """
    init_storage()
    with open(CSV_FILE_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for item in items:
            writer.writerow(item)


def get_next_id(items: List[Dict]) -> int:
    """
    새로운 제품에 부여할 고유 ID 번호(기존 최대 ID + 1)를 계산합니다.
    """
    if not items:
        return 1
    return max(item["id"] for item in items) + 1


def add_item(name: str, category: str, open_date: str, period_months: int, end_date: str) -> Dict:
    """
    새 제품을 추가하고 CSV 파일에 저장합니다.
    추가된 새 제품 딕셔너리를 반환합니다.
    """
    items = load_items()
    new_id = get_next_id(items)
    
    new_item = {
        "id": new_id,
        "name": name.strip(),
        "category": category.strip(),
        "open_date": open_date.strip(),
        "period_months": int(period_months),
        "end_date": end_date.strip()
    }
    
    items.append(new_item)
    save_items(items)
    return new_item


def update_item(item_id: int, name: str, category: str, open_date: str, period_months: int, end_date: str) -> bool:
    """
    지정된 ID의 제품 정보를 수정하고 CSV 파일에 저장합니다.
    성공 시 True, 해당 ID가 없으면 False를 반환합니다.
    """
    items = load_items()
    updated = False
    
    for item in items:
        if item["id"] == item_id:
            item["name"] = name.strip()
            item["category"] = category.strip()
            item["open_date"] = open_date.strip()
            item["period_months"] = int(period_months)
            item["end_date"] = end_date.strip()
            updated = True
            break
            
    if updated:
        save_items(items)
    return updated


def delete_item(item_id: int) -> bool:
    """
    지정된 ID의 제품을 삭제하고 CSV 파일에 저장합니다.
    성공 시 True, 해당 ID가 없으면 False를 반환합니다.
    """
    items = load_items()
    initial_count = len(items)
    items = [item for item in items if item["id"] != item_id]
    
    if len(items) < initial_count:
        save_items(items)
        return True
    return False
