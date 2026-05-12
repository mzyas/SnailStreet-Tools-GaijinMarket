# core.py
"""
Core functions for Gaijin Market Trade Automation.
Gaijin Market 取引自動化のコア機能。
Gaijin Market 交易自动化核心功能。

Extracted from main.py to be shared between CLI and GUI.
main.py から抽出され、CLI と GUI で共有されます。
从 main.py 提取，供 CLI 和 GUI 共用。
"""
import pyperclip
import os
import sys
import subprocess
import shutil
from datetime import datetime, timedelta
from parser import parse_message_node


def connect_browser(playwright_instance):
    """
    Connect to an already-running Chrome via CDP and locate the trading history page.
    既存の Chrome に CDP 経由で接続し、取引履歴ページを探します。
    通过 CDP 连接到已运行的 Chrome，并定位交易历史页面。

    Returns:
        (True, (browser, context, target_page))  — success.
        (False, "no_cdp")                        — Chrome not running / port 9222 closed.
        (False, "no_page")                       — Chrome connected but no trading history page.
    """
    try:
        browser = playwright_instance.chromium.connect_over_cdp("http://localhost:9222")
    except Exception:
        return False, "no_cdp"

    context = browser.contexts[0]
    target_page = None
    for pg in context.pages:
        if "trade.gaijin.net/history" in pg.url:
            target_page = pg
            break

    if not target_page:
        return False, "no_page"

    return True, (browser, context, target_page)


def detect_language(target_page):
    """
    Detect website language from the notifications title text.
    通知タイトルからウェブサイトの言語を検出します。
    从通知标题文字检测网站语言。

    Returns:
        str: "zh_CN", "en_US", or None if detection fails.
    """
    try:
        title_el = target_page.query_selector('div._notificationsTitle_vxfqb_16')
        title_text = title_el.inner_text().strip() if title_el else ""
    except Exception:
        title_text = ""

    if "通知" in title_text:
        return "zh_CN"
    elif title_text:
        return "en_US"
    else:
        return None


def fetch_records(target_page, start_date, end_date, lm):
    """
    Fetch all .message nodes from the page, parse them, and filter by date.
    ページから .message ノードを取得・解析し、日付でフィルタリングします。
    从页面抓取所有 .message 节点，解析并按日期过滤。

    Args:
        target_page: Playwright page object.
        start_date: datetime object (inclusive).
        end_date:   datetime object (inclusive).

    Returns:
        list[dict]: Parsed and filtered records, sorted by date ascending.
    """
    messages = target_page.query_selector_all('a.message')
    all_data = []

    for msg in messages:
        data = parse_message_node(msg, lm=lm)
        if data and data['dt_obj'] and start_date <= data['dt_obj'] <= end_date:
            all_data.append(data)

    all_data.sort(key=lambda x: x['dt_obj'] if x['dt_obj'] else datetime.min)
    return all_data


def format_tsv(records):
    """
    Format parsed records into Tab-Separated Values string.
    解析済みレコードをタブ区切り形式の文字列にフォーマットします。
    将解析后的记录格式化为制表符分隔的字符串。

    14 columns: type, name, dateOnly, bP, bQ, "", sP, sQ,
                "", "", "", "", "", oid
    """
    csv_lines = []
    for item in records:
        row = [
            item['type'], item['name'], item['dateOnly'],
            item['bP'], item['bQ'], "",
            item['sP'], item['sQ'],
            "", "", "", "", "", item['oid']
        ]
        csv_lines.append("\t".join(row))
    return "\n".join(csv_lines)


def copy_to_clipboard(text):
    """Copy text to system clipboard.  テキストをクリップボードにコピー。  将文本复制到剪贴板。"""
    pyperclip.copy(text)


def get_default_date_range():
    """
    Calculate default date range: 31 days ago → yesterday 23:59:59.
    デフォルトの日付範囲を計算：31日前 → 昨日の 23:59:59。
    计算默认日期范围：31天前 → 昨天 23:59:59。

    Returns:
        tuple: (start_date_datetime, end_date_datetime, start_date_str)
    """
    now = datetime.now()
    default_start = now - timedelta(days=31)
    yesterday_end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
    return default_start, yesterday_end, default_start.strftime("%Y/%m/%d")


def _find_chrome_path():
    """
    Locate the Chrome/Chromium executable on this system.
    システム上の Chrome/Chromium 実行ファイルを探します。
    查找本机 Chrome/Chromium 可执行文件路径。

    Returns:
        str or None: Full path to the executable, or None if not found.
    """
    # 1. Try Windows registry (reg query fallback)
    #    レジストリから検索
    #    尝试 Windows 注册表
    if sys.platform == "win32":
        try:
            import winreg
            for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for subkey in (
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chromium.exe",
                ):
                    try:
                        key = winreg.OpenKey(root, subkey)
                        path, _ = winreg.QueryValueEx(key, "")
                        winreg.CloseKey(key)
                        if os.path.isfile(path):
                            return path
                    except OSError:
                        continue
        except Exception:
            pass

    # 2. shutil.which lookup
    #    shutil.which で検索
    #    尝试 PATH 查找
    for name in ("chrome", "chromium", "chrome.exe", "chromium.exe",
                 "google-chrome", "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found

    # 3. Default installation paths (Windows)
    #    デフォルトのインストール先
    #    默认安装路径
    default_paths = []
    if sys.platform == "win32":
        default_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    elif sys.platform == "darwin":
        default_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif sys.platform.startswith("linux"):
        default_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
        ]

    for p in default_paths:
        if os.path.isfile(p):
            return p

    return None


def launch_chrome(project_root: str, open_url: str = "https://trade.gaijin.net"):
    """
    Launch Chrome with remote debugging enabled (port 9222) and isolated user data.
    リモートデバッグ有効 (ポート 9222) で Chrome を起動し、独立したユーザーデータを使用します。
    以远程调试模式 (端口 9222) 启动 Chrome，使用独立的用户数据目录。

    Args:
        project_root:  Project root directory (contains ChromeGaijinMarketData/).
        open_url:      URL to open after launch.
                       Default: https://trade.gaijin.net

    Returns:
        tuple: (success: bool, message: str)
    """
    chrome_path = _find_chrome_path()
    if not chrome_path:
        return False, (
            "Chrome executable not found.\n"
            "Please install Chrome or set it in PATH.\n"
            "Chrome の実行ファイルが見つかりません。\n"
            "Chrome をインストールするか PATH に追加してください。\n"
            "找不到 Chrome 可执行文件，请安装 Chrome 或将其添加到 PATH。"
        )

    user_data_dir = os.path.join(project_root, "ChromeGaijinMarketData")
    os.makedirs(user_data_dir, exist_ok=True)

    cmd = [
        chrome_path,
        f"--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        open_url,
    ]

    try:
        subprocess.Popen(cmd, cwd=project_root)
        return True, "Chrome launched.  /  Chrome を起動しました。  /  Chrome 已启动。"
    except Exception as e:
        return False, str(e)
