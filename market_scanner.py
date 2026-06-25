import sys, os, json, re, feedparser, requests, warnings
warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings()

BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(BASE, "ai_news_2months.txt")

# ========== RSS源 ==========
RSS_SOURCES = {
    "华尔街见闻": "https://feed.wallstreetcn.com/news/global",
    "36氪": "https://36kr.com/feed",
}

# ========== AI产业链严格关键词 ==========
AI_CORE_KWS = [
    "AI", "人工智能", "算力", "大模型", "芯片", "半导体", "英伟达", "NVIDIA",
    "光模块", "PCB", "HBM", "存储芯片", "DRAM", "NAND",
    "液冷", "散热", "CoWoS", "先进封装",
    "国产替代", "自主可控", "数据中心", "GPU", "服务器",
    "机器人", "具身智能", "Agent", "AI应用", "AI代理",
    "Token", "Capex", "资本开支",
    "六氟化钨", "铟", "氮化铝", "钨", "铋", "金刚石",
    "鸿海", "富士康", "台积电", "OpenAI", "Anthropic", "智谱", "DeepSeek",
    "字节跳动", "三星", "SK海力士", "美光", "谷歌", "DeepMind",
    "推理", "端侧AI", "AI PC", "NPU",
    "半导体设备", "半导体材料",
    "DDR5", "长江存储",
    "电力.*AI", "AI.*电力",
    "Codex", "微信.*AI", "豆包",
    "GLM", "GPT", "Claude", "Gemini",
    "AI芯片", "国产GPU", "昇腾", "寒武纪", "海光", "天数智芯",
    "光刻胶", "光刻机",
    "AI基础设施", "AI资本开支", "AI基建",
    "超算", "百亿亿次",
    "AI模型", "开源模型", "AI出口管制",
    "AI公司", "AI企业", "AI独角兽",
    "AI PC", "NPU",
    "AI存储", "AI服务器",
]

BLOCK_KWS = [
    "药明康德", "创新药", "CAR-T", "双抗", "ADC", "基因编辑",
    "白酒", "啤酒", "饮料", "咖啡", "奶茶",
    "房地产", "楼市", "房贷",
    "汽车销量", "油价", "汽油",
    "电影票房", "世界杯", "足球",
    "黄金", "金价",
    "减肥", "医美",
    "餐饮", "外卖",
    "时装", "美妆",
    "教育", "教培",
    "旅游", "航空", "酒店",
    "银行", "保险", "券商",
    "水泥", "钢铁", "煤炭",
    "农业", "养猪", "粮食",
    "光伏", "风电", "新能源车",
    "碳酸锂", "固态电池",
    "折叠屏.*iPhone", "智能手表",
    "IPO.*募资", "增资", "回购",
    "途虎", "养车", "药房",
]


def is_ai_related(title, summary):
    text = (title + " " + summary).lower()
    for kw in BLOCK_KWS:
        if kw.lower() in text:
            return False
    for kw in AI_CORE_KWS:
        if kw.lower() in text:
            return True
    return False


def parse_existing_json():
    items = []
    data_dir = os.path.join(BASE, "news_site", "public", "data")
    if not os.path.exists(data_dir):
        return items
    for fname in sorted(os.listdir(data_dir)):
        if not fname.endswith(".json") or fname == "index.json" or fname == "breakthrough.json":
            continue
        fp = os.path.join(data_dir, fname)
        with open(fp, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                date = data.get("date", fname.replace(".json", ""))
                for n in data.get("news", []):
                    n["_source"] = f"每日资讯({date})"
                    items.append(n)
            except:
                pass
    return items


def parse_breakthrough_json():
    items = []
    fp = os.path.join(BASE, "news_site", "public", "data", "breakthrough.json")
    if not os.path.exists(fp):
        return items
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)
        for n in data:
            items.append({
                "title": n["title"],
                "summary": f"{n['summary']} 【产业链解释】{n['deepAnalysis'][:200]}【大白话结论】{n['deepAnalysis'][-200:]}",
                "_source": f"爆炸新闻({n['date']})",
            })
    return items


def fetch_rss(name, url):
    entries = []
    try:
        resp = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=15, verify=False)
        if resp.status_code != 200:
            return []
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:20]:
            title = (entry.get("title") or "").strip()
            summary = re.sub(r'<[^>]+>', '', entry.get("summary", entry.get("description", ""))).strip()[:300]
            if title:
                entries.append({"title": title, "summary": summary, "source": name})
    except:
        pass
    return entries


