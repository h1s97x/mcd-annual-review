#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦当劳 MCP 数据拉取脚本（mcd-order-report Skill 的数据源）。

拉取 order-list / query-my-coupons / campaign-calendar / list-nutrition-foods，
归一化为 orders.json 供 generate_report.py 使用。

Token 从环境变量 MCD_MCP_TOKEN 读取（不硬编码，避免泄露）。
麦当劳 MCP 返回的是「说明文字 + 内嵌 JSON/表格」，本脚本负责把真实结构解析出来。

用法:
  python fetch_orders.py probe     # 探测四个工具的真实返回结构，落盘 raw_dump.json
  python fetch_orders.py all       # 拉真实数据并归一化为 orders.json
"""
import json
import os
import re
import sys
from datetime import datetime
import urllib.request
import urllib.error

MCP_URL = "https://mcp.mcd.cn"
TOOLS = ["order-list", "query-my-coupons", "campaign-calendar", "list-nutrition-foods"]


def get_token():
    t = os.environ.get("MCD_MCP_TOKEN", "")
    if not t:
        sys.exit("缺少环境变量 MCD_MCP_TOKEN，请先 export MCD_MCP_TOKEN=你的Token")
    return t


def _post(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    req.add_header("Authorization", "Bearer " + get_token())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode("utf-8", "replace")}
    except Exception as e:  # noqa: BLE001
        return {"_error": str(e)}
    return _parse(raw)


def _parse(raw):
    raw = raw.strip()
    if raw.startswith("{"):
        try:
            return json.loads(raw)
        except Exception:  # noqa: BLE001
            pass
    out = None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            chunk = line[5:].strip()
            if chunk:
                try:
                    out = json.loads(chunk)
                except Exception:  # noqa: BLE001
                    pass
    return out or {"_raw": raw[:500]}


def initialize():
    _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                      "clientInfo": {"name": "mcd-order-report", "version": "1.0.0"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"})


def call_tool(name, arguments=None):
    initialize()
    r = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
               "params": {"name": name, "arguments": arguments or {}}})
    return extract_text(r)


def extract_text(resp):
    if not isinstance(resp, dict):
        return resp
    if "_http_error" in resp or "_error" in resp:
        return resp
    result = resp.get("result") or {}
    content = result.get("content") or []
    texts = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text":
            texts.append(c.get("text", ""))
    joined = "\n".join(texts)
    return joined


def _find_original_json(text):
    """从 '## Original Response' 之后提取内嵌 JSON 并解析。"""
    idx = text.find("## Original Response")
    if idx == -1:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}
    sub = text[idx:]
    s = sub.find("{")
    e = sub.rfind("}")
    if s == -1 or e == -1:
        return {}
    try:
        return json.loads(sub[s:e + 1])
    except Exception:  # noqa: BLE001
        return {}


def _parse_nutrition(text):
    """解析 list-nutrition-foods：data 字段是 '[160]{cols}:\\n rows' 文本表。"""
    obj = _find_original_json(text)
    data = obj.get("data") if isinstance(obj, dict) else None
    if not isinstance(data, str):
        return []
    m = re.search(r"\]\{([^}]*)\}", data)
    cols = [c.strip() for c in m.group(1).split(",")] if m else []
    out = []
    for line in data.split("\n"):
        line = line.strip()
        if not line or line.startswith("["):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < len(cols):
            continue
        rec = dict(zip(cols, parts))
        out.append(rec)
    return out


def _parse_campaigns(text):
    """解析 campaign-calendar 的 markdown 活动列表。"""
    out = []
    blocks = re.split(r"####\s*", text)
    for b in blocks[1:]:
        dm = re.match(r"(.*?)(?:\n|$)", b)
        date = dm.group(1).strip() if dm else ""
        titles = re.findall(r"\*\*活动标题\*\*[：:]\s*(.+?)(?=\n)", b)
        descs = re.findall(r"\*\*活动内容介绍\*\*[：:]\s*(.+?)(?=\n\s*\n|\n\s*\*\*|$)", b, re.S)
        for i, t in enumerate(titles):
            out.append({"date": date, "title": t.strip(),
                        "desc": (descs[i].strip() if i < len(descs) else "")})
    return out


def probe():
    dump = {}
    for t in TOOLS:
        print(">> calling", t)
        dump[t] = call_tool(t)
        v = dump[t]
        if isinstance(v, str):
            print("   text len:", len(v), "| head:", v[:60].replace("\n", " "))
    with open("raw_dump.json", "w", encoding="utf-8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=2)
    print("saved raw_dump.json")


def transform():
    with open("raw_dump.json", encoding="utf-8") as f:
        dump = json.load(f)
    ol = dump.get("order-list", "") or ""
    nut_text = dump.get("list-nutrition-foods", "") or ""
    camp_text = dump.get("campaign-calendar", "") or ""
    coup_text = dump.get("query-my-coupons", "") or ""

    ol_json = _find_original_json(ol) if isinstance(ol, str) else {}
    orders = []
    if isinstance(ol_json, dict):
        orders = (ol_json.get("data") or {}).get("list", []) or []

    nutrition = _parse_nutrition(nut_text) if isinstance(nut_text, str) else []
    campaigns = _parse_campaigns(camp_text) if isinstance(camp_text, str) else []
    coupons = [] if ("暂无" in coup_text) else []

    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "mcd-mcp",
        "orders": orders,
        "nutrition": nutrition,
        "campaigns": campaigns,
        "coupons": coupons,
    }
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved orders.json | orders=%d nutrition=%d campaigns=%d coupons=%d"
          % (len(orders), len(nutrition), len(campaigns), len(coupons)))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "probe"
    if mode == "probe":
        probe()
    elif mode == "all":
        probe()
        transform()
    else:
        print("usage: fetch_orders.py [probe|all]")


if __name__ == "__main__":
    main()
