"""
LifeCheck - CSV 데이터 저장 및 관리 모듈 (storage.py)
담당: 팀원 2 (파일 입출력 및 데이터 관리)

- data/items.csv 파일 자동 생성 및 관리
- 제품 정보의 등록(Create), 조회(Read), 수정(Update), 삭제(Delete) 처리
- UTF-8 with BOM(utf-8-sig) 인코딩 적용으로 엑셀 및 윈도우 환경 한글 깨짐 방지
"""

import os
import csv
import json
import tempfile
from datetime import date
from typing import List, Dict

# 데이터 저장 디렉토리 및 CSV 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_FILE_PATH = os.path.join(DATA_DIR, "items.csv")
SETTINGS_FILE_PATH = os.path.join(DATA_DIR, "settings.json")

CSV_HEADERS = ["id", "name", "category", "open_date", "period_months", "end_date",
               "usage_status", "completed_date"]
URGENT_DAY_OPTIONS = (7, 14, 30)


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
                    "end_date": row["end_date"],
                    # 기존 6열 CSV는 파일을 변경하지 않고 사용 중 제품으로 읽습니다.
                    "usage_status": row.get("usage_status") or "사용중",
                    "completed_date": row.get("completed_date") or "",
                }
                items.append(item)
            except (ValueError, KeyError, TypeError):
                # 손상되었거나 잘못된 행은 건너뜁니다.
                continue
    return items


def save_items(items: List[Dict]) -> None:
    """
    전체 제품 리스트를 CSV 파일에 저장합니다. 저장 실패 시 기존 파일을 보존합니다.
    """
    init_storage()
    def write_csv(f):
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for item in items:
            row = dict(item)
            row.setdefault("usage_status", "사용중")
            row.setdefault("completed_date", "")
            writer.writerow(row)

    _atomic_write(CSV_FILE_PATH, write_csv, "utf-8-sig")


def _atomic_write(path: str, write_content, encoding: str) -> None:
    """같은 폴더의 임시 파일에 쓴 뒤 교체하여 CSV와 설정 파일의 잘림을 방지합니다."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding=encoding, newline="",
                                         dir=os.path.dirname(path), delete=False) as f:
            temp_path = f.name
            write_content(f)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and os.path.exists(temp_path):
            os.unlink(temp_path)


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
        "end_date": end_date.strip(),
        "usage_status": "사용중",
        "completed_date": "",
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
            if item["usage_status"] == "사용완료":
                return False  # 완료 이력은 새 제품 등록으로 재사용하며 원본은 보존합니다.
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


# ---------------- 추가 기능 4·5 / 팀원 3 (계산·테스트 담당) ----------------

def load_settings() -> Dict:
    """설정이 없거나 손상된 경우 기본 임박 기준 30일을 사용합니다."""
    try:
        with open(SETTINGS_FILE_PATH, encoding="utf-8-sig") as f:
            settings = json.load(f)
        days = settings["urgent_days"]
        if type(days) is int and days in URGENT_DAY_OPTIONS:
            return {"urgent_days": days}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return {"urgent_days": 30}


def save_settings(urgent_days: int) -> None:
    """7·14·30일 중 선택한 임박 기준을 저장합니다."""
    if type(urgent_days) is not int or urgent_days not in URGENT_DAY_OPTIONS:
        raise ValueError("기간 임박 기준은 7일, 14일, 30일 중 선택해 주세요.")
    _atomic_write(SETTINGS_FILE_PATH, lambda f: json.dump(
        {"urgent_days": urgent_days}, f, ensure_ascii=False, indent=2
    ), "utf-8")


def complete_item(item_id: int, completed_date: str) -> bool:
    """사용 중인 제품을 완료 처리합니다. 개봉일 이전·미래 완료일은 허용하지 않습니다."""
    completed_date = completed_date.strip()
    if len(completed_date) != 10:
        raise ValueError("사용 완료일은 YYYY-MM-DD 형식으로 입력해 주세요.")
    completed = date.fromisoformat(completed_date)
    if completed > date.today():
        raise ValueError("사용 완료일은 오늘 이후로 지정할 수 없습니다.")
    items = load_items()
    for item in items:
        if item["id"] != item_id or item["usage_status"] == "사용완료":
            continue
        if completed < date.fromisoformat(item["open_date"]):
            raise ValueError("사용 완료일은 개봉일보다 빠를 수 없습니다.")
        item["usage_status"] = "사용완료"
        item["completed_date"] = completed_date
        save_items(items)
        return True
    return False
