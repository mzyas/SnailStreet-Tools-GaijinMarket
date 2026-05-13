# main.py
# CLI entry point for Gaijin Market Trade Automation.
# Gaijin Market 取引自動化の CLI エントリポイント。
# Gaijin Market 交易自动化 CLI 入口点。

from playwright.sync_api import sync_playwright
from datetime import datetime
from i18n import LanguageManager
from version import VERSION
from core import connect_browser, detect_language, fetch_records, format_tsv, copy_to_clipboard, get_default_date_range
import itemName


def run():
    print(f"Gaijin Trade Automator v{VERSION}")
    """
    CLI mode: connect to Chrome, detect language, input date,
    fetch records and copy TSV to clipboard.
    CLI モード：Chrome に接続し、言語を検出し、日付を入力し、
    レコードを取得して TSV をクリップボードにコピーします。
    CLI 模式：连接 Chrome、检测语言、输入日期、抓取记录并复制 TSV 到剪贴板。
    """
    lm = None
    with sync_playwright() as p:
        try:
            # 1.Connect to Chrome.
            # 1.Chrome に接続。
            # 1.连接到 Chrome。
            ok, data = connect_browser(p)
            if not ok:
                if data == "no_cdp":
                    print("Error: Chrome not detected (port 9222).")
                    print("错误：未检测到 Chrome（端口 9222），请先运行 start_chrome.bat。")
                    print("Please run start_chrome.bat first to launch Chrome with remote debugging.")
                else:
                    print("Error: Trading history page not found! Please open it manually first.")
                    print("错误：未找到交易历史页面！请先手动打开交易通知页面。")
                return

            browser, context, target_page = data

            # 2.Confirm login.
            # 2.ログイン確認。
            # 2.确认登录。
            input("Please confirm you have logged in to the Notifications page. Press Enter to continue...\n"
                  "请确认已登录到交易通知界面，按 Enter 继续...")

            # 3.Detect language.
            # 3.言語を検出。
            # 3.检测语言。
            detected_lang = detect_language(target_page)
            if detected_lang is None:
                print("Error: Could not detect page language.")
                print("错误：未能检测到页面语言标识")
                print("Ensure transaction notification page is loaded correctly.")
                print("请确保交易通知页面已正确加载。")
                return

            lm = LanguageManager(detected_lang)
            lang_name = lm.t("prompt.lang_name")
            print(lm.t("prompt.detected_lang") % lang_name)

            # 4.Sync itemName module.
            # 4.itemName モジュールを同期。
            # 4.同步 itemName 模块。
            itemName.reload_lang(detected_lang)

            # 5.Interactive date input.
            # 5.対話型日付入力。
            # 5.交互式输入日期。
            _, yesterday_end, default_start_str = get_default_date_range()
            d_input = input(lm.t("prompt.enter_date") % default_start_str) or default_start_str
            start_date = datetime.strptime(d_input, "%Y/%m/%d")

            print(lm.t("prompt.connected_page") % target_page.title())
            print(lm.t("prompt.fetching_data"))

            # 6.Fetch and filter.
            # 6.取得とフィルタリング。
            # 6.抓取与过滤。
            all_data = fetch_records(target_page, start_date, yesterday_end, lm)

            if not all_data:
                print(lm.t("prompt.no_records"))
                copy_to_clipboard(" ")
                return

            # 7.Format and copy.
            # 7.フォーマットとコピー。
            # 7.格式化与复制。
            tsv = format_tsv(all_data)
            copy_to_clipboard(tsv)

            print("-" * 30)
            print(lm.t("prompt.fetch_success") % len(all_data))
            print(lm.t("prompt.data_copied"))
            print("-" * 30)

        except Exception as e:
            if lm is not None:
                print(f"{lm.t('prompt.error_connecting')}: {e}")
            else:
                print(f"Error: {e}\n运行异常: {e}")


if __name__ == "__main__":
    run()