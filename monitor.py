import requests
import schedule
import time
import os

# ─── 从环境变量读取配置（在 Render 后台填写，不要改这里）───
SERVER_CHAN_KEY = os.environ.get("SERVER_CHAN_KEY", "")
SHOP_ID         = os.environ.get("SHOPEE_SHOP_ID", "")
ITEMS           = os.environ.get("SHOPEE_ITEM_IDS", "").split(",")
CHECK_INTERVAL  = int(os.environ.get("CHECK_INTERVAL_MINUTES", "5"))  # 默认5分钟

# ─── 记录上次库存（程序重启会重置，属正常现象）───
prev_stocks = {}


def send_wechat(title: str, content: str):
    """通过 Server酱 推送消息到微信"""
    if not SERVER_CHAN_KEY:
        print("[警告] SERVER_CHAN_KEY 未设置，跳过推送")
        return
    try:
        resp = requests.post(
            f"https://sctapi.ftqq.com/{SERVER_CHAN_KEY}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        result = resp.json()
        if result.get("code") == 0:
            print(f"[推送成功] {title}")
        else:
            print(f"[推送失败] {result}")
    except Exception as e:
        print(f"[推送异常] {e}")


def check_item(item_id: str):
    """检测单个商品的所有 SKU 库存"""
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

        # 获取商品名称
        item_name = data.get("data", {}).get("item", {}).get("name", f"商品{item_id}")
        models = data.get("data", {}).get("item", {}).get("models", [])

        if not models:
            print(f"[无SKU] {item_name}（item_id={item_id}），请检查 SHOP_ID 是否正确")
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

            # 首次运行：只记录，不推送
            if prev is None:
                prev_stocks[sid] = stock
                print(f"[初始化] {item_name} · {name}：当前库存 {stock} 件")
                continue

            # 补货：从 0 或低库存 → 有货
            if prev == 0 and stock > 0:
                send_wechat(
                    f"【补货】{item_name}",
                    f"> **SKU**：{name}  \n"
                    f"> **库存变化**：0 → {stock} 件  \n"
                    f"> [点击查看商品](https://shopee.co.id/product/{SHOP_ID}/{item_id})"
                )

            # 缺货：有货 → 0
            elif stock == 0 and prev > 0:
                send_wechat(
                    f"【缺货】{item_name}",
                    f"> **SKU**：{name}  \n"
                    f"> **库存变化**：{prev} → 0 件（已售罄）"
                )

            prev_stocks[sid] = stock

    except requests.exceptions.Timeout:
        print(f"[超时] item_id={item_id}，稍后重试")
    except Exception as e:
        print(f"[错误] item_id={item_id}：{e}")


def job():
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*40}")
    print(f"[{now}] 开始检测，共 {len(ITEMS)} 个商品")
    for item_id in ITEMS:
        check_item(item_id)
        time.sleep(2)  # 每个商品之间间隔 2 秒，避免请求过频
    print(f"检测完成，{CHECK_INTERVAL} 分钟后再次检测")


# ─── 启动 ───
print("=" * 40)
print("Shopee 补货监控启动")
print(f"监控商品数：{len(ITEMS)}")
print(f"检测间隔：{CHECK_INTERVAL} 分钟")
print(f"Server酱 Key：{'已配置' if SERVER_CHAN_KEY else '未配置！'}")
print("=" * 40)

job()  # 启动时立刻执行一次
schedule.every(CHECK_INTERVAL).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(30)
