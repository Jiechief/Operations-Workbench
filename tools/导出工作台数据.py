# -*- coding: utf-8 -*-
"""从后台导出的 Excel 重新生成 ops-data.js（可提交进 git 的数据管线）。

用法：
  python tools/导出工作台数据.py "D:\\下载\\截至11.24数据.xlsx"
  python tools/导出工作台数据.py 输入.xlsx 自定义输出.js

做的事：
  1. 自动定位表头行（容忍后台导出前面多几行标题）
  2. 逐格原值导出（不四舍五入），空值 null，日期转 YYYYMMDD 整数
  3. 剔除汇总行、按 admin_mbr_id 去重，并在文件里记录剔除了什么
  4. 写入 meta.nonnull / meta.numSum，供页面「校验数值合计」与自检使用
"""
import json
import os
import re
import sys
import datetime
def load_ws(path):
    from openpyxl import load_workbook
    wb = load_workbook(path, data_only=True)
    names = wb.sheetnames
    best = None
    for nm in names:
        ws = wb[nm]
        if ws.max_row >= 5 and ws.max_column >= 20:
            best = ws
            break
    if best is None:
        raise SystemExit("没找到像样的数据工作表，sheet=" + str(names))
    return best, names[0] if not best.title else best.title


INTS = set([9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
            30, 32, 34, 36, 38, 40, 43, 44, 45, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71,
            72, 73, 74, 75, 76, 78, 80, 81, 84, 85, 87, 88, 89, 91, 94, 95])
RATIO = set([31, 33, 35, 37, 39, 41, 42, 77, 79, 82])
NUM = set([83, 86, 90, 92, 93])
MONEY = set([96, 97, 98])
GROUPS = [
    (1, 3, "基础"), (4, 7, "行业"), (8, 10, "服务"), (11, 20, "优爆品"),
    (21, 29, "商品结构"), (30, 41, "P4P推广"), (42, 45, "商品结构"),
    (46, 60, "组织归属"), (61, 75, "不满足原因"), (76, 79, "历史对比"),
    (80, 82, "P4P推广"), (83, 95, "行业基准"), (96, 98, "P4P推广"),
]
SHOW = [2, 3, 4, 10, 11, 12, 13, 14, 15, 21, 27, 29, 51, 96]
SUMS = ["合计", "总计", "小计", "汇总", "平均", "均值"]


def group_of(i):
    for lo, hi, g in GROUPS:
        if lo <= i <= hi:
            return g
    return "其他"


def type_of(i, label, vals):
    if i in INTS or i in RATIO or i in NUM or i in MONEY:
        pass
    if i == 8:
        return "date"
    if i == 3:
        return "yn"
    if i == 10:
        return "rank"
    if i in RATIO:
        return "ratio"
    if i in MONEY:
        return "money"
    if i in NUM:
        return "num"
    nonnull = [v for v in vals if v is not None]
    if nonnull and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in nonnull):
        if all(0 <= v <= 1 for v in nonnull):
            return "ratio"
        return "int"
    return "text"


def main(src, out):
    ws, sheet = load_ws(src)
    hdr = 0
    for r in range(1, min(ws.max_row, 9) + 1):
        line = "|".join("" if ws.cell(r, c).value is None else str(ws.cell(r, c).value)
                        for c in range(1, min(ws.max_column, 40) + 1))
        if "公司名称" in line or "admin_mbr_id" in line:
            hdr = r
            break
    ncol = ws.max_column
    headers = []
    for c in range(1, ncol + 1):
        v = ws.cell(hdr, c).value
        headers.append(str(v).strip() if v not in (None, "") else ("第%d列" % c))
    rows = []
    for r in range(hdr + 1, ws.max_row + 1):
        line = []
        any_v = False
        for c in range(1, ncol + 1):
            v = ws.cell(r, c).value
            if isinstance(v, (datetime.datetime, datetime.date)):
                v = int(v.strftime("%Y%m%d"))
            if v is None or (isinstance(v, str) and v.strip() == ""):
                line.append(None)
            else:
                line.append(v)
                any_v = True
        if any_v:
            rows.append(line)
    ni, ii = headers.index("公司名称") if "公司名称" in headers else 1, \
             headers.index("admin_mbr_id") if "admin_mbr_id" in headers else 0
    kept, seen, dup, cut = [], {}, [], 0
    for line in rows:
        nm = "" if line[ni] is None else str(line[ni])
        idv = "" if line[ii] is None else str(line[ii])
        if any(w in nm or w in idv for w in SUMS) or re.match(r"^[\d.,%]+$", nm or ""):
            cut += 1
            continue
        pk = idv or nm
        if not pk:
            cut += 1
            continue
        if pk in seen:
            dup.append(nm or pk)
            continue
        seen[pk] = 1
        kept.append(line)
    nonnull, numsum = [], []
    for c in range(1, ncol + 1):
        k, s = 0, 0.0
        for line in kept:
            v = line[c - 1]
            if v is not None:
                k += 1
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    s += v
        nonnull.append(k)
        t = type_of(c, headers[c - 1], [line[c - 1] for line in kept])
        numsum.append(round(s, 6) if (k and t in ("int", "num", "ratio", "money")) else None)
    cols = [{"i": c, "key": headers[c - 1], "label": headers[c - 1],
             "type": type_of(c, headers[c - 1], [line[c - 1] for line in kept]),
             "group": group_of(c), "show": c in SHOW} for c in range(1, ncol + 1)]
    m = re.search(r"(\d{1,2}\.\d{1,2})", os.path.basename(src))
    meta = {"source": os.path.basename(src), "sheet": sheet,
            "asOf": (m.group(1) if m else ""), "rows": len(kept), "cols": ncol,
            "generatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "generator": "tools 导出工作台数据.py（openpyxl 逐格原值）",
            "nonnull": nonnull, "numSum": numsum,
            "skipped": {"sum": cut, "dup": dup[:20], "empty": 0}, "hdrRow": hdr}
    js = ("/* 由 %s 生成，值逐格原样保留；请勿手改。 */\nwindow.OPS_DATA = %s;\n"
          % (os.path.basename(src), json.dumps({"meta": meta, "cols": cols, "rows": kept},
                                               ensure_ascii=False, separators=(",", ":"), allow_nan=False)))
    with open(out, "w", encoding="utf-8") as f:
        f.write(js)
    print("OK %s -> %s" % (os.path.basename(src), out))
    print("rows=%d cols=%d asOf=%s skipped=%d dup=%d bytes=%d"
          % (len(kept), ncol, meta["asOf"], cut, len(dup), os.path.getsize(out)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "ops-data.js"))
