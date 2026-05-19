import requests
import time
import os
import json

SERVER_CHAN_KEY = os.environ.get("SERVER_CHAN_KEY", "")
SHOP_ID         = os.environ.get("SHOPEE_SHOP_ID", "")
ITEMS           = os.environ.get("SHOPEE_ITEM_IDS", "").split(",")

def send_wechat(title, content):
    if not SERVER_CHAN_KEY:
        print("[警告] SERVER_CHAN_KEY 未设置")
        return
    try:
        resp = requests.post(
            f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        print(f"[推送] {title} → {resp.json()}")
    except Exception as e:
        print(f"[推送失败] {e}")

def load_prev():
    """读取上次库存记录"""
    try:
        with open("prev_stocks.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_prev(data):
    """保存本次库存记录"""
    with open("prev_stocks.json", "w") as f:
        json.dump(data, f)

def check_item(item_id, prev_stocks):
    item_id = item_id.strip()
    if not item_id:
        return
    try:
        resp = requests.get(
            "https://shopee.co.id/api/v4/item/get",
            params={"itemid": item_id, "shopid": SHOP_ID},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://shopee.co.id/",
            },
            timeout=15
        )
        data = resp.json()
        item_name = data.get("data", {}).get("item", {}).get("name", f"商品{item_id}")
        models = data.get("data", {}).get("item", {}).get("models", [])

        if not models:
            print(f"[无SKU] {item_name}，请检查 SHOP_ID 是否正确")
            return

        for sku in models:
            sid   = str(sku.get("modelid", ""))
            name  = sku.get("name", "默认SKU")
            stock = (
                sku.get("stock_info_v2", {})
                   .get("summary_info", {})
                   .get("total_available_stock", 0)
            )
            prev = prev_stocks.get(sid)

            if prev is None:
                print(f"[初始化] {item_name} · {name}：{stock} 件")
            elif prev == 0 and stock > 0:
                send_wechat(
                    f"【补货】{item_name}",
                    f"> **SKU**：{name}  \n> **库存**：0 → {stock} 件  \n> [查看商品](https://shopee.co.id/product/{SHOP_ID}/{item_id})"
                )
            elif stock == 0 and prev > 0:
                send_wechat(
                    f"【缺货】{item_name}",
                    f"> **SKU**：{name}  \n> **库存**：{prev} → 0 件（已售罄）"
                )
            else:
                print(f"[正常] {item_name} · {name}：{stock} 件")

            prev_stocks[sid] = stock

    except Exception as e:
        print(f"[错误] item_id={item_id}：{e}")

# ─── 主程序，运行一次就退出 ───
print(f"开始检测，共 {len(ITEMS)} 个商品")
prev = load_prev()

for item_id in ITEMS:
    check_item(item_id, prev)
    time.sleep(2)

save_prev(prev)
print("检测完成")
