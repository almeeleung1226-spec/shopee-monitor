# Shopee 补货监控 · 部署说明

## 文件说明
- `monitor.py`      主监控脚本
- `requirements.txt` 依赖库
- `Procfile`         Render 启动配置

---

## 部署步骤

### 1. 上传到 GitHub
1. 打开 https://github.com，登录后点右上角 "+" → New repository
2. 仓库名填 `shopee-monitor`，选 Public，点 Create
3. 把这 3 个文件全部拖进去，点 Commit changes

### 2. 部署到 Render（免费）
1. 打开 https://render.com，用 GitHub 账号登录
2. 点 "New +" → 选 "Background Worker"
3. 选择刚才的 GitHub 仓库
4. 填写以下配置：
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: python monitor.py
5. 往下找 "Environment Variables"，添加以下变量：

| 变量名                  | 说明                              | 示例值              |
|------------------------|----------------------------------|---------------------|
| SERVER_CHAN_KEY         | Server酱 SendKey                 | SCT123456Txxx       |
| SHOPEE_SHOP_ID          | Shopee 店铺 ID                   | 12345678            |
| SHOPEE_ITEM_IDS         | 商品 ID，多个用英文逗号分隔         | 111111,222222       |
| CHECK_INTERVAL_MINUTES  | 检测间隔分钟数（默认 5）           | 5                   |

6. 点 "Create Background Worker"，等待部署完成

### 3. 获取 Server酱 SendKey
1. 打开 https://sct.ftqq.com
2. 微信扫码登录
3. 复制页面上的 SendKey，填入 Render 环境变量

### 4. 获取 Shopee 商品 ID 和店铺 ID
打开任意 Shopee 商品页面，URL 格式如下：
https://shopee.co.id/商品名-i.{SHOP_ID}.{ITEM_ID}

例如：https://shopee.co.id/Nike-i.87654321.12345678
- SHOP_ID  = 87654321
- ITEM_ID  = 12345678

---

## 运行后会看到的日志
```
========================================
Shopee 补货监控启动
监控商品数：2
检测间隔：5 分钟
Server酱 Key：已配置
========================================
[初始化] Nike Air Max · 黑色/41：当前库存 0 件
[初始化] Nike Air Max · 白色/40：当前库存 15 件
检测完成，5 分钟后再次检测
...
[补货] Nike Air Max · 黑色/41：0 → 8 件 → 微信收到推送
```

## 常见问题
- **收不到推送**：检查 SERVER_CHAN_KEY 是否正确，Server酱免费版每天限 5 条
- **[无SKU] 提示**：SHOPEE_SHOP_ID 填错了，重新从商品 URL 里获取
- **[超时] 提示**：Shopee 偶尔限速，正常现象，下次会自动重试