def fetch_eastmoney():
    entries = []
    try:
        url = "https://np-weblist.eastmoney.com/comm/web/getNewsByColumns"
        params = {"client": "web", "biz": "web_news_col", "columnId": "global",
                  "page_size": "30", "page_index": "1"}
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        news = data.get("data", {}).get("list", [])
        for n in news:
            title = (n.get("title") or n.get("name") or "").strip()
            digest = (n.get("digest") or n.get("content") or "")[:300]
            if title:
                entries.append({"title": title, "summary": digest, "source": "东方财富"})
    except:
        pass
    return entries


def extract_analysis(summary):
    impact = ""
    chain = ""
    conclusion = ""

    m = re.search(r'【影响程度】([^【]*)', summary)
    if m:
        impact = m.group(1).strip()

    m = re.search(r'【产业链解释】([^【]*)', summary)
    if m:
        chain = m.group(1).strip()

    m = re.search(r'【大白话结论】([^【]*)', summary)
    if m:
        conclusion = m.group(1).strip()

    if not chain and not conclusion:
        chain = summary[:200]

    return impact, chain, conclusion


def format_item(item, idx):
    title = item.get("title", "")
    summary = item.get("summary", "") or item.get("deepAnalysis", "")
    source = item.get("_source", item.get("source", ""))

    impact, chain, conclusion = extract_analysis(summary)

    lines = []
    lines.append(f"【{idx}】{title}")
    lines.append(f"  📅 来源: {source}")
    lines.append(f"  📝 摘要: {summary[:200]}")
    if impact:
        lines.append(f"  ⚡ 影响程度: {impact}")
    if chain:
        lines.append(f"  🔗 产业链影响: {chain}")
    if conclusion:
        lines.append(f"  💡 大白话结论: {conclusion}")
    lines.append("")
    return "\n".join(lines)


def main():
    print("=" * 50)
    print("AI算力产业链新闻采集 (近2个月)")
    print("=" * 50)

    all_items = []

    print("\n[1/4] 解析历史JSON数据...")
    json_items = parse_existing_json()
    print(f"  每日资讯JSON: {len(json_items)}条")

    print("[2/4] 解析爆炸新闻数据...")
    bt_items = parse_breakthrough_json()
    print(f"  爆炸新闻JSON: {len(bt_items)}条")
    all_items.extend(json_items)
    all_items.extend(bt_items)

    print("[3/4] 采集RSS实时新闻...")
    rss_entries = []
    for name, url in RSS_SOURCES.items():
        entries = fetch_rss(name, url)
        rss_entries.extend(entries)
        print(f"  {name}: {len(entries)}条")

    em_entries = fetch_eastmoney()
    print(f"  东方财富: {len(em_entries)}条")

    rss_ai = [e for e in rss_entries + em_entries if is_ai_related(e["title"], e.get("summary", ""))]
    print(f"  AI相关过滤后: {len(rss_ai)}条")
    for e in rss_ai:
        all_items.append(e)

    print("[4/4] 去重+过滤+格式化...")
    seen = set()
    unique = []
    for item in all_items:
        key = item.get("title", "")[:40].strip().lower()
        if key and key not in seen:
            seen.add(key)
            if is_ai_related(item.get("title", ""), item.get("summary", "") or item.get("deepAnalysis", "")):
                unique.append(item)

    print(f"  去重过滤前: {len(all_items)}条")
    print(f"  去重过滤后: {len(unique)}条")

    output_lines = []
    output_lines.append("=" * 70)
    output_lines.append("AI算力产业链 新闻汇编（近2个月）")
    output_lines.append(f"  共 {len(unique)} 条，采集时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output_lines.append("=" * 70)
    output_lines.append("")

    for idx, item in enumerate(unique, 1):
        formatted = format_item(item, idx)
        output_lines.append(formatted)

    result = "\n".join(output_lines)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n✅ 已生成: {OUTPUT}")
    print(f"   共 {len(unique)} 条，{len(result)} 字符")

    # 打印前3条预览
    print("\n--- 预览前3条 ---")
    for line in result.split("\n")[:15]:
        print(line)


if __name__ == "__main__":
    main()
