"""
LifeCheck - 날짜 계산 및 상태 판정 모듈 (calculator.py)
담당: 팀원 3 (연산 로직 및 데이터 검증)

- 개봉일과 사용 가능 기간(개월)을 바탕으로 사용 종료일 계산
- 현재 날짜 기준 남은 일수 계산
- 남은 일수에 따른 상태('사용가능', '기간임박', '기간만료') 판정
- 날짜 형식 및 값에 대한 유효성 검사
"""

from datetime import datetime, date
import calendar


def validate_date_format(date_str: str) -> bool:
    """
    날짜 문자열이 'YYYY-MM-DD' 형식이고 실제 유효한 날짜인지 검증합니다.
    예: '2026-10-01' -> True, '2026-02-30' -> False, '20261001' -> False
    """
    if not isinstance(date_str, str):
        return False
    date_str = date_str.strip()
    if len(date_str) != 10:
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def calculate_end_date(open_date_str: str, period_months: int) -> str:
    """
    개봉일(YYYY-MM-DD)에 사용 가능 개월 수를 더하여 종료일(YYYY-MM-DD)을 계산합니다.
    월말 날짜 초과(예: 1월 31일 + 1개월 -> 2월 28일)를 안전하게 보정합니다.
    """
    if not validate_date_format(open_date_str):
        raise ValueError("올바른 날짜 형식(YYYY-MM-DD)이 아닙니다.")
    if not isinstance(period_months, int) or period_months <= 0:
        raise ValueError("사용 가능 기간은 1 이상의 정수여야 합니다.")

    open_dt = datetime.strptime(open_date_str.strip(), "%Y-%m-%d").date()
    
    # 새로운 연도와 월 계산
    total_months = open_dt.month + period_months
    new_year = open_dt.year + (total_months - 1) // 12
    new_month = (total_months - 1) % 12 + 1
    
    # 해당 월의 최대 일수 확인 (예: 윤년 2월 29일, 평년 28일 등)
    max_day_in_month = calendar.monthrange(new_year, new_month)[1]
    new_day = min(open_dt.day, max_day_in_month)
    
    end_dt = date(new_year, new_month, new_day)
    return end_dt.strftime("%Y-%m-%d")


def calculate_remaining_days(end_date_str: str, base_date: date = None) -> int:
    """
    기준 날짜(기본값: 오늘)를 기준으로 사용 종료일까지 남은 일수를 계산합니다.
    - 양수: 남은 일수
    - 0: 오늘 만료
    - 음수: 만료 후 지난 일수
    """
    if not validate_date_format(end_date_str):
        raise ValueError("올바른 날짜 형식(YYYY-MM-DD)이 아닙니다.")
    
    if base_date is None:
        base_date = date.today()
        
    end_dt = datetime.strptime(end_date_str.strip(), "%Y-%m-%d").date()
    delta = (end_dt - base_date).days
    return delta


def get_item_status(remaining_days: int) -> str:
    """
    남은 일수를 기준으로 제품의 상태를 반환합니다.
    - 음수 (< 0): '기간만료'
    - 0일 ~ 30일: '기간임박'
    - 31일 이상: '사용가능'
    """
    if remaining_days < 0:
        return "기간만료"
    elif 0 <= remaining_days <= 30:
        return "기간임박"
    else:
        return "사용가능"
