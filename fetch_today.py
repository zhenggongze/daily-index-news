"""采集今天新闻 + 生成分析"""
import sys, os, re, json, requests, time
import warnings, urllib3
warnings.filterwarnings("ignore")
urllib3.disable_warnings()

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE, ".trae", "skills", "a-stock-data")
sys.path.insert(0, SKILLS_DIR)

from datetime import datetime
from scripts.news import global_news as eastmoney_news
import feedparser

RSS_SOURCES = [
    ("华尔街见闻", "https://feed.wallstreetcn.com/news/global"),
    ("IT之家", "https://www.ithome.com/feed/"),
    ("爱范儿", "https://www.ifanr.com/feed"),
    ("199IT", "https://www.199it.com/feed"),
    ("Tom's Hardware", "https://www.tomshardware.com/feeds/all"),
    ("ServeTheHome", "https://www.servethehome.com/feed"),
]

BLOCK = [
    "ETF", "etf", "资金净流入", "资金流入", "吸金", "成交额", "成交量", "交投活跃",
    "换手", "净流入", "主力资金", "北向资金净",
    "涨停", "跌停", "大涨", "暴涨", "20cm", "10cm", "涨超", "涨近",
    "盘中", "收盘", "尾盘", "早盘", "涨幅",
    "ETF汇添富", "ETF华夏", "ETF平安", "ETF广发",
    "洗澡水", "酷派", "飞傲", "华擎", "红魔", "九州风神", "日产", "周星驰",
    "票房", "电影", "世界杯", "足球", "LPR", "利率", "央行",
    "暂无", "无关", "没有",
]

CORE_KWS = [
    "AI", "人工智能", "算力", "大模型", "芯片", "半导体", "英伟达", "NVIDIA",
    "光模块", "PCB", "HBM", "存储", "液冷", "散热", "CoWoS", "先进封装",
    "国产替代", "自主可控", "华为", "数据中心", "GPU", "服务器",
    "人形机器人", "具身智能", "Agent", "AI应用",
    "Token", "Capex", "资本开支", "自动驾驶", "端侧", "边缘计算",
    "六氟化钨", "铟", "氮化铝", "钨", "铋", "金刚石",
    "鸿海", "富士康", "台积电", "OpenAI", "Anthropic", "智谱",
    "字节跳动", "三星", "SK海力士", "美光",
]

MATERIALS = {
    "六氟化钨": "六氟化钨是半导体ALD工艺关键前驱体，3D NAND层数突破1000层推动需求激增",
    "铟": "铟是磷化铟光芯片核心材料，AI光模块从400G→800G→1.6T迭代驱动需求爆发，中国掌控75%储量",
    "氮化铝": "氮化铝陶瓷基板是AI芯片和光模块不可替代的散热基材，日本垄断75%高端产能",
    "钨": "钨是半导体PVD靶材和AI-PCB微钻关键材料，AI服务器PCB升级驱动需求倍增",
    "铋": "铋是相变存储器和二维晶体管接触层核心材料，中国出口管制后供给骤降80%",
    "HBM": "HBM是AI GPU内存瓶颈，HBM4带宽是前代2倍+，CoWoS产能决定GPU出货量",
    "CoWoS": "CoWoS先进封装产能是AI芯片出货瓶颈，台积电年增100%+仍供不应求",
    "硅光": "硅光技术在1.6T/3.2T光模块实现电光集成，功耗降低40%+",
    "PCB": "AI服务器PCB从16层向30层+升级，mSAP工艺供不应求，价值量提升3-5倍",
    "液冷": "AI服务器单机柜功率从10kW向100kW+跃升，液冷成为唯一可行散热方案",
    "金刚石": "金刚石热导率2000W/m·K是铜5倍硅15倍，AI芯片热管理终极方案",
    "光模块": "AI数据中心互联从400G→800G→1.6T迭代，1.6T光模块ASP是800G的2倍+",
}

ALLOWED = [
    "英伟达", "NVIDIA", "华为", "中芯国际", "台积电", "三星", "SK海力士",
    "美光", "英特尔", "AMD", "高通", "苹果", "微软", "谷歌", "Meta",
    "OpenAI", "Anthropic", "特斯拉", "SpaceX",
    "中际旭创", "工业富联", "立讯精密", "北方华创", "中微公司",
    "寒武纪", "海光信息", "智谱", "百度", "阿里", "腾讯", "字节跳动",
    "比亚迪", "宁德时代", "小米", "鸿海", "富士康",
]

MAINLINE_MAP = {
    "智谱": "D", "三星": "B", "谷歌": "B,D", "超硅": "A", "硅片": "A",
    "鸿海": "B", "英伟达": "B", "Rubin": "B", "存储芯片": "B",
    "HBM": "B", "韩国芯片": "B", "铟": "B", "氮化铝": "B",
    "OpenAI": "D", "ChatGPT": "D", "Claude": "D",
    "液冷": "B", "PCB": "B", "金刚石": "B",
    "海力士": "B", "美光": "B", "电容": "B",
    "SpaceX": "D", "皮尤": "D", "黄仁勋": "B", "华为": "A",
    "苹果": "D", "字节": "A", "先进封装": "B", "CoWoS": "B",
    "推理": "D", "Codex": "D", "Isaac": "C", "机器人": "C",
    "Agent": "D", "骁龙": "B", "ACE指令集": "B", "Anthropic": "A,D",
    "管制": "A", "链博会": "D", "宁德": "D", "FERC": "D", "Sanders": "D",
}

def get_mainline(title):
    for kw, ml in MAINLINE_MAP.items():
        if kw.lower() in title.lower():
            return ml
    return "D"

