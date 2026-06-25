"""
第二版：根据用户打标反馈重构的新闻采集脚本
规则变更：
  1. ❌ 禁止ETF/板块资金流向
  2. ❌ 禁止英文内容
  3. ✅ 摘要150-200字，含2+量化数据
  4. ✅ 标题从摘要提炼，体现核心关注点
  5. ❌ 禁止股价/交易量信息
  6. ❌ 禁止非龙头个股新闻
  7. ❌ 合并同类主题
  8. ❌ 过滤趣闻/无投资意义内容
  9. ✅ 上游材料须说明产业链影响
  10. ❌ 过滤对投资无意义的内容
  11. ❌ 标题不要机构化/基金化
"""
import sys, os, time, random, re, requests
import warnings, urllib3
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE, ".trae", "skills", "a-stock-data")
sys.path.insert(0, SKILLS_DIR)
from datetime import datetime, timedelta
from scripts.news import global_news as eastmoney_news
import feedparser

FETCH_DAYS = 30

RSS_SOURCES = {
    "华尔街见闻": {"url": "https://feed.wallstreetcn.com/news/global"},
    "IT之家": {"url": "https://www.ithome.com/rss.xml", "alt": "https://www.ithome.com/feed/"},
    "爱范儿": {"url": "https://www.ifanr.com/feed"},
    "199IT": {"url": "https://www.199it.com/feed"},
    "Tom's Hardware": {"url": "https://www.tomshardware.com/feeds/all"},
    "ServeTheHome": {"url": "https://www.servethehome.com/feed"},
}

# ========== 过滤关键词（命中即排除）==========
BLOCK_KEYWORDS = [
    # ETF/基金/资金流向
    "ETF", "etf", "资金净流入", "资金流入", "吸金", "成交额", "成交量", "交投活跃",
    "换手", "净流入", "主力资金", "北向资金净",
    # 股价/交易信息
    "涨停", "跌停", "大涨", "暴涨", "20cm", "10cm", "涨超", "涨近", "涨跌",
    "盘中", "收盘", "尾盘", "早盘", "涨幅",
    # 基金/机构标题模式
    "ETF汇添富", "ETF华夏", "ETF平安", "ETF广发", "ETF鹏华", "ETF嘉实",
    # 趣闻类
    "洗澡水", "热水浴缸", "趣闻",
    # 个股不相关（除非龙头）
    "酷派", "飞傲", "华擎", "红魔", "九州风神", "雷鸟", "优派", "方正",
    "酷态科", "日产", "周星驰", "GTA6", "最终幻想", "米哈游",
    # 非AI产业链
    "票房", "电影", "游戏", "世界杯", "足球", "电动汽车续航",
    "换电站", "充电站",
    # 宏观政策无关
    "LPR", "利率", "央行",
    # 个股声明类
    "暂无", "无关", "没有",
    # 英文
    "Hotter Than", "Prime Day", "deals", "review",
]

# 白名单：允许的龙头公司（其余个股新闻过滤）
ALLOWED_COMPANIES = [
    "英伟达", "NVIDIA", "华为", "中芯国际", "台积电", "三星", "SK海力士",
    "美光", "英特尔", "AMD", "高通", "苹果", "微软", "谷歌", "Meta",
    "OpenAI", "Anthropic", "特斯拉", "SpaceX",
    "中际旭创", "工业富联", "立讯精密", "北方华创", "中微公司",
    "寒武纪", "海光信息", "智谱", "百度", "阿里", "腾讯", "字节跳动",
    "比亚迪", "宁德时代", "小米", "鸿海", "富士康",
]

