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
    try:
        with open("prev_stocks.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_prev(data):
    with open("prev_stocks.json", "w") as f:
        json.dump(data, f)

def check_item(item_id, prev_stocks):
    item_id = item_i
