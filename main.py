# main.py
import pyperclip
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
from parser import parse_message_node


def run():
    # 1.Interactive date input.
    # 1.対話型日付入力
    # 1.交互式输入日期
    now = datetime.now()
    default_start = (now - timedelta(days=31)).strftime("%Y/%m/%d")
    d_input = input(f"Please enter start date (YYYY/M/D) [Default {default_start}]: ") or default_start
    start_date = datetime.strptime(d_input, "%Y/%m/%d")

    # End date: 23:59:59 of the day prior to execution.
    # 終了日：実行前日の 23:59:59
    # 结束日期为脚本执行日前一天 23:59:59
    yesterday_end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)

    with sync_playwright() as p:
        try:
            # 2.Connect to Chrome (Remote Debugging: 9222)
            # 2.起動済みの Chrome に接続 (ポート 9222)
            # 2.连接到你已经手动打开的 Chrome (端口 9222)
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]

            # 3.Apply lock to trading pages on all tabs.
            # 3.全タブ内の取引ページ固定を有効化
            # 3.在所有标签页中锁定交易页面
            target_page = None
            for pg in context.pages:
                if "trade.gaijin.net/history" in pg.url:
                    target_page = pg
                    break

            if not target_page:
                print("Error: Trading history page not found! Please open it manually first.")
                return

            print(f"Connected to page: {target_page.title()}")
            print("Fetching data...")

            # 4.Fetch and Filter
            # 4.取得とフィルタリング
            # 4.抓取与过滤
            messages = target_page.query_selector_all('a.message')
            all_data = []

            for msg in messages:
                data = parse_message_node(msg)
                # Date filtering # 日付フィルタリング # 日期过滤
                if data and data['dt_obj'] and start_date <= data['dt_obj'] <= yesterday_end:
                    all_data.append(data)

            if not all_data:
                print("No records found matching the criteria.")
                pyperclip.copy(" ")
                return

            # 5.Sort and Output
            # 5.ソートと出力
            # 5.排序与输出
            all_data.sort(key=lambda x: x['dt_obj'] if x['dt_obj'] else 0)

            csv_lines = []
            for item in all_data:
                # Map to predefined Excel headers
                # Excel既定のヘッダーに対応
                # 对应excel预制列名称
                # [type, name, dateOnly, bP, bQ, "", sP, sQ, "", "", "", "", "", oid]
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
            print(f"Fetch successful! Found {len(all_data)} records.")
            print("Data successfully copied to clipboard.")
            print("-" * 30)

        except Exception as e:
            print(f"Exception: {e}")


if __name__ == "__main__":
    run()
