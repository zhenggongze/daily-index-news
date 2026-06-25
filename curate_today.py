"""将 curated TSV 转为网站 JSON"""
import json, os, re
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "news_today_curated.txt")
DATA_DIR = os.path.join(BASE, "news_site", "public", "data")

ML_MAP = {
    "高盛.*AI.*中美": "D", "三星.*HBM": "B", "英伟达.*液冷": "B",
    "算力.*不再稀缺": "D", "微软.*雪佛龙.*电力": "B",
    "SpaceX.*Reflection.*算力": "B", "端侧AI.*升级": "D",
    "长川科技.*预增": "A", "诺奖得主.*Anthropic": "D",
    "Codex.*大更新": "D", "字节跳动洽购.*GPU": "A",
    "长江存储.*NAND": "A", "华为.*PC.*逆势": "A",
    "AI职场.*报告": "D", "三星DS.*亏损": "A",
    "皮尤调查.*AI": "D", "演语科技.*营收": "D",
    "微信.*AI.*小微": "D", "AI支付宝.*Agent": "D",
    "DDR5.*爆发": "B", "Counterpoint.*华为逆势": "A",
    "亚太.*数据中心": "B", "上交所.*大模型.*上市": "D",
    "南大光电.*光刻胶": "A", "三星.*UFS": "B",
    "三星.*折叠屏": "D",
}

def get_ml(title):
    for kw, ml in ML_MAP.items():
        if re.search(kw, title):
            return ml
    return "D"

def detect_impact(summary):
    if "【影响程度】大" in summary: return "大"
    if "【影响程度】中" in summary: return "中"
    return "小"

items = []
with open(SRC, "r", encoding="utf-8") as f:
    lines = f.readlines()

current_title = ""
current_summary = ""
for line in lines:
    line = line.rstrip()
    if not line: 
        continue
    if line.startswith("标题\t"):
        continue
    parts = line.split("\t")
    if len(parts) >= 2:
        if current_title and "——本条与AI产业链无关" not in current_summary:
            items.append({"title": current_title, "summary": current_summary})
        current_title = parts[0].strip()
        summary = parts[1].strip()
        if len(parts) >= 3 and parts[2].strip():
            summary += " " + parts[2].strip()
        current_summary = summary
if current_title and "——本条与AI产业链无关" not in current_summary:
    items.append({"title": current_title, "summary": current_summary})

news_list = []
for i, item in enumerate(items):
    news_list.append({
        "id": i,
        "title": item["title"],
        "summary": item["summary"],
        "mainline": get_ml(item["title"]),
        "impact": detect_impact(item["summary"]),
        "source": "精选",
        "time": ""
    })

def extract_conclusion(summary):
    m = re.search(r'【大白话结论】([^【]*)', summary)
    if m:
        c = m.group(1).strip().replace("💡", "").strip()
        return c[:35] if len(c) > 35 else c
    return ""

daily_summary = {}
global_seen = set()
for ml in ["A", "B", "C", "D"]:
    items_ml = [n for n in news_list if ml in n["mainline"]]
    items_ml.sort(key=lambda n: {"大": 0, "中": 1, "小": 2}.get(n["impact"], 3))
    parts = []
    for n in items_ml:
        c = extract_conclusion(n["summary"])
        if c and c not in global_seen:
            global_seen.add(c)
            parts.append(c)
        if len(parts) >= 3:
            break
    daily_summary[ml] = "；".join(parts) if parts else "——"

today = "2026-06-23"
data = {
    "date": today,
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "count": len(news_list),
    "news": news_list,
    "daily_summary": daily_summary
}

os.makedirs(DATA_DIR, exist_ok=True)
with open(os.path.join(DATA_DIR, f"{today}.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

idx_path = os.path.join(DATA_DIR, "index.json")
existing = []
if os.path.exists(idx_path):
    with open(idx_path) as f:
        existing = json.load(f).get("dates", [])
if "2026-06-22" not in existing:
    existing.append("2026-06-22")
if today not in existing:
    existing.append(today)
existing.sort()
with open(idx_path, "w", encoding="utf-8") as f:
    json.dump({"dates": existing, "count": len(existing)}, f, ensure_ascii=False, indent=2)

print(f"✅ 已写入: {today}.json ({len(news_list)}条)")
print(f"主线: A={sum(1 for n in news_list if 'A' in n['mainline'])}, B={sum(1 for n in news_list if 'B' in n['mainline'])}, C={sum(1 for n in news_list if 'C' in n['mainline'])}, D={sum(1 for n in news_list if 'D' in n['mainline'])}")
print(f"影响: 大={sum(1 for n in news_list if n['impact']=='大')}, 中={sum(1 for n in news_list if n['impact']=='中')}")
