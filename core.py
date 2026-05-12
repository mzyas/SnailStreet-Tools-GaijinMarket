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
from datetime import datetime, timedelta
from parser import parse_message_node
from i18n import LanguageManager
import itemName


def connect_browser(playwright_instance):
    """
    Connect to an already-running Chrome via CDP and locate the trading history page.
    既存の Chrome に CDP 経由で接続し、取引履歴ページを探します。
    通过 CDP 连接到已运行的 Chrome，并定位交易历史页面。

    Returns:
        tuple: (browser, context, target_page) on success.
        None:  if page not found.
    """
    try:
        browser = playwright_instance.chromium.connect_over_cdp("http://localhost:9222")
    except Exception:
        return None

    context = browser.contexts[0]
    target_page = None
    for pg in context.pages:
        if "trade.gaijin.net/history" in pg.url:
            target_page = pg
            break

    if not target_page:
        return None

    return browser, context, target_page


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