# itemName.py
import os
import csv
from i18n import LanguageManager

# Default LanguageManager (fallback).
# デフォルトの LanguageManager（フォールバック）。
# 默认 LanguageManager（回退）。
_LM = LanguageManager("zh_CN")

if _LM.lang == "zh_CN":
    NATIONS = ["美国", "苏联", "德国", "英国", "日本", "中国", "意大利", "法国", "瑞典", "以色列"]
else:
    NATIONS = ["USA", "USSR", "Germany", "Great Britain", "Japan", "China", "Italy", "France", "Sweden", "Israel"]

# Determine base directory:
#   - PyInstaller bundle:  sys.executable のあるディレクトリ
#     打包后: exe 所在目录
#   - Normal Python:       __file__ のあるディレクトリ
#     通常実行: 脚本所在目录
import sys as _sys

if getattr(_sys, 'frozen', False):
    # Running as a PyInstaller bundle — Item_Name/ sits next to the .exe
    # PyInstaller バンドル実行中 — Item_Name/ は .exe の隣
    # 打包运行 — Item_Name/ 在 exe 旁边
    base_dir = os.path.dirname(_sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# CSV path for decoration items.
# 装飾品アイテムの CSV パス。
# 装饰品 CSV 路径。
file_path = os.path.join(base_dir, 'Item_Name', _LM.csv_for("Decoration"))


def load_other_items(csv_path=None):
    if csv_path is None:
        csv_path = file_path
    items = []
    if not os.path.exists(csv_path):
        print(f"Error: File not found {csv_path}")
        return items
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                items.append(row[0])
    return items


# Other (non-Vehicle, non-Camouflage) items.
# その他（車両・塗装以外）のアイテム。
# 其它物品（非载具、非涂装）。
OTHER_ITEMS = load_other_items()


def reload_lang(lang: str):
    """
    Dynamically reload NATIONS / CSV path for a new language.
    新しい言語に合わせて NATIONS と CSV パスを動的に再読み込み。
    为新的语言动态重新加载 NATIONS 和 CSV 路径。
    """
    global NATIONS, file_path, OTHER_ITEMS, _LM
    _LM = LanguageManager(lang)
    if _LM.lang == "zh_CN":
        NATIONS = ["美国", "苏联", "德国", "英国", "日本", "中国", "意大利", "法国", "瑞典", "以色列"]
    else:
        NATIONS = ["USA", "USSR", "Germany", "Great Britain", "Japan", "China", "Italy", "France", "Sweden", "Israel"]
    file_path = os.path.join(base_dir, 'Item_Name', _LM.csv_for("Decoration"))
    OTHER_ITEMS = load_other_items(file_path)