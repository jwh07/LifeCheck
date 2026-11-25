"""
LifeCheck - 생활용품 데이터 관리 모듈 (product_manager.py)
담당: 기능 1 (생활용품 등록, 조회, 수정, 삭제 및 CSV 저장)

- CSV 파일을 통한 제품 데이터 영구 저장 (프로그램 재실행 시에도 데이터 유지)
- Windows Excel 환경에서도 한글이 깨지지 않는 utf-8-sig 인코딩 적용
- 제품 등록(Add), 전체 조회(Get All), 단일 조회(Get by ID), 수정(Update), 삭제(Delete)
"""

import os
import csv
from typing import List, Dict, Optional

# 데이터 디렉토리 및 CSV 파일 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "products.csv")

# CSV 파일 헤더 정의
# id: 고유 식별 번호
# name: 제품명
# category: 제품 분류 (화장품, 세정용품, 위생용품 등)
# open_date: 구매일 또는 개봉일 (YYYY-MM-DD)
# period_months: 사용 가능 기간 (개월 단위)
CSV_HEADERS = ["id", "name", "category", "open_date", "period_months"]


def init_storage() -> None:
    """데이터 저장 디렉토리 및 CSV 파일이 없으면 자동 생성합니다."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def get_all_products() -> List[Dict]:
    """CSV 파일에서 모든 제품 목록을 읽어 반환합니다."""
    init_storage()
    products = []

    with open(CSV_PATH, mode="r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                item = {
                    "id": int(row["id"]),
                    "name": row["name"],
                    "category": row["category"],
                    "open_date": row["open_date"],
                    "period_months": int(row["period_months"])
                }
                products.append(item)
            except (ValueError, KeyError):
                # 데이터 형식이 잘못되었거나 누락된 행은 건너뜁니다.
                continue
    return products


def get_product_by_id(product_id: int) -> Optional[Dict]:
    """특정 ID를 가진 제품 정보를 조회합니다."""
    products = get_all_products()
    for product in products:
        if product["id"] == product_id:
            return product
    return None


def get_next_id(products: List[Dict]) -> int:
    """새로운 제품에 부여할 고유 ID (기존 최대 ID + 1)를 반환합니다."""
    if not products:
        return 1
    return max(p["id"] for p in products) + 1


def add_product(name: str, category: str, open_date: str, period_months: int) -> Dict:
    """새로운 제품을 등록하고 CSV 파일에 저장합니다."""
    init_storage()
    products = get_all_products()
    new_id = get_next_id(products)

    new_product = {
        "id": new_id,
        "name": name.strip(),
        "category": category.strip(),
        "open_date": open_date.strip(),
        "period_months": int(period_months)
    }

    products.append(new_product)
    _save_all(products)
    return new_product


def update_product(product_id: int, name: str, category: str, open_date: str, period_months: int) -> bool:
    """기존 제품 정보를 수정하고 CSV 파일에 저장합니다."""
    products = get_all_products()
    updated = False

    for product in products:
        if product["id"] == product_id:
            product["name"] = name.strip()
            product["category"] = category.strip()
            product["open_date"] = open_date.strip()
            product["period_months"] = int(period_months)
            updated = True
            break

    if updated:
        _save_all(products)
    return updated


def delete_product(product_id: int) -> bool:
    """특정 ID의 제품을 삭제하고 CSV 파일에 반영합니다."""
    products = get_all_products()
    initial_len = len(products)
    products = [p for p in products if p["id"] != product_id]

    if len(products) < initial_len:
        _save_all(products)
        return True
    return False


def _save_all(products: List[Dict]) -> None:
    """제품 목록 전체를 CSV 파일에 덮어씁니다."""
    init_storage()
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for p in products:
            writer.writerow(p)
