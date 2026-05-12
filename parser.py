# parser.py
import re
from datetime import datetime
import itemName
from i18n import LanguageManager

_LM = LanguageManager("zh_CN")
_LAST_LANG = _LM.lang  # Track language for dynamic reloading


def parse_message_node(msg_node, lm=None):
    global _LAST_LANG
    if lm is None:
        lm = _LM
    # Dynamically reload NATIONS / OTHER_ITEMS when language changes
    if lm.lang != _LAST_LANG:
        itemName.reload_lang(lm.lang)
        _LAST_LANG = lm.lang
    # 1.Raw text fetching
    # 1.原文テキストの抽出
    # 1.基础文本获取
    full_text = msg_node.inner_text()
    is_buy = lm.t("parser.purchase_completed") in full_text
    is_sell = lm.t("parser.sale_completed") in full_text

    if not is_buy and not is_sell:
        return None

    # 2.Date parsing
    # 2.日付の解析
    # 2.日期解析
    date_el = msg_node.query_selector('.eventDate')
    dt_obj = None
    date_only = ""
    if date_el:
        raw_str = date_el.inner_text().strip()
        # Format processing #フォーマットの処理 # 处理格式 # 26.04.2026 — 13:45
        parts = re.split(r'[—\-]', raw_str)
        date_part = parts[0].strip()
        time_part = parts[1].strip().replace('.', ':') if len(parts) > 1 else "00:00"

        p = date_part.split('.')
        if len(p) == 3:
            # Ordered by: # ソート順: # 这里的顺序是: # p[0]=Day, p[1]=Month, p[2]=Year
            date_only = f"{p[2]}/{int(p[1])}/{int(p[0])}"
            dt_obj = datetime.strptime(f"{p[2]}-{p[1]}-{p[0]} {time_part}", "%Y-%m-%d %H:%M")

    # 3.Name and type determination
    # 3.名称とタイプの判定
    # 3.名称与类型判断
    name_el = msg_node.query_selector('.name')
    if not name_el: return None
    original_name = name_el.inner_text().strip()
    # Remove special characters for type matching
    # 特殊文字を除去してタイプを判定
    # 移除特殊字符进行类型匹配
    clean_name = re.sub('[^\u4e00-\u9fa5a-zA-Z0-9()（）]', '', original_name)

    item_type = lm.t("parser.type_camouflage")
    # Check for "Other" type
    # 「その他」の判定
    # 判断是否为“其它”
    if any(re.sub('[^\u4e00-\u9fa5a-zA-Z0-9()（）]', '', item) in clean_name for item in itemName.OTHER_ITEMS):
        item_type = lm.t("parser.type_other")
    else:
        has_bracket = bool(re.search(r'[(（].*?[)）]', clean_name))
        if has_bracket and any(nation in clean_name for nation in itemName.NATIONS):
            item_type = lm.t("parser.type_vehicle")

    # 4.Price and Quantity
    # 4.価格と数量
    # 4.价格与数量
    price_el = msg_node.query_selector('.price')
    raw_p = "0"
    if price_el:
        # Extract price part and filter out non-numeric characters
        # 価格部分を抽出し、非数字をフィルタリング
        # 取价格部分并过滤掉非数字
        price_text = price_el.inner_text().strip()
        tokens = price_text.split()
        # Pick first token that contains at least one digit after cleaning
        for t in tokens:
            cleaned = re.sub(r'[^\d.]', '', t)
            if cleaned:
                raw_p = cleaned
                break

    count_el = msg_node.query_selector('.count span') or msg_node.query_selector('.count')
    raw_c = "1"
    if count_el:
        raw_c = re.sub(r'[xX×]', '', count_el.inner_text()).strip()

    # 5.Order ID
    # 5.注文ID
    # 5.订单ID
    oid_el = msg_node.query_selector('.eventOrderId')
    oid = oid_el.inner_text().strip() if oid_el else ""

    return {
        "dt_obj": dt_obj,
        "type": item_type,
        "name": original_name,
        "dateOnly": date_only,
        "bP": raw_p if is_buy else "0",
        "bQ": raw_c if is_buy else "0",
        "sP": raw_p if is_sell else "0",
        "sQ": raw_c if is_sell else "0",
        "oid": oid
    }