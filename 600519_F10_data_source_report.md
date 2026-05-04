# 600519 贵州茅台 · 妙想 F10 数据源调研报告

> **调研时间**：2026-04-27
> **调研页面**：https://aif10.eastmoney.com/pc_extendf10/choicef10.html?code=600519
> **调研范围**：A股 F10 共 14 个一级模块、50+ 个二级子栏目
> **调研方式**：浏览器逐栏目点击 + DevTools Network 抓包

---

## 目录

1. [调研对象与目标](#1-调研对象与目标)
2. [整体架构观察](#2-整体架构观察)
3. [模块字段与接口映射](#3-模块字段与接口映射)
4. [数据更新频率与采集调度](#4-数据更新频率与采集调度)
5. [字段标准化建议](#5-字段标准化建议)
6. [调用示例](#6-调用示例)
7. [风险与限制](#7-风险与限制)
8. [工程化落地方案](#8-工程化落地方案)

---

## 1. 调研对象与目标

**调研页面**

```
https://aif10.eastmoney.com/pc_extendf10/choicef10.html?code=600519
```

**调研目标**

把这个 F10 页面及其全部子栏目作为一个长期可工程化的数据源来评估，为后续做爬取建库、自动化分析提供一份“字段地图 + 接口地图”。

**调研方式**

在 Chrome 中逐个点击 4 个一级菜单组（A股F10 / 三板F10 / 港股F10 / 美股F10）下的 14 个一级模块，及每个一级模块下的 2~13 个二级子栏目，并在每次切换时通过 DevTools Network 抓取后端 XHR/Fetch 请求，记录接口域名、`reportName` 标识、关键过滤参数和返回字段。

---

## 2. 整体架构观察

整个站点是一个嵌套在跨域 `iframe` 中的 SPA：

| 层级 | 域名 | 作用 |
| --- | --- | --- |
| 外层壳 | `aif10.eastmoney.com` | 顶部 4 个 F10 菜单组 |
| 内容渲染 | `emweb.eastmoney.com/PC_HSF10/` | 内层页面与组件 |
| 主数据后端 | `datacenter.eastmoney.com/securities/api/data/v1/get` | 结构化 JSON |
| 资讯/公告/研报 | `np-anotice-pc / np-cnotice-pc / np-creport-pc` | 长文内容 |
| 实时行情 | `push2.eastmoney.com/api/qt/stock/get` | 分钟级行情 |

这意味着对长期数据源建设非常友好：**不需要解析 HTML，只要按 `reportName` 把每张“逻辑表”固定下来，就能稳定取到结构化 JSON**。

接口的统一签名：

```text
https://datacenter.eastmoney.com/securities/api/data/v1/get
  ?reportName=<逻辑表名>
  &columns=<字段列表 或 ALL>
  &filter=(SECUCODE="600519.SH")(...其他过滤)
  &pageNumber=1&pageSize=N
  &sortTypes=...&sortColumns=...
  &source=HSF10&client=PC
```

`SECUCODE` 拼接规则：

| 市场 | 后缀 | 示例 |
| --- | --- | --- |
| 上交所 | `.SH` | `600519.SH`（贵州茅台） |
| 深交所 | `.SZ` | `000858.SZ`（五粮液） |
| 北交所 | `.BJ` | `xxxxxx.BJ` |
| 港交所 | `.HK` | `00700.HK` |

按需替换即可批量复用到全市场任何一只股票。

---

## 3. 模块字段与接口映射

> 表中接口前缀均为 `datacenter.eastmoney.com/securities/api/data/v1/get?reportName=`（除标注 `data/get` 外）。
> 每个模块都附 600519 贵州茅台的实际样例数据，便于直观理解返回结构。

### 3.1 操盘必读

**子栏目 → 接口**

| 子栏目 | 后端 reportName |
| --- | --- |
| 最新指标 | `RPT_PCF10_FINANCEMAINFINADATA`、`RPT_DMSK_NEWINDICATOR` |
| 大事提醒 | `RPT_F10_REMIND_RELATIONSHIP` |
| 估值分析 | `RPT_STOCKVALUATIONTANTILE` |
| 主要指标趋势 | `RPTA_DATA_IF_LINECHART`、`RPTA_DATA_IF_INDICATOR` |
| 股东户数趋势 | `RPT_F10_EH_HOLDERNUM`、`RPT_CUSTOM_DMSK_TREND` |
| 龙虎榜 | `RPT_DAILYBILLBOARD_DETAILSNEW`、`RPT_OPERATEDEPT_TRADE` |
| 大宗交易 | `RPT_DATA_BLOCKTRADE` |
| 融资融券 | `RPT_MARGIN_STATISTICS_STOCKS`、`RPT_STOCK_MARGINTRENDEXPLAIN` |
| 实时行情 | `push2.eastmoney.com/api/qt/stock/get` |

**600519 实际样例（最新指标，2026 一季报）**

| 指标 | 数值 | 指标 | 数值 |
| --- | --- | --- | --- |
| 基本每股收益 | 21.7545 元 | 每股净资产 | 216.3223 元 |
| 稀释每股收益 | 21.7600 元 | 每股未分配利润 | 175.0003 元 |
| 每股经营现金流 | 21.4889 元 | 每股公积金 | 0.0013 元 |
| 总股本 | 12.52 亿股 | 流通股本 | 12.52 亿股 |
| 总市值 | 1.756 万亿元 | 流通市值 | 1.756 万亿元 |
| 市盈率（动） | 16.12 | 市盈率（TTM） | 21.23 |
| 加权 ROE | 10.57% | 毛利率 | 89.76% |
| 资产负债率 | 12.12% | 营业总收入 | 547.0 亿元 |
| 归母净利润 | 272.4 亿元 | 营收同比 | +6.34% |

---

### 3.2 股东研究

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 股东人数 | `RPT_F10_EH_HOLDERNUM` |
| 实控人 | `RPT_F10_EH_RELATION` |
| 报告期列表 | `RPT_F10_EH_HOLDERSDATE`、`RPT_F10_EH_FREEHOLDERSDATE` |
| 十大股东 | `RPT_F10_EH_HOLDERS` |
| 十大流通股东 | `RPT_F10_EH_FREEHOLDERS` |
| 股东持股变动 | `RPT_F10_SHAREHOLDER_CHANGE` |
| 流通股东合计 | `RPT_F10_FREE_TOTALHOLDNUM` |
| 机构持仓概览 | `RPT_F10_MAIN_ORGHOLDDETAILS` |
| 基金持仓明细 | `RPT_MAIN_ORGHOLDDETAIL` |
| 沪深港通持股 | `RPT_MUTUAL_STOCK_HOLDRANKN_NEW`、`RPT_NORTH_ORG_HOLDDETAIL_NEW` |
| 限售解禁 | `RPTA_APP_LIFTFUTURE`、`RPTA_APP_ACCUMDETAILS` |

**600519 实际样例（股东人数趋势）**

| 报告期 | 股东人数(户) | 较上期变化 | 人均流通股 | 股价 | 筹码集中度 |
| --- | --- | --- | --- | --- | --- |
| 2026-03-31 | 24.32 万 | -4.98% | 5150 | 1450.0 | 非常分散 |
| 2025-12-31 | 25.59 万 | +7.29% | 4893 | 1377.18 | 非常分散 |
| 2025-09-30 | 23.85 万 | +8.09% | 5250 | 1419.81 | 非常分散 |
| 2025-06-30 | 22.07 万 | +14.67% | 5692 | 1385.92 | 非常分散 |
| 2025-03-31 | 19.24 万 | -7.44% | 6528 | 1505.36 | 非常分散 |

**600519 实际样例（十大流通股东，2026-03-31）**

| 排名 | 股东名称 | 持股性质 |
| --- | --- | --- |
| 1 | 中国贵州茅台酒厂（集团）有限责任公司 | 国家股 |
| 2 | 香港中央结算有限公司 | 境外法人 |
| 3 | 贵州茅台酒厂集团技术开发公司 | 国有法人 |

> 实际接口字段还包含：`HOLDER_RANK`、`HOLD_NUM`、`FREE_HOLDNUM_RATIO`、`HOLD_NUM_CHANGE`、`CHANGE_RATIO` 等。

---

### 3.3 经营分析

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 主营范围 | `RPT_HSF9_BASIC_ORGINFO` |
| 主营构成 | `RPT_F10_FN_MAINOP` |
| 经营评述 | `RPT_F10_OP_BUSINESSANALYSIS` |

**600519 实际样例（主营构成 2025 年报）**

按产品分类：

| 产品 | 主营收入 | 收入比例 | 主营成本 | 毛利率 |
| --- | --- | --- | --- | --- |
| 茅台酒 | 1465 亿元 | 86.77% | 94.85 亿元 | 93.53% |
| 其他系列酒 | 222.7 亿元 | 13.19% | 53.21 亿元 | 76.11% |

按地区分类：

| 地区 | 主营收入 | 收入比例 | 毛利率 |
| --- | --- | --- | --- |
| 国内 | 1639 亿元 | 97.09% | 91.21% |
| 国外 | 48.50 亿元 | 2.87% | 91.69% |

---

### 3.4 核心题材

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 概念题材 | `RPT_F10_CORETHEME_BOARDTYPE` |
| 题材亮点 | `RPT_F10_CORETHEME_CONTENT` |
| 题材详情 | `RPT_F10_CORETHEME_CONTENT`（KEY_CLASSIF_CODE 全集） |
| 人气龙头 | `RTP_F10_POPULAR_LEADING` |

**600519 实际样例**

精选概念板块：

| 板块名 | 板块涨跌 |
| --- | --- |
| 白酒 | -1.69% |
| 超级品牌 | +0.16% |
| 央国企改革 | -0.57% |
| 电商概念 | -0.41% |
| 西部大开发 | -0.57% |

题材亮点：

- **行业背景**：白酒行业
- **核心竞争力**：产品品质卓越、品牌美誉度高、生产工艺独特、文化辐射力强、环境不可复制

入选理由：茅台历史悠久，是中国白酒的符号象征，多次获得国际和国内大奖，品牌价值位列 2018 年全球50大最具价值烈酒品牌榜首。高端白酒行业集中度高，按销售收入计茅台占比 63% 位列第一。

---

### 3.5 资讯公告

**子栏目 → 接口**

| 子栏目 | 接口 |
| --- | --- |
| 相关资讯 | `emdcnewsapp.eastmoney.com/infoService`（POST） |
| 相关公告列表 | `np-anotice-pc.eastmoney.com/api/security/ann?market_stock_list=1.600519` |
| 公告全文 | `np-cnotice-pc.eastmoney.com/api/content/ann?art_code=...` |
| 资讯/研报全文 | `np-creport-pc.eastmoney.com/api/content/rep?art_code=...` |

**600519 实际样例**

| 日期 | 类型 | 标题 |
| --- | --- | --- |
| 2026-04-25 | 公告 | 贵州茅台 2026 年第一季度报告 |
| 2026-04-25 | 公告 | 贵州茅台 2026 年第一季度主要经营数据公告 |
| 2026-04-17 | 公告 | 贵州茅台关于日常关联交易的公告 |
| 2026-04-27 | 资讯 | 上市公司 2025 年度分红方案一览 |
| 2026-04-27 | 资讯 | 37 股获融资净买入额超 1 亿元 |

---

### 3.6 公司大事

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 大事字典 | `RPT_F10_REMIND_RELATIONSHIP` |
| 限售解禁 | `RPTA_APP_LIFTFUTURE` |
| 股东持股变动 | `RPT_F10_SHAREHOLDER_CHANGE` |
| 高管持股变动 | `RPT_EXECUTIVE_HOLD_DETAILS` |
| 龙虎榜 | `RPT_DAILYBILLBOARD_DETAILSNEW`、`RPT_OPERATEDEPT_TRADE` |
| 大宗交易 | `RPT_DATA_BLOCKTRADE` |
| 融资融券 | `RPT_MARGIN_STATISTICS_STOCKS` |
| 同类事件 | `RTP_F10_ADVANCE_DETAIL_NEW` |

**600519 实际样例（大事提醒事件流）**

| 日期 | 事件类型 | 内容 |
| --- | --- | --- |
| 2026-04-25 | 一季报披露 | 归母净利润 272.4 亿元，同比 +1.47%，EPS 21.76 元 |
| 2026-04-25 | 股东户数 | A 股股东户数 24.32 万户，环比减少 1.27 万户（-4.98%） |
| 2026-04-24 | 沪深港通 | 沪股通成交总额 22.26 亿元 |
| 2026-04-24 | 融资融券 | 融资余额 180.3 亿元，融资净买入 3.987 亿元 |
| 2026-04-22 | 大宗交易 | 成交均价 1409.50 元，溢价 0.00%，成交 1 万股 |
| 2026-04-17 | 年报披露 | 2025 年归母净利润 823.2 亿元，同比 -4.53%，EPS 65.66 元 |
| 2026-04-17 | 分红送转 | 2025 年度分配 10 派 279.93 元（含税） |

---

### 3.7 公司概况

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 基本资料 | `RPT_F10_BASIC_ORGINFO` |
| 发行信息 | `RPT_PCF10_ORG_ISSUEINFO` |
| 发展历程 | `RPT_ORG_COURSECHANGE` |
| 重大重组 | `RPT_ORG_RECAPITALIZE` |
| 参股控股 | `RPT_F10_PUBLIC_OP_HOLDINGORG` |

**600519 实际样例（基本资料）**

| 字段 | 值 |
| --- | --- |
| 公司名称 | 贵州茅台酒股份有限公司 |
| 英文名称 | Kweichow Moutai Co., Ltd. |
| A 股代码 | 600519 |
| A 股简称 | 贵州茅台 |
| 曾用名 | 贵州茅台 → G茅台 |
| 证券类别 | 上交所主板 A 股 |
| 所属东财行业 | 食品饮料-白酒Ⅱ-白酒Ⅲ |
| 上市交易所 | 上海证券交易所 |
| 法人代表 / 董事长 | 陈华 |
| 总经理 | 王莉（代） |
| 董秘 | 余思明（代） |
| 联系电话 | 0851-22386002 |
| 公司网址 | www.moutaichina.com |
| 办公地址 | 贵州省仁怀市茅台镇 |
| 注册资本 | 12.52 亿元 |
| 雇员人数 | 34992 人 |
| 会计事务所 | 天健会计师事务所 |

---

### 3.8 同行比较

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 行业归属 | `RPT_F10_RELATE_GN`（BOARD_TYPE_NEW=2） |
| 成长性比较 | `RPT_PCF10_INDUSTRY_GROWTH` |
| 估值比较 | `RPT_PCF10_INDUSTRY_CVALUE` |
| 杜邦分析比较 | `RPT_PCF10_INDUSTRY_DBFX` |
| 市场表现 | `RPT_PCF10_MARKETPER` |
| 公司规模 | `RPT_PCF10_INDUSTRY_MARKET` |

**600519 实际样例（成长性比较 EPS 增长率，行业排名 9/21）**

| 指标 | 茅台 | 行业平均 | 行业中值 |
| --- | --- | --- | --- |
| 3 年复合 | 9.56 | -11.71 | 5.20 |
| 25A | -4.34 | -28.33 | -29.40 |
| TTM | -6.78 | -38.79 | -23.35 |
| 26E | 8.68 | -17.54 | -16.00 |
| 27E | 5.85 | 71.55 | 12.32 |
| 28E | 1.93 | 2.32 | 4.64 |

**600519 实际样例（估值比较，行业排名 4/21）**

| 指标 | 茅台 | 行业平均 |
| --- | --- | --- |
| PEG | 1.64 | -0.42 |
| PE 25A | 22.19 | 80.33 |
| PE TTM | 22.19 | -26.34 |
| PE 26E | 20.47 | 51.36 |
| PS TTM | 10.62 | 5.24 |

---

### 3.9 盈利预测

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 评级统计 | `RPT_HSF10_RES_ORGRATING` |
| 机构预测 | `RPT_HSF10_RES_ORGPREDICT` |
| 预测均值 | `RPT_HSF10_RESPREDICT_STATISTICS` |
| 预测统计扩展 | `RPT_HSF10_RESPREDICT_COUNTSTATISTICS` |
| 预测明细 | `RPT_HSF10_RES_PREDICTDETAIL` |

**600519 实际样例（评级统计）**

| 时间窗口 | 评级系数 | 综合评级 | 买入 | 增持 | 中性 | 减持 | 卖出 | 总家数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 月内 | 4.91 | 买入 | 30 | 3 | 0 | 0 | 0 | 33 |
| 3 月内 | 4.89 | 买入 | 31 | 4 | 0 | 0 | 0 | 35 |
| 6 月内 | 4.83 | 买入 | 38 | 8 | 0 | 0 | 0 | 46 |
| 1 年内 | 4.80 | 买入 | 43 | 11 | 0 | 0 | 0 | 54 |

**600519 实际样例（机构预测，部分机构）**

| 机构 | 2026E EPS | 2026E PE | 2027E EPS | 2027E PE |
| --- | --- | --- | --- | --- |
| 近六月平均 | 71.01 | 20.47 | 75.15 | 19.34 |
| 方正证券 | 68.63 | 21.25 | 73.25 | 19.91 |
| 中金公司 | 66.93 | 21.79 | 69.66 | 20.94 |
| 国信证券 | 67.38 | 21.64 | 71.40 | 20.43 |
| 华创证券 | 67.63 | 21.57 | 70.65 | 20.64 |

---

### 3.10 研究报告

**子栏目 → 接口**

| 子栏目 | 接口 |
| --- | --- |
| 研报摘要 / 公司研报 / 行业研报 | `np-creport-pc.eastmoney.com/api/content/rep?art_code=...` |

**600519 实际样例（近期研报标题）**

| 日期 | 标题 |
| --- | --- |
| 2026-04-27 | i 茅台大放异彩，2026 年稳健开局 |
| 2026-04-27 | 2026Q1 收入稳健增长，市场化改革成效逐步显现 |
| 2026-04-26 | 改革成效凸显，i 茅台放量激增 |
| 2026-04-26 | 2026 年一季报点评：锐意改革全面 2C，强势开局确立企稳 |
| 2026-04-26 | 业绩符合预期，市场化改革成效斐然 |

---

### 3.11 财务分析

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 主要指标（按报告期） | `RPT_F10_FINANCE_MAINFINADATA`（data/get） |
| 主要指标（按单季） | `RPT_F10_QTR_MAINFINADATA` |
| 杜邦分析 | `RPT_F10_FINANCE_DUPONT` |
| 资产负债表 | `RPT_F10_FINANCE_GBALANCE`（data/get） |
| 利润表（累计） | `RPT_F10_FINANCE_GINCOME` |
| 利润表（单季） | `RPT_F10_FINANCE_GINCOMEQC` |
| 现金流量表（累计） | `RPT_F10_FINANCE_GCASHFLOW` |
| 现金流量表（单季） | `RPT_F10_FINANCE_GCASHFLOWQC` |
| 百分比/同比报表 | `RPT_F10_FINANCE_GRATIO` |
| 公司类型（决定模板） | `RPT_F10_PUBLIC_COMPANYTPYE` |
| 原始财报披露 | `RPT_PCF10_ORIG_REPORT` |

> ⚠️ **关键提示**：财务接口里 `RPT_F10_PUBLIC_COMPANYTPYE` 决定了公司归属的财报模板（一般工商企业 / 银行 / 保险 / 券商）。在长期入库时一定要先按这个字段决定字段集，否则不同模板下字段名差异会很大。茅台对应的是“一般工商企业”模板。

**600519 实际样例（主要指标历史时序）**

| 报告期 | EPS | 每股净资产 | 每股经营现金流 | 营收 | 归母净利润 |
| --- | --- | --- | --- | --- | --- |
| 2026-03-31 | 21.7600 | 216.3223 | 21.4889 | 547.0 亿 | 272.4 亿 |
| 2025-12-31 | 65.6600 | 195.3554 | 49.1285 | 1721 亿 | 823.2 亿 |
| 2025-09-30 | 51.5300 | 205.2831 | 30.5020 | 1309 亿 | 645.0 亿 |
| 2025-06-30 | 36.1800 | 189.9753 | 10.4435 | 910.9 亿 | 452.8 亿 |
| 2025-03-31 | 21.3800 | 205.6665 | 7.0126 | 514.4 亿 | 268.5 亿 |

---

### 3.12 分红融资

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 分红融资概览 | `RPT_F10_DIVIDENDNEW_PROFILE` |
| 分红提示 | `RPT_F10_DIVIDENDNEW_LITY` |
| 分红排名 | `RPT_PCF10_DIVIDENDNEW_RANK` |
| 分红明细 | `RPT_F10_DIVIDEND_MAIN` |
| 分红汇总（按年） | `RPT_F10_DIVIDEND_COMPRE`、`RPT_F10_DIVIDEND_3YEAR` |
| 融资明细 | `RPT_F10_DIVIDEND_SEO` |
| 分红影响 | `RPT_F10_DIVIDEND_CURVE`、`RPT_F10_DIVIDEND_EFFECT` |

**600519 实际样例（分红融资概览）**

| 字段 | 值 |
| --- | --- |
| 股息率 | 3.56% |
| 股利支付率 | 79.00%（行业排名第 3） |
| 派现融资比 | 179.04 倍 |
| 累计派现 | 31 次 / 4018 亿元 |
| 累计融资 | 1 次 / 22.44 亿元（仅首发） |
| 潜在派现概率 | 中 |
| 近 5 年派现 | 9 次 |
| 2025 年报每股派现 | 27.993 元（含税） |

---

### 3.13 股本结构

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 限售解禁 | `RPTA_APP_LIFTFUTURE` |
| 股本结构 | `RPT_F10_EH_EQUITY` |
| 历年股本变动 | `RPT_F10_EH_EQUITY` 全量 |
| 股本构成 | `RPT_F10_EH_EQUITY` |

**600519 实际样例（股本结构）**

股份流通受限表：

| 项目 | 数值（万股） | 占比 |
| --- | --- | --- |
| 未流通股份 | 0 | 0.00% |
| 流通受限股份 | 0 | 0.00% |
| 已流通股份 | 125,227.02 | 100.00% |
| **总股本** | **125,227.02** | **100.00%** |

流通股份分布：

| 项目 | 数值（万股） | 占比 |
| --- | --- | --- |
| 已上市流通 A 股 | 125,227.02 | 100.00% |
| 已上市流通 B 股 | 0 | 0.00% |
| 境外上市流通股 | 0 | 0.00% |

---

### 3.14 公司高管

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 高管列表 | `RPT_F10_ORGINFO_MANAINTRO` |
| 高管持股变动 | `RPT_F10_TRADE_EXCHANGEHOLD` |
| 管理层简介 | `RPT_F10_ORGINFO_MANAINTRO`（columns=ALL） |

**600519 实际样例（高管列表，2025-12-31 报告期）**

| 序号 | 姓名 | 性别 | 年龄 | 学历 | 薪酬 | 职务 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 陈华 | 男 | 54 | 硕士 | -- | 董事长、法定代表人、董事 |
| 2 | 王莉 | 女 | 54 | 硕士 | -- | 代理总经理、董事 |
| 3 | 钟正强 | 男 | 55 | 本科 | 113.8 万 | 副总经理 |
| 4 | 向平 | 男 | 54 | 硕士 | 62.89 万 | 副总经理 |
| 5 | 张旭 | 男 | 52 | 本科 | 57.44 万 | 副总经理 |
| 6 | 周雪 | 女 | 48 | 本科 | -- | 董事 |
| 7 | 韦芳 | 女 | 54 | 本科 | 89.80 万 | 职工董事 |
| 8 | 余思明 | 男 | 50 | 本科 | -- | 代理董事会秘书、财务总监 |
| 9 | 郭田勇 | 男 | 58 | 博士 | 20.00 万 | 独立董事 |
| 10 | 盛雷鸣 | 男 | 56 | 博士 | 20.00 万 | 独立董事 |
| 11 | 王鴑 | 男 | 49 | 博士 | 20.00 万 | 独立董事 |

**600519 实际样例（高管及相关人员持股变动）**

| 日期 | 变动人 | 变动数量 | 交易均价 | 结存股票 | 交易方式 | 与高管关系 |
| --- | --- | --- | --- | --- | --- | --- |
| 2018-09-26 | 万波 | -700 | 725.9 元 | 0 | 二级市场买卖 | 本人 |
| 2017-12-28 | 万波 | +700 | 689.0 元 | 700 | 二级市场买卖 | 本人 |

---

### 3.15 资本运作

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 募集资金来源 | `RPT_F10_CAPITAL_RAISE` |
| 项目进度 | `RPT_F10_CAPITAL_ITEM` |

**600519 实际样例（募集资金来源）**

| 公告日期 | 发行类别 | 实际募资净额 |
| --- | --- | --- |
| 2001-07-26 | 首发新股 | 220,217.45 万元（22.44 亿元） |

**600519 实际样例（项目进度节选）**

| 项目名称 | 公告日期 | 计划投资（万元） | 已投入（万元） | 建设期（年） | 收益率 | 回收期（年） |
| --- | --- | --- | --- | --- | --- | --- |
| 一、二包装生产线技改工程 | 2013-08-31 | 19,930 | 19,929.84 | 2.00 | -- | -- |
| 中低度茅台酒改扩建工程 | 2013-08-31 | 13,776 | 13,776.00 | 2.00 | 36.40% | 4.75 |
| 1000 吨茅台酒技改工程 | 2013-08-31 | 27,268 | 28,664.33 | 1.00 | 28.70% | 5.25 |
| 700 吨茅台酒扩建工程 | 2013-08-31 | 9,430 | 9,620.56 | 3.00 | 14.00% | 10.00 |
| 老区茅台酒必扩建工程 | 2013-08-31 | 9,986 | 10,083.22 | 3.00 | 14.30% | 9.75 |

---

### 3.16 关联个股

**子栏目 → 接口**

| 子栏目 | reportName |
| --- | --- |
| 行业归属 | `RPT_F10_RELATE_GN`（BOARD_TYPE_NEW=2） |
| 同行业排名 | `RPT_F10_RELATE_RANK` |
| 区间涨跌幅榜 | `RPT_F10_RELATE_RANK`（按 Change3/6/12） |
| 同概念排名 | `RPT_F10_RELATE_RANK`（BOARD_TYPE_NEW=3） |
| 同地域排名 | `RPT_F10_RELATE_RANK`（BOARD_TYPE_NEW=4） |

**600519 实际样例（同行业个股排名，白酒Ⅱ）**

| 序号 | 代码 | 名称 | 总市值 | 营收 | 归母净利 | 营收同比 | 归母同比 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 600519 | 贵州茅台 | 1.826 万亿 | 547.0 亿 | 272.4 亿 | +6.34% | +1.47% |
| 2 | 000858 | 五粮液 | 3931 亿 | -- | -- | -- | -- |
| 3 | 600809 | 山西汾酒 | 1732 亿 | -- | -- | -- | -- |
| 4 | 000568 | 泸州老窖 | 1511 亿 | -- | -- | -- | -- |
| 5 | 002304 | 洋河股份 | 751.3 亿 | -- | -- | -- | -- |
| 6 | 000596 | 古井贡酒 | 578.8 亿 | -- | -- | -- | -- |
| 7 | 603369 | 今世缘 | 332.3 亿 | -- | -- | -- | -- |

**600519 实际样例（区间涨幅榜）**

| 周期 | 代码 | 名称 | 涨跌幅 |
| --- | --- | --- | --- |
| 3 日 | 600696 | *ST 岩石 | +15.97% |
| 3 日 | 603198 | 迎驾贡酒 | +13.08% |
| 6 日 | 600696 | *ST 岩石 | +33.98% |
| 12 日 | 603198 | 迎驾贡酒 | +11.44% |

---

## 4. 数据更新频率与采集调度

| 频率桶 | 涉及模块 | 调度建议 |
| --- | --- | --- |
| 实时（分钟级） | 行情、市值/涨跌、概念板块涨跌、同行排名涨跌 | 交易日 9:25–15:05 每 1–5 分钟 |
| 日级 | 龙虎榜、大宗交易、融资融券、沪深港通、研报/资讯/公告增量、大事提醒、估值分位、人气龙头 | 每日盘后 17:00 一次 |
| 周级 | 机构评级统计、研报评级聚合、十大股东持股变动 | 每周一次 |
| 季度（事件驱动） | 财务三大表、主要财务指标、杜邦、主营构成、十大股东、机构持仓、股东人数、单季 EPS/营收 | 业绩披露窗口前后每日轮询，命中后入库；常规期每周校对 |
| 半年/年 | 分红方案、融资明细、限售解禁计划、高管列表、管理层简介 | 每月一次扫描 |
| 缓变 | 公司基本资料、发展历程、参股控股、经营范围、所属行业 | 每月或每季度刷新 |
| 一次性 | IPO 信息、首发募资项目进度 | 入库一次后增量监控 |

---

## 5. 字段标准化建议

**5.1 主键标准**

所有接口都把 `SECUCODE="600519.SH"` 当作主键过滤。建议在数据库的标的主表里同时保留：

- `secucode`（带后缀，如 `600519.SH`）
- `security_code`（不带后缀，如 `600519`）

所有事实表用 `secucode` 做外键。

**5.2 报告期型数据**

财务、股东、机构持仓、主营构成等，都遵循 `(SECUCODE, REPORT_DATE / END_DATE)` 联合唯一键，且服务端会保留约 8 期历史。**要做长期序列必须每期采集后做累积入库，而不是覆盖式快照**。

**5.3 事件型数据**

公告、龙虎榜、大宗、融券、限售解禁、分红除权等，都带原始公告日期或交易日期。唯一键建议：

```
(SECUCODE, NOTICE_DATE / TRADE_DATE, [事件子类型])
```

**5.4 财务模板差异**

`RPT_F10_PUBLIC_COMPANYTPYE` 决定财报模板：

| 模板 | 说明 |
| --- | --- |
| 一般工商企业 | 茅台属于此类 |
| 银行 | 字段大量调整 |
| 保险 | 含承保/精算特有科目 |
| 券商 | 含经纪/投行特有科目 |

**5.5 机构持仓枚举**

`RPT_F10_MAIN_ORGHOLDDETAILS` 的 `ORG_TYPE`：

| ORG_TYPE | 含义 |
| --- | --- |
| 00 | 汇总 |
| 01 | 基金 |
| 02 | QFII |
| 03 | 社保 |
| 04 | 券商 |
| 05 | 保险 |
| 06 | 信托 |

**5.6 板块/行业类接口**

通过 `BOARD_CODE` 做关联（茅台对应 1277 白酒Ⅲ）。`BOARD_TYPE_NEW`：

| BOARD_TYPE_NEW | 含义 |
| --- | --- |
| 1 | 指数 |
| 2 | 行业 |
| 3 | 概念 |
| 4 | 地域 |

是切换“同行 / 同概念 / 同地域”三张表的开关。

---

## 6. 调用示例

**示例 1 · 最新指标**

```http
GET https://datacenter.eastmoney.com/securities/api/data/v1/get
    ?reportName=RPT_PCF10_FINANCEMAINFINADATA
    &columns=ALL
    &filter=(SECUCODE="600519.SH")
    &pageNumber=1&pageSize=1
    &sortTypes=-1&sortColumns=REPORT_DATE
    &source=HSF10&client=PC
```

返回：最新一期主要财务指标的全字段，含 EPS、净资产、市值、PE、ROE、毛利率、资产负债率等。

**示例 2 · 财务主指标历史时序**

```http
GET https://datacenter.eastmoney.com/securities/api/data/get
    ?type=RPT_F10_FINANCE_MAINFINADATA
    &sty=APP_F10_MAINFINADATA
    &filter=(SECUCODE="600519.SH")
    &p=1&ps=200
    &sr=-1&st=REPORT_DATE
    &source=HSF10&client=PC
```

**示例 3 · 十大流通股东**

```http
GET https://datacenter.eastmoney.com/securities/api/data/v1/get
    ?reportName=RPT_F10_EH_FREEHOLDERS
    &columns=ALL
    &filter=(SECUCODE="600519.SH")(END_DATE='2026-03-31')
    &sortTypes=1&sortColumns=HOLDER_RANK
    &source=HSF10&client=PC
```

**示例 4 · 分红明细**

```http
GET https://datacenter.eastmoney.com/securities/api/data/v1/get
    ?reportName=RPT_F10_DIVIDEND_MAIN
    &columns=ALL
    &filter=(SECUCODE="600519.SH")
    &pageNumber=1&pageSize=10
    &sortTypes=-1&sortColumns=NOTICE_DATE
    &source=HSF10&client=PC
```

**示例 5 · 实时行情**

```http
GET https://push2.eastmoney.com/api/qt/stock/get
    ?secid=1.600519
    &fields=f57,f58,f43,f44,f45,f46,f48,f60,f168,f169,f170,f171
    &fltt=2
```

字段含义（部分）：`f43` 最新价、`f44` 最高、`f45` 最低、`f46` 开盘、`f60` 昨收、`f168` 换手率、`f169` 涨跌额、`f170` 涨跌幅、`f171` 振幅。

---

## 7. 风险与限制

这是东财对内 F10 的内部接口，没有公开 SLA。长期采集时建议遵循三个工程原则：

**7.1 限速**

合理控制并发，建议：

- 单 IP 不超过 2 QPS
- 夜间批量取数（22:00 之后）
- 加上 `Referer: https://emweb.eastmoney.com/` 和正常 UA 以兼容反爬

**7.2 重试与幂等**

每次响应里都有 `success / code / data` 包裹结构。做成可重试的幂等抓取，遇到非 200 或空数组时退避重试（建议指数退避：1s / 2s / 4s / 8s）。

**7.3 Schema 校验**

接口的 `reportName` 偶有迭代（v0 `data/get` 和 v1 `data/v1/get` 共存就是历史演进的痕迹）。上线前给每张逻辑表配一份 schema 校验，发现字段缺失/新增时告警。

---

## 8. 工程化落地方案

如果直接做成数据仓库，建议的 6 张主题域即可覆盖 95% 的分析需求：

| 主题域 | 说明 | 来源模块 |
| --- | --- | --- |
| `stock_master` | 公司主数据：基本资料、发展历程、参股控股 | 模块 7 |
| `fin_period` | 财务期次：三大表、主要指标、杜邦、主营构成 | 模块 11 + 3 |
| `shareholder_period` | 股东期次：十大股东、机构持仓、户数、沪深港通 | 模块 2 |
| `event_log` | 事件流：公告、龙虎、大宗、融券、解禁、分红、高管变动 | 模块 5/6/12/14 |
| `peer_snapshot` | 同行/估值/成长/杜邦/规模日级快照 | 模块 8/16 |
| `forecast` | 评级与机构预测、研报 | 模块 9/10 |

再外加一张 `realtime_quote` 走 `push2.eastmoney.com` 接口取分钟级行情，整套 F10 的能力就被完整地数据化了。

**建议的表结构骨架（以 `fin_period` 为例）**

```sql
CREATE TABLE fin_period (
    secucode        VARCHAR(12)  NOT NULL,    -- 600519.SH
    security_code   VARCHAR(8)   NOT NULL,    -- 600519
    report_date     DATE         NOT NULL,    -- 2026-03-31
    report_type     VARCHAR(16)  NOT NULL,    -- 一季报 / 中报 / 三季报 / 年报
    company_type    VARCHAR(16)  NOT NULL,    -- 一般 / 银行 / 保险 / 券商
    eps             DECIMAL(20,4),
    bps             DECIMAL(20,4),
    revenue         DECIMAL(20,2),
    net_profit      DECIMAL(20,2),
    raw_payload     JSON,                     -- 原始接口响应留底
    fetched_at      TIMESTAMP    NOT NULL,
    PRIMARY KEY (secucode, report_date, report_type)
);
```

**采集任务编排**

```
调度器（Airflow / XXL-Job / cron）
  ├─ realtime_quote_minute       每 1 分钟（交易时段）
  ├─ event_log_daily              每日 17:00
  ├─ peer_snapshot_daily          每日 18:00
  ├─ shareholder_period_weekly    每周一 02:00
  ├─ fin_period_quarter_watch     业绩披露窗口每日 06:00
  ├─ forecast_weekly              每周二 03:00
  └─ stock_master_monthly         每月 1 日 04:00
```

---

## 附录 A：本次调研已抓取的接口完整清单

| reportName | 模块 | 用途 |
| --- | --- | --- |
| `RPT_PCF10_FINANCEMAINFINADATA` | 操盘必读 | 最新主要财务指标 |
| `RPT_DMSK_NEWINDICATOR` | 操盘必读 | PE 动/静解释 |
| `RPT_STOCKVALUATIONTANTILE` | 操盘必读 | 估值分位 |
| `RPTA_DATA_IF_LINECHART` | 操盘必读 | 指标趋势线 |
| `RPTA_DATA_IF_INDICATOR` | 操盘必读 | 指标元数据 |
| `RPT_CUSTOM_DMSK_TREND` | 操盘必读 | 自定义趋势 |
| `RPT_DAILYBILLBOARD_DETAILSNEW` | 操盘必读 / 公司大事 | 龙虎榜日明细 |
| `RPT_OPERATEDEPT_TRADE` | 操盘必读 / 公司大事 | 营业部买卖 |
| `RPT_DATA_BLOCKTRADE` | 操盘必读 / 公司大事 | 大宗交易 |
| `RPT_MARGIN_STATISTICS_STOCKS` | 操盘必读 / 公司大事 | 融资融券 |
| `RPT_STOCK_MARGINTRENDEXPLAIN` | 操盘必读 | 融券趋势解释 |
| `RPT_F10_EH_HOLDERNUM` | 股东研究 | 股东人数 |
| `RPT_F10_EH_RELATION` | 股东研究 | 实控人 |
| `RPT_F10_EH_HOLDERSDATE` | 股东研究 | 报告期列表（十大） |
| `RPT_F10_EH_FREEHOLDERSDATE` | 股东研究 | 报告期列表（流通） |
| `RPT_F10_EH_HOLDERS` | 股东研究 | 十大股东 |
| `RPT_F10_EH_FREEHOLDERS` | 股东研究 | 十大流通股东 |
| `RPT_F10_SHAREHOLDER_CHANGE` | 股东研究 / 公司大事 | 股东变动 |
| `RPT_F10_FREE_TOTALHOLDNUM` | 股东研究 | 流通股东合计 |
| `RPT_F10_MAIN_ORGHOLDDETAILS` | 股东研究 | 机构持仓概览 |
| `RPT_MAIN_ORGHOLDDETAIL` | 股东研究 | 基金/机构持仓明细 |
| `RPT_MUTUAL_STOCK_HOLDRANKN_NEW` | 股东研究 | 沪深港通持股 |
| `RPT_NORTH_ORG_HOLDDETAIL_NEW` | 股东研究 | 北向机构明细 |
| `RPTA_APP_LIFTFUTURE` | 股东 / 大事 / 股本 | 限售解禁 |
| `RPTA_APP_ACCUMDETAILS` | 公司大事 | 持有人解禁明细 |
| `RPT_HSF9_BASIC_ORGINFO` | 经营分析 | 经营范围 |
| `RPT_F10_FN_MAINOP` | 经营分析 | 主营构成 |
| `RPT_F10_OP_BUSINESSANALYSIS` | 经营分析 | 经营评述 |
| `RPT_F10_CORETHEME_BOARDTYPE` | 核心题材 | 概念板块 |
| `RPT_F10_CORETHEME_CONTENT` | 核心题材 | 题材要点 |
| `RTP_F10_POPULAR_LEADING` | 核心题材 | 板块龙头 |
| `RPT_F10_REMIND_RELATIONSHIP` | 公司大事 | 事件分类字典 |
| `RPT_EXECUTIVE_HOLD_DETAILS` | 公司大事 | 高管持股变动 |
| `RTP_F10_ADVANCE_DETAIL_NEW` | 公司大事 | 同类事件扩展 |
| `RPT_F10_BASIC_ORGINFO` | 公司概况 | 基本资料 |
| `RPT_PCF10_ORG_ISSUEINFO` | 公司概况 | 发行信息 |
| `RPT_ORG_COURSECHANGE` | 公司概况 | 发展历程 |
| `RPT_ORG_RECAPITALIZE` | 公司概况 | 重大重组 |
| `RPT_F10_PUBLIC_OP_HOLDINGORG` | 公司概况 | 参股控股 |
| `RPT_F10_RELATE_GN` | 同行 / 关联 | 板块归属 |
| `RPT_PCF10_INDUSTRY_GROWTH` | 同行比较 | 成长性比较 |
| `RPT_PCF10_INDUSTRY_CVALUE` | 同行比较 | 估值比较 |
| `RPT_PCF10_INDUSTRY_DBFX` | 同行比较 | 杜邦比较 |
| `RPT_PCF10_MARKETPER` | 同行比较 | 市场表现 |
| `RPT_PCF10_INDUSTRY_MARKET` | 同行比较 | 公司规模排名 |
| `RPT_HSF10_RES_ORGRATING` | 盈利预测 | 评级统计 |
| `RPT_HSF10_RES_ORGPREDICT` | 盈利预测 | 机构预测 |
| `RPT_HSF10_RESPREDICT_STATISTICS` | 盈利预测 | 预测均值 |
| `RPT_HSF10_RESPREDICT_COUNTSTATISTICS` | 盈利预测 | 预测扩展统计 |
| `RPT_HSF10_RES_PREDICTDETAIL` | 盈利预测 | 预测明细 |
| `RPT_F10_PUBLIC_COMPANYTPYE` | 财务分析 | 公司类型/模板 |
| `RPT_F10_FINANCE_DUPONT` | 财务分析 | 杜邦分析 |
| `RPT_F10_FINANCE_GBALANCE` | 财务分析 | 资产负债表 |
| `RPT_F10_FINANCE_GINCOME` | 财务分析 | 利润表（累计） |
| `RPT_F10_FINANCE_GINCOMEQC` | 财务分析 | 利润表（单季） |
| `RPT_F10_FINANCE_GCASHFLOW` | 财务分析 | 现金流量表（累计） |
| `RPT_F10_FINANCE_GCASHFLOWQC` | 财务分析 | 现金流量表（单季） |
| `RPT_F10_FINANCE_GRATIO` | 财务分析 | 百分比/同比报表 |
| `RPT_F10_FINANCE_MAINFINADATA` | 财务分析 | 主要指标（按报告期） |
| `RPT_F10_QTR_MAINFINADATA` | 财务分析 | 主要指标（按单季） |
| `RPT_PCF10_ORIG_REPORT` | 财务分析 | 原始财报披露 |
| `RPT_F10_DIVIDENDNEW_PROFILE` | 分红融资 | 分红融资概览 |
| `RPT_F10_DIVIDENDNEW_LITY` | 分红融资 | 派现概率 |
| `RPT_PCF10_DIVIDENDNEW_RANK` | 分红融资 | 分红排名 |
| `RPT_F10_DIVIDEND_MAIN` | 分红融资 | 分红明细 |
| `RPT_F10_DIVIDEND_COMPRE` | 分红融资 | 分红汇总 |
| `RPT_F10_DIVIDEND_3YEAR` | 分红融资 | 近 3 年分红 |
| `RPT_F10_DIVIDEND_SEO` | 分红融资 | 增发/配股明细 |
| `RPT_F10_DIVIDEND_CURVE` | 分红融资 | 分红曲线 |
| `RPT_F10_DIVIDEND_EFFECT` | 分红融资 | 分红影响 |
| `RPT_F10_EH_EQUITY` | 股本结构 | 股本结构与历年变动 |
| `RPT_F10_ORGINFO_MANAINTRO` | 公司高管 | 高管列表与简介 |
| `RPT_F10_TRADE_EXCHANGEHOLD` | 公司高管 | 高管持股变动 |
| `RPT_F10_CAPITAL_RAISE` | 资本运作 | 募集资金来源 |
| `RPT_F10_CAPITAL_ITEM` | 资本运作 | 募集项目进度 |
| `RPT_F10_RELATE_RANK` | 关联个股 | 同行/同概念/同地域排名 |

---

> **报告结束**
>
> 本报告基于 2026-04-27 抓取，接口路径与字段命名以东方财富妙想 F10 当时实际响应为准。后续若发现 `reportName` 变更或字段调整，请以最新接口响应为准更新本文档。
