"""
LifeCheck - 생활용품 사용 기간 관리 프로그램 (main.py)
담당: 팀원 1 (GUI 화면 구성 및 사용자 이벤트 처리)

- tkinter / ttk 기반의 직관적인 데스크톱 GUI
- 제품 등록, 조회, 수정, 삭제(CRUD) 및 입력 초기화
- 상태별(전체, 기간임박, 기간만료, 사용가능) 실시간 목록 필터링
- 목록 선택 시 입력폼 자동 완성 및 상태별 하이라이트 색상 태그
- 입력값 유효성 검사 및 안내 대화상자(messagebox) 연동
- 추가 기능 4·5의 GUI 연동과 이벤트 처리는 팀원 3 (계산·테스트 담당) 작업
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date
import csv

import storage
import calculator


class LifeCheckApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LifeCheck - 생활용품 사용 기간 관리 프로그램")
        self.root.geometry("1160x720")
        self.root.minsize(980, 660)

        # 현재 선택된 제품의 ID (수정/삭제 시 사용, 미선택 시 None)
        self.selected_item_id = None
        self.selected_item_status = None

        # 필터 상태 변수 ("전체", "기간임박", "기간만료", "사용가능")
        self.filter_var = tk.StringVar(value="전체")
        # [추가 기능 / 팀원 3] 기존 화면에 검색·이력·알림 설정만 확장
        self.view_var = tk.StringVar(value="사용 중")
        self.search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar(value="전체")
        self.sort_var = tk.StringVar(value="등록 순")
        self.urgent_days = storage.load_settings()["urgent_days"]
        self.urgent_days_var = tk.StringVar(value=str(self.urgent_days))
        self.current_date = date.today()

        # 스타일 설정
        self.setup_styles()

        # UI 화면 구성
        self.create_widgets()

        # 데이터베이스(CSV) 초기화 및 첫 화면 목록 갱신
        self.refresh_item_list()
        self.search_var.trace_add("write", lambda *_: self.refresh_item_list())
        self.root.after_idle(self.show_startup_alert)
        self.root.after(60000, self.check_date_change)

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
        self.today_label = ttk.Label(header_frame, text=f"기준일: {today_str}", font=("Malgun Gothic", 9), foreground="#7F8C8D")
        self.today_label.pack(side=tk.RIGHT, pady=5)

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

        self.btn_complete = ttk.Button(btn_frame, text="사용 완료", command=self.handle_complete)
        self.btn_complete.grid(row=2, column=0, padx=2, pady=3, sticky="ew")

        self.btn_register_again = ttk.Button(btn_frame, text="같은 제품 다시 등록", command=self.handle_register_again)
        self.btn_register_again.grid(row=2, column=1, padx=2, pady=3, sticky="ew")
        self.update_action_buttons()

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

        self.lbl_stat_completed = ttk.Label(summary_frame, text="사용 완료 이력: 0개")
        self.lbl_stat_completed.pack(anchor=tk.W, pady=1)

    def create_right_panel(self, parent):
        """우측 필터 및 Treeview 목록 패널"""
        right_frame = ttk.LabelFrame(parent, text=" [ 생활용품 목록 및 상태 ] ", padding="15")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # [추가 기능 / 팀원 3] 기존 목록 위에 조회 및 알림 설정 추가
        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill=tk.X, pady=(0, 8))
        view_combo = ttk.Combobox(toolbar, textvariable=self.view_var,
                                  values=["사용 중", "사용 완료 이력"], state="readonly", width=14)
        view_combo.pack(side=tk.LEFT, padx=(0, 8))
        view_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh_item_list())
        ttk.Label(toolbar, text="임박 기준").pack(side=tk.LEFT)
        urgent_combo = ttk.Combobox(toolbar, textvariable=self.urgent_days_var,
                                    values=[str(d) for d in storage.URGENT_DAY_OPTIONS],
                                    state="readonly", width=3)
        urgent_combo.pack(side=tk.LEFT, padx=4)
        urgent_combo.bind("<<ComboboxSelected>>", self.handle_urgent_days_change)
        ttk.Label(toolbar, text="일").pack(side=tk.LEFT, padx=(0, 10))
        self.sort_combo = ttk.Combobox(toolbar, textvariable=self.sort_var,
                                       values=["등록 순", "남은 기간순"], state="readonly", width=12)
        self.sort_combo.pack(side=tk.LEFT)
        self.sort_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh_item_list())
        ttk.Button(toolbar, text="새로 고침", command=self.refresh_item_list).pack(side=tk.RIGHT)

        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(search_frame, text="제품명 검색").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(search_frame, textvariable=self.search_var, width=18).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Label(search_frame, text="분류").pack(side=tk.LEFT, padx=(0, 5))
        self.category_filter_combo = ttk.Combobox(
            search_frame, textvariable=self.category_filter_var, values=["전체"],
            state="readonly", width=10)
        self.category_filter_combo.pack(side=tk.LEFT)
        self.category_filter_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh_item_list())

        # 상단 필터 영역
        filter_frame = ttk.Frame(right_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="보기 필터: ", font=("Malgun Gothic", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))

        filters = [("전체 보기", "전체"), ("⚠️ 기간 임박", "기간임박"), ("🚨 기간 만료", "기간만료"), ("✅ 사용 가능", "사용가능")]
        self.status_filter_buttons = []
        for text, mode in filters:
            rb = ttk.Radiobutton(
                filter_frame,
                text=text,
                value=mode,
                variable=self.filter_var,
                command=self.refresh_item_list
            )
            rb.pack(side=tk.LEFT, padx=6)
            self.status_filter_buttons.append(rb)

        # Treeview 표 (목록)
        columns = ("id", "name", "category", "open_date", "end_date", "remaining", "status", "completed_date")
        list_frame = ttk.Frame(right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")

        # 각 컬럼 헤더 및 너비 설정
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="제품명")
        self.tree.heading("category", text="분류")
        self.tree.heading("open_date", text="개봉일")
        self.tree.heading("end_date", text="사용종료일")
        self.tree.heading("remaining", text="남은 기간")
        self.tree.heading("status", text="상태")
        self.tree.heading("completed_date", text="사용 완료일")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("name", width=140, anchor=tk.W)
        self.tree.column("category", width=80, anchor=tk.CENTER)
        self.tree.column("open_date", width=90, anchor=tk.CENTER)
        self.tree.column("end_date", width=90, anchor=tk.CENTER)
        self.tree.column("remaining", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        self.tree.column("completed_date", width=95, anchor=tk.CENTER)

        # 스크롤바 연결
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        horizontal = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar.set, xscrollcommand=horizontal.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.list_count_label = ttk.Label(right_frame, text="조회 결과: 0개")
        self.list_count_label.pack(anchor=tk.W, pady=(5, 0))

        # 항목 선택 이벤트 바인딩
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 상태별 폰트/색상 태그 정의
        self.tree.tag_configure("expired", foreground="#C0392B", background="#FDEDEC")  # 연한 빨강
        self.tree.tag_configure("urgent", foreground="#D35400", background="#FEF9E7")   # 연한 주황
        self.tree.tag_configure("normal", foreground="#27AE60")                         # 초록
        self.tree.tag_configure("completed", foreground="#616A6B")
        self.tree.tag_configure("error", foreground="#7D3C98")

    # ---------------- UI 이벤트 및 핸들러 ----------------

    def set_today_date(self):
        """오늘 날짜를 개봉일 입력창에 삽입"""
        self.entry_open_date.delete(0, tk.END)
        self.entry_open_date.insert(0, date.today().strftime("%Y-%m-%d"))

    def clear_input_fields(self):
        """입력 필드를 비우고 선택 상태를 초기화"""
        self.selected_item_id = None
        self.selected_item_status = None
        self.entry_name.delete(0, tk.END)
        self.combo_category.set("화장품")
        self.set_today_date()
        self.entry_period.delete(0, tk.END)
        
        # 목록 선택 해제
        selected = self.tree.selection()
        if selected:
            self.tree.selection_remove(selected)
        self.update_action_buttons()

    def update_action_buttons(self):
        """조회 조건 변경 후 숨겨진 제품을 잘못 수정하거나 삭제하지 않도록 선택 상태를 반영."""
        selected = self.selected_item_id is not None
        active = selected and self.selected_item_status == "사용중"
        self.btn_update.configure(state="normal" if active else "disabled")
        self.btn_delete.configure(state="normal" if selected else "disabled")
        self.btn_complete.configure(state="normal" if active else "disabled")
        self.btn_register_again.configure(
            state="normal" if selected and not active else "disabled")

    def load_items_safely(self):
        """입출력 오류를 안내하고 실패와 빈 목록을 구분합니다."""
        try:
            return storage.load_items()
        except (OSError, csv.Error) as exc:
            messagebox.showerror("불러오기 실패", f"제품 데이터를 읽을 수 없습니다.\n{exc}")
            return None

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
        try:
            storage.add_item(name, category, open_date, period_months, end_date)
        except (OSError, csv.Error, ValueError) as exc:
            messagebox.showerror("저장 실패", f"제품을 등록하지 못했습니다.\n{exc}")
            return
        
        messagebox.showinfo("등록 완료", f"'{name}' 제품이 성공적으로 등록되었습니다.")
        self.clear_input_fields()
        self.view_var.set("사용 중")
        self.filter_var.set("전체")
        self.category_filter_var.set("전체")
        self.search_var.set("")
        self.refresh_item_list()

    def handle_update(self):
        """제품 수정 처리"""
        if self.selected_item_id is None:
            messagebox.showwarning("선택 오류", "수정할 제품을 우측 목록에서 먼저 클릭하여 선택해 주세요.")
            return

        if self.selected_item_status != "사용중":
            messagebox.showwarning("수정 불가", "완료 이력은 보존됩니다. '같은 제품 다시 등록'을 이용해 주세요.")
            return

        validated = self.validate_inputs()
        if not validated:
            return

        name, category, open_date, period_months, end_date = validated
        try:
            success = storage.update_item(self.selected_item_id, name, category, open_date, period_months, end_date)
        except (OSError, csv.Error, ValueError) as exc:
            messagebox.showerror("저장 실패", f"제품을 수정하지 못했습니다.\n{exc}")
            return
        
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

        try:
            success = storage.delete_item(self.selected_item_id)
        except (OSError, csv.Error, ValueError) as exc:
            messagebox.showerror("저장 실패", f"제품을 삭제하지 못했습니다.\n{exc}")
            return
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
            self.selected_item_id = None
            self.selected_item_status = None
            self.update_action_buttons()
            return

        item_row = self.tree.item(selected_items[0])
        values = item_row["values"]
        if not values:
            return

        # values: (id, name, category, open_date, end_date, remaining, status)
        item_id = int(values[0])
        self.selected_item_id = item_id

        # storage에서 원본 데이터 찾아 개월 수 함께 로드
        all_items = self.load_items_safely()
        if all_items is None:
            self.clear_input_fields()
            return
        current_item = next((item for item in all_items if item["id"] == item_id), None)

        if current_item:
            self.selected_item_status = current_item["usage_status"]
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, current_item["name"])

            self.combo_category.set(current_item["category"])

            self.entry_open_date.delete(0, tk.END)
            self.entry_open_date.insert(0, current_item["open_date"])

            self.entry_period.delete(0, tk.END)
            self.entry_period.insert(0, str(current_item["period_months"]))
            self.update_action_buttons()
        else:
            self.clear_input_fields()

    def refresh_item_list(self):
        """CSV 데이터를 읽고 현재 날짜 기준 계산 후 목록 및 요약 정보 갱신"""
        all_items = self.load_items_safely()
        if all_items is None:
            return
        self.clear_input_fields()
        # 기존 목록 비우기
        for row in self.tree.get_children():
            self.tree.delete(row)

        history = self.view_var.get() == "사용 완료 이력"
        categories = ["전체"] + sorted({item["category"] for item in all_items})
        self.category_filter_combo.configure(values=categories)
        if self.category_filter_var.get() not in categories:
            self.category_filter_var.set("전체")
        for button in self.status_filter_buttons:
            button.configure(state="disabled" if history else "normal")
        self.sort_combo.configure(state="disabled" if history else "readonly")
        active_columns = ("id", "name", "category", "open_date", "end_date", "remaining", "status")
        self.tree.configure(displaycolumns=active_columns + ("completed_date",) if history else active_columns)
        self.current_date = date.today()
        self.today_label.configure(text=f"기준일: {self.current_date:%Y년 %m월 %d일}")
        active_items = calculator.filter_items(all_items, urgent_days=self.urgent_days,
                                                base_date=self.current_date)
        urgent_count = sum(item["status"] == "기간임박" for item in active_items)
        expired_count = sum(item["status"] == "기간만료" for item in active_items)
        visible_items = calculator.filter_items(
            all_items, query=self.search_var.get(), category=self.category_filter_var.get(),
            status=self.filter_var.get(), history=history,
            sort_by_remaining=self.sort_var.get() == "남은 기간순",
            urgent_days=self.urgent_days, base_date=self.current_date)

        for item in visible_items:
            rem_days = item["remaining_days"]
            status = item["status"]

            # 남은 기간 표시 포맷
            if rem_days is None:
                rem_text = "—"
            elif rem_days > 0:
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
            elif status == "사용완료":
                tag = "completed"
            elif status == "계산오류":
                tag = "error"

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
                    status,
                    item["completed_date"],
                ),
                tags=(tag,)
            )

        # 하단 요약 라벨 갱신
        self.lbl_stat_total.config(text=f"사용 중 제품: {len(active_items)}개")
        self.lbl_stat_urgent.config(text=f"⚠️ 기간 임박: {urgent_count}개")
        self.lbl_stat_expired.config(text=f"🚨 기간 만료: {expired_count}개")
        self.lbl_stat_completed.config(text=f"사용 완료 이력: {len(all_items) - len(active_items)}개")
        self.list_count_label.config(text=f"조회 결과: {len(visible_items)}개 · 임박 기준: {self.urgent_days}일")

    # ---------------- 추가 기능 4·5 / 팀원 3 (계산·테스트 담당) ----------------

    def handle_urgent_days_change(self, event=None):
        days = int(self.urgent_days_var.get())
        try:
            storage.save_settings(days)
        except (OSError, ValueError) as exc:
            self.urgent_days_var.set(str(self.urgent_days))
            messagebox.showerror("설정 저장 실패", str(exc))
            return
        self.urgent_days = days
        self.refresh_item_list()

    def show_startup_alert(self):
        items = self.load_items_safely()
        if items is None:
            return
        alerts = calculator.get_alert_items(items, self.urgent_days)
        if not alerts:
            return
        expired = sum(item["status"] == "기간만료" for item in alerts)
        lines = [f"임박 기준 {self.urgent_days}일 · 기간 임박 {len(alerts) - expired}개 · 기간 만료 {expired}개", ""]
        for item in alerts[:10]:
            days = item["remaining_days"]
            period = f"{abs(days)}일 지남" if days < 0 else f"{days}일 남음"
            lines.append(f"• {item['name']}: {item['status']} ({period})")
        if len(alerts) > 10:
            lines.append(f"외 {len(alerts) - 10}개 — 목록에서 확인해 주세요.")
        messagebox.showinfo("교체 시기 안내", "\n".join(lines))

    def handle_complete(self):
        if self.selected_item_id is None or self.selected_item_status != "사용중":
            messagebox.showwarning("선택 오류", "사용 완료 처리할 사용 중 제품을 선택해 주세요.")
            return
        completed_date = simpledialog.askstring(
            "사용 완료", "사용 완료일을 입력해 주세요. (YYYY-MM-DD)",
            initialvalue=date.today().isoformat(), parent=self.root)
        if completed_date is None:
            return
        if not calculator.validate_date_format(completed_date):
            messagebox.showwarning("날짜 형식 오류", "사용 완료일은 YYYY-MM-DD 형식의 유효한 날짜여야 합니다.")
            return
        try:
            success = storage.complete_item(self.selected_item_id, completed_date)
        except (OSError, csv.Error, ValueError) as exc:
            messagebox.showerror("사용 완료 처리 실패", str(exc))
            return
        if success:
            self.refresh_item_list()
            messagebox.showinfo("사용 완료", "사용 완료 이력에 보관했습니다. 상단 목록에서 이력을 확인할 수 있습니다.")
        else:
            self.refresh_item_list()
            messagebox.showwarning("처리 실패", "제품이 없거나 이미 사용 완료 처리되었습니다.")

    def handle_register_again(self):
        if self.selected_item_id is None or self.selected_item_status != "사용완료":
            messagebox.showwarning("선택 오류", "사용 완료 이력에서 다시 등록할 제품을 선택해 주세요.")
            return
        items = self.load_items_safely()
        if items is None:
            return
        item = next((item for item in items if item["id"] == self.selected_item_id), None)
        if item is None:
            self.refresh_item_list()
            return
        self.view_var.set("사용 중")
        self.filter_var.set("전체")
        self.category_filter_var.set("전체")
        self.search_var.set("")
        self.refresh_item_list()
        self.entry_name.insert(0, item["name"])
        self.combo_category.set(item["category"])
        self.entry_period.insert(0, str(item["period_months"]))
        self.entry_open_date.focus_set()
        messagebox.showinfo("같은 제품 다시 등록", "기존 정보를 입력했습니다. 새 개봉일과 사용 기간을 확인한 뒤 '등록'을 눌러 주세요.")

    def check_date_change(self):
        """자정을 넘겨 계속 실행해도 기준일과 상태를 갱신합니다."""
        if date.today() != self.current_date:
            self.refresh_item_list()
        self.root.after(60000, self.check_date_change)


def main():
    root = tk.Tk()
    app = LifeCheckApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
