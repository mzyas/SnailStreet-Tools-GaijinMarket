# itemName.py
import os
import csv

NATIONS = ["USA", "USSR", "Germany", "Great Britain", "Japan", "China", "Italy", "France", "Sweden", "Israel"]
#NATIONS = ["美国", "苏联", "德国", "英国", "日本", "中国", "意大利", "法国", "瑞典", "以色列"]

# Get the absolute path of the current script
# 実行中スクリプトの絶対パスを取得
# 获取当前脚本所在的绝对路径
base_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the correct CSV path
# 正しいCSVパスを構築
# 拼接出正确的 CSV 路径
file_path = os.path.join(base_dir, 'Item_Name', 'Decoration_zh.csv')
#file_path = os.path.join(base_dir, 'Item_Name', 'Decoration_eng.csv')


def load_other_items():
    items = []
    if not os.path.exists(file_path):
        print(f"Error: File not found {file_path}")
        return items

    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                items.append(row[0])
    return items


OTHER_ITEMS = load_other_items()