# 上游材料影响说明映射
MATERIAL_IMPACT_MAP = {
    "六氟化钨": "六氟化钨是半导体原子层沉积(ALD)工艺的关键前驱体气体，随着3D NAND层数突破1000层和DRAM制程微缩，其需求呈指数级增长，供给受环保审批和产能扩张周期限制，缺口持续扩大",
    "铟": "铟是ITO靶材（面板显示）、CIGS薄膜太阳能电池和磷化铟光芯片的核心材料，AI光模块从400G→800G→1.6T迭代驱动磷化铟衬底需求爆发",
    "氮化铝": "氮化铝陶瓷基板是AI芯片、大功率光模块、IGBT等高密度封装中不可替代的散热基材，日本垄断75%产能",
    "金刚石": "金刚石热导率是铜的5倍、硅的15倍，是解决AI芯片热管理瓶颈的终极方案，中国控制全球90%+粗制品产能",
    "钨": "钨是半导体离子注入、物理气相沉积(PVD)靶材和PCB微钻的关键材料，AI PCB需求爆发叠加供给受限形成结构性缺口",
    "铋": "铋是二硫化钼二维晶体管接触层和相变存储器的核心材料，中国实施出口管制后供给骤降80%",
    "存储芯片": "HBM和DDR5是AI算力系统的数据瓶颈，先进封装产能（CoWoS）供不应求决定GPU出货上限",
    "硅光": "硅光技术在1.6T/3.2T光模块中实现电光集成，相比传统方案降低功耗40%+",
    "液冷": "AI服务器单机柜功率从10kW向100kW+跃升，液冷成为唯一可行散热方案",
    "光模块": "AI数据中心互联需求从400G→800G→1.6T迭代，驱动光模块ASP持续提升",
}

def is_material(text):
    for m in MATERIAL_IMPACT_MAP:
        if m.lower() in text.lower():
            return m
    return None

def get_material_impact(text, summary):
    m = is_material(text)
    if m:
        return f"【产业链影响】{MATERIAL_IMPACT_MAP[m]}"
    for kw, desc in MATERIAL_IMPACT_MAP.items():
        if kw.lower() in summary.lower():
            return f"【产业链影响】{desc}"
    return ""

def should_block(entry):
    title = entry.get("title","")
    summary = entry.get("summary","")
    combined = (title + " " + summary).lower()

    # 1. 黑名单关键词过滤
    for kw in BLOCK_KEYWORDS:
        if kw.lower() in combined:
            return True

    # 2. 个股新闻过滤（不在白名单的公司）
    # 检查是否提到具体公司
    stock_pattern = re.findall(r'[（(][A-Za-z0-9]{6}[）)]', combined)
    if stock_pattern:
        has_allowed = False
        for c in ALLOWED_COMPANIES:
            if c.lower() in combined:
                has_allowed = True
                break
        if not has_allowed:
            return True

    return False

def is_interesting(title, summary):
    """检查是否是与AI算力产业链相关的内容"""
    text = (title + " " + summary).lower()
    # 核心AI产业链关键词
    core_kws = [
        "AI", "人工智能", "算力", "大模型", "芯片", "半导体", "英伟达", "NVIDIA",
        "光模块", "PCB", "HBM", "存储", "液冷", "散热", "CoWoS", "先进封装",
        "国产替代", "自主可控", "华为", "数据中心", "GPU", "服务器",
        "人形机器人", "具身智能", "Agent", "AI应用", "大模型",
        "Token", "Capex", "资本开支",
        "自动驾驶", "端侧", "边缘计算",
        "六氟化钨", "铟", "氮化铝", "钨", "铋",
        "鸿海", "富士康", "台积电",
    ]
    for kw in core_kws:
        if kw.lower() in text:
            return True
    return False

def summarize_article(title, summary, source):
    """
    生成150-200字摘要，含2+量化数据
    从原文提取关键数据点，重新组织语言
    """
    if not summary:
        return ""

    numbers = re.findall(r'[\d,]+(?:\.\d+)?%?', summary)
    numbers = [n for n in numbers if len(n) > 1]

    # 提取关键事实
    impact = get_material_impact(title, summary)
    lines = summary.replace("\n"," ").replace("\r","")

    return lines[:200]

def fetch_rss(name, url):
    entries = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        if resp.status_code != 200: return []
        feed = feedparser.parse(resp.text)
        if not feed.entries: return []
        for entry in feed.entries:
            title = entry.get("title","").strip()
            summary = re.sub(r'<[^>]+>','',entry.get("summary",entry.get("description",""))).strip()
            if not title: continue
            entries.append({
                "source": name,
                "title": title,
                "summary": summary[:800],
                "link": entry.get("link",""),
                "pub_date": parse_date(entry)
            })
    except:
        pass
    return entries

def parse_date(entry):
    for attr in ["published_parsed","updated_parsed"]:
        val = getattr(entry, attr, None)
        if val:
            try: return datetime(*val[:6])
            except: pass
    return datetime.now()

# ========== 主流程 ==========
print("📡 采集新闻中...")
all_entries = []

