# main.py
import pyperclip
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
from parser import parse_message_node
from i18n import LanguageManager
import itemName


def run():
    lm = None
    with sync_playwright() as p:
        try:
            # 1.Connect to Chrome (Remote Debugging: 9222)
            # 1. Chrome に接続 (リモートデバッグ: 9222)
            # 1. 连接到 Chrome (远程调试: 9222)
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]

            # 2.Find trading history page.
            # 2. 取引履歴ページを検索
            # 2. 查找交易历史页面
            target_page = None
            for pg in context.pages:
                if "trade.gaijin.net/history" in pg.url:
                    target_page = pg
                    break

            if not target_page:
                # Bilingual: English first, then Chinese.
                # バイリンガル：英語→中国語の順
                # 双语：先英语后中文
                print("Error: Trading history page not found! Please open it manually first.")
                print("错误：未找到交易历史页面！请先手动打开交易通知页面。")
                return

            # 3.Confirm login with bilingual prompt (hardcoded).
            # 3. バイリンガルでログイン確認（ハードコード）
            # 3. 双语确认登录（硬编码）
            input("Please confirm you have logged in to the Notifications page. Press Enter to continue...\n请确认已登录到交易通知界面，按 Enter 继续...")

            # 4.Detect site language from the notifications title text.
            # 4. ページタイトルから言語を検出
            # 4. 从通知标题文字检测网站语言
            try:
                title_el = target_page.query_selector('div._notificationsTitle_vxfqb_16')
                title_text = title_el.inner_text().strip() if title_el else ""
            except Exception:
                title_text = ""

            if "通知" in title_text:
                detected_lang = "zh_CN"
            elif title_text:
                detected_lang = "en_US"
            else:
                # Bilingual: English first, then Chinese. else is Redundant guard.
                # バイリンガル：英語→中国語の順 else は冗長ガード
                # 双语：先英语后中文 else 是冗余判断
                print(f"Error: Could not detect page language (title='{title_text}')")
                print("错误：未能检测到页面语言标识")
                print(f"Ensure transaction notification page is loaded correctly, or report this issue.")
                print("请确保交易通知页面已正确加载，或报告此问题。")
                
                return

            lm = LanguageManager(detected_lang)
            lang_name = lm.t("prompt.lang_name")
            print(lm.t("prompt.detected_lang") % lang_name)

            # Sync itemName module with the detected language.
            # itemName モジュールを検出言語に同期
            # 将 itemName 模块同步到检测到的语言
            itemName.reload_lang(detected_lang)

            # 5.Interactive date input.
            # 5. 対話型日付入力
            # 5. 交互式输入日期
            now = datetime.now()
            default_start = (now - timedelta(days=31)).strftime("%Y/%m/%d")
            d_input = input(lm.t("prompt.enter_date") % default_start) or default_start
            start_date = datetime.strptime(d_input, "%Y/%m/%d")

            # End date: 23:59:59 of the day prior to execution.
            # 終了日：実行前日の 23:59:59
            # 结束日期为脚本执行日前一天 23:59:59
            yesterday_end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)

            print(lm.t("prompt.connected_page") % target_page.title())
            print(lm.t("prompt.fetching_data"))

            # 6.Fetch and Filter
            # 6. 取得とフィルタリング
            # 6. 抓取与过滤
            messages = target_page.query_selector_all('a.message')
            all_data = []

            for msg in messages:
                data = parse_message_node(msg, lm=lm)
                if data and data['dt_obj'] and start_date <= data['dt_obj'] <= yesterday_end:
                    all_data.append(data)

            if not all_data:
                print(lm.t("prompt.no_records"))
                pyperclip.copy(" ")
                return

            # 7.Sort and Output
            # 7. ソートと出力
            # 7. 排序与输出
            all_data.sort(key=lambda x: x['dt_obj'] if x['dt_obj'] else 0)

            csv_lines = []
            for item in all_data:
                row = [
                    item['type'], item['name'], item['dateOnly'],
                    item['bP'], item['bQ'], "",
                    item['sP'], item['sQ'],
                    "", "", "", "", "", item['oid']
                ]
                csv_lines.append("\t".join(row))

            final_output = "\n".join(csv_lines)
            pyperclip.copy(final_output)

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