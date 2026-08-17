---
name: westmonth-inventory-check
description: 查询西之月(westmonth.com)平台SKU在美国站的具体库存数量。当用户提到西之月库存、westmonth库存、SKU有没有货、库存数量查询、美国站库存检查、batch库存、westmonth inventory、stock check时触发。即使用户只说"查一下库存"也触发。
---

# 西之月库存查询

查询 westmonth.com 平台上指定 SKU 在美国站（delivery_region_id=3）的具体库存数量。

## API 说明

两步查询，无需登录认证：

1. **搜索 API**：`GET https://api-x.westmonth.com/product-center/shop/products/load-list?indistinct={SKU}&page=1&size=5`
   - 用 SKU 编号模糊搜索，返回 `product_id`
   - 必须用 `indistinct` 参数（不是 `keyword`）

2. **详情 API**：`GET https://api-x.westmonth.com/product-center/shop/products/detail?product_id={product_id}&delivery_region_id=5`
   - 返回 `skus[].delivery_regions` 中的各站点库存
   - `delivery_region_id=3` = 美国站，取 `qty` 字段为库存数量
   - `delivery_region_id=5` = 中国站，`qty=99999` 表示不限量
   - `delivery_region_id=14` = 欧盟站

## 请求头

```
User-Agent: Mozilla/5.0
Accept: application/json
Referer: https://westmonth.com/
```

## 使用指引

1. **单个 SKU 查询**：传入 SKU 编号，脚本自动走两步 API，返回美国站库存数量。
2. **批量 SKU 查询**：传入多个 SKU（逗号分隔或 JSON 数组），逐个查询，结果合并输出。
3. **输出**：JSON 文件（含每个 SKU 的库存数量、状态、产品信息）+ `Saved full response` 协议输出。

### 关键字段

| 字段 | 说明 |
|---|---|
| `sku` | 用户输入的 SKU 编号 |
| `us_stock_qty` | 美国站库存数量（delivery_region_id=3 的 qty） |
| `status` | 有货(qty>0) / 缺货(qty=0) / 未找到 |
| `product_name` | 产品名称 |
| `product_url` | 产品页面链接 |

## 调用方式

```bash
# 单个 SKU
python scripts/check_inventory.py --sku "ZP-A01-0007-01"

# 多个 SKU（逗号分隔）
python scripts/check_inventory.py --sku "ZP-A01-0007-01,EEA01-A072-4-VT1"

# 从文件读取 SKU 列表（每行一个 SKU）
python scripts/check_inventory.py --sku-file /path/to/sku_list.txt
```

## 输出

脚本落盘 JSON 结果到会话目录 `data/` 下，并通过 stdout 输出 `Saved full response: <路径>`。

如需生成 HTML 报告，调用 `linkfox-report-generator` skill，传入 JSON 结果。

## 限制

- API 无需登录，但搜索结果可能因未登录而返回不完整。
- `qty=99999` 是中国站"不限量"标记，非真实库存。
- 每次查询间隔 0.5 秒，避免请求过快。
- 美国站 `delivery_region_id=3` 不存在时标注"无美国站数据"。

## 报告产物

⚠ 生成报告必须先阅读 SKILL `linkfox-report-generator` 并遵循其规范：样式、排版、md/html 导出、元信息块统统由它负责，本 skill 不得复制报告样式或 html 模板。
