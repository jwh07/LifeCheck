"""팀원 3: 기존 CSV 호환성과 추가 기능의 사용자 흐름을 검증합니다.

실행: python -m unittest discover -s tests -v
GUI 테스트는 tkinter를 실행할 수 없는 환경에서만 건너뜁니다.
모든 저장 작업은 테스트 폴더의 임시 디렉터리에서 수행합니다.
"""

import copy
import csv
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import calculator
import storage


def product(item_id=1, name="선크림", category="화장품", remaining=9,
            base_date=date(2026, 11, 16), completed=False):
    return {
        "id": item_id, "name": name, "category": category,
        "open_date": "2020-01-01", "period_months": 6,
        "end_date": (base_date + timedelta(days=remaining)).isoformat(),
        "usage_status": "사용완료" if completed else "사용중",
        "completed_date": "2020-06-01" if completed else "",
    }


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.base_date = date(2026, 11, 16)
        self.items = [
            product(1, "토너 A", remaining=9),
            product(2, "토너 B", remaining=-3),
            product(3, "샴푸", "세정용품", remaining=90),
            product(4, "토너 완료", remaining=-30, completed=True),
        ]

    def test_month_end_leap_year_and_year_change(self):
        for opened, months, expected in [
            ("2026-01-31", 1, "2026-02-28"),
            ("2024-01-31", 1, "2024-02-29"),
            ("2024-02-29", 12, "2025-02-28"),
            ("2026-12-31", 2, "2027-02-28"),
        ]:
            with self.subTest(opened=opened, months=months):
                self.assertEqual(calculator.calculate_end_date(opened, months), expected)

    def test_invalid_dates_and_periods(self):
        for value in ["2026-02-30", "20261116", "2026-1-1", "", None]:
            with self.subTest(value=value):
                self.assertFalse(calculator.validate_date_format(value))
        for months in [0, -1, "6", 1.5]:
            with self.subTest(months=months), self.assertRaises(ValueError):
                calculator.calculate_end_date("2026-11-16", months)

    def test_remaining_days_and_default_status_are_backward_compatible(self):
        self.assertEqual(calculator.calculate_remaining_days("2026-11-25", self.base_date), 9)
        self.assertEqual(calculator.get_item_status(30), "기간임박")
        self.assertEqual(calculator.get_item_status(31), "사용가능")

    def test_each_custom_threshold_boundary(self):
        for threshold in (7, 14, 30):
            for days, expected in [(-1, "기간만료"), (0, "기간임박"),
                                   (threshold, "기간임박"), (threshold + 1, "사용가능")]:
                with self.subTest(threshold=threshold, days=days):
                    self.assertEqual(calculator.get_item_status(days, threshold), expected)

    def test_combined_name_category_status_and_sort(self):
        result = calculator.filter_items(
            self.items, query="  토너  ", category="화장품", status="기간임박",
            sort_by_remaining=True, base_date=self.base_date)
        self.assertEqual([item["id"] for item in result], [1])
        result = calculator.filter_items(self.items, query="a", base_date=self.base_date)
        self.assertEqual([item["id"] for item in result], [1])

    def test_empty_search_result(self):
        self.assertEqual(calculator.filter_items(self.items, query="없는 제품"), [])

    def test_remaining_sort_includes_expired_first(self):
        result = calculator.filter_items(self.items, sort_by_remaining=True, base_date=self.base_date)
        self.assertEqual([item["id"] for item in result], [2, 1, 3])

    def test_history_ignores_active_status_filter_and_keeps_search(self):
        result = calculator.filter_items(
            self.items, history=True, status="사용가능", query="완료", category="화장품")
        self.assertEqual([item["id"] for item in result], [4])
        self.assertEqual(result[0]["status"], "사용완료")
        self.assertIsNone(result[0]["remaining_days"])

    def test_history_newest_first(self):
        other = product(5, completed=True)
        other["completed_date"] = "2020-07-01"
        result = calculator.filter_items(self.items + [other], history=True)
        self.assertEqual([item["id"] for item in result], [5, 4])

    def test_alerts_exclude_completed_and_follow_setting(self):
        for threshold, expected in [(7, [2]), (14, [2, 1]), (30, [2, 1])]:
            with self.subTest(threshold=threshold):
                result = calculator.get_alert_items(self.items, threshold, self.base_date)
                self.assertEqual([item["id"] for item in result], expected)

    def test_invalid_date_stays_visible_last_and_never_alerts(self):
        damaged = product(5)
        damaged["end_date"] = "invalid"
        items = self.items + [damaged]
        result = calculator.filter_items(items, sort_by_remaining=True, base_date=self.base_date)
        self.assertEqual(result[-1]["status"], "계산오류")
        self.assertEqual(result[-1]["id"], 5)
        self.assertNotIn(5, [item["id"] for item in calculator.get_alert_items(items)])

    def test_queries_do_not_mutate_original_items(self):
        original = copy.deepcopy(self.items)
        calculator.filter_items(self.items, sort_by_remaining=True)
        calculator.filter_items(self.items, history=True)
        calculator.get_alert_items(self.items)
        self.assertEqual(self.items, original)


class StorageFixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="lifecheck-test-", dir=Path(__file__).parent)
        self.addCleanup(temp.cleanup)
        self.data_dir = Path(temp.name)
        self.csv_path = self.data_dir / "items.csv"
        self.settings_path = self.data_dir / "settings.json"
        for name, value in [
            ("DATA_DIR", str(self.data_dir)), ("CSV_FILE_PATH", str(self.csv_path)),
            ("SETTINGS_FILE_PATH", str(self.settings_path)),
        ]:
            mock = patch.object(storage, name, value)
            mock.start()
            self.addCleanup(mock.stop)

    def write_legacy_csv(self):
        with self.csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(storage.CSV_HEADERS[:6])
            writer.writerow([1, "기존 선크림", "화장품", "2020-01-01", 6, "2020-07-01"])

    def add_product(self):
        return storage.add_item("선크림", "화장품", "2020-01-01", 6, "2020-07-01")


class StorageTests(StorageFixture):
    def test_legacy_csv_read_does_not_rewrite_file(self):
        self.write_legacy_csv()
        original = self.csv_path.read_bytes()
        items = storage.load_items()
        self.assertEqual(items[0]["usage_status"], "사용중")
        self.assertEqual(items[0]["completed_date"], "")
        self.assertEqual(self.csv_path.read_bytes(), original)

    def test_legacy_csv_migrates_on_write_without_losing_products(self):
        self.write_legacy_csv()
        new = self.add_product()
        items = storage.load_items()
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["name"], "기존 선크림")
        self.assertEqual(new["id"], 2)
        self.assertTrue(self.csv_path.read_bytes().startswith(b"\xef\xbb\xbf"))
        with self.csv_path.open(encoding="utf-8-sig") as f:
            self.assertEqual(next(csv.reader(f)), storage.CSV_HEADERS)

    def test_existing_create_read_update_delete(self):
        item = self.add_product()
        self.assertEqual(storage.load_items(), [item])
        self.assertTrue(storage.update_item(item["id"], "수정 토너", "기타", "2020-02-01", 3, "2020-05-01"))
        self.assertEqual(storage.load_items()[0]["name"], "수정 토너")
        self.assertTrue(storage.delete_item(item["id"]))
        self.assertEqual(storage.load_items(), [])
        self.assertFalse(storage.delete_item(item["id"]))

    def test_complete_and_reregister_keep_original_history(self):
        item = self.add_product()
        self.assertTrue(storage.complete_item(item["id"], "2020-06-01"))
        history = storage.load_items()[0]
        new = storage.add_item(history["name"], history["category"], "2020-06-02", 6, "2020-12-02")
        self.assertNotEqual(item["id"], new["id"])
        self.assertEqual(storage.load_items()[0], history)
        self.assertEqual(new["usage_status"], "사용중")
        self.assertEqual(new["completed_date"], "")
        self.assertEqual(history["completed_date"], "2020-06-01")

    def test_duplicate_completion_and_history_update_do_not_change_history(self):
        item = self.add_product()
        storage.complete_item(item["id"], "2020-06-01")
        original = self.csv_path.read_bytes()
        self.assertFalse(storage.complete_item(item["id"], "2020-06-02"))
        self.assertFalse(storage.complete_item(999, "2020-06-02"))
        self.assertFalse(storage.update_item(item["id"], "덮어쓰기", "기타", "2020-02-01", 1, "2020-03-01"))
        self.assertEqual(self.csv_path.read_bytes(), original)

    def test_invalid_completion_dates_do_not_write(self):
        item = self.add_product()
        original = self.csv_path.read_bytes()
        for value in ["2019-12-31", "2020-02-30", "20200601", "", (date.today() + timedelta(days=1)).isoformat()]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                storage.complete_item(item["id"], value)
            self.assertEqual(self.csv_path.read_bytes(), original)

    def test_csv_write_failure_keeps_original_file_and_cleans_temp_file(self):
        self.add_product()
        original = self.csv_path.read_bytes()
        with patch.object(storage.os, "replace", side_effect=PermissionError("file in use")):
            with self.assertRaises(PermissionError):
                self.add_product()
        self.assertEqual(self.csv_path.read_bytes(), original)
        self.assertEqual(list(self.data_dir.iterdir()), [self.csv_path])

    def test_settings_persist_all_supported_thresholds(self):
        self.assertEqual(storage.load_settings(), {"urgent_days": 30})
        self.assertFalse(self.settings_path.exists())
        for days in (7, 14, 30):
            storage.save_settings(days)
            self.assertEqual(storage.load_settings(), {"urgent_days": days})

    def test_corrupt_and_invalid_settings_fall_back_to_default(self):
        for text in ['{broken', 'null', '[]', '{}', '{"urgent_days":"7"}', '{"urgent_days":0}']:
            with self.subTest(text=text):
                self.settings_path.write_text(text, encoding="utf-8")
                self.assertEqual(storage.load_settings(), {"urgent_days": 30})

    def test_invalid_setting_and_failed_save_keep_previous_setting(self):
        storage.save_settings(14)
        for value in [0, 1, -7, 31, "7", True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                storage.save_settings(value)
        with patch.object(storage.os, "replace", side_effect=PermissionError("file in use")):
            with self.assertRaises(PermissionError):
                storage.save_settings(7)
        self.assertEqual(storage.load_settings(), {"urgent_days": 14})


class GuiTests(StorageFixture):
    """실제 Tk 위젯을 사용하며 안내 대화상자만 대체합니다."""

    def setUp(self):
        super().setUp()
        try:
            import tkinter as tk
            import main
        except ImportError as exc:
            self.skipTest(f"tkinter 없음: {exc}")
        self.main = main
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk GUI 실행 불가: {exc}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        for name in ["showinfo", "showwarning", "showerror", "askyesno"]:
            mock = patch.object(main.messagebox, name, return_value=True)
            setattr(self, name, mock.start())
            self.addCleanup(mock.stop)
        mock = patch.object(main.simpledialog, "askstring", return_value="2020-06-01")
        self.ask_date = mock.start()
        self.addCleanup(mock.stop)
        storage.save_items([
            product(1, "토너 A", remaining=9, base_date=date.today()),
            product(2, "샴푸", "세정용품", remaining=-1, base_date=date.today()),
            product(3, "완료 토너", completed=True),
        ])
        self.app = main.LifeCheckApp(self.root)
        self.root.update()
        self.showerror.assert_not_called()
        self.showinfo.reset_mock()

    def visible_ids(self):
        return [int(self.app.tree.item(row, "values")[0]) for row in self.app.tree.get_children()]

    def select(self, item_id):
        row = next(row for row in self.app.tree.get_children()
                   if int(self.app.tree.item(row, "values")[0]) == item_id)
        self.app.tree.selection_set(row)
        self.app.on_tree_select(None)

    def test_gui_search_custom_category_status_and_sort(self):
        self.app.sort_var.set("남은 기간순")
        self.app.refresh_item_list()
        self.assertEqual(self.visible_ids(), [2, 1])
        self.app.category_filter_var.set("화장품")
        self.app.filter_var.set("기간임박")
        self.app.search_var.set("토너")
        self.assertEqual(self.visible_ids(), [1])
        self.assertIn("1개", self.app.list_count_label.cget("text"))

    def test_gui_filter_change_clears_selection(self):
        self.select(1)
        self.assertEqual(self.app.selected_item_id, 1)
        self.app.search_var.set("없는 제품")
        self.assertIsNone(self.app.selected_item_id)
        self.assertEqual(str(self.app.btn_update.cget("state")), "disabled")
        self.assertEqual(str(self.app.btn_delete.cget("state")), "disabled")
        self.app.handle_delete()
        self.assertEqual(len(storage.load_items()), 3)

    def test_gui_complete_history_reregister_and_original_crud(self):
        self.select(1)
        self.app.handle_complete()
        self.assertEqual(self.visible_ids(), [2])
        self.app.view_var.set("사용 완료 이력")
        self.app.refresh_item_list()
        self.assertEqual(set(self.visible_ids()), {1, 3})
        self.assertIn("completed_date", self.app.tree.cget("displaycolumns"))
        self.select(1)
        original = storage.load_items()[0]
        self.assertEqual(str(self.app.btn_update.cget("state")), "disabled")
        self.app.handle_register_again()
        self.assertEqual(self.app.entry_name.get(), "토너 A")
        self.assertEqual(self.app.entry_open_date.get(), date.today().isoformat())
        self.assertIsNone(self.app.selected_item_id)
        self.app.handle_add()
        self.assertEqual(storage.load_items()[0], original)
        self.assertEqual(self.visible_ids(), [2, 4])
        self.select(4)
        self.app.entry_name.delete(0, "end")
        self.app.entry_name.insert(0, "새 토너")
        self.app.handle_update()
        self.assertEqual(storage.load_items()[-1]["name"], "새 토너")
        self.select(4)
        self.app.handle_delete()
        self.assertEqual(len(storage.load_items()), 3)
        self.showerror.assert_not_called()

    def test_gui_completion_cancel_and_invalid_date(self):
        self.select(1)
        for value in [None, "잘못된 날짜", "2019-01-01"]:
            self.ask_date.return_value = value
            self.app.handle_complete()
            self.assertEqual(storage.load_items()[0]["usage_status"], "사용중")

    def test_gui_threshold_updates_display_and_setting(self):
        self.app.filter_var.set("기간임박")
        self.app.urgent_days_var.set("7")
        self.app.handle_urgent_days_change()
        self.assertEqual(self.visible_ids(), [])
        self.assertEqual(storage.load_settings(), {"urgent_days": 7})
        self.app.urgent_days_var.set("14")
        self.app.handle_urgent_days_change()
        self.assertEqual(self.visible_ids(), [1])

    def test_gui_threshold_save_error_restores_previous_choice(self):
        self.app.urgent_days_var.set("7")
        with patch.object(storage, "save_settings", side_effect=PermissionError("file in use")):
            self.app.handle_urgent_days_change()
        self.assertEqual(self.app.urgent_days_var.get(), "30")
        self.assertEqual(self.app.urgent_days, 30)
        self.showerror.assert_called_once()

    def test_gui_startup_alert_uses_all_active_products_not_search(self):
        self.app.search_var.set("없는 제품")
        self.app.show_startup_alert()
        text = self.showinfo.call_args.args[1]
        self.assertIn("토너 A", text)
        self.assertIn("샴푸", text)
        self.assertNotIn("완료 토너", text)

    def test_gui_startup_reads_persisted_settings(self):
        storage.save_settings(7)
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            app = self.main.LifeCheckApp(root)
            root.update()
            self.assertEqual(app.urgent_days, 7)
            self.assertEqual(app.urgent_days_var.get(), "7")
        finally:
            root.destroy()

    def test_gui_date_rollover_refreshes_current_date(self):
        self.app.current_date = date.today() - timedelta(days=1)
        self.app.check_date_change()
        self.assertEqual(self.app.current_date, date.today())
        self.assertIn(date.today().strftime("%Y년 %m월 %d일"), self.app.today_label.cget("text"))

    def test_gui_controls_fit_default_and_minimum_window(self):
        # 투명 창으로 실제 배치를 계산하되 사용자 화면을 가리지 않습니다.
        self.root.attributes("-alpha", 0)
        self.root.deiconify()
        for width, height in [(1160, 720), (980, 660)]:
            with self.subTest(width=width, height=height):
                self.root.geometry(f"{width}x{height}")
                self.root.update()
                for parent in [self.app.sort_combo.master, self.app.category_filter_combo.master]:
                    for widget in parent.winfo_children():
                        self.assertTrue(widget.winfo_ismapped())
                        self.assertLessEqual(widget.winfo_x() + widget.winfo_width(), parent.winfo_width())
                for button in [self.app.btn_complete, self.app.btn_register_again]:
                    self.assertGreaterEqual(button.winfo_width(), button.winfo_reqwidth())
                self.assertGreater(self.app.tree.winfo_height(), 100)
        self.root.withdraw()


if __name__ == "__main__":
    unittest.main()
