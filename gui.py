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
from version import VERSION
import itemName
from core import (
    connect_browser,
    detect_language,
    fetch_records,
    format_tsv,
    copy_to_clipboard,
    get_default_date_range,
    launch_chrome,
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
            "pending_detect": self._lm.t("gui.pending_detect", "Pending"),
            "checking": self._lm.t("gui.checking", "Checking..."),
            "page": self._lm.t("gui.page", "Page"),
            "lang_label": self._lm.t("gui.lang_label", "Site Language"),

            # --- Date section ---
            "date_section": self._lm.t("gui.date_section", "Date Range"),
            "start_date": self._lm.t("gui.start_date", "Start Date"),
            "end_date": self._lm.t("gui.end_date", "End Date (auto)"),

            # --- Action buttons ---
            "btn_launch_chrome": self._lm.t("gui.btn_launch_chrome", "Launch Chrome"),
            "btn_fetch": self._lm.t("gui.btn_fetch", "Start Fetch"),
            "btn_stop": self._lm.t("gui.btn_stop", "Stop"),
            "btn_copy": self._lm.t("gui.btn_copy", "Copy TSV"),
            "btn_export": self._lm.t("gui.btn_export", "Export CSV"),
            "btn_clear": self._lm.t("gui.btn_clear", "Clear Results"),

            # --- Results column headers ---
            "results": self._lm.t("gui.results", "Results"),
            "col_type": self._lm.t("gui.col_type", "Type"),
            "col_name": self._lm.t("gui.col_name", "Item Name"),
            "col_date": self._lm.t("gui.col_date", "Date"),
            "col_purch_price": self._lm.t("gui.col_purch_price", "Purch. Price"),
            "col_purch_qty": self._lm.t("gui.col_purch_qty", "Purch. Qty"),
            "col_purch_total": self._lm.t("gui.col_purch_total", "Total Purch."),
            "col_sale_price": self._lm.t("gui.col_sale_price", "Sale Price"),
            "col_sale_qty": self._lm.t("gui.col_sale_qty", "Sale Qty"),
            "col_sale_total": self._lm.t("gui.col_sale_total", "Total Sales"),
            "col_net": self._lm.t("gui.col_net", "Net Received"),
            "col_backup": self._lm.t("gui.col_backup", "Static Backup"),
            "col_note1": self._lm.t("gui.col_note1", "Note 1"),
            "col_note2": self._lm.t("gui.col_note2", "Note 2"),
            "col_oid": self._lm.t("gui.col_oid", "Order No."),

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
        self.root.title(f"{self._tm("title")} v{VERSION}")

    def _tm(self, key: str, *args):
        return self._t(key, *args)

    def _refresh_ui_texts(self):
        """Refresh all UI text elements after language change."""
        self.root.title(f"{self._tm("title")} v{VERSION}")
        self._lbl_chrome_frame.config(text=self._tm("chrome_status"))
        self._update_chrome_status(force=True)
        self._lbl_date_frame.config(text=self._tm("date_section"))
        self._lbl_start.config(text=self._tm("start_date") + ":")
        self._lbl_end.config(text=self._tm("end_date") + ":")
        self._btn_launch.config(text=self._tm("btn_launch_chrome"))
        self._btn_fetch.config(text=self._tm("btn_fetch"))
        self._btn_copy.config(text=self._tm("btn_copy"))
        self._btn_export.config(text=self._tm("btn_export"))
        self._btn_clear.config(text=self._tm("btn_clear"))
        self._lbl_results_frame.config(text=self._tm("results"))
        self._update_results_label()
        self._lbl_log_frame.config(text=self._tm("log"))
        self._rebuild_tree_columns()

    def _update_chrome_status(self, force=False):
        if self._chrome_connected:
            text, color = self._tm("connected"), "green"
        elif self._is_fetching:
            text, color = self._tm("checking"), "orange"
        else:
            text, color = self._tm("pending_detect"), "gray"
        self._lbl_chrome_status.config(text=text, foreground=color)

    # ==================================================================
    # UI Build
    # UI 構築
    # UI 构建
    # ==================================================================
    def _build_ui(self):
        # ---- Top bar: launch chrome + language switch ----
        top_bar = ttk.Frame(self.root)
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 0))

        self._btn_launch = ttk.Button(top_bar, text=self._tm("btn_launch_chrome"),
                                      command=self._on_launch_chrome)
        self._btn_launch.pack(side=tk.LEFT, padx=(0, 15))

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

        self._lbl_chrome_status = ttk.Label(chrome_inner, text=self._tm("pending_detect"),
                                            foreground="gray", font=("", 10, "bold"))
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
        self._btn_fetch.pack(side=tk.LEFT, padx=(10, 5))

        self._progress = ttk.Progressbar(date_inner, mode="indeterminate", length=180)
        self._progress.pack(side=tk.LEFT, padx=(5, 0))

        # ---- Results section ----
        self._lbl_results_frame = ttk.LabelFrame(self.root, text=self._tm("results"),
                                                 padding=10)
        self._lbl_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        # ---- Action buttons (horizontal, above results count) ----
        btn_frame = ttk.Frame(self._lbl_results_frame)
        btn_frame.pack(anchor=tk.W, pady=(0, 5))

        self._btn_copy = ttk.Button(btn_frame, text=self._tm("btn_copy"),
                                    command=self._on_copy)
        self._btn_copy.pack(side=tk.LEFT, padx=(0, 8))

        self._btn_export = ttk.Button(btn_frame, text=self._tm("btn_export"),
                                      command=self._on_export)
        self._btn_export.pack(side=tk.LEFT, padx=(0, 8))

        self._btn_clear = ttk.Button(btn_frame, text=self._tm("btn_clear"),
                                     command=self._on_clear)
        self._btn_clear.pack(side=tk.LEFT)

        self._lbl_results_count = ttk.Label(self._lbl_results_frame, text="", foreground="gray")
        self._lbl_results_count.pack(anchor=tk.W)

        # TreeView — 14 columns matching TSV/Excel format
        # TreeView — TSV/Excel フォーマットに対応する 14 列
        # TreeView — 14 列对齐 TSV/Excel 格式
        columns = ("type", "name", "date",
                   "bP", "bQ", "purch_total",
                   "sP", "sQ", "sale_total",
                   "net", "backup", "note1", "note2", "oid")
        self._tree = ttk.Treeview(self._lbl_results_frame, columns=columns, show="headings",
                                  height=10)
        self._tree.heading("type", text=self._tm("col_type"))
        self._tree.heading("name", text=self._tm("col_name"))
        self._tree.heading("date", text=self._tm("col_date"))
        self._tree.heading("bP", text=self._tm("col_purch_price"))
        self._tree.heading("bQ", text=self._tm("col_purch_qty"))
        self._tree.heading("purch_total", text=self._tm("col_purch_total"))
        self._tree.heading("sP", text=self._tm("col_sale_price"))
        self._tree.heading("sQ", text=self._tm("col_sale_qty"))
        self._tree.heading("sale_total", text=self._tm("col_sale_total"))
        self._tree.heading("net", text=self._tm("col_net"))
        self._tree.heading("backup", text=self._tm("col_backup"))
        self._tree.heading("note1", text=self._tm("col_note1"))
        self._tree.heading("note2", text=self._tm("col_note2"))
        self._tree.heading("oid", text=self._tm("col_oid"))

        self._tree.column("type", width=70)
        self._tree.column("name", width=220)
        self._tree.column("date", width=90, anchor=tk.CENTER)
        self._tree.column("bP", width=80, anchor=tk.E)
        self._tree.column("bQ", width=60, anchor=tk.CENTER)
        self._tree.column("purch_total", width=80, anchor=tk.E)
        self._tree.column("sP", width=80, anchor=tk.E)
        self._tree.column("sQ", width=60, anchor=tk.CENTER)
        self._tree.column("sale_total", width=80, anchor=tk.E)
        self._tree.column("net", width=90, anchor=tk.E)
        self._tree.column("backup", width=90, anchor=tk.E)
        self._tree.column("note1", width=70)
        self._tree.column("note2", width=70)
        self._tree.column("oid", width=110)

        scrollbar = ttk.Scrollbar(self._lbl_results_frame, orient=tk.VERTICAL,
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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
        """Re-set tree headings after language switch.
        言語切替後に TreeView の見出しを再設定します。
        语言切换后重新设置 TreeView 列标题。"""
        self._tree.heading("type", text=self._tm("col_type"))
        self._tree.heading("name", text=self._tm("col_name"))
        self._tree.heading("date", text=self._tm("col_date"))
        self._tree.heading("bP", text=self._tm("col_purch_price"))
        self._tree.heading("bQ", text=self._tm("col_purch_qty"))
        self._tree.heading("purch_total", text=self._tm("col_purch_total"))
        self._tree.heading("sP", text=self._tm("col_sale_price"))
        self._tree.heading("sQ", text=self._tm("col_sale_qty"))
        self._tree.heading("sale_total", text=self._tm("col_sale_total"))
        self._tree.heading("net", text=self._tm("col_net"))
        self._tree.heading("backup", text=self._tm("col_backup"))
        self._tree.heading("note1", text=self._tm("col_note1"))
        self._tree.heading("note2", text=self._tm("col_note2"))
        self._tree.heading("oid", text=self._tm("col_oid"))

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
    # Launch Chrome
    # Chrome の起動
    # 启动 Chrome
    # ==================================================================
    def _on_launch_chrome(self):
        """Launch Chrome via core.launch_chrome()."""
        # Determine project root:
        #   - PyInstaller bundle: exe 所在目录
        #     打包后: exe 所在目录
        #   - Normal Python:      __file__ 所在目录
        #     通常実行: __file__ 所在目录
        import sys as _sys2
        if getattr(_sys2, 'frozen', False):
            project_root = os.path.dirname(os.path.abspath(_sys2.executable))
        else:
            project_root = os.path.dirname(os.path.abspath(__file__))
        ok, msg = launch_chrome(project_root)
        if ok:
            self._log(msg)
        else:
            messagebox.showerror(self._tm("msg_error"), msg)

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
                ok, data = connect_browser(p)
                if not ok:
                    err_key = "msg_no_chrome" if data == "no_cdp" else "msg_no_page"
                    self._result_queue.put(("error", self._tm(err_key)))
                    return

                browser, context, target_page = data
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
        """Fill TreeView from self._records with full 14-column TSV layout.
        self._records から 14 列の TSV レイアウトで TreeView を埋めます。
        使用完整 14 列 TSV 布局填充 TreeView。"""
        for row in self._tree.get_children():
            self._tree.delete(row)

        for rec in self._records:
            # Truncate name if too long
            name = rec['name']
            if len(name) > 40:
                name = name[:38] + "…"

            # 14 columns: type, name, date, bP, bQ, purch_total,
            #             sP, sQ, sale_total, net, backup, note1, note2, oid
            # Calculated cells (purch_total, sale_total, net) left empty —
            # user fills them via Excel formulas after pasting.
            self._tree.insert("", tk.END, values=(
                rec['type'],
                name,
                rec['dateOnly'],
                rec['bP'],
                rec['bQ'],
                "",            # purch_total — left for Excel formula
                rec['sP'],
                rec['sQ'],
                "",            # sale_total  — left for Excel formula
                "",            # net         — left for Excel formula
                "",            # backup
                "",            # note1
                "",            # note2
                rec['oid'],
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
            # CSV header translation (i18n-keyed, same as tree headings)
            # CSV ヘッダー翻訳 (i18n キー、ツリー見出しと同じ)
            # CSV 表头翻译 (i18n key, 与 tree 列标题一致)
            header = [
                self._tm("col_type"),
                self._tm("col_name"),
                self._tm("col_date"),
                self._tm("col_purch_price"),
                self._tm("col_purch_qty"),
                self._tm("col_purch_total"),
                self._tm("col_sale_price"),
                self._tm("col_sale_qty"),
                self._tm("col_sale_total"),
                self._tm("col_net"),
                self._tm("col_backup"),
                self._tm("col_note1"),
                self._tm("col_note2"),
                self._tm("col_oid"),
            ]
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for rec in self._records:
                    writer.writerow([
                        rec['type'],
                        rec['name'],
                        rec['dateOnly'],
                        rec['bP'],
                        rec['bQ'],
                        "",          # purch_total — Excel formula
                        rec['sP'],
                        rec['sQ'],
                        "",          # sale_total  — Excel formula
                        "",          # net         — Excel formula
                        "",          # backup
                        "",          # note1
                        "",          # note2
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