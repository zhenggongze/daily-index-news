"""
种子数据：将50条新闻写入 news_site/public/data/
包含每日四主线聚合总结（挤压式精炼）
"""
import sys, os, json, re

BASE = os.path.dirname(os.path.abspath(__file__))
NEWS_SRC = os.path.join(BASE, "news_50_v4.txt")
DATA_DIR = os.path.join(BASE, "news_site", "public", "data")
os.makedirs(DATA_DIR, exist_ok=True)

MAINLINE_MAP = {
    "智谱": "D", "三星HBM": "B", "谷歌TPU": "B, D", "上海超硅": "A",
    "鸿海.*Rubin": "B", "存储芯片市场": "B", "韩国芯片出口": "B", "铟价": "B",
    "氮化铝": "B", "OpenAI": "D", "ChatGPT": "D", "三星向员工": "D",
    "英伟达Rubin.*液冷": "B", "中国AI模型训练成本": "D",
    "AI Agent.*CPU": "D", "AI PCB": "B", "金刚石散热": "B",
    "SK海力士市值": "B", "花旗看高美光": "B", "电容成AI": "B",
    "SpaceX上市": "D", "皮尤调查": "D", "员工已用AI工具": "D",
    "黄仁勋链博会": "B", "华为鸿蒙": "A", "苹果加价锁定": "D",
    "字节跳动洽购": "A", "英特尔前海力士": "B", "AI推理加速": "D",
    "OpenAI Codex": "D", "Isaac Sim": "C", "华为PC出货": "A",
    "三星DS部门": "A", "Anthropic F5": "A", "ACE指令集": "B",
    "骁龙X2": "B", "全球手机降8%": "A", "宁德时代": "D",
    "FERC": "D", "Sanders提案": "D", "P5 Fab 2": "B",
    "Rubin机架单价": "B", "链博会首设AI": "D", "Agent激增": "D",
    "金刚石.*液冷": "B", "芯片出口连涨": "B", "低成本优势": "D",
    "存储三巨头": "B",
}

def get_mainline(title):
    for kw, ml in MAINLINE_MAP.items():
        if re.search(kw, title, re.I):
            return ml
    return "D"

def detect_impact(summary):
    if "【影响程度】大" in summary: return "大"
    if "【影响程度】中" in summary: return "中"
    return "小"

def extract_conclusion(summary):
    """提取结论部分，干掉前缀"""
    m = re.search(r'【大白话结论】([^【]*)', summary)
    if m:
        text = m.group(1).strip()
    else:
        text = ""
    text = text.replace("💡", "").strip()
    return text

def compress_one(conclusion):
    """把一条结论压缩到极致：取核心判断句，砍掉废话"""
    if not conclusion or len(conclusion) < 5:
        return ""
    # 砍掉尾句铺垫
    text = conclusion
    # 取第一句
    first = re.split(r'[。！？]', text)[0].strip()
    # 砍掉常见废话前缀
    first = re.sub(r'^(所以|因此|这意味着|说明|这意味着|可以说|本质上|说白了)', '', first)
    # 如果还是太长，从中间砍
    if len(first) > 35:
        first = first[:32] + "…"
    return first

def build_mainline_summary(news_list, ml, global_seen=None):
    """对某条主线，收集所有新闻的结论，压缩后合并（支持全局去重）"""
    items = [n for n in news_list if ml in n["mainline"]]
    if not items:
        return "——"
    if global_seen is None:
        global_seen = set()
    items.sort(key=lambda n: {"大": 0, "中": 1, "小": 2}.get(n["impact"], 3))
    parts = []
    for n in items:
        c = compress_one(extract_conclusion(n["summary"]))
        if c and c not in global_seen:
            global_seen.add(c)
            parts.append(c)
        if len(parts) >= 3:
            break
    if not parts:
        return "——"
    return "；".join(parts)

# 解析TSV
items = []
with open(NEWS_SRC, "r", encoding="utf-8") as f:
    for line in f.readlines()[1:]:
        line = line.strip()
        if not line: continue
        parts = line.split("\t")
        if len(parts) >= 2:
            title = parts[0].strip()
            summary = parts[1].strip()
            if len(parts) >= 3 and parts[2].strip():
                summary += " " + parts[2].strip()
            items.append({"title": title, "summary": summary})

news_list = []
for i, item in enumerate(items):
    t = item["title"]
    s = item["summary"]
    news_list.append({
        "id": i,
        "title": t,
        "summary": s,
        "mainline": get_mainline(t),
        "impact": detect_impact(s),
        "source": "精选",
        "time": ""
    })

# 计算四主线聚合总结（全局去重）
daily_summary = {}
global_seen = set()
for ml in ["A", "B", "C", "D"]:
    summary_text = build_mainline_summary(news_list, ml, global_seen)
    daily_summary[ml] = summary_text

data = {
    "date": "2026-06-22",
    "updated": "2026-06-22 15:00",
    "count": len(news_list),
    "news": news_list,
    "daily_summary": daily_summary
}

filepath = os.path.join(DATA_DIR, "2026-06-22.json")
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

index_path = os.path.join(DATA_DIR, "index.json")
with open(index_path, "w", encoding="utf-8") as f:
    json.dump({"dates": ["2026-06-22"], "count": 1}, f, ensure_ascii=False, indent=2)

print(f"✅ 种子数据已写入: {filepath} ({len(news_list)}条)")
print(f"\n四主线聚合总结:")
for ml in ["A", "B", "C", "D"]:
    label = {"A": "A国产替代", "B": "B英伟达链", "C": "C具身智能", "D": "D大厂应用"}[ml]
    print(f"  {label}: {daily_summary[ml]}")
