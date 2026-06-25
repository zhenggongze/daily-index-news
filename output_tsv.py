"""
采集新闻并输出TSV文本，供用户复制到Excel
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

# ========== 配置区 ==========
FETCH_DAYS = 30
RSS_SOURCES = {
    "华尔街见闻": {"url": "https://feed.wallstreetcn.com/news/global", "alt_urls": []},
    "IT之家": {"url": "https://www.ithome.com/rss.xml", "alt_urls": ["https://feed.ithome.com/", "https://www.ithome.com/feed/"]},
    "爱范儿": {"url": "https://www.ifanr.com/feed", "alt_urls": []},
    "199IT": {"url": "https://www.199it.com/feed", "alt_urls": []},
    "NVIDIA Blog": {"url": "https://developer.nvidia.com/blog/feed", "alt_urls": []},
    "Tom's Hardware": {"url": "https://www.tomshardware.com/feeds/all", "alt_urls": []},
    "ServeTheHome": {"url": "https://www.servethehome.com/feed", "alt_urls": []},
}

KEYWORDS_MAINLINE = {
    "A": {"name": "国产替代自主可控", "keywords": [
        "国产替代","自主可控","半导体","芯片","晶圆","光刻","大基金","信创","EDA","IP核",
        "HBM","先进封装","存储芯片","设备国产","中芯国际","华大九天","北方华创","中微公司",
        "长鑫存储","长江存储","龙芯","飞腾","海光","寒武纪","昇腾","华为","麒麟",
        "国产GPU","国产AI芯片","国产化率","渗透率","良率突破","光刻机","刻蚀机",
        "Chiplet","2.5D封装","3D封装","TSV","硅通孔","国芯","景嘉微","澜起科技","兆易创新","通富微电"
    ]},
    "B": {"name": "英伟达全球供应链", "keywords": [
        "NVIDIA","英伟达","GB200","B300","B200","NVL72","NVL36","Rubin","Blackwell","Hopper",
        "光模块","光互联","CPO","硅光","LPO","PCB","覆铜板","高速铜缆","DAC","AEC",
        "散热","液冷","浸没式液冷","冷板式液冷","服务器","GPU服务器","AI服务器",
        "H100","H200","B100","A100","CoWoS","先进封装产能","一供","二供","份额提升","ASP提升",
        "中际旭创","天孚通信","新易盛","工业富联","沪电股份","胜宏科技","深南电路",
        "英伟达认证","NVIDIA认证","数据中心GPU","800G","1.6T","1.6T光模块","NVLink","InfiniBand"
    ]},
    "C": {"name": "具身智能产业化", "keywords": [
        "人形机器人","具身智能","灵巧手","力矩传感器","六维力传感器","减速器","谐波减速器",
        "RV减速器","丝杠","滚珠丝杠","行星滚柱丝杠","特斯拉","Optimus","擎天柱",
        "边缘推理","边缘计算","端侧AI","NPU","波士顿动力","Figure AI","优必选","宇树科技","智元机器人",
        "小批量量产","BOM成本下降","工厂实测","物流场景","端到端模型上车","仿真训练平台",
        "电机","关节模组","编码器","空心杯电机","拓普集团","三花智控","绿的谐波",
        "双环传动","鸣志电器","汇川技术","机器人大模型","RT-2","通用机器人","人形机器人量产","万台产能"
    ]},
    "D": {"name": "大厂AI软件应用落地", "keywords": [
        "大模型","Token","Agent","AI Agent","RAG","MaaS","DAU","MAU","月活","日活",
        "Capex","资本开支","资本支出","API调用","API收入","Token消耗","多模态","多模态模型",
        "GPT-5","Claude","Gemini","AI应用","AI落地","企业级AI","AI PC","端侧NPU","AI手机",
        "Kimi","文心一言","通义千问","智谱","百川","豆包","DeepSeek","Qwen","GLM",
        "AIGC","生成式AI","Copilot","AI编程","付费转化","正向毛利","商业化",
        "微软","谷歌","Meta","OpenAI","Anthropic","BAT","字节跳动","华为盘古",
        "算力基建","智算中心","东数西算","IDC","数据中心","数字经济"
    ]}
}
GENERAL_AI_KEYWORDS = ["AI","人工智能","算力","深度学习","神经网络","机器学习","大模型","LLM","AIGC","生成式AI","智能"]
INTERESTING_KEYWORDS = [
    "自动驾驶","智能驾驶","FSD","Robotaxi","量子计算","量子芯片","低空经济","无人机","eVTOL",
    "苹果","Vision Pro","AR","VR","MR","Sora","视频生成","AI制药","AI医疗",
    "数字人","虚拟人","6G","卫星互联网","星链","固态电池","钠离子电池",
    "碳化硅","SiC","第三代半导体","RISC-V","开源芯片","商业航天","SpaceX","脑机接口","Neuralink"
]

def parse_date(entry):
    for attr in ["published_parsed","updated_parsed"]:
        val = getattr(entry, attr, None)
        if val:
            try: return datetime(*val[:6])
            except: pass
    return datetime.now()

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
            entries.append({
                "source": name, "title": title, "summary": summary[:500],
                "link": entry.get("link",""), "pub_date": parse_date(entry)
            })
    except: pass
    return entries

def fetch_eastmoney():
    entries = []
    for page in range(1, 4):
        try:
            result = eastmoney_news(page=page, page_size=20)
            if not result: break
            for item in result:
                if not item: continue
                title = item.get("title",item.get("art_title","")).strip()
                if not title: continue
                summary = re.sub(r'<[^>]+>','',item.get("summary",item.get("art_stitle","")))[:500]
                entries.append({
                    "source": "东方财富资讯", "title": title, "summary": summary,
                    "link": item.get("url",item.get("art_url","")), "pub_date": datetime.now()
                })
            time.sleep(1.5)
        except: pass
    return entries

def match_mainline(title, summary):
    text = (title + " " + summary).lower()
    results = []
    for ml_id, cfg in KEYWORDS_MAINLINE.items():
        for kw in cfg["keywords"]:
            if kw.lower() in text:
                results.append((ml_id, cfg["name"], kw))
    if not results:
        for kw in GENERAL_AI_KEYWORDS:
            if kw.lower() in text:
                results.append(("D", "大厂AI软件应用落地", kw))
                break
    return results

def is_interesting(title, summary):
    text = (title + " " + summary).lower()
    for kw in INTERESTING_KEYWORDS:
        if kw.lower() in text: return True
    return False

# ========== 主流程 ==========
print("📡 采集新闻中...")
all_entries = []
for name, cfg in RSS_SOURCES.items():
    e = fetch_rss(name, cfg["url"])
    all_entries.extend(e)
    if not e and cfg["alt_urls"]:
        for au in cfg["alt_urls"]:
            e = fetch_rss(name, au)
            all_entries.extend(e)
            if e: break

e = fetch_eastmoney()
all_entries.extend(e)

# 去重
seen = set()
deduped = []
for entry in all_entries:
    key = entry["title"][:50].strip().lower()
    if key and key not in seen:
        seen.add(key)
        deduped.append(entry)
print(f"采集 {len(all_entries)} 条，去重后 {len(deduped)} 条")

# 分类
primary = []
secondary = []
primary_set = set()
for entry in deduped:
    m = match_mainline(entry["title"], entry.get("summary",""))
    key = entry["title"][:40].lower()
    if m:
        primary.append(entry)
        primary_set.add(key)
    elif is_interesting(entry["title"], entry.get("summary","")):
        if key not in primary_set:
            secondary.append(entry)
            primary_set.add(key)
    else:
        if key not in primary_set:
            secondary.append(entry)
            primary_set.add(key)

# 取100 + 50
primary.sort(key=lambda x: x.get("pub_date",datetime.now()), reverse=True)
primary_100 = primary[:100]
secondary.sort(key=lambda x: x.get("pub_date",datetime.now()), reverse=True)
secondary_50 = (secondary[:50]) if len(secondary) >= 50 else (secondary + [{"source":"--","title":"--","summary":"--","link":"--","pub_date":datetime.now()}]* (50-len(secondary)))

print(f"主集: {len(primary_100)} 条, 补充: {len(secondary_50)} 条")

# 输出TSV到文件
output_txt_path = os.path.join(BASE, "tsv_output_for_excel.txt")
with open(output_txt_path, "w", encoding="utf-8") as f:
    f.write("=== 复制以下内容到Excel(用数据-自文本/CSV, 分隔符选制表符) ===\n\n")
    f.write("序号\t信源\t发布时间\t标题\t摘要\t系统预判主线\t系统预判细分环节\t你的判断-主线归属\t你的判断-触发条件\t你的判断-价值评分(1-5)\t你的判断-置信度\t链接\t类型\n")

    all_items = [(item, "主集100") for item in primary_100] + [(item, "补充50") for item in secondary_50]
    cutoff = datetime.now() - timedelta(days=FETCH_DAYS)

    rn = 0
    for idx, (item, ntype) in enumerate(all_items, 1):
        title = item["title"]
        summary = item.get("summary","")
        pd_ = item.get("pub_date", datetime.now())

        if isinstance(pd_, datetime) and pd_ < cutoff and ntype == "主集100":
            continue

        m = match_mainline(title, summary)
        if m:
            ml = ", ".join(set(x[0] for x in m))
            sg = ", ".join(set(x[2] for x in m))
        elif ntype == "补充50":
            ml = "可能感兴趣"
            sg = "非四条主线"
        else:
            ml = "未识别"
            sg = ""
        ds = pd_.strftime("%Y-%m-%d") if isinstance(pd_, datetime) else str(pd_)
        rn += 1
        line = f"{rn}\t{item['source']}\t{ds}\t{title.replace(chr(9),' ').replace(chr(10),' ')}\t{summary[:300].replace(chr(9),' ').replace(chr(10),' ')}\t{ml}\t{sg}\t\t\t\t\t{str(item.get('link','')).replace(chr(9),' ')}\t{ntype}\n"
        f.write(line)

    f.write(f"\n=== 以上共 {rn} 条 ===\n\n")
    f.write("=== 打标说明（请参考以下规则填写第8-11列）===\n\n")
    f.write("列H - 主线归属: A/B/C/D/跨主线/不相关\n")
    f.write("列I - 触发条件: 1(国产替代验证)/2(英伟达链绑定)/3(具身智能拐点)/4(大厂应用爆发)/5(跨主线)/0(无)\n")
    f.write("列J - 价值评分: 1-5分(1=噪声/3=有参考/5=里程碑)\n")
    f.write("列K - 置信度: 高(官方公告)/中(行业媒体)/低(传言)\n")

print(f"\n✅ 已保存到: {output_txt_path}")
print(f"✅ 共 {rn} 条数据")
print("请复制该文件内容到Excel中（使用数据→自文本/CSV，分隔符选制表符）")
