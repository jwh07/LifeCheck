"""
LifeCheck - 생활용품 사용 기간 관리 프로그램 (app.py)
담당: 전체 프로그램 구성 및 기본 GUI 화면 제작 (전원희) + 기능 1 (생활용품 등록 및 관리)

[디자인 컨셉]
- 화이트 배경(#FFFFFF, #F8FAFC)에 연한 하늘색(#E0F2FE, #0284C7)을 포인트로 한 모던 데스크톱 UI
- 왼쪽 사이드바 (대시보드, 전체 제품, 기간 임박, 기간 만료, 사용 완료 이력, 설정)
- 메인 화면 상단 헤더 및 요약 카드
- 기능 1: 생활용품 목록(Treeview) 조회, 신규 등록(Modal), 수정, 삭제(CSV 연동)
- 기능 2~5: 팀원들이 연계 개발할 수 있도록 화면 기본 구조 완비
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import product_manager

# ================= 색상 및 스타일 상수 =================
COLOR_BG_WHITE = "#FFFFFF"
COLOR_BG_SUB = "#F8FAFC"
COLOR_BORDER = "#E2E8F0"

COLOR_POINT_SKY = "#0284C7"       # 주요 포인트 하늘색
COLOR_LIGHT_SKY = "#E0F2FE"       # 연한 하늘색 배경
COLOR_HOVER_SKY = "#BAE6FD"       # 버튼 호버 하늘색
COLOR_DEEP_NAVY = "#0F172A"       # 진한 텍스트 네이비
COLOR_MUTED_GRAY = "#64748B"      # 보조 텍스트 회색

COLOR_DANGER_RED = "#EF4444"      # 삭제/위험 색상
COLOR_WARNING_AMBER = "#F59E0B"   # 주의 색상


class ProductDialog(tk.Toplevel):
    """제품 등록 및 수정을 위한 팝업 대화상자"""
    def __init__(self, parent, title="제품 등록", initial_data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x420")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG_WHITE)
        self.result = None
        self.initial_data = initial_data

        # 부모 창 중앙에 위치 설정
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.center_window(parent)

    def center_window(self, parent):
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = parent_x + (parent_w - w) // 2
        y = parent_y + (parent_h - h) // 2
        self.geometry(f"+{x}+{y}")

    def create_widgets(self):
        # 헤더 프레임
        header = tk.Frame(self, bg=COLOR_LIGHT_SKY, height=60, padx=20, pady=15)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_text = "✨ " + self.title()
        tk.Label(
            header,
            text=title_text,
            font=("Malgun Gothic", 12, "bold"),
            bg=COLOR_LIGHT_SKY,
            fg=COLOR_POINT_SKY
        ).pack(side=tk.LEFT)

        # 본문 입력 폼 프레임
        form = tk.Frame(self, bg=COLOR_BG_WHITE, padx=25, pady=20)
        form.pack(fill=tk.BOTH, expand=True)

        # 1. 제품명
        tk.Label(form, text="제품명 *", font=("Malgun Gothic", 9, "bold"), bg=COLOR_BG_WHITE, fg=COLOR_DEEP_NAVY).pack(anchor="w", pady=(0, 3))
        self.entry_name = tk.Entry(form, font=("Malgun Gothic", 10), relief="solid", bd=1, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.entry_name.pack(fill=tk.X, pady=(0, 12), ipady=3)

        # 2. 제품 분류
        tk.Label(form, text="제품 분류 *", font=("Malgun Gothic", 9, "bold"), bg=COLOR_BG_WHITE, fg=COLOR_DEEP_NAVY).pack(anchor="w", pady=(0, 3))
        self.combo_category = ttk.Combobox(
            form,
            values=["화장품", "세정용품", "위생용품", "의약외품", "생활기타"],
            font=("Malgun Gothic", 9),
            state="normal"
        )
        self.combo_category.pack(fill=tk.X, pady=(0, 12), ipady=3)
        self.combo_category.set("화장품")

        # 3. 구매일 또는 개봉일
        date_header = tk.Frame(form, bg=COLOR_BG_WHITE)
        date_header.pack(fill=tk.X, pady=(0, 3))
        tk.Label(date_header, text="구매일 또는 개봉일 (YYYY-MM-DD) *", font=("Malgun Gothic", 9, "bold"), bg=COLOR_BG_WHITE, fg=COLOR_DEEP_NAVY).pack(side=tk.LEFT)
        btn_today = tk.Button(
            date_header,
            text="오늘 날짜",
            font=("Malgun Gothic", 8),
            bg=COLOR_LIGHT_SKY,
            fg=COLOR_POINT_SKY,
            relief="flat",
            cursor="hand2",
            command=self.set_today
        )
        btn_today.pack(side=tk.RIGHT)

        self.entry_date = tk.Entry(form, font=("Malgun Gothic", 10), relief="solid", bd=1, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.entry_date.pack(fill=tk.X, pady=(0, 12), ipady=3)
        self.entry_date.insert(0, date.today().strftime("%Y-%m-%d"))

        # 4. 사용 가능 기간 (개월)
        tk.Label(form, text="사용 가능 기간 (개월 단위) *", font=("Malgun Gothic", 9, "bold"), bg=COLOR_BG_WHITE, fg=COLOR_DEEP_NAVY).pack(anchor="w", pady=(0, 3))
        period_box = tk.Frame(form, bg=COLOR_BG_WHITE)
        period_box.pack(fill=tk.X, pady=(0, 20))
        self.entry_period = tk.Entry(period_box, font=("Malgun Gothic", 10), relief="solid", bd=1, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.entry_period.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        tk.Label(period_box, text=" 개월", font=("Malgun Gothic", 9), bg=COLOR_BG_WHITE, fg=COLOR_MUTED_GRAY).pack(side=tk.LEFT, padx=(5, 0))

        # 기존 데이터 채우기 (수정 모드일 때)
        if self.initial_data:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, self.initial_data["name"])
            self.combo_category.set(self.initial_data["category"])
            self.entry_date.delete(0, tk.END)
            self.entry_date.insert(0, self.initial_data["open_date"])
            self.entry_period.delete(0, tk.END)
            self.entry_period.insert(0, str(self.initial_data["period_months"]))

        # 하단 액션 버튼 프레임
        btn_frame = tk.Frame(self, bg=COLOR_BG_SUB, height=55, padx=20)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        btn_frame.pack_propagate(False)

        btn_cancel = tk.Button(
            btn_frame,
            text="취소",
            font=("Malgun Gothic", 9),
            bg="#E2E8F0",
            fg=COLOR_DEEP_NAVY,
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, pady=12, padx=(5, 0))

        btn_save = tk.Button(
            btn_frame,
            text="저장하기",
            font=("Malgun Gothic", 9, "bold"),
            bg=COLOR_POINT_SKY,
            fg="#FFFFFF",
            relief="flat",
            padx=18,
            pady=5,
            cursor="hand2",
            command=self.on_save
        )
        btn_save.pack(side=tk.RIGHT, pady=12)

    def set_today(self):
        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, date.today().strftime("%Y-%m-%d"))

    def on_save(self):
        name = self.entry_name.get().strip()
        category = self.combo_category.get().strip()
        open_date = self.entry_date.get().strip()
        period_str = self.entry_period.get().strip()

        # 1. 필수값 누락 검증
        if not name:
            messagebox.showwarning("입력 오류", "제품명을 입력해 주세요.", parent=self)
            self.entry_name.focus()
            return
        if not category:
            messagebox.showwarning("입력 오류", "제품 분류를 선택해 주세요.", parent=self)
            self.combo_category.focus()
            return
        if not open_date:
            messagebox.showwarning("입력 오류", "구매일 또는 개봉일을 입력해 주세요.", parent=self)
            self.entry_date.focus()
            return
        if not period_str:
            messagebox.showwarning("입력 오류", "사용 가능 기간을 입력해 주세요.", parent=self)
            self.entry_period.focus()
            return

        # 2. 날짜 형식 검증 (YYYY-MM-DD)
        try:
            datetime.strptime(open_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "날짜 형식 오류",
                "날짜 형식이 올바르지 않습니다.\n'YYYY-MM-DD' 형식으로 입력해 주세요. (예: 2026-10-01)",
                parent=self
            )
            self.entry_date.focus()
            return

        # 3. 개월 수 숫자 검증
        try:
            period_months = int(period_str)
            if period_months <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("숫자 입력 오류", "사용 가능 기간은 1 이상의 정수로 입력해 주세요. (예: 6)", parent=self)
            self.entry_period.focus()
            return

        self.result = {
            "name": name,
            "category": category,
            "open_date": open_date,
            "period_months": period_months
        }
        self.destroy()


class LifeCheckUI:
    """LifeCheck 메인 윈도우 UI 클래스"""
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LifeCheck - 생활용품 사용 기간 관리 프로그램")
        self.root.geometry("1100x680")
        self.root.minsize(980, 600)
        self.root.configure(bg=COLOR_BG_SUB)

        # 현재 활성화된 메뉴 이름
        self.current_menu = "전체 제품"
        self.menu_buttons = {}

        # 데이터 저장소 초기화
        product_manager.init_storage()

        # UI 스타일 설정
        self.setup_styles()

        # 레이아웃 생성
        self.create_layout()

        # 첫 화면(전체 제품) 표시
        self.switch_view("전체 제품")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview 스타일 (모던 화이트 & 하늘색 포인트)
        style.configure(
            "Treeview.Heading",
            font=("Malgun Gothic", 9, "bold"),
            background=COLOR_LIGHT_SKY,
            foreground=COLOR_DEEP_NAVY,
            relief="flat",
            padding=6
        )
        style.map("Treeview.Heading", background=[("active", COLOR_HOVER_SKY)])

        style.configure(
            "Treeview",
            font=("Malgun Gothic", 9),
            background=COLOR_BG_WHITE,
            fieldbackground=COLOR_BG_WHITE,
            foreground=COLOR_DEEP_NAVY,
            rowheight=30,
            bordercolor=COLOR_BORDER,
            borderwidth=1
        )
        style.map(
            "Treeview",
            background=[("selected", COLOR_LIGHT_SKY)],
            foreground=[("selected", COLOR_POINT_SKY)]
        )

    def create_layout(self):
        # 1. 왼쪽 사이드바
        self.sidebar = tk.Frame(self.root, bg=COLOR_BG_WHITE, width=220, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # 사이드바 로고 영역
        logo_frame = tk.Frame(self.sidebar, bg=COLOR_BG_WHITE, height=75, padx=20, pady=15)
        logo_frame.pack(fill=tk.X)
        logo_frame.pack_propagate(False)

        tk.Label(
            logo_frame,
            text="✨ LifeCheck",
            font=("Malgun Gothic", 14, "bold"),
            bg=COLOR_BG_WHITE,
            fg=COLOR_POINT_SKY
        ).pack(anchor="w")

        tk.Label(
            logo_frame,
            text="생활용품 사용 기간 관리",
            font=("Malgun Gothic", 8),
            bg=COLOR_BG_WHITE,
            fg=COLOR_MUTED_GRAY
        ).pack(anchor="w")

        # 구분선
        tk.Frame(self.sidebar, bg=COLOR_BORDER, height=1).pack(fill=tk.X, padx=10, pady=(0, 10))

        # 사이드바 메뉴 목록
        menu_items = [
            ("📊 대시보드", "대시보드"),
            ("📦 전체 제품", "전체 제품"),
            ("⚠️ 기간 임박", "기간 임박"),
            ("🚨 기간 만료", "기간 만료"),
            ("📋 사용 완료 이력", "사용 완료 이력"),
            ("⚙️ 설정", "설정")
        ]

        menu_container = tk.Frame(self.sidebar, bg=COLOR_BG_WHITE)
        menu_container.pack(fill=tk.X, padx=10)

        for label_text, key in menu_items:
            btn = tk.Button(
                menu_container,
                text="  " + label_text,
                font=("Malgun Gothic", 9, "bold"),
                anchor="w",
                bg=COLOR_BG_WHITE,
                fg=COLOR_DEEP_NAVY,
                relief="flat",
                padx=10,
                pady=10,
                cursor="hand2",
                command=lambda k=key: self.switch_view(k)
            )
            btn.pack(fill=tk.X, pady=2)
            self.menu_buttons[key] = btn

        # 사이드바 하단 정보 카드
        bottom_card = tk.Frame(self.sidebar, bg=COLOR_LIGHT_SKY, padx=12, pady=12)
        bottom_card.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=15)
        tk.Label(
            bottom_card,
            text="심화프로그래밍 팀플",
            font=("Malgun Gothic", 8, "bold"),
            bg=COLOR_LIGHT_SKY,
            fg=COLOR_POINT_SKY
        ).pack(anchor="w")
        tk.Label(
            bottom_card,
            text="담당: UI 및 기능 1 구현\n(생활용품 등록 및 관리)",
            font=("Malgun Gothic", 8),
            bg=COLOR_LIGHT_SKY,
            fg=COLOR_DEEP_NAVY,
            justify="left"
        ).pack(anchor="w", pady=(3, 0))

        # 2. 오른쪽 메인 콘텐츠 영역
        self.main_container = tk.Frame(self.root, bg=COLOR_BG_SUB)
        self.main_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 상단 헤더 바
        self.create_top_header()

        # 동적 콘텐츠 뷰 영역 (메뉴별 전환)
        self.content_frame = tk.Frame(self.main_container, bg=COLOR_BG_SUB, padx=25, pady=15)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

    def create_top_header(self):
        top_bar = tk.Frame(self.main_container, bg=COLOR_BG_WHITE, height=75, padx=25, highlightthickness=1, highlightbackground=COLOR_BORDER)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)

        left_info = tk.Frame(top_bar, bg=COLOR_BG_WHITE)
        left_info.pack(side=tk.LEFT, fill=tk.Y, pady=12)

        self.lbl_view_title = tk.Label(
            left_info,
            text="전체 제품 관리",
            font=("Malgun Gothic", 13, "bold"),
            bg=COLOR_BG_WHITE,
            fg=COLOR_DEEP_NAVY
        )
        self.lbl_view_title.pack(anchor="w")

        self.lbl_view_desc = tk.Label(
            left_info,
            text="등록된 모든 생활용품을 조회하고, 신규 등록·수정·삭제를 진행할 수 있습니다.",
            font=("Malgun Gothic", 8),
            bg=COLOR_BG_WHITE,
            fg=COLOR_MUTED_GRAY
        )
        self.lbl_view_desc.pack(anchor="w")

        # 우측 오늘 날짜
        right_info = tk.Frame(top_bar, bg=COLOR_BG_WHITE)
        right_info.pack(side=tk.RIGHT, fill=tk.Y, pady=18)
        today_str = date.today().strftime("%Y년 %m월 %d일")
        tk.Label(
            right_info,
            text=f"📅 오늘 기준일: {today_str}",
            font=("Malgun Gothic", 9, "bold"),
            bg=COLOR_LIGHT_SKY,
            fg=COLOR_POINT_SKY,
            padx=10,
            pady=4
        ).pack()

    def update_sidebar_selection(self, selected_key):
        """선택된 사이드바 메뉴 버튼에 연한 하늘색 하이라이트 적용"""
        for key, btn in self.menu_buttons.items():
            if key == selected_key:
                btn.configure(
                    bg=COLOR_LIGHT_SKY,
                    fg=COLOR_POINT_SKY
                )
            else:
                btn.configure(
                    bg=COLOR_BG_WHITE,
                    fg=COLOR_DEEP_NAVY
                )

    def switch_view(self, view_name):
        """사이드바 메뉴 클릭 시 해당 화면으로 전환"""
        self.current_menu = view_name
        self.update_sidebar_selection(view_name)

        # 기존 콘텐츠 위젯 삭제
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if view_name == "전체 제품":
            self.lbl_view_title.config(text="전체 제품 관리 (기능 1)")
            self.lbl_view_desc.config(text="등록된 모든 생활용품을 확인하고, 신규 등록·수정·삭제를 관리합니다.")
            self.render_products_view()

        elif view_name == "대시보드":
            self.lbl_view_title.config(text="대시보드 (Dashboard)")
            self.lbl_view_desc.config(text="생활용품 현황 및 핵심 통계를 한눈에 확인합니다.")
            self.render_dashboard_view()

        elif view_name == "기간 임박":
            self.lbl_view_title.config(text="기간 임박 제품 (기능 3 예정)")
            self.lbl_view_desc.config(text="사용 기간이 30일 이내로 남은 제품들을 별도로 확인합니다.")
            self.render_placeholder_view("기능 3: 사용 기간 임박 제품 확인", "팀원(원태희)이 기능 2의 남은 기간 계산 로직을 연계하여 구현할 화면입니다.")

        elif view_name == "기간 만료":
            self.lbl_view_title.config(text="기간 만료 제품 (기능 3 예정)")
            self.lbl_view_desc.config(text="사용 가능 기간이 종료된 제품들을 확인하고 교체 여부를 결정합니다.")
            self.render_placeholder_view("기능 3: 기간 만료 제품 확인", "팀원(원태희)이 사용 종료일 경과 여부를 연계하여 구현할 화면입니다.")

        elif view_name == "사용 완료 이력":
            self.lbl_view_title.config(text="사용 완료 및 교체 이력 (기능 5 예정)")
            self.lbl_view_desc.config(text="사용을 마친 제품의 보관 이력을 확인하고, 같은 제품을 간편하게 다시 등록합니다.")
            self.render_placeholder_view("기능 5: 사용 완료 및 교체 이력 관리", "팀원(원태희)이 사용 완료 처리 및 재등록 기능을 구현할 화면입니다.")

        elif view_name == "설정":
            self.lbl_view_title.config(text="환경 설정 (기능 4 예정)")
            self.lbl_view_desc.config(text="기간 임박 기준(7일/14일/30일) 및 알림 옵션을 설정합니다.")
            self.render_placeholder_view("기능 4: 맞춤형 기간 알림 및 환경 설정", "팀원(원태희)이 알림 기준값 선택 및 저장(JSON) 기능을 구현할 화면입니다.")

    # ================= 1. 전체 제품 화면 (기능 1 중심) =================

    def render_products_view(self):
        """기능 1: 생활용품 목록 조회, 등록, 수정, 삭제 화면"""
        # 1. 상단 요약 카드 및 액션 툴바
        top_action_frame = tk.Frame(self.content_frame, bg=COLOR_BG_SUB)
        top_action_frame.pack(fill=tk.X, pady=(0, 15))

        # 좌측 요약 박스
        summary_card = tk.Frame(
            top_action_frame,
            bg=COLOR_BG_WHITE,
            padx=18,
            pady=10,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER
        )
        summary_card.pack(side=tk.LEFT)

        products = product_manager.get_all_products()
        tk.Label(summary_card, text="등록된 생활용품", font=("Malgun Gothic", 8), bg=COLOR_BG_WHITE, fg=COLOR_MUTED_GRAY).pack(anchor="w")
        self.lbl_total_count = tk.Label(
            summary_card,
            text=f"총 {len(products)}개",
            font=("Malgun Gothic", 14, "bold"),
            bg=COLOR_BG_WHITE,
            fg=COLOR_POINT_SKY
        )
        self.lbl_total_count.pack(anchor="w")

        # 우측 액션 버튼들 (제품 등록 버튼을 가장 눈에 띄게 배치)
        btn_box = tk.Frame(top_action_frame, bg=COLOR_BG_SUB)
        btn_box.pack(side=tk.RIGHT, pady=5)

        # ➕ 제품 등록 버튼 (강조: 하늘색/블루)
        btn_add = tk.Button(
            btn_box,
            text="➕ 새 제품 등록",
            font=("Malgun Gothic", 10, "bold"),
            bg=COLOR_POINT_SKY,
            fg="#FFFFFF",
            relief="flat",
            padx=16,
            pady=7,
            cursor="hand2",
            command=self.open_add_dialog
        )
        btn_add.pack(side=tk.LEFT, padx=5)

        # ✏️ 수정 버튼
        btn_edit = tk.Button(
            btn_box,
            text="✏️ 선택 수정",
            font=("Malgun Gothic", 9),
            bg=COLOR_BG_WHITE,
            fg=COLOR_DEEP_NAVY,
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.open_edit_dialog
        )
        btn_edit.pack(side=tk.LEFT, padx=5)

        # 🗑️ 삭제 버튼
        btn_delete = tk.Button(
            btn_box,
            text="🗑️ 선택 삭제",
            font=("Malgun Gothic", 9),
            bg=COLOR_BG_WHITE,
            fg=COLOR_DANGER_RED,
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.handle_delete
        )
        btn_delete.pack(side=tk.LEFT, padx=5)

        # 🔄 새로고침 버튼
        btn_refresh = tk.Button(
            btn_box,
            text="🔄",
            font=("Malgun Gothic", 9),
            bg=COLOR_BG_WHITE,
            fg=COLOR_MUTED_GRAY,
            relief="solid",
            bd=1,
            padx=8,
            pady=6,
            cursor="hand2",
            command=self.load_product_table
        )
        btn_refresh.pack(side=tk.LEFT, padx=5)

        # 2. 제품 목록 표 (Treeview)
        table_card = tk.Frame(
            self.content_frame,
            bg=COLOR_BG_WHITE,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            padx=10,
            pady=10
        )
        table_card.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "name", "category", "open_date", "period_months")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="제품명")
        self.tree.heading("category", text="제품 분류")
        self.tree.heading("open_date", text="구매일 / 개봉일")
        self.tree.heading("period_months", text="사용 가능 기간")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("category", width=140, anchor="center")
        self.tree.column("open_date", width=160, anchor="center")
        self.tree.column("period_months", width=140, anchor="center")

        # 스크롤바
        scrollbar = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 더블 클릭 시 수정 대화상자 오픈 바인딩
        self.tree.bind("<Double-1>", lambda event: self.open_edit_dialog())

        # 데이터 로드
        self.load_product_table()

        # 하단 팁 라벨
        tip_lbl = tk.Label(
            self.content_frame,
            text="💡 항목을 클릭한 뒤 [선택 수정]을 누르거나, 항목을 더블 클릭하면 제품 정보를 수정할 수 있습니다.",
            font=("Malgun Gothic", 8),
            bg=COLOR_BG_SUB,
            fg=COLOR_MUTED_GRAY
        )
        tip_lbl.pack(anchor="w", pady=(8, 0))

    def load_product_table(self):
        """CSV에서 데이터를 읽어 표와 요약 카드를 새로고침"""
        # 기존 표 내용 비우기
        for item in self.tree.get_children():
            self.tree.delete(item)

        products = product_manager.get_all_products()
        for p in products:
            period_text = f"{p['period_months']}개월"
            self.tree.insert(
                "",
                tk.END,
                values=(p["id"], p["name"], p["category"], p["open_date"], period_text)
            )

        if hasattr(self, "lbl_total_count"):
            self.lbl_total_count.config(text=f"총 {len(products)}개")

    def open_add_dialog(self):
        """제품 신규 등록 팝업창 열기"""
        dialog = ProductDialog(self.root, title="새 생활용품 등록")
        self.root.wait_window(dialog)

        if dialog.result:
            new_p = product_manager.add_product(
                name=dialog.result["name"],
                category=dialog.result["category"],
                open_date=dialog.result["open_date"],
                period_months=dialog.result["period_months"]
            )
            messagebox.showinfo("등록 완료", f"'{new_p['name']}' 제품이 성공적으로 등록되었습니다.")
            self.load_product_table()

    def open_edit_dialog(self):
        """선택된 제품 수정 팝업창 열기"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 오류", "수정할 제품을 목록에서 먼저 클릭하여 선택해 주세요.")
            return

        values = self.tree.item(selected[0])["values"]
        product_id = int(values[0])
        product_data = product_manager.get_product_by_id(product_id)

        if not product_data:
            messagebox.showerror("오류", "해당 제품 데이터를 찾을 수 없습니다.")
            return

        dialog = ProductDialog(self.root, title="제품 정보 수정", initial_data=product_data)
        self.root.wait_window(dialog)

        if dialog.result:
            success = product_manager.update_product(
                product_id=product_id,
                name=dialog.result["name"],
                category=dialog.result["category"],
                open_date=dialog.result["open_date"],
                period_months=dialog.result["period_months"]
            )
            if success:
                messagebox.showinfo("수정 완료", f"'{dialog.result['name']}' 제품 정보가 성공적으로 수정되었습니다.")
                self.load_product_table()
            else:
                messagebox.showerror("수정 실패", "제품 수정 중 오류가 발생했습니다.")

    def handle_delete(self):
        """선택된 제품 삭제 처리"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 오류", "삭제할 제품을 목록에서 먼저 클릭하여 선택해 주세요.")
            return

        values = self.tree.item(selected[0])["values"]
        product_id = int(values[0])
        product_name = values[1]

        confirm = messagebox.askyesno(
            "삭제 확인",
            f"정말로 '{product_name}' 제품을 삭제하시겠습니까?\n\n삭제된 정보는 CSV 파일에서도 영구적으로 제거됩니다."
        )
        if not confirm:
            return

        success = product_manager.delete_product(product_id)
        if success:
            messagebox.showinfo("삭제 완료", f"'{product_name}' 제품이 삭제되었습니다.")
            self.load_product_table()
        else:
            messagebox.showerror("삭제 실패", "제품 삭제 중 오류가 발생했습니다.")

    # ================= 2. 대시보드 화면 =================

    def render_dashboard_view(self):
        """대시보드 화면"""
        products = product_manager.get_all_products()

        # 요약 카드 그리드
        cards_frame = tk.Frame(self.content_frame, bg=COLOR_BG_SUB)
        cards_frame.pack(fill=tk.X, pady=(0, 20))

        # 카드 1: 전체 제품
        self._create_stat_card(cards_frame, "📦 전체 등록 제품", f"{len(products)}개", "기능 1에서 관리 중", COLOR_POINT_SKY)

        # 카드 2: 기간 임박 예정
        self._create_stat_card(cards_frame, "⚠️ 기간 임박 제품", "- 개", "기능 2/3 연계 예정", COLOR_WARNING_AMBER)

        # 카드 3: 기간 만료 예정
        self._create_stat_card(cards_frame, "🚨 기간 만료 제품", "- 개", "기능 2/3 연계 예정", COLOR_DANGER_RED)

        # 바로가기 안내 카드
        action_card = tk.Frame(self.content_frame, bg=COLOR_BG_WHITE, padx=25, pady=25, highlightthickness=1, highlightbackground=COLOR_BORDER)
        action_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            action_card,
            text="✨ LifeCheck 기본 기능 안내",
            font=("Malgun Gothic", 12, "bold"),
            bg=COLOR_BG_WHITE,
            fg=COLOR_DEEP_NAVY
        ).pack(anchor="w", pady=(0, 8))

        guide_text = (
            "• 현재 '전체 제품' 메뉴에서 생활용품의 신규 등록, 조회, 수정, 삭제가 모두 작동합니다.\n"
            "• 등록된 데이터는 'data/products.csv'에 안전하게 저장되어 프로그램을 종료해도 유지됩니다.\n"
            "• 팀원들이 기능 2(사용 기간 계산)와 기능 3(임박/만료 확인), 기능 4, 5를 연결할 수 있도록\n"
            "  화면별 구조와 사이드바 메뉴가 모두 설계되어 있습니다."
        )
        tk.Label(
            action_card,
            text=guide_text,
            font=("Malgun Gothic", 9),
            bg=COLOR_BG_WHITE,
            fg=COLOR_MUTED_GRAY,
            justify="left"
        ).pack(anchor="w", pady=(0, 20))

        btn_go_products = tk.Button(
            action_card,
            text="👉 전체 제품 관리로 이동하기",
            font=("Malgun Gothic", 10, "bold"),
            bg=COLOR_POINT_SKY,
            fg="#FFFFFF",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
            command=lambda: self.switch_view("전체 제품")
        )
        btn_go_products.pack(anchor="w")

    def _create_stat_card(self, parent, title, value, subtext, color):
        card = tk.Frame(
            parent,
            bg=COLOR_BG_WHITE,
            padx=20,
            pady=15,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER
        )
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(card, text=title, font=("Malgun Gothic", 9, "bold"), bg=COLOR_BG_WHITE, fg=COLOR_MUTED_GRAY).pack(anchor="w")
        tk.Label(card, text=value, font=("Malgun Gothic", 16, "bold"), bg=COLOR_BG_WHITE, fg=color).pack(anchor="w", pady=4)
        tk.Label(card, text=subtext, font=("Malgun Gothic", 8), bg=COLOR_BG_WHITE, fg=COLOR_MUTED_GRAY).pack(anchor="w")

    # ================= 3. 기능 2~5 플레이스홀더 화면 =================

    def render_placeholder_view(self, feature_title, description):
        """팀원들이 구현할 기능 2~5의 기본 UI 구조 및 연계 안내 프레임"""
        card = tk.Frame(
            self.content_frame,
            bg=COLOR_BG_WHITE,
            padx=35,
            pady=40,
            highlightthickness=1,
            highlightbackground=COLOR_BORDER
        )
        card.pack(fill=tk.BOTH, expand=True)

        icon_label = tk.Label(card, text="🛠️", font=("Segoe UI Emoji", 32), bg=COLOR_BG_WHITE)
        icon_label.pack(pady=(10, 10))

        tk.Label(
            card,
            text=feature_title,
            font=("Malgun Gothic", 13, "bold"),
            bg=COLOR_BG_WHITE,
            fg=COLOR_DEEP_NAVY
        ).pack(pady=(0, 8))

        tk.Label(
            card,
            text=description,
            font=("Malgun Gothic", 9),
            bg=COLOR_BG_WHITE,
            fg=COLOR_MUTED_GRAY,
            justify="center"
        ).pack(pady=(0, 20))

        info_box = tk.Frame(card, bg=COLOR_LIGHT_SKY, padx=20, pady=15)
        info_box.pack(fill=tk.X, padx=50)

        tk.Label(
            info_box,
            text="📌 팀원 연계 개발 안내",
            font=("Malgun Gothic", 9, "bold"),
            bg=COLOR_LIGHT_SKY,
            fg=COLOR_POINT_SKY
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            info_box,
            text="• 이 화면은 기본 레이아웃이 준비되어 있어, 담당 팀원이 해당 기능의 표나 설정 위젯을\n  손쉽게 추가하여 결합할 수 있도록 모듈화되어 있습니다.",
            font=("Malgun Gothic", 8),
            bg=COLOR_LIGHT_SKY,
            fg=COLOR_DEEP_NAVY,
            justify="left"
        ).pack(anchor="w")


def main():
    root = tk.Tk()
    app = LifeCheckUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
