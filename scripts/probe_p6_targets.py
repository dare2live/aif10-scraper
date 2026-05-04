"""P6 迁移目标实测 — 跑一遍所有计划用妙想替代 datacenter-web 的 reportName + 5 个独家.

用茅台 600519.SH 为基准, 报告每个接口的:
- 状态 (200 / 0 行 / 失败)
- 实际行数
- 耗时
- 字段清单 (前 10 列)
- 样本第一行

输出 JSON: docs/p6_probe_<date>.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from aif10_scraper import AIF10Client


SECUCODE = "600519.SH"


# (capability_name, reportName, kwargs_overrides)
# kwargs: secucode 默认=600519.SH, page_size 默认=10
PROBES = [
    # ===== P6 迁移: 替代 datacenter-web 直连的 =====
    ("十大流通股东 (原 datacenter-web RPT_F10_EH_FREEHOLDERS)", "RPT_F10_EH_FREEHOLDERS", {}),
    ("龙虎榜 (原 datacenter-web RPT_DAILYBILLBOARD_*)", "RPT_DAILYBILLBOARD_DETAILSNEW", {}),
    ("龙虎榜营业部", "RPT_OPERATEDEPT_TRADE", {}),
    ("大宗交易", "RPT_DATA_BLOCKTRADE", {}),
    ("融资融券 (原 datacenter-web RPT_MARGIN_*)", "RPT_MARGIN_STATISTICS_STOCKS", {}),
    ("融券趋势解释", "RPT_STOCK_MARGINTRENDEXPLAIN", {}),
    ("机构持仓 ORG_TYPE 分桶 (含 QFII=02)", "RPT_F10_MAIN_ORGHOLDDETAILS", {}),
    ("QFII 持仓 (特殊报表)", "RPT_DMSK_HOLDERS", {}),
    ("机构调研 (特殊报表)", "RPT_ORG_SURVEYNEW", {}),

    # ===== 妙想独家 (tdxhub 没的) =====
    ("股东人数趋势 ⭐", "RPT_F10_EH_HOLDERNUM", {}),
    ("估值分位 ⭐ (PE/PB/PS PEG 历史分位)", "RPT_STOCKVALUATIONTANTILE", {}),
    ("同行估值排名", "RPT_PCF10_INDUSTRY_CVALUE", {}),
    ("同行成长排名", "RPT_PCF10_INDUSTRY_GROWTH", {}),
    ("一致预期/评级", "RPT_HSF10_RES_ORGRATING", {}),

    # ===== 项目主用 (P2 待接通) =====
    ("十大股东 (持股变动)", "RPT_F10_EH_HOLDERS", {}),
    ("机构持仓明细 (按机构)", "RPT_MAIN_ORGHOLDDETAIL", {}),
    ("沪深港通持股", "RPT_MUTUAL_STOCK_HOLDRANKN_NEW", {}),
    ("主营构成", "RPT_F10_FN_MAINOP", {}),
    ("基本资料", "RPT_F10_BASIC_ORGINFO", {}),
    ("公司类型", "RPT_F10_PUBLIC_COMPANYTPYE", {}),
]


def probe_one(client: AIF10Client, label: str, report_name: str, kwargs: dict) -> dict:
    """单 reportName 探测."""
    secucode = kwargs.get("secucode", SECUCODE)
    page_size = kwargs.get("page_size", 10)

    t0 = time.time()
    try:
        result = client.get_v1(
            report_name,
            page=1,
            page_size=page_size,
            secucode=secucode,
        )
        elapsed = time.time() - t0
        data = result.get("data") or []
        pages = result.get("pages") or 0
        total = result.get("count") or 0

        sample = {}
        cols = []
        if data:
            first_row = data[0]
            cols = list(first_row.keys())
            # 取前 8 个字段做 sample (避免过长)
            sample = {k: first_row[k] for k in cols[:8]}

        return {
            "label": label,
            "report_name": report_name,
            "status": "ok" if data else "empty",
            "elapsed_s": round(elapsed, 2),
            "rows": len(data),
            "total_pages": pages,
            "total_count": total,
            "n_cols": len(cols),
            "cols_first_15": cols[:15],
            "sample_row": sample,
        }
    except Exception as exc:
        return {
            "label": label,
            "report_name": report_name,
            "status": "fail",
            "elapsed_s": round(time.time() - t0, 2),
            "error": f"{type(exc).__name__}: {str(exc)[:200]}",
        }


def main():
    print(f"=== P6 迁移目标实测 — secucode={SECUCODE} ===")
    print(f"  共 {len(PROBES)} 个 reportName")
    print()

    client = AIF10Client(retry=2, timeout=10.0)
    results = []
    for i, (label, report_name, kwargs) in enumerate(PROBES, 1):
        print(f"  [{i:>2}/{len(PROBES)}] {label[:50]:50s}", end=" ", flush=True)
        r = probe_one(client, label, report_name, kwargs)
        icon = {"ok": "✓", "empty": "○", "fail": "✗"}[r["status"]]
        if r["status"] == "ok":
            print(f"{icon} {r['rows']:>3} rows / {r['n_cols']:>3} cols / {r['elapsed_s']:.2f}s / total={r['total_count']}")
        elif r["status"] == "empty":
            print(f"{icon} 空 / {r['elapsed_s']:.2f}s")
        else:
            print(f"{icon} {r.get('error','?')[:80]}")
        results.append(r)
    client.close()

    # 汇总
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_empty = sum(1 for r in results if r["status"] == "empty")
    n_fail = sum(1 for r in results if r["status"] == "fail")
    print()
    print(f"=== 汇总: {n_ok} ok / {n_empty} empty / {n_fail} fail ===")

    # 写 JSON
    out = ROOT / "docs" / "p6_probe.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"secucode": SECUCODE, "results": results,
                    "summary": {"ok": n_ok, "empty": n_empty, "fail": n_fail}},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  详细报告: {out}")


if __name__ == "__main__":
    main()
