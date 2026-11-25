"""
LifeCheck - 생활용품 사용 기간 관리 프로그램 (main.py)
담당: 팀원 1 (GUI 화면 구성 및 사용자 이벤트 처리)

- tkinter / ttk 기반의 직관적인 데스크톱 GUI
- 제품 등록, 조회, 수정, 삭제(CRUD) 및 입력 초기화
- 상태별(전체, 기간임박, 기간만료, 사용가능) 실시간 목록 필터링
- 목록 선택 시 입력폼 자동 완성 및 상태별 하이라이트 색상 태그
- 입력값 유효성 검사 및 안내 대화상자(messagebox) 연동
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import storage
import calculator


class LifeCheckApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LifeCheck - 생활용품 사용 기간 관리 프로그램")
        self.root.geometry("1020x620")
        self.root.minsize(900, 550)

        # 현재 선택된 제품의 ID (수정/삭제 시 사용, 미선택 시 None)
        self.selected_item_id = None

        # 필터 상태 변수 ("전체", "기간임박", "기간만료", "사용가능")
        self.filter_var = tk.StringVar(value="전체")

        # 스타일 설정
        self.setup_styles()

        # UI 화면 구성
        self.create_widgets()

        # 데이터베이스(CSV) 초기화 및 첫 화면 목록 갱신
        storage.init_storage()
        self.refresh_item_list()

    def setup_styles(self):
        """GUI 위젯 스타일 지정"""
        style = ttk.Style()
        style.theme_use("clam")

        # 폰트 및 패딩 스타일
        style.configure("Title.TLabel", font=("Malgun Gothic", 15, "bold"), foreground="#2C3E50")
        style.configure("SubTitle.TLabel", font=("Malgun Gothic", 10, "bold"), foreground="#34495E")
        style.configure("Header.TLabel", font=("Malgun Gothic", 11, "bold"), foreground="#2C3E50")
        style.configure("TLabel", font=("Malgun Gothic", 9))
        style.configure("TButton", font=("Malgun Gothic", 9), padding=5)
        style.configure("Primary.TButton", font=("Malgun Gothic", 9, "bold"), padding=6)
        
        # Treeview 표 스타일
        style.configure("Treeview.Heading", font=("Malgun Gothic", 9, "bold"), background="#EAECEE")
        style.configure("Treeview", font=("Malgun Gothic", 9), rowheight=26)

    def create_widgets(self):
        """메인 레이아웃 및 컴포넌트 생성"""
        # 최상단 타이틀 바
        header_frame = ttk.Frame(self.root, padding="15 10 15 5")
        header_frame.pack(fill=tk.X)
        title_label = ttk.Label(header_frame, text="✨ LifeCheck - 생활용품 사용 기간 관리", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        today_str = date.today().strftime("%Y년 %m월 %d일")
        today_label = ttk.Label(header_frame, text=f"기준일: {today_str}", font=("Malgun Gothic", 9), foreground="#7F8C8D")
        today_label.pack(side=tk.RIGHT, pady=5)

        # 메인 컨테이너 (좌측 입력창 + 우측 목록창)
        main_container = ttk.Frame(self.root, padding="15 5 15 15")
        main_container.pack(fill=tk.BOTH, expand=True)

        # 좌측 패널: 제품 정보 입력 및 버튼
        self.create_left_panel(main_container)

        # 우측 패널: 필터 및 제품 목록 표
        self.create_right_panel(main_container)

    def create_left_panel(self, parent):
        """좌측 입력 폼 및 액션 버튼 패널"""
        left_frame = ttk.LabelFrame(parent, text=" [ 제품 정보 입력 및 관리 ] ", padding="15")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 1. 제품명
        ttk.Label(left_frame, text="제품명 *", style="SubTitle.TLabel").pack(anchor=tk.W, pady=(0, 2))
        self.entry_name = ttk.Entry(left_frame, width=28, font=("Malgun Gothic", 9))
        self.entry_name.pack(fill=tk.X, pady=(0, 10))

        # 2. 제품 분류
        ttk.Label(left_frame, text="제품 분류 *", style="SubTitle.TLabel").pack(anchor=tk.W, pady=(0, 2))
        self.combo_category = ttk.Combobox(
            left_frame,
            values=["화장품", "세정용품", "위생용품", "의약외품", "기타"],
            state="normal",
            font=("Malgun Gothic", 9)
        )
        self.combo_category.pack(fill=tk.X, pady=(0, 10))
        self.combo_category.set("화장품")

        # 3. 개봉일 (구매일 또는 개봉일)
        open_date_header = ttk.Frame(left_frame)
        open_date_header.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(open_date_header, text="개봉일 (YYYY-MM-DD) *", style="SubTitle.TLabel").pack(side=tk.LEFT)
        btn_today = ttk.Button(open_date_header, text="오늘", width=4, command=self.set_today_date)
        btn_today.pack(side=tk.RIGHT)

        self.entry_open_date = ttk.Entry(left_frame, font=("Malgun Gothic", 9))
        self.entry_open_date.pack(fill=tk.X, pady=(0, 10))
        self.entry_open_date.insert(0, date.today().strftime("%Y-%m-%d"))

        # 4. 사용 가능 기간 (개월)
        ttk.Label(left_frame, text="사용 가능 기간 (개월 수) *", style="SubTitle.TLabel").pack(anchor=tk.W, pady=(0, 2))
        period_frame = ttk.Frame(left_frame)
        period_frame.pack(fill=tk.X, pady=(0, 15))
        self.entry_period = ttk.Entry(period_frame, font=("Malgun Gothic", 9))
        self.entry_period.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(period_frame, text=" 개월").pack(side=tk.LEFT)

        # 액션 버튼 그리드
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 15))

        self.btn_add = ttk.Button(btn_frame, text="➕ 등록", style="Primary.TButton", command=self.handle_add)
        self.btn_add.grid(row=0, column=0, padx=2, pady=3, sticky="ew")

        self.btn_update = ttk.Button(btn_frame, text="✏️ 수정", command=self.handle_update)
        self.btn_update.grid(row=0, column=1, padx=2, pady=3, sticky="ew")

        self.btn_delete = ttk.Button(btn_frame, text="🗑️ 삭제", command=self.handle_delete)
        self.btn_delete.grid(row=1, column=0, padx=2, pady=3, sticky="ew")

        self.btn_clear = ttk.Button(btn_frame, text="🔄 초기화", command=self.clear_input_fields)
        self.btn_clear.grid(row=1, column=1, padx=2, pady=3, sticky="ew")

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        # 하단 상태 요약 카드
        summary_frame = ttk.LabelFrame(left_frame, text=" [ 등록 현황 요약 ] ", padding="10")
        summary_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        self.lbl_stat_total = ttk.Label(summary_frame, text="전체 제품: 0개", font=("Malgun Gothic", 9))
        self.lbl_stat_total.pack(anchor=tk.W, pady=1)

        self.lbl_stat_urgent = ttk.Label(summary_frame, text="⚠️ 기간 임박: 0개", font=("Malgun Gothic", 9, "bold"), foreground="#D35400")
        self.lbl_stat_urgent.pack(anchor=tk.W, pady=1)

        self.lbl_stat_expired = ttk.Label(summary_frame, text="🚨 기간 만료: 0개", font=("Malgun Gothic", 9, "bold"), foreground="#C0392B")
        self.lbl_stat_expired.pack(anchor=tk.W, pady=1)

    def create_right_panel(self, parent):
        """우측 필터 및 Treeview 목록 패널"""
        right_frame = ttk.LabelFrame(parent, text=" [ 생활용품 목록 및 상태 ] ", padding="15")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 상단 필터 영역
        filter_frame = ttk.Frame(right_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="보기 필터: ", font=("Malgun Gothic", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))

        filters = [("전체 보기", "전체"), ("⚠️ 기간 임박 (30일 이내)", "기간임박"), ("🚨 기간 만료", "기간만료"), ("✅ 사용 가능", "사용가능")]
        for text, mode in filters:
            rb = ttk.Radiobutton(
                filter_frame,
                text=text,
                value=mode,
                variable=self.filter_var,
                command=self.refresh_item_list
            )
            rb.pack(side=tk.LEFT, padx=6)

        # Treeview 표 (목록)
        columns = ("id", "name", "category", "open_date", "end_date", "remaining", "status")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", selectmode="browse")

        # 각 컬럼 헤더 및 너비 설정
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="제품명")
        self.tree.heading("category", text="분류")
        self.tree.heading("open_date", text="개봉일")
        self.tree.heading("end_date", text="사용종료일")
        self.tree.heading("remaining", text="남은 기간")
        self.tree.heading("status", text="상태")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=140, anchor=tk.W)
        self.tree.column("category", width=80, anchor=tk.CENTER)
        self.tree.column("open_date", width=90, anchor=tk.CENTER)
        self.tree.column("end_date", width=90, anchor=tk.CENTER)
        self.tree.column("remaining", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=80, anchor=tk.CENTER)

        # 스크롤바 연결
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 항목 선택 이벤트 바인딩
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 상태별 폰트/색상 태그 정의
        self.tree.tag_configure("expired", foreground="#C0392B", background="#FDEDEC")  # 연한 빨강
        self.tree.tag_configure("urgent", foreground="#D35400", background="#FEF9E7")   # 연한 주황
        self.tree.tag_configure("normal", foreground="#27AE60")                         # 초록

    # ---------------- UI 이벤트 및 핸들러 ----------------

    def set_today_date(self):
        """오늘 날짜를 개봉일 입력창에 삽입"""
        self.entry_open_date.delete(0, tk.END)
        self.entry_open_date.insert(0, date.today().strftime("%Y-%m-%d"))

    def clear_input_fields(self):
        """입력 필드를 비우고 선택 상태를 초기화"""
        self.selected_item_id = None
        self.entry_name.delete(0, tk.END)
        self.combo_category.set("화장품")
        self.set_today_date()
        self.entry_period.delete(0, tk.END)
        
        # 목록 선택 해제
        selected = self.tree.selection()
        if selected:
            self.tree.selection_remove(selected)

    def validate_inputs(self):
        """
        입력창 값 유효성 검사
        유효하면 (name, category, open_date, period_months, end_date) 튜플 반환,
        오류가 있으면 경고 메시지 출력 후 None 반환
        """
        name = self.entry_name.get().strip()
        category = self.combo_category.get().strip()
        open_date = self.entry_open_date.get().strip()
        period_str = self.entry_period.get().strip()

        # 1. 필수값 누락 검사
        if not name:
            messagebox.showwarning("입력 오류", "제품명을 입력해 주세요.")
            self.entry_name.focus()
            return None
        if not category:
            messagebox.showwarning("입력 오류", "제품 분류를 선택하거나 입력해 주세요.")
            self.combo_category.focus()
            return None
        if not open_date:
            messagebox.showwarning("입력 오류", "개봉일을 입력해 주세요.")
            self.entry_open_date.focus()
            return None
        if not period_str:
            messagebox.showwarning("입력 오류", "사용 가능 기간(개월)을 입력해 주세요.")
            self.entry_period.focus()
            return None

        # 2. 날짜 형식 검사
        if not calculator.validate_date_format(open_date):
            messagebox.showwarning(
                "날짜 형식 오류",
                "개봉일 형식이 올바르지 않습니다.\n'YYYY-MM-DD' 형식으로 입력해 주세요. (예: 2026-10-01)"
            )
            self.entry_open_date.focus()
            return None

        # 3. 사용 가능 기간 정수 검사
        try:
            period_months = int(period_str)
            if period_months <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("숫자 입력 오류", "사용 가능 기간은 1 이상의 정수로 입력해 주세요. (예: 6)")
            self.entry_period.focus()
            return None

        # 4. 종료일 계산
        try:
            end_date = calculator.calculate_end_date(open_date, period_months)
        except Exception as e:
            messagebox.showerror("계산 오류", f"종료일 계산 중 오류가 발생했습니다: {e}")
            return None

        return name, category, open_date, period_months, end_date

    def handle_add(self):
        """제품 등록 처리"""
        validated = self.validate_inputs()
        if not validated:
            return

        name, category, open_date, period_months, end_date = validated
        storage.add_item(name, category, open_date, period_months, end_date)
        
        messagebox.showinfo("등록 완료", f"'{name}' 제품이 성공적으로 등록되었습니다.")
        self.clear_input_fields()
        self.refresh_item_list()

    def handle_update(self):
        """제품 수정 처리"""
        if self.selected_item_id is None:
            messagebox.showwarning("선택 오류", "수정할 제품을 우측 목록에서 먼저 클릭하여 선택해 주세요.")
            return

        validated = self.validate_inputs()
        if not validated:
            return

        name, category, open_date, period_months, end_date = validated
        success = storage.update_item(self.selected_item_id, name, category, open_date, period_months, end_date)
        
        if success:
            messagebox.showinfo("수정 완료", f"'{name}' 제품 정보가 수정되었습니다.")
            self.clear_input_fields()
            self.refresh_item_list()
        else:
            messagebox.showerror("수정 실패", "해당 제품을 찾을 수 없습니다.")

    def handle_delete(self):
        """제품 삭제 처리"""
        if self.selected_item_id is None:
            messagebox.showwarning("선택 오류", "삭제할 제품을 우측 목록에서 먼저 클릭하여 선택해 주세요.")
            return

        name = self.entry_name.get().strip()
        confirm = messagebox.askyesno("삭제 확인", f"정말로 '{name}' 제품을 삭제하시겠습니까?\n삭제된 데이터는 복구할 수 없습니다.")
        if not confirm:
            return

        success = storage.delete_item(self.selected_item_id)
        if success:
            messagebox.showinfo("삭제 완료", "제품이 삭제되었습니다.")
            self.clear_input_fields()
            self.refresh_item_list()
        else:
            messagebox.showerror("삭제 실패", "해당 제품을 찾을 수 없습니다.")

    def on_tree_select(self, event):
        """목록에서 제품을 클릭했을 때 좌측 입력창에 해당 데이터를 채움"""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item_row = self.tree.item(selected_items[0])
        values = item_row["values"]
        if not values:
            return

        # values: (id, name, category, open_date, end_date, remaining, status)
        item_id = int(values[0])
        self.selected_item_id = item_id

        # storage에서 원본 데이터 찾아 개월 수 함께 로드
        all_items = storage.load_items()
        current_item = next((item for item in all_items if item["id"] == item_id), None)

        if current_item:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, current_item["name"])

            self.combo_category.set(current_item["category"])

            self.entry_open_date.delete(0, tk.END)
            self.entry_open_date.insert(0, current_item["open_date"])

            self.entry_period.delete(0, tk.END)
            self.entry_period.insert(0, str(current_item["period_months"]))

    def refresh_item_list(self):
        """CSV 데이터를 읽고 현재 날짜 기준 계산 후 목록 및 요약 정보 갱신"""
        # 기존 목록 비우기
        for row in self.tree.get_children():
            self.tree.delete(row)

        all_items = storage.load_items()
        current_filter = self.filter_var.get()

        total_count = len(all_items)
        urgent_count = 0
        expired_count = 0

        for item in all_items:
            try:
                rem_days = calculator.calculate_remaining_days(item["end_date"])
                status = calculator.get_item_status(rem_days)
            except Exception:
                rem_days = 0
                status = "계산오류"

            # 통계 집계
            if status == "기간임박":
                urgent_count += 1
            elif status == "기간만료":
                expired_count += 1

            # 필터링 조건 확인
            if current_filter != "전체" and status != current_filter:
                continue

            # 남은 기간 표시 포맷
            if rem_days > 0:
                rem_text = f"D-{rem_days} ({rem_days}일)"
            elif rem_days == 0:
                rem_text = "D-Day (오늘)"
            else:
                rem_text = f"D+{-rem_days} ({-rem_days}일 지남)"

            # 상태별 색상 태그
            tag = "normal"
            if status == "기간만료":
                tag = "expired"
            elif status == "기간임박":
                tag = "urgent"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    item["id"],
                    item["name"],
                    item["category"],
                    item["open_date"],
                    item["end_date"],
                    rem_text,
                    status
                ),
                tags=(tag,)
            )

        # 하단 요약 라벨 갱신
        self.lbl_stat_total.config(text=f"전체 제품: {total_count}개")
        self.lbl_stat_urgent.config(text=f"⚠️ 기간 임박: {urgent_count}개")
        self.lbl_stat_expired.config(text=f"🚨 기간 만료: {expired_count}개")


def main():
    root = tk.Tk()
    app = LifeCheckApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