def should_block(title, summary):
    combined = (title + " " + summary).lower()
    for kw in BLOCK:
        if kw.lower() in combined:
            return True
    eng_count = sum(1 for c in combined[:200] if c.isascii() and c.isalpha())
    if eng_count > 120:
        return True
    return False

def is_interesting(title, summary):
    text = (title + " " + summary).lower()
    for kw in CORE_KWS:
        if kw.lower() in text:
            return True
    return False

def get_impact_analysis(title, summary):
    """生成影响分析：核心事实+产业链解释+结论"""
    text = title + " " + summary
    parts = []

    # 提取关键数字
    nums = re.findall(r'[\d,.]+%?', summary[:300])
    key_nums = nums[:3]

    # 产业链影响
    for kw, desc in MATERIALS.items():
        if kw.lower() in text.lower():
            parts.append(f"【产业链影响】{desc}")

    # 基本结论模板
    return "; ".join(parts) if parts else ""

def fetch_rss(url, name):
    entries = []
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
        if resp.status_code != 200: return []
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:30]:
            title = entry.get("title", "").strip()
            summary = re.sub(r'<[^>]+>', '', entry.get("summary", entry.get("description", ""))).strip()
            if title:
                entries.append({"title": title, "summary": summary[:500], "source": name})
    except:
        pass
    return entries

# ====== 主流程 ======
print("📡 采集今日新闻...")
all_entries = []

for label, url in RSS_SOURCES:
    entries = fetch_rss(url, label)
    all_entries.extend(entries)
    print(f"  {label}: {len(entries)}条")

# 东财
for page in range(1, 4):
    try:
        result = eastmoney_news(page=page, page_size=20)
        if not result: break
        for item in result:
            title = item.get("title", item.get("art_title", "")).strip()
            if not title: continue
            summary = re.sub(r'<[^>]+>', '', item.get("summary", item.get("art_stitle", "")))[:500]
            all_entries.append({"title": title, "summary": summary, "source": "东方财富"})
        time.sleep(1.5)
    except:
        pass
print(f"  东方财富: {len(all_entries) - sum(1 for e in all_entries if e['source'] != '东方财富')}条")

# 去重
seen = set()
deduped = []
for e in all_entries:
    key = e["title"][:50].strip().lower()
    if key and key not in seen:
        seen.add(key)
        deduped.append(e)
print(f"\n去重后: {len(deduped)}条")

# 过滤
filtered = []
for e in deduped:
    if should_block(e["title"], e.get("summary", "")):
        continue
    if not is_interesting(e["title"], e.get("summary", "")):
        continue
    filtered.append(e)
print(f"过滤后: {len(filtered)}条")

# 每条生成分析（取前30条）
filtered = filtered[:50]
print(f"选取: {len(filtered)}条\n")

METAS = {
    "A": {"label": "国产替代自主可控", "emoji": "🔬"},
    "B": {"label": "英伟达全球供应链", "emoji": "🔗"},
    "C": {"label": "具身智能产业化", "emoji": "🤖"},
    "D": {"label": "大厂AI应用落地", "emoji": "📱"},
}

# 构建输出TSV
output_path = os.path.join(BASE, "news_today.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("标题\t内容摘要\t【打标5】\n")
    for i, e in enumerate(filtered, 1):
        t = e["title"]
        s = e.get("summary", "")
        s_clean = s.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        s_clean = re.sub(r'[^。]*ETF[^。]*。?', '', s_clean)
        s_clean = re.sub(r'[^。]*资金[^。]*。?', '', s_clean)

        # 摘要120-200字
        if len(s_clean) > 200:
            s_clean = s_clean[:197] + "..."

        # 产业链影响
        impact = get_impact_analysis(t, s_clean)
        if impact and impact not in s_clean:
            s_clean = s_clean.rstrip("。") + "。" + impact

        # 主线
        ml = get_mainline(t)
        f.write(f"{t}\t{s_clean}\t\n")

print(f"✅ 已保存: {output_path}")
print(f"共 {len(filtered)} 条")

# 同时生成JSON给网站
DATA_DIR = os.path.join(BASE, "news_site", "public", "data")
os.makedirs(DATA_DIR, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
news_list = []
for i, e in enumerate(filtered):
    t = e["title"]
    s = e.get("summary", "")
    s_clean = s.replace("\n", " ").replace("\t", " ")[:200]
    impact = get_impact_analysis(t, s_clean)
    if impact and impact not in s_clean:
        s_clean = s_clean.rstrip("。") + "。" + impact

    imp = "大"
    news_list.append({
        "id": i,
        "title": t,
        "summary": s_clean,
        "mainline": get_mainline(t),
        "impact": imp,
        "source": e.get("source", ""),
        "time": ""
    })

# 更新index
index_path = os.path.join(DATA_DIR, "index.json")
existing_dates = []
if os.path.exists(index_path):
    with open(index_path, "r") as f:
        existing_dates = json.load(f).get("dates", [])
if "2026-06-22" not in existing_dates:
    existing_dates.append("2026-06-22")
if today not in existing_dates:
    existing_dates.append(today)
existing_dates.sort()
with open(index_path, "w", encoding="utf-8") as f:
    json.dump({"dates": existing_dates, "count": len(existing_dates)}, f, ensure_ascii=False, indent=2)

data_file = os.path.join(DATA_DIR, f"{today}.json")
with open(data_file, "w", encoding="utf-8") as f:
    json.dump({
        "date": today,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(news_list),
        "news": news_list
    }, f, ensure_ascii=False, indent=2)

print(f"\n✅ 网站数据: {data_file} ({len(news_list)}条)")
print(f"✅ 索引: {index_path}")