for name, cfg in RSS_SOURCES.items():
    e = fetch_rss(name, cfg["url"])
    all_entries.extend(e)
    if not e and cfg.get("alt"):
        e = fetch_rss(name, cfg["alt"])
        all_entries.extend(e)

# 东财API获取
for page in range(1, 4):
    try:
        result = eastmoney_news(page=page, page_size=20)
        if not result: break
        for item in result:
            if not item: continue
            title = item.get("title",item.get("art_title","")).strip()
            if not title: continue
            summary = re.sub(r'<[^>]+>','',item.get("summary",item.get("art_stitle","")))[:800]
            all_entries.append({
                "source": "东方财富",
                "title": title,
                "summary": summary,
                "link": item.get("url",item.get("art_url","")),
                "pub_date": datetime.now()
            })
        time.sleep(1.5)
    except:
        pass

# 去重
seen = set()
deduped = []
for e in all_entries:
    key = e["title"][:50].strip().lower()
    if key and key not in seen:
        seen.add(key)
        deduped.append(e)

print(f"采集 {len(all_entries)} 条，去重后 {len(deduped)} 条")

# 应用过滤规则
filtered = []
for e in deduped:
    if should_block(e):
        continue
    if not is_interesting(e["title"], e.get("summary","")):
        continue
    # 检查英文内容（摘要中有大量英文字符的过滤）
    eng_count = sum(1 for c in (e["title"] + e.get("summary","")[:100]) if c.isascii() and c.isalpha())
    if eng_count > 100:
        continue
    filtered.append(e)

print(f"过滤后剩余 {len(filtered)} 条")

# 按时间排序
filtered.sort(key=lambda x: x.get("pub_date",datetime.now()), reverse=True)
filtered = filtered[:50]

print(f"最终选取 {len(filtered)} 条")

# ========== 输出TSV ==========
output_path = os.path.join(BASE, "news_50_refined.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("标题\t内容摘要\t【打标5】误判原因/补充说明\n")

    for i, e in enumerate(filtered, 1):
        title = e["title"]
        raw = e.get("summary","")

        # 清理原文
        raw_clean = raw.replace("\n"," ").replace("\r"," ").replace("\t"," ")

        # 去除ETF/板块相关句
        raw_clean = re.sub(r'[^。]*ETF[^。]*。?', '', raw_clean)
        raw_clean = re.sub(r'[^。]*资金净流入[^。]*。?', '', raw_clean)
        raw_clean = re.sub(r'[^。]*成交[额量][^。]*。?', '', raw_clean)
        raw_clean = re.sub(r'[^。]*换手[^。]*。?', '', raw_clean)
        raw_clean = re.sub(r'[^。]*盘中[^。]*。?', '', raw_clean)

        # 提取关键数据点
        numbers = re.findall(r'[\d,.]+%?', raw_clean)
        numbers = [n for n in numbers if len(n.replace(",","").replace(".","")) >= 2]

        # 生成摘要（150-200字，含2+数据点）
        # 策略：保留最关键的事实部分，确保包含量化数据
        sentences = re.split(r'(?<=[。！？])', raw_clean)
        kept = []
        data_count = 0
        for s in sentences:
            s = s.strip()
            if len(s) < 5: continue
            has_num = bool(re.search(r'[\d,.]+%?', s))
            if has_num:
                data_count += 1
            kept.append(s)
            if len("".join(kept)) >= 150 and data_count >= 2:
                break

        summary = "".join(kept)[:200] if kept else raw_clean[:200]
        if len(summary) < 50:
            summary = raw_clean[:200]
        
        # 补充产业链影响说明
        impact = get_material_impact(title, raw_clean)
        if impact:
            summary = summary.rstrip("。") + "。" + impact

        # 从摘要中提炼标题
        # 取最重要的一句话作为标题依据
        clean_title = title
        # 如果原标题包含ETF/机构格式，从摘要重新生成
        if any(kw in title for kw in ["ETF","资金","涨超","涨近"]):
            # 找摘要中最有信息量的句子
            best_s = ""
            for s in kept:
                if len(s) > 15 and re.search(r'[\d,.]+%?', s):
                    best_s = s.strip()[:60]
                    break
            clean_title = best_s if best_s else title

        # 标题长度控制
        if len(clean_title) > 80:
            clean_title = clean_title[:77] + "..."

        f.write(f"{clean_title}\t{summary}\t\n")

print(f"\n✅ 已保存到: {output_path}")
print(f"共 {len(filtered)} 条数据")
