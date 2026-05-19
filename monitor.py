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
        print(f"[推送] {title} -> {resp.json()}")
    except Exception as e:
        print(f"[推送失败] {e}")


def load_prev():
    try:
        with open("prev_stocks.json", "r") as f:
            return json.load(f)
    except:
        return {}


def save_prev(data):
    with open("prev_stocks.json", "w") as f:
        json.dump(data, f)


def check_item(item_id, prev_stocks):
    item_id = item_id.strip()
    if not item_id:
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://shopee.co.id/product/{SHOP_ID}/{item_id}",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        url = f"https://shopee.co.id/api/v4/item/get?itemid={item_id}&shopid={SHOP_ID}"
        print(f"[请求] {url}")
        resp = requests.get(url, headers=headers, timeout=15)
        print(f"[HTTP状态] {resp.status_code}")

        raw = resp.text
        print(f"[原始响应前500字] {raw[:500]}")

        result = resp.json()

        # 兼容不同响应格式
        item = (
            result.get("data", {}).get("item")
            or result.get("item")
            or result.get("data")
            or {}
        )

        item_name = item.get("name", f"商品{item_id}")
        models = item.get("models", [])

        print(f"[商品名] {item_name}")
        print(f"[SKU数量] {len(models)}")

        if not models:
            # 无变体商品，直接读 stock 字段
            stock = item.get("stock", 0)
            sid = str(item_id)
            prev = prev_stocks.get(sid)
            print(f"[单规格库存] {stock} 件")

            if prev is None:
                print(f"[初始化] {item_name}：{stock} 件")
            elif prev == 0 and stock > 0:
                send_wechat(
                    f"【补货】{item_name}",
                    f"> 库存：0 -> {stock} 件\n> [查看商品](https://shopee.co.id/product/{SHOP_ID}/{item_id})"
                )
            elif stock == 0 and prev > 0:
                send_wechat(
                    f"【缺货】{item_name}",
                    f"> 库存：{prev} -> 0 件（已售罄）"
                )
            else:
                print(f"[正常] {item_name}：{stock} 件")

            prev_stocks[sid] = stock
            return

        for sku in models:
            sid  = str(sku.get("modelid", ""))
            name = sku.get("name", "默认SKU")
            stock = (
                sku.get("stock_info_v2", {}).get("summary_info", {}).get("total_available_stock")
                or sku.get("stock", 0)
            )
            prev = prev_stocks.get(sid)
            print(f"[SKU] {name}：{stock} 件")

            if prev is None:
                print(f"[初始化] {item_name} · {name}：{stock} 件")
            elif prev == 0 and stock > 0:
                send_wechat(
                    f"【补货】{item_name}",
                    f"> SKU：{name}\n> 库存：0 -> {stock} 件\n> [查看商品](https://shopee.co.id/product/{SHOP_ID}/{item_id})"
                )
            elif stock == 0 and prev > 0:
                send_wechat(
                    f"【缺货】{item_name}",
                    f"> SKU：{name}\n> 库存：{prev} -> 0 件（已售罄）"
                )
            else:
                print(f"[正常] {item_name} · {name}：{stock} 件")

            prev_stocks[sid] = stock

    except Exception as e:
        print(f"[错误] item_id={item_id}：{e}")


# 主程序
print("=" * 40)
print(f"开始检测，共 {len(ITEMS)} 个商品")
print(f"SHOP_ID: {SHOP_ID}")
print(f"ITEMS: {ITEMS}")
print("=" * 40)

prev = load_prev()

for item_id in ITEMS:
    check_item(item_id, prev)
    time.sleep(2)

save_prev(prev)
print("检测完成")
