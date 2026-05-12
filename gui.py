# gui.py
"""
Tkinter GUI for Gaijin Market Trade Automation.
Gaijin Market 取引自動化の Tkinter GUI。
Gaijin Market 交易自动化 Tkinter 图形界面。

Zero extra dependencies – uses only Python standard library + existing project modules.
追加依存ゼロ – Python 標準ライブラリ + 既存のプロジェクトモジュールのみ。
零额外依赖 – 仅使用 Python 标准库 + 现有项目模块。
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import os
from datetime import datetime

from playwright.sync_api import sync_playwright

from i18n import LanguageManager
import itemName
from core import (
    connect_browser,
    detect_language,
    fetch_records,
    format_tsv,
    copy_to_clipboard,
    get_default_date_range,
)


class GaijinMarketGUI:
    """Main GUI application window.  メインGUIアプリケーションウィンドウ。  主 GUI 应用程序窗口。"""

    # ------------------------------------------------------------------
    # GUI translation keys  (initialized after _lm is created)
    # GUI 翻訳キー  (_lm 作成後に初期化)
    # GUI 翻译键  (在 _lm 创建后初始化)
    # ------------------------------------------------------------------
    _T = {}

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gaijin Market Trade Automator")
        self.root.geometry("960x680")
        self.root.minsize(800, 500)

        self._lm = LanguageManager("zh_CN")
        self._load_gui_texts()

        # State
        # 状態
        # 状态
        self._records = []
        self._is_fetching = False
        self._chrome_connected = False
        self._result_queue = queue.Queue()

        self._build_ui()
        self._poll_queue()

    # ------------------------------------------------------------------
    # PUBLIC API – allow update after language change
    # 公開 API – 言語変更後の更新を許可
    # 公开 API – 允许语言变更后更新
    # ------------------------------------------------------------------
    def reload_language(self, lang: str):
        """Switch display language.  表示言語を切り替えます。  切换显示语言。"""
        self._lm = LanguageManager(lang)
        self._load_gui_texts()
        self._refresh_ui_texts()

    # ==================================================================
    # Internal helpers
    # 内部ヘルパー
    # 内部助手
    # ==================================================================
    def _t(self, key: str, *args) -> str:
        txt = self._T.get(key, key)
        if args:
            return txt % args
        return txt

    def _load_gui_texts(self):
        self._T = {
            # --- Window title ---
            "title": self._lm.t("gui.title", "Gaijin Market Trade Automator"),

            # --- Chrome status ---
            "chrome_status": self._lm.t("gui.chrome_status", "Chrome Status"),
            "connected": self._lm.t("gui.connected", "Connected"),
            "disconnected": self._lm.t("gui.disconnected", "Disconnected"),
            "checking": self._lm.t("gui.checking", "Checking..."),
            "page": self._lm.t("gui.page", "Page"),
            "lang_label": self._lm.t("gui.lang_label", "Site Language"),

            # --- Date section ---
            "date_section": self._lm.t("gui.date_section", "Date Range"),
            "start_date": self._lm.t("gui.start_date", "Start Date"),
            "end_date": self._lm.t("gui.end_date", "End Date (auto)"),

            # --- Action buttons ---
            "btn_fetch": self._lm.t("gui.btn_fetch", "Start Fetch"),
            "btn_stop": self._lm.t("gui.btn_stop", "Stop"),
            "btn_copy": self._lm.t("gui.btn_copy", "Copy TSV"),
            "btn_export": self._lm.t("gui.btn_export", "Export CSV"),
            "btn_clear": self._lm.t("gui.btn_clear", "Clear Results"),

            # --- Results ---
            "results": self._lm.t("gui.results", "Results"),
            "col_index": self._lm.t("gui.col_index", "#"),
            "col_type": self._lm.t("gui.col_type", "Type"),
            "col_name": self._lm.t("gui.col_name", "Name"),
            "col_date": self._lm.t("gui.col_date", "Date"),
            "col_action": self._lm.t("gui.col_action", "Buy/Sell"),
            "col_price": self._lm.t("gui.col_price", "Price"),
            "col_qty": self._lm.t("gui.col_qty", "Qty"),

            # --- Log section ---
            "log": self._lm.t("gui.log", "Log"),

            # --- Messages ---
            "msg_no_chrome": self._lm.t("gui.msg_no_chrome",
                                         "Chrome not detected (port 9222). Please run start_chrome.bat first."),
            "msg_no_page": self._lm.t("gui.msg_no_page",
                                       "Trading notifications page not found.\nOpen trade.gaijin.net → Notifications → View All."),
            "msg_no_records": self._lm.t("gui.msg_no_records", "No records found in the selected date range."),
            "msg_fetch_ok": self._lm.t("gui.msg_fetch_ok", "Fetch complete: %d records."),
            "msg_copied": self._lm.t("gui.msg_copied", "Copied %d records to clipboard."),
            "msg_exported": self._lm.t("gui.msg_exported", "Exported to %s"),
            "msg_error": self._lm.t("gui.msg_error", "Error"),
        }
        self.root.title(self._tm("title"))

    def _tm(self, key: str, *args):
        return self._t(key, *args)

    def _refresh_ui_texts(self):
        """Refresh all UI text elements after language change."""
        self.root.title(self._tm("title"))
        self._lbl_chrome_frame.config(text=self._tm("chrome_status"))
        self._update_chrome_status(force=True)
        self._lbl_date_frame.config(text=self._tm("date_section"))
        self._lbl_start.config(text=self._tm("start_date") + ":")
        self._lbl_end.config(text=self._tm("end_date") + ":")
        self._btn_fetch.config(text=self._tm("btn_fetch"))
        self._btn_copy.config(text=self._tm("btn_copy"))
        self._btn_export.config(text=self._tm("btn_export"))
        self._btn_clear.config(text=self._tm("btn_clear"))
        self._lbl_results_frame.config(text=self._tm("results"))
        self._update_results_label()
        self._lbl_log_frame.config(text=self._tm("log"))
        self._rebuild_tree_columns()

    def _update_chrome_status(self, force=False):
        connected = self._chrome_connected
        text = self._tm("connected") if connected else self._tm("disconnected")
        color = "green" if connected else "red"
        self._lbl_chrome_status.config(text=text, foreground=color)

    # ==================================================================
    # UI Build
    # UI 構築
    # UI 构建
    # ==================================================================
    def _build_ui(self):
        # ---- Top bar: language switch ----
        top_bar = ttk.Frame(self.root)
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Label(top_bar, text="🌐").pack(side=tk.LEFT, padx=(0, 5))
        self._btn_zh = ttk.Button(top_bar, text="中文", width=6,
                                  command=lambda: self._on_lang_switch("zh_CN"))
        self._btn_zh.pack(side=tk.LEFT, padx=2)

        self._btn_en = ttk.Button(top_bar, text="EN", width=6,
                                  command=lambda: self._on_lang_switch("en_US"))
        self._btn_en.pack(side=tk.LEFT, padx=2)

        # ---- Chrome status section ----
        self._lbl_chrome_frame = ttk.LabelFrame(self.root, text=self._tm("chrome_status"),
                                                padding=10)
        self._lbl_chrome_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        chrome_inner = ttk.Frame(self._lbl_chrome_frame)
        chrome_inner.pack(fill=tk.X)

        self._lbl_chrome_status = ttk.Label(chrome_inner, text=self._tm("disconnected"),
                                            foreground="red", font=("", 10, "bold"))
        self._lbl_chrome_status.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(chrome_inner, text=f"{self._tm('page')}:").pack(side=tk.LEFT)
        self._lbl_page = ttk.Label(chrome_inner, text="—", foreground="gray")
        self._lbl_page.pack(side=tk.LEFT, padx=(2, 20))

        ttk.Label(chrome_inner, text=f"{self._tm('lang_label')}:").pack(side=tk.LEFT)
        self._lbl_site_lang = ttk.Label(chrome_inner, text="—", foreground="gray")
        self._lbl_site_lang.pack(side=tk.LEFT, padx=(2, 10))

        # ---- Date section ----
        self._lbl_date_frame = ttk.LabelFrame(self.root, text=self._tm("date_section"),
                                              padding=10)
        self._lbl_date_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        date_inner = ttk.Frame(self._lbl_date_frame)
        date_inner.pack(fill=tk.X)

        self._lbl_start = ttk.Label(date_inner, text=self._tm("start_date") + ":")
        self._lbl_start.pack(side=tk.LEFT)

        self._var_start = tk.StringVar()
        _, _, default_start_str = get_default_date_range()
        self._entry_start = ttk.Entry(date_inner, textvariable=self._var_start, width=14)
        self._entry_start.pack(side=tk.LEFT, padx=(5, 20))
        self._var_start.set(default_start_str)

        self._lbl_end = ttk.Label(date_inner, text=self._tm("end_date") + ":")
        self._lbl_end.pack(side=tk.LEFT)

        self._var_end = tk.StringVar()
        self._entry_end = ttk.Entry(date_inner, textvariable=self._var_end, width=14,
                                    state="readonly")
        self._entry_end.pack(side=tk.LEFT, padx=(5, 20))
        self._update_end_date_display()

        ttk.Separator(date_inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y,
                                                           padx=(10, 10))

        self._btn_fetch = ttk.Button(date_inner, text=self._tm("btn_fetch"),
                                     command=self._on_fetch)
        self._btn_fetch.pack(side=tk.LEFT, padx=(0, 5))

        self._progress = ttk.Progressbar(date_inner, mode="indeterminate", length=180)
        self._progress.pack(side=tk.LEFT, padx=(5, 0))

        # ---- Results section ----
        self._lbl_results_frame = ttk.LabelFrame(self.root, text=self._tm("results"),
                                                 padding=10)
        self._lbl_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        self._lbl_results_count = ttk.Label(self._lbl_results_frame, text="", foreground="gray")
        self._lbl_results_count.pack(anchor=tk.W)

        # TreeView
        columns = ("index", "type", "name", "date", "action", "price", "qty")
        self._tree = ttk.Treeview(self._lbl_results_frame, columns=columns, show="headings",
                                  height=10)
        self._tree.heading("index", text=self._tm("col_index"))
        self._tree.heading("type", text=self._tm("col_type"))
        self._tree.heading("name", text=self._tm("col_name"))
        self._tree.heading("date", text=self._tm("col_date"))
        self._tree.heading("action", text=self._tm("col_action"))
        self._tree.heading("price", text=self._tm("col_price"))
        self._tree.heading("qty", text=self._tm("col_qty"))

        self._tree.column("index", width=40, anchor=tk.CENTER)
        self._tree.column("type", width=80)
        self._tree.column("name", width=240)
        self._tree.column("date", width=100, anchor=tk.CENTER)
        self._tree.column("action", width=80, anchor=tk.CENTER)
        self._tree.column("price", width=100, anchor=tk.E)
        self._tree.column("qty", width=60, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self._lbl_results_frame, orient=tk.VERTICAL,
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ---- Action buttons ----
        btn_frame = ttk.Frame(self._lbl_results_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        self._btn_copy = ttk.Button(btn_frame, text=self._tm("btn_copy"),
                                    command=self._on_copy)
        self._btn_copy.pack(side=tk.LEFT, padx=(0, 5))

        self._btn_export = ttk.Button(btn_frame, text=self._tm("btn_export"),
                                      command=self._on_export)
        self._btn_export.pack(side=tk.LEFT, padx=(0, 5))

        self._btn_clear = ttk.Button(btn_frame, text=self._tm("btn_clear"),
                                     command=self._on_clear)
        self._btn_clear.pack(side=tk.LEFT)

        # ---- Log section ----
        self._lbl_log_frame = ttk.LabelFrame(self.root, text=self._tm("log"), padding=10)
        self._lbl_log_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        self._log_text = tk.Text(self._lbl_log_frame, height=6, state=tk.DISABLED,
                                 wrap=tk.WORD, font=("Consolas", 9))
        log_scroll = ttk.Scrollbar(self._lbl_log_frame, orient=tk.VERTICAL,
                                   command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_scroll.set)

        self._log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _rebuild_tree_columns(self):
        """Re-set tree headings after language switch."""
        self._tree.heading("index", text=self._tm("col_index"))
        self._tree.heading("type", text=self._tm("col_type"))
        self._tree.heading("name", text=self._tm("col_name"))
        self._tree.heading("date", text=self._tm("col_date"))
        self._tree.heading("action", text=self._tm("col_action"))
        self._tree.heading("price", text=self._tm("col_price"))
        self._tree.heading("qty", text=self._tm("col_qty"))

    def _update_end_date_display(self):
        _, end_dt, _ = get_default_date_range()
        self._var_end.set(end_dt.strftime("%Y/%m/%d"))

    def _update_results_label(self):
        count = len(self._records)
        if count > 0:
            label_text = f"{self._tm('results')}: {count}"
        else:
            label_text = self._tm("results")
        self._lbl_results_count.config(text=label_text)

    # ==================================================================
    # Logging
    # ログ出力
    # 日志
    # ==================================================================
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        self._log_text.config(state=tk.NORMAL)
        self._log_text.insert(tk.END, line)
        self._log_text.see(tk.END)
        self._log_text.config(state=tk.DISABLED)

    def _log_poll(self, message: str):
        """Thread-safe log from worker thread.  worker スレッドからの安全なログ。"""
        self.root.after(0, self._log, message)

    # ==================================================================
    # Language switch
    # 言語切り替え
    # 语言切换
    # ==================================================================
    def _on_lang_switch(self, lang: str):
        # Update LM and itemName
        itemName.reload_lang(lang)
        self.reload_language(lang)

        # Highlight active button
        if lang == "zh_CN":
            self._btn_zh.state(["pressed"])
            self._btn_en.state(["!pressed"])
        else:
            self._btn_en.state(["pressed"])
            self._btn_zh.state(["!pressed"])

        # Sync site lang label if connected
        if self._chrome_connected:
            self._lbl_site_lang.config(text="中文" if lang == "zh_CN" else "English",
                                       foreground="blue")

        self._log(f"Language switched to {lang}  /  言語切替: {lang}  /  语言切换至 {lang}")

    # ==================================================================
    # Fetch worker (runs in background thread)
    # 取得ワーカー（バックグラウンドスレッドで実行）
    # 抓取工作线程（在后台线程中运行）
    # ==================================================================
    def _fetch_worker(self):
        try:
            self._log_poll("Connecting to Chrome...")
            with sync_playwright() as p:
                result = connect_browser(p)
                if result is None:
                    self._result_queue.put(("error", self._tm("msg_no_chrome")))
                    return

                browser, context, target_page = result
                self._log_poll(f"Connected to: {target_page.title()}")

                # Detect language
                detected_lang = detect_language(target_page)
                if detected_lang is None:
                    self._result_queue.put(("error",
                        "Could not detect page language. Ensure Notifications page is loaded."))
                    return

                lm = LanguageManager(detected_lang)
                self._result_queue.put(("lang", detected_lang, lm.t("prompt.lang_name")))

                # Parse date
                start_str = self._var_start.get().strip()
                try:
                    start_date = datetime.strptime(start_str, "%Y/%m/%d")
                except ValueError:
                    self._result_queue.put(("error",
                        f"Invalid date format: '{start_str}'. Use YYYY/M/D."))
                    return

                _, end_date, _ = get_default_date_range()

                self._log_poll(f"Fetching records from {start_date.strftime('%Y/%m/%d')} "
                               f"to {end_date.strftime('%Y/%m/%d')}...")
                self._log_poll(f"Site language: {detected_lang}")

                # Sync itemName for correct CSV
                itemName.reload_lang(detected_lang)

                records = fetch_records(target_page, start_date, end_date, lm)
                tsv = format_tsv(records) if records else ""

                self._result_queue.put(("ok", records, tsv))

        except Exception as e:
            self._result_queue.put(("error", str(e)))

    def _on_fetch(self):
        if self._is_fetching:
            return

        start_str = self._var_start.get().strip()
        if not start_str:
            messagebox.showwarning(self._tm("btn_fetch"), "Please enter a start date.")
            return

        self._is_fetching = True
        self._btn_fetch.config(state=tk.DISABLED, text=self._tm("btn_fetch") + "...")
        self._progress.start(10)
        self._log("Starting fetch...  /  抓取を開始...  /  开始抓取...")

        thread = threading.Thread(target=self._fetch_worker, daemon=True)
        thread.start()

    # ==================================================================
    # Queue polling (main thread)
    # キューポーリング（メインスレッド）
    # 队列轮询（主线程）
    # ==================================================================
    def _poll_queue(self):
        try:
            while True:
                msg = self._result_queue.get_nowait()
                self._handle_result(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _handle_result(self, msg):
        kind = msg[0]

        if kind == "error":
            self._is_fetching = False
            self._progress.stop()
            self._btn_fetch.config(state=tk.NORMAL, text=self._tm("btn_fetch"))
            err_text = msg[1]
            self._log(f"ERROR: {err_text}")
            messagebox.showerror(self._tm("msg_error"), err_text)

        elif kind == "lang":
            detected_lang = msg[1]
            lang_name = msg[2]
            # Update site language display
            self.root.after(0, lambda: self._lbl_site_lang.config(
                text=lang_name, foreground="blue"))
            self._chrome_connected = True
            self._update_chrome_status()
            self._lbl_page.config(text="trade.gaijin.net/history", foreground="black")

        elif kind == "ok":
            self._is_fetching = False
            self._progress.stop()
            self._btn_fetch.config(state=tk.NORMAL, text=self._tm("btn_fetch"))

            records = msg[1]
            tsv = msg[2]

            self._records = records
            self._cached_tsv = tsv if records else ""
            self._populate_tree()

            if records:
                self._log(self._tm("msg_fetch_ok") % len(records))
            else:
                self._log(self._tm("msg_no_records"))
                messagebox.showinfo(self._tm("results"), self._tm("msg_no_records"))

    # ==================================================================
    # TreeView population
    # TreeView へのデータ投入
    # TreeView 数据填充
    # ==================================================================
    def _populate_tree(self):
        """Fill TreeView from self._records."""
        for row in self._tree.get_children():
            self._tree.delete(row)

        for i, rec in enumerate(self._records):
            # Determine action (Buy / Sell)
            if rec['bP'] != "0" and float(rec['bP']) > 0:
                action = "Buy"
                price = rec['bP']
                qty = rec['bQ']
            else:
                action = "Sell"
                price = rec['sP']
                qty = rec['sQ']

            # Truncate name if too long
            name = rec['name']
            if len(name) > 40:
                name = name[:38] + "…"

            self._tree.insert("", tk.END, values=(
                i + 1,
                rec['type'],
                name,
                rec['dateOnly'],
                action,
                price,
                qty,
            ))

        self._update_results_label()

    # ==================================================================
    # Button actions
    # ボタンアクション
    # 按钮操作
    # ==================================================================
    def _on_copy(self):
        if not hasattr(self, '_cached_tsv') or not self._cached_tsv:
            messagebox.showinfo(self._tm("btn_copy"), self._tm("msg_no_records"))
            return
        copy_to_clipboard(self._cached_tsv)
        self._log(self._tm("msg_copied") % len(self._records))

    def _on_export(self):
        if not self._records:
            messagebox.showinfo(self._tm("btn_export"), self._tm("msg_no_records"))
            return

        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"gaiin_market_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not filepath:
            return

        import csv
        try:
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Index", "Type", "Name", "Date", "Action", "Price", "Qty", "OrderID"])
                for i, rec in enumerate(self._records):
                    writer.writerow([
                        i + 1,
                        rec['type'],
                        rec['name'],
                        rec['dateOnly'],
                        "Buy" if (rec['bP'] != "0" and float(rec['bP']) > 0) else "Sell",
                        rec['bP'] if (rec['bP'] != "0" and float(rec['bP']) > 0) else rec['sP'],
                        rec['bQ'] if (rec['bP'] != "0" and float(rec['bP']) > 0) else rec['sQ'],
                        rec['oid'],
                    ])
            self._log(self._tm("msg_exported") % filepath)
        except Exception as e:
            messagebox.showerror(self._tm("msg_error"), str(e))

    def _on_clear(self):
        self._records = []
        if hasattr(self, '_cached_tsv'):
            del self._cached_tsv
        for row in self._tree.get_children():
            self._tree.delete(row)
        self._update_results_label()
        self._log("Results cleared.  /  結果をクリアしました。  /  已清空结果。")

    # ==================================================================
    # Run
    # 実行
    # 运行
    # ==================================================================
    def run(self):
        self._log("GUI started.  /  GUI を起動しました。  /  GUI 已启动。")
        self._log("Tip: Run start_chrome.bat first, then log in and open Notifications page.")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        if self._is_fetching:
            if not messagebox.askokcancel("Quit", "A fetch is in progress. Really quit?\n抓取还在进行中，确定退出吗？"):
                return
        self.root.destroy()


if __name__ == "__main__":
    app = GaijinMarketGUI()
    app.run()