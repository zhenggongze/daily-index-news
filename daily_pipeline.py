#!/usr/bin/env python3
"""
AI算力产业链每日资讯 全自动流水线 v3
流程：RSS采集 → 去重 → LLM批量分类(20-shot prompt) → 只对相关新闻逐条深度分析 → 写入JSON
目标产出：10-25条/天高质量新闻，cron-job.org 每天 08:07 触发
"""
import os, sys, re, json, time, warnings
from datetime import datetime, date

warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings()

import requests
import feedparser

BASE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(BASE, ".trae", "skills", "a-stock-data")
sys.path.insert(0, SKILLS_DIR)

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "")
if not DEEPSEEK_KEY:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            DEEPSEEK_KEY = winreg.QueryValueEx(k, "DEEPSEEK_KEY")[0]
    except:
        pass
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"
DATA_DIR = os.path.join(BASE, "news_site", "public", "data")
os.makedirs(DATA_DIR, exist_ok=True)

RSS_SOURCES = [
    ("华尔街见闻", "https://feed.wallstreetcn.com/news/global"),
    ("36氪8点1氪", "https://36kr.com/feed"),
    ("量子位", "https://www.qbitai.com/feed"),
    ("雷锋网", "https://www.leiphone.com/feed"),
    ("InfoQ", "https://www.infoq.cn/feed"),
    ("钛媒体", "https://www.tmtpost.com/rss.xml"),
    ("IEEE Spectrum", "https://spectrum.ieee.org/feeds/type/news.rss"),
    ("SemiconductorEngineering", "https://semiengineering.com/feed"),
    ("SemiWiki", "https://semiwiki.com/feed"),
    ("Phoronix", "https://www.phoronix.com/rss.php"),
    ("Tom's Hardware", "https://www.tomshardware.com/feeds/all"),
    ("ServeTheHome", "https://www.servethehome.com/feed"),
]

ML_MAP = {
    "智谱": "D", "超硅": "A", "硅片": "A",
    "鸿海": "B", "英伟达": "B", "Rubin": "B", "Rubin": "B",
    "HBM": "B", "存储芯片": "B", "DDR5": "B",
    "液冷": "B", "PCB": "B", "光模块": "B",
    "长江存储": "A", "NAND": "B",
    "海力士": "B", "美光": "B", "三星.*存储": "B",
    "OpenAI": "D", "ChatGPT": "D", "Codex": "D",
    "Claude": "D", "Anthropic": "A,D",
    "微信.*AI": "D", "豆包": "D", "DeepSeek": "D",
    "Agent.*OS": "D", "Agent.*平台": "D",
    "华为.*PC": "A", "华为.*手机": "A", "华为.*逆势": "A",
    "半导体设备": "A", "光刻胶": "A", "长川": "A",
    "字节.*GPU": "A", "天数智芯": "A",
    "诺奖.*Anthropic": "D",
    "机器人": "C", "Isaac": "C", "具身": "C",
    "开普勒": "C",
    "端侧AI": "D", "AI PC": "D",
    "AI职场": "D", "AI.*使用率": "D",
    "新能源.*AI": "D", "AI.*电力": "B",
    "三星DS": "A",
    "宁德时代": "D",
}

def get_mainline(title):
    for kw, ml in ML_MAP.items():
        if re.search(kw, title, re.I):
            return ml
    return "D"

def split_compound_title(title):
    """拆分复合标题（如钛晨报/氪星晚报等汇总类文章，含多条独立新闻）

    Pattern 1: "氪星晚报 ｜ Meta投400亿建数据中心；字节探索自动驾驶；扩大消费规划"
             -> ["Meta投400亿建数据中心", "字节探索自动驾驶", "扩大消费规划"]
    Pattern 2: "【钛晨报】李强主持经济座谈会；Meta投400亿建数据中心"
             -> ["李强主持经济座谈会", "Meta投400亿建数据中心"]
    返回拆分后的子标题列表，无法拆分时返回原始标题的单元素列表
    """
    # Pattern 1: "prefix ｜ item1；item2；item3"（全角竖线 + 全角分号）
    if "\uff5c" in title and "\uff1b" in title:
        parts = title.split("\uff5c", 1)
        body = parts[1].strip()
        items = [item.strip() for item in body.split("\uff1b") if item.strip()]
        if len(items) >= 2:
            return items

    # Pattern 2: "【prefix】item1；item2；item3"
    m = re.match(r"^(\u3010[^\u3011]+\u3011)\s*(.+)$", title)
    if m and "\uff1b" in m.group(2):
        body = m.group(2).strip()
        items = [item.strip() for item in body.split("\uff1b") if item.strip()]
        if len(items) >= 2:
            return items

    return [title]


def fetch_rss(url, name):
    entries = []
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30, verify=False)
        if resp.status_code != 200:
            print(f"    {name}: HTTP {resp.status_code}")
            return []
        feed = feedparser.parse(resp.text)
        count = len(feed.entries)
        split_count = 0
        for entry in feed.entries[:30]:
            title = (entry.get("title") or "").strip()
            summary = re.sub(r'<[^>]+>', '', entry.get("summary", entry.get("description", ""))).strip()
            if not title:
                continue
            sub_titles = split_compound_title(title)
            for sub in sub_titles:
                entries.append({"title": sub, "summary": summary[:400], "source": name, "url": entry.get("link", "")})
            if len(sub_titles) > 1:
                split_count += len(sub_titles) - 1
        total = len(entries)
        info = f"\u2705 {count}\u6761" if count > 0 else f"\u26a0\ufe0f 0\u6761 (\u53ef\u80fd\u975eRSS\u6216\u89e3\u6790\u5931\u8d25)"
        if split_count > 0:
            info += f" \u2192 \u62c6\u5206+{split_count}\u6761"
        print(f"    {name}: {info}")
    except Exception as e:
        print(f"    {name}: \u274c {type(e).__name__}: {str(e)[:80]}")
    return entries

def extract_conclusion(summary):
    m = re.search(r'【大白话结论】([^【]*)', summary)
    if m:
        c = m.group(1).strip()
        c = c.replace("💡", "").strip()
        return c[:35] if len(c) > 35 else c
    return ""

def gen_daily_summary(news_list):
    global_seen = set()
    result = {}
    for ml in ["A", "B", "C", "D"]:
        items = [n for n in news_list if ml in n["mainline"]]
        items.sort(key=lambda n: {"大": 0, "中": 1, "小": 2}.get(n["impact"], 3))
        parts = []
        for n in items:
            c = extract_conclusion(n["summary"])
            if c and c not in global_seen:
                global_seen.add(c)
                parts.append(c)
            if len(parts) >= 3:
                break
        result[ml] = "；".join(parts) if parts else "——"
    return result

CLASSIFY_PROMPT = """你是一个顶级AI算力/半导体产业链分析师。逐条判断以下新闻是否与 AI算力产业链投资 直接相关。

每一条新闻必须输出一个JSON对象（字段见末尾），必须逐条对应，不要合并或跳过。

==== 头部公司清单（仅关注这些公司，小公司噪音过滤） ====

美国（含台湾）：
- GPU/AI芯片：英伟达、AMD、Intel、博通、Marvell
- 代工/封装：台积电、日月光、安靠
- 存储：美光、SK海力士、三星
- 半导体设备：ASML、应用材料、泛林半导体、KLA
- 云厂商CapEx：微软、谷歌、Meta、亚马逊、Oracle
- 模型公司：OpenAI、Anthropic
- 网络/光通信：博通、Marvell、Arista、Coherent、Lumentum

日本：
- 硅片：信越化学、SUMCO
- 光刻胶：JSR、东京应化
- 电子特气：大阳日酸
- 靶材：日矿金属
- CMP材料：Fujimi、日东电工

中国：
- AI芯片：华为海思、寒武纪、海光信息
- 代工/封装：中芯国际、长电科技、通富微电
- 存储：长江存储、长鑫存储
- 半导体设备：北方华创、中微公司、拓荆科技、长川科技
- 光模块：中际旭创、新易盛、天孚通信
- PCB：沪电股份、胜宏科技
- 液冷/散热：英维克
- 模型/应用：字节豆包、DeepSeek、智谱、Qwen

==== 相关性判断标准 ====

relevant=true（相关）— 以下任一情况：
1. 新闻直接涉及上述头部公司的AI算力相关动态（产品/产能/业绩/战略/技术）
2. 中小公司新闻但与头部公司有直接供应链关系（如"某小公司成为英伟达供应商"）
3. AI电力/能源基础设施：数据中心用核能/天然气/电力协议——直接影响算力成本或供给
4. AI对半导体上游关键材料的需求信号：如六氟化钨/铟/氮化铝/金刚石等供需紧张
5. 国家级AI算力政策/出口管制/制裁

relevant=false（不相关）— 以下任一情况：
1. 仅涉及非头部公司且无板块级影响：新闻只提到清单外的中小公司，且金额/产能/技术均不达板块级
2. 消费电子：手机（含折叠屏）/平板/手表/耳机/音箱/手环/笔记本（除非内容明确讨论AI PC芯片）
3. 汽车：自动驾驶车型交付/发布/价格调整（除非内容明确讨论自动驾驶芯片或AI训练）
4. 人事/组织：公司聘用/离任/退休/组织架构调整/人事任命
5. 慈善/捐款/公益/社会责任
6. 媒体评论/喊话：如"央视评XX""人民日报XX"——无实质产业链信息
7. 招聘：公司发布的招聘信息（即使是AI公司）
8. 产品外观曝光/谍照/渲染图
9. 操作系统/App更新（与AI硬件产业链无关）
10. 纯消费级产品发布：如电视/空调/冰箱/扫地机器人/数据线
11. 排行榜/盘点/汇总类文章
12. 与半导体/AI产业链无关的公司行为
13. 支付/银行卡/银联类新闻
14. 无人机/相机等硬件（与AI芯片/算力无关）
15. 纯科普/环境/碳足迹文章（无具体公司或数据）

==== 故事线标签（relevant=true时必须打1-3个标签，relevant=false时填空数组） ====

| 标签 | 覆盖场景 |
|------|---------|
| 扩产 | CoWoS/HBM/GPU产能扩张、建厂、量产爬坡、设备采购、资本开支 |
| 涨价 | 芯片/存储/材料/代工涨价、供需紧张提价 |
| 降价 | 价格战、降价抢单、毛利率下行 |
| 技术 | 新工艺/新架构/新产品、路线图、技术突破 |
| 国产替代 | 国内厂商突破、替代进口、自主可控 |
| 政策 | 出口管制/制裁/补贴/产业政策 |
| 业绩 | 财报/指引/超预期/不及预期 |
| 并购 | 融资/并购/战略投资/IPO |
| 需求 | 云厂商CapEx指引、AI训练需求、订单可见度 |
| 供给 | 产能瓶颈/短缺/供给释放/库存变化 |
| 风险 | 供应链中断/地缘风险/客户集中度/技术路线风险 |

impact判断标准（仅relevant=true时填 大/中/小；relevant=false时填"无"）：
- "大"：可能引发板块级行情或改变产业链竞争格局。单笔融资/订单≥100亿美元，或国家级政策/出口管制，或颠覆性技术发布
- "中"：对特定环节/公司有实质性影响。融资/订单10~100亿美元，或龙头业绩超预期，或重要技术路线切换
- "小"：信息量有限。融资<10亿美元，或单一产品发布，或远期路线图，或主观观点
- 涉及头部公司时正常判断影响度；涉及非头部公司但与头部有供应链关系时，影响度上限为"中"

==== 示例（严谨参照）====

示例1 — 相关(大)：
标题：台积电宣布2nm工艺2026年Q1量产，产能已被苹果英伟达预订一空
相关：true | 影响：大 | 标签：["扩产","技术","供给"]
理由：先进制程突破+产能扩张

示例2 — 相关(大)：
标题：英伟达发布Rubin Ultra GPU，AI训练性能提升4倍
相关：true | 影响：大 | 标签：["技术","需求"]
理由：旗舰GPU换代，重新定义算力格局

示例3 — 相关(大)：
标题：美商务部新增对华AI芯片出口管制清单
相关：true | 影响：大 | 标签：["政策","国产替代","风险"]
理由：出口管制板块级冲击

示例4 — 相关(大)：
标题：字节跳动新设"算力基建部"直管AI算力采购
相关：true | 影响：大 | 标签：["需求","扩产"]
理由：字节算力战略转向，涉及GPU大规模采购

示例5 — 相关(大)：
标题：当台积电三星SK海力士都在抢货，电子级氢氟酸成为AI芯片制造不可替代的"化学钥匙"
相关：true | 影响：大 | 标签：["供给","涨价"]
理由：新材料替代+A股直接供应商

示例6 — 相关(中)：
标题：SK海力士清州工厂订购逾200台HBM4测试仪，总价4000亿韩元
相关：true | 影响：中 | 标签：["扩产","供给"]
理由：HBM4设备采购量级可观

示例7 — 相关(中)：
标题：中际旭创预计Q3营收同比增长180%，800G光模块出货超预期
相关：true | 影响：中 | 标签：["业绩","扩产"]
理由：光模块龙头业绩超预期

示例8 — 相关(小)：
标题：三星1.4nm工艺或将于2029年重启量产
相关：true | 影响：小 | 标签：["技术","扩产"]
理由：时间线太远(2029年)，无实质影响

示例9 — 不相关：
标题：Omdia：2026年Q1三星折叠面板份额降至27%
相关：false | 标签：[]
理由：折叠面板是消费电子

示例10 — 不相关：
标题：小米REDMI K90至尊版手机发布：骁龙8至尊版+主动散热风扇，首销到手价2799元起
相关：false | 标签：[]
理由：手机发布，消费电子

示例11 — 不相关：
标题：央视评寒武纪市值破万亿：更需一份清醒定力
相关：false | 标签：[]
理由：媒体评论喊话，无产业链信息

示例12 — 不相关：
标题：美光科技宣布投入2.5亿美元助力百万儿童储蓄
相关：false | 标签：[]
理由：慈善行为，非产业动态

示例13 — 不相关：
标题：深开鸿KaihongOS桌面版V5.0.2.30更新上线
相关：false | 标签：[]
理由：操作系统小版本更新

示例14 — 不相关：
标题：大疆无人机DJI Fly鸿蒙版App正式上架华为应用市场
相关：false | 标签：[]
理由：无人机App上架，与算力无关

示例15 — 不相关：
标题：银联推出AI智算卡：银行卡开始「外挂」大模型
相关：false | 标签：[]
理由：银行卡金融产品，与算力无关

示例16 — 不相关：
标题：AI能源使用的环境成本：碳足迹、水足迹与土地足迹
相关：false | 标签：[]
理由：科普文章，无具体公司或数据

示例17 — 不相关：
标题：华为官宣全球首个商用多模态文旅大模型规模化应用，衍生品销售200万元
相关：false | 标签：[]
理由：项目规模太小(营收仅200万)，可忽略

示例18 — 不相关：
标题：对比鲜明！美股创"六年来最佳一季"，黄金经历"十多年来最差一季"
相关：false | 标签：[]
理由：社会共识/公开已知信息，无增量投资价值

示例19 — 不相关：
标题：寒武纪万亿市值夜的"冷水"：上游涨价挤压利润
相关：false | 标签：[]
理由：公司自身风险提示公告，非实质变化

示例20 — 不相关：
标题：近一年收益220%，汇丰晋信陈平：AI算力中最看好光模块
相关：false | 标签：[]
理由：基金经理主观观点，无新增数据

示例21 — 相关(中)：
标题：MiniMax融资19亿美元加码算力
相关：true | 影响：中 | 标签：["并购","扩产","需求"]
理由：19亿美元在10~100亿区间，推动算力采购但非板块级

示例22 — 不相关（非头部公司）：
标题：某AI初创公司获得5000万元天使轮融资
相关：false | 标签：[]
理由：非头部公司，金额过小，无板块级影响

==== 待分类新闻列表 ====

输出格式（JSON数组，每条对应一条输入新闻）：
[
  {"idx":0,"relevant":true,"impact":"大","story_tags":["扩产","技术"],"reason":"简短理由≤15字"},
  {"idx":1,"relevant":false,"impact":"无","story_tags":[],"reason":"简短理由≤15字"},
  ...
]

输入新闻："""

def llm_classify_batch(candidates):
    if not candidates or not DEEPSEEK_KEY:
        return []

    CHUNK_SIZE = 50
    all_results = []
    total = len(candidates)

    for chunk_start in range(0, total, CHUNK_SIZE):
        chunk = candidates[chunk_start:chunk_start + CHUNK_SIZE]
        lines = []
        for i, item in enumerate(chunk):
            global_idx = chunk_start + i
            t = item["title"]
            s = item.get("summary", "")[:200]
            lines.append(f"idx={global_idx} | 标题：{t}\n摘要：{s}")

        user_msg = CLASSIFY_PROMPT + "\n\n---\n\n".join(lines)
        progress = f"{chunk_start + 1}-{min(chunk_start + len(chunk), total)}/{total}"
        print(f"  LLM批量分类 {progress}（{len(chunk)}条）...")

        chunk_ok = False
        retry_delays = [2, 4]
        for attempt in range(3):
            try:
                r = requests.post(DEEPSEEK_URL, json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [{"role": "user", "content": user_msg}],
                    "temperature": 0.2,
                    "max_tokens": 8192,
                }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=180)

                if r.status_code != 200:
                    if attempt < 2:
                        time.sleep(retry_delays[attempt])
                        continue
                    print(f"    ⚠️ HTTP {r.status_code}: {r.text[:100]}")
                    break

                content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                json_str = content.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                bracket = json_str.find("[")
                end = json_str.rfind("]")
                if bracket >= 0 and end > bracket:
                    json_str = json_str[bracket:end+1]

                results = json.loads(json_str)
                if isinstance(results, list):
                    rel = sum(1 for r in results if r.get("relevant"))
                    all_results.extend(results)
                    print(f"    ✅ 相关 {rel}/{len(results)}")
                    chunk_ok = True
                    break
                if attempt < 2:
                    time.sleep(retry_delays[attempt])
                    continue
                print(f"    ⚠️ 分类结果非数组")
                break
            except json.JSONDecodeError:
                if attempt < 2:
                    time.sleep(retry_delays[attempt])
                    continue
                print(f"    ⚠️ JSON解析失败")
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(retry_delays[attempt])
                    continue
                print(f"    ⚠️ 调用失败: {e}")
                break

        if not chunk_ok:
            for i in range(len(chunk)):
                all_results.append({"idx": chunk_start + i, "relevant": False, "impact": "无", "reason": "分类超时"})

    rel_count = sum(1 for r in all_results if r.get("relevant"))
    print(f"  分类完成：相关 {rel_count} 条 / 总计 {len(all_results)} 条")
    return all_results

ANALYZE_PROMPT = """你是一个顶级的AI算力/半导体产业链分析师，分析直接辅助基金经理做买卖决策。

仔细阅读新闻后，请按以下步骤思考，然后输出JSON：

第一步：提炼摘要
用一句简洁的话概括本条新闻的核心事实（50字左右）。要求：不要重复标题已表达的信息、不要写标题里已经有的话；语言通顺完整不要截断；结尾不要有多余符号，不要出现残缺的句子。

第二步：分析产业链影响
找出新闻中所有具体数字（金额、增长率、价格、估值等），结合这些数据判断对AI算力产业链的具体影响。解释清楚"为什么"和"怎么传导"的：例如某公司降价→上游供应商利润被压缩→设备采购延迟→中游订单减少。必须指名道姓列出1-3家直接相关的A股公司及原因。找不到A股标的就诚实说没找到。注意：语句完整通顺、不要有任何多余或错误的标点符号。

根据故事线标签采用对应的重点分析框架：
- 【扩产】必须说清：谁在扩、扩什么环节、多少金额/产能、预计何时投产、利好哪些A股设备/材料/配套公司、产能释放后对供需格局的影响
- 【涨价】必须说清：谁涨价、涨幅多少、供需紧张原因、传导路径（上游→中游→下游）、谁受益谁受损
- 【降价】必须说清：谁降价、降幅多少、价格战原因、对毛利率的影响、谁受损最严重
- 【技术】必须说清：技术参数对比（vs上代/vs竞品）、替代了什么、技术路线切换影响、A股标的
- 【国产替代】必须说清：替代了哪家海外厂商、国产化率变化、技术差距、A股标的
- 【政策】必须说清：政策具体内容、影响哪些公司、影响程度、反制措施
- 【业绩】必须说清：核心财务数据、同比/环比变化、超预期/不及预期点、对产业链的指引意义
- 【并购】必须说清：交易金额、估值、战略意图、对竞争格局的影响
- 【需求】必须说清：需求来源（哪家云厂商/模型公司）、需求规模、可持续性、利好环节
- 【供给】必须说清：供给瓶颈/释放的具体环节、供需缺口、价格影响
- 【风险】必须说清：风险具体描述、影响范围、可能性、应对策略

头部公司聚焦原则：
- 优先分析新闻中涉及的头部公司，小公司只在作为"头部公司供应链角色"时才提及
- A股标的推荐时，优先推荐头部清单内的A股公司
- 如果新闻涉及的A股公司不在头部清单内，诚实说"该公司非头部，需观察"

第三步：大白话结论
用像真人聊天的大白话直接说出结论，让普通投资者一听就懂"这事儿跟我有什么关系"。不要加任何开场标签或总结词。

影响力度判断标准：
- "大"=可能引发板块级行情或改变产业链竞争格局。单笔融资/订单≥100亿美元，或国家级政策/出口管制，或颠覆性技术发布
- "中"=对特定环节/公司有实质性影响。融资/订单10~100亿美元，或龙头业绩超预期，或重要技术路线切换
- "小"=信息量有限。融资<10亿美元，或单一产品发布，或远期路线图，或主观观点

关键原则（必须遵守）：
1. 社会共识/公开已知信息 → "小"或直接排除
2. 基金经理/分析师主观观点（无新增数据） → "小"
3. 机构警告/喊话（无具体数据支撑） → "小"
4. 公司自身风险提示/常规公告 → "小"
5. 新材料替代且有A股直接供应关系 → "大"或"中"
6. 已发生在海外的行情（非A股） → "小"
7. 单笔融资/订单在10~100亿美元区间 → "中"而非"大"，如MiniMax 19亿美元、Positron 7.5亿美元均判"中"

严格按以下JSON格式输出，不要在JSON外添加任何其他文字：
{
  "impact": "大",
  "digest": "简洁摘要（50字左右，不重复标题，语句完整）",
  "analysis": "产业链影响分析（150-250字，含具体数据和A股标的，标点正确）",
  "conclusion": "大白话结论（30-60字，无总结词）"
}

新闻内容："""


def enrich_short_summary(title, raw_summary, url):
    """若原始摘要<300字，尝试从文章URL获取完整内容补充"""
    if not raw_summary or len(raw_summary) >= 300:
        return raw_summary
    if not url:
        return raw_summary
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code != 200:
            return raw_summary
        text = re.sub(r'<[^>]+>', ' ', resp.text)
        text = re.sub(r'\s+', ' ', text).strip()
        enriched = text[:3000] if len(text) > len(raw_summary) else raw_summary
        if len(enriched) > len(raw_summary):
            print(f"  原始摘要过短({len(raw_summary)}字)，已从URL补充至{len(enriched)}字")
            return enriched
        return raw_summary
    except Exception:
        return raw_summary


def deepseek_analyze_one(item, index):
    title = item.get("title", "")
    raw = item.get("_raw_summary", item.get("summary", ""))
    url = item.get("url", "")
    raw = enrich_short_summary(title, raw, url)
    summary = raw[:1000]

    story_tags = item.get("story_tags", [])
    tags_str = "、".join(story_tags) if story_tags else "无"
    user_msg = ANALYZE_PROMPT + f"标题：{title}\n故事线标签：{tags_str}\n内容：{summary}"

    retry_delays = [2, 4]
    for attempt in range(3):
        try:
            r = requests.post(DEEPSEEK_URL, json={
                "model": DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": user_msg}],
                "temperature": 0.5,
                "max_tokens": 2048,
            }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=120)

            if r.status_code != 200:
                print(f"  #{index} 返回{r.status_code}: {r.text[:100]}")
                if attempt < len(retry_delays):
                    time.sleep(retry_delays[attempt])
                    continue
                return None

            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")

            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            result = json.loads(json_str)
            return result

        except json.JSONDecodeError:
            if attempt < len(retry_delays):
                time.sleep(retry_delays[attempt])
                continue
            print(f"  #{index} JSON解析失败，跳过")
            return None
        except Exception as e:
            if attempt < len(retry_delays):
                time.sleep(retry_delays[attempt])
                continue
            print(f"  #{index} 调用失败: {e}")
            return None

    return None


def apply_ai_analysis(news_items):
    if not DEEPSEEK_KEY:
        print("  ⚠️ 未配置DEEPSEEK_KEY，跳过AI分析")
        return

    total = len(news_items)
    print(f"  逐条AI分析中（共{total}条，每条约需3-5秒）...")

    ok = 0
    failed_items = []
    for i, item in enumerate(news_items):
        result = deepseek_analyze_one(item, i + 1)
        if result is None:
            print(f"  [{i+1}/{total}] ❌ 失败")
            failed_items.append(item)
            continue

        impact = result.get("impact", "中")
        digest = result.get("digest", "")
        analysis = result.get("analysis", "")
        conclusion = result.get("conclusion", "")

        parts = []
        if digest:
            parts.append(digest.rstrip("。"))
        parts.append(f"【影响程度】{impact}")

        if analysis:
            parts.append(f"【产业链影响】{analysis.rstrip('。')}")

        if conclusion:
            parts.append(f"【大白话结论】{conclusion}")

        raw = "。".join(parts)
        raw = raw.replace("。。", "。")
        item["summary"] = raw
        item["impact"] = impact
        ok += 1

        print(f"  [{i+1}/{total}] ✓ {impact} {item['title'][:30]}...")
        time.sleep(0.5)

    # ============ 硬编码保障：每条新闻必须包含【产业链影响】和【大白话结论】 ============
    fixed = 0

    def pick_marker(tag, txt):
        m = re.search(tag + r'[^【]*', txt)
        return m.group(0).strip() if m else ""

    def strip_markers(txt):
        return re.sub(r'【[^】]*】[^【]*', '', txt).strip().rstrip("。")

    for item in news_items:
        s = item.get("summary", "")
        raw = item.get("_raw_summary", "")
        title = item.get("title", "")
        impact = item.get("impact", "中")

        if "【产业链影响】" in s and "【大白话结论】" in s:
            continue

        fixed += 1
        # DeepSeek成功时 s 带标记，失败时 s == raw（无标记）
        is_deepseek_fail = "【影响程度】" not in s
        raw_clean = re.sub(r'【[^】]*】', '', raw).strip().rstrip("。")
        s_clean = strip_markers(s).rstrip("。")

        # 取原文中最有信息量的关键句（非重复段落）
        def first_key_sentence(txt, min_len=30):
            txt = txt.strip()
            for sep in ["。", "；", "！", "？", "\n"]:
                parts = [p.strip() for p in txt.split(sep) if len(p.strip()) > min_len]
                if parts:
                    return parts[0] + ("。" if sep == "。" else sep)
            return txt[:min_len] + "……"

        if is_deepseek_fail:
            # DeepSeek完全失败：raw是唯一信息源，拆分使用避免重复
            key_sentence = first_key_sentence(raw_clean)
            item["summary"] = f"{key_sentence}【影响程度】{impact}。【产业链影响】{title}。{raw_clean}。【大白话结论】{key_sentence}"
        else:
            # DeepSeek部分成功：有标记但不全
            base = s_clean if s_clean else raw_clean
            final_parts = [base] if base else []
            final_parts.append(pick_marker("【影响程度】", s) or f"【影响程度】{impact}")

            if not pick_marker("【产业链影响】", s):
                ctx = raw_clean[:300]
                final_parts.append(f"【产业链影响】{title}。{ctx}")

            if not pick_marker("【大白话结论】", s):
                raw_short = raw_clean[:150]
                final_parts.append(f"【大白话结论】{raw_short}")

            item["summary"] = "。".join(final_parts).replace("。。", "。")

    if fixed:
        print(f"  ⚠️ 硬编码补全: 补了 {fixed} 条的缺失模块")

    for item in failed_items:
        item["_deepseek_fully_failed"] = True

    print(f"  ✓ AI分析完成: {ok}/{total}条（{fixed}条补全）")


def quick_ai_summary(title, summary):
    clean = re.sub(r'<[^>]+>', '', summary)[:500]
    clean = re.sub(r'IT之家.*?日消息', '', clean)
    clean = re.sub(r'#欢迎关注爱范儿.*$', '', clean)
    clean = re.sub(r'#欢迎关注.*$', '', clean)
    clean = re.sub(r'\n+', '', clean)
    clean = clean.replace("\t", " ").strip()
    if len(clean) > 400:
        clean = clean[:397] + "..."
    return clean

def load_recent_seen(days=7):
    """从 OSS 拉取最近 days 天的数据文件，建立已采集的 URL 和标题集合（用于跨日去重）
    注意：排除今天，避免重新生成时把自己也去重"""
    today_str = date.today().strftime("%Y-%m-%d")
    seen_urls = set()
    seen_titles = set()
    base = "https://portfolio-analysis.top/news/data"
    try:
        r = requests.get(f"{base}/index.json", timeout=10)
        if r.status_code != 200:
            return seen_urls, seen_titles
        all_dates = r.json().get("dates", [])
    except Exception:
        return seen_urls, seen_titles

    # 只取最近 days 天，但排除今天（避免重新生成时把自己去重）
    recent = [d for d in sorted(all_dates, reverse=True) if d != today_str][:days]
    for ds in recent:
        try:
            r = requests.get(f"{base}/{ds}.json", timeout=10)
            if r.status_code != 200:
                continue
            news = r.json().get("news", [])
            for n in news:
                u = (n.get("url") or "").strip()
                t = (n.get("title") or "").strip().lower()
                if u:
                    seen_urls.add(u)
                if t:
                    seen_titles.add(t)
        except Exception:
            continue
    print(f"  跨日去重: 加载最近 {len(recent)} 天数据，已有 {len(seen_urls)} 个URL、{len(seen_titles)} 个标题")
    return seen_urls, seen_titles


def is_dup_cross_day(item, seen_urls, seen_titles):
    """URL 完全匹配 或 标题完全匹配 → 判定为跨日重复"""
    u = (item.get("url") or "").strip()
    t = (item.get("title") or "").strip().lower()
    if u and u in seen_urls:
        return True
    if t and t in seen_titles:
        return True
    return False


def update_website_index():
    idx_path = os.path.join(DATA_DIR, "index.json")
    dates = set()
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".json") and fname not in ("index.json", "breakthrough.json"):
            dates.add(fname.replace(".json", ""))
    try:
        r = requests.get("https://portfolio-analysis.top/news/data/index.json", timeout=10)
        if r.status_code == 200:
            remote = r.json().get("dates", [])
            dates.update(remote)
    except Exception:
        pass
    sorted_dates = sorted(dates)
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump({"dates": sorted_dates, "count": len(sorted_dates)}, f, ensure_ascii=False, indent=2)
    for ds in sorted_dates:
        fpath = os.path.join(DATA_DIR, f"{ds}.json")
        if not os.path.exists(fpath):
            try:
                r = requests.get(f"https://portfolio-analysis.top/news/data/{ds}.json", timeout=10)
                if r.status_code == 200:
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(r.json(), f, ensure_ascii=False, indent=2)
                    print(f"  ✅ 已从 OSS 补回缺失的数据: {ds}.json")
            except Exception:
                pass

TITLE_REWRITE_PROMPT = """你是一个中文新闻标题编辑。将以下新闻标题处理成适合AI算力产业链投资者阅读的中文标题。

规则：
1. 纯英文标题 → 翻译为简洁中文
2. 标题中若包含多个子事件（用分隔符隔开） → 只保留与AI算力/半导体/芯片直接相关的事件
3. 处理后的标题长度不超过40个中文字符
4. 保持客观，不加主观评价

注意：早报/早餐/8点1氪等汇总类标题已在本地预处理提取了核心事件，不需要再处理。

输出格式（JSON数组，与输入一一对应）：
[
  {"idx":0,"title":"处理后标题"},
  {"idx":1,"title":"处理后标题"},
  ...
]

输入新闻："""

def extract_first_event_from_summary(item):
    summary = item.get("summary", "")
    text = re.sub(r'<[^>]+>', '', summary).strip()
    if not text or len(text) < 10:
        return ""
    parts = re.split(r'[；;｜|]\s*(?=\d+[\.\、\s]+)', text[:800], maxsplit=5)
    for part in parts:
        part = re.sub(r'^\d+[\.\、\s]+', '', part).strip()
        if len(part) >= 10:
            return part[:60]
    return text[:60]

def rewrite_titles(news_list):
    if not news_list or not DEEPSEEK_KEY:
        return

    # 阶段0：本地预处理壳标题（早报/早餐/8点1氪等汇总类）
    SHELL_KWS = ["IT早报", "早报", "早餐", "FM-Radio", "FM |", "晚报", "日报", "Edge AI Daily", "8点1氪"]
    for i, item in enumerate(news_list):
        t = item["title"]
        if any(kw in t for kw in SHELL_KWS):
            chinese_chars = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
            if chinese_chars < 15:
                extracted = extract_first_event_from_summary(item)
                if extracted:
                    old = item["title"]
                    news_list[i]["title"] = extracted
                    print(f"    本地提取: {old[:25]} → {extracted}")
                else:
                    news_list[i]["_is_empty_shell"] = True
                    print(f"    🗑️ 空壳标题丢弃: {t[:40]}")

    # 收集需要DeepSeek改写的标题（英文标题）
    need_rewrite_idx = [i for i, item in enumerate(news_list)
        if not item.get("_is_empty_shell") and re.search(r'[A-Za-z]{3,}', item["title"])
        and sum(1 for c in item["title"][:100] if c.isascii() and c.isalpha()) / max(len(item["title"][:100]), 1) > 0.15]

    if not need_rewrite_idx:
        return

    CHUNK_SIZE = 15
    total = len(need_rewrite_idx)
    rewritten = 0
    failed = 0

    for chunk_start in range(0, total, CHUNK_SIZE):
        chunk_indices = need_rewrite_idx[chunk_start:chunk_start + CHUNK_SIZE]
        lines = []
        for local_idx, orig_idx in enumerate(chunk_indices):
            lines.append(f"idx={local_idx} | 原始标题：{news_list[orig_idx]['title']}")
        user_msg = TITLE_REWRITE_PROMPT + "\n\n---\n\n".join(lines)
        progress = f"{chunk_start + 1}-{min(chunk_start + len(chunk_indices), total)}/{total}"

        chunk_ok = False
        for attempt in range(3):
            try:
                r = requests.post(DEEPSEEK_URL, json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [{"role": "user", "content": user_msg}],
                    "temperature": 0.2,
                    "max_tokens": 4096,
                }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"}, timeout=120)

                if r.status_code != 200:
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    break

                content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                json_str = content.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                bracket = json_str.find("[")
                end = json_str.rfind("]")
                if bracket >= 0 and end > bracket:
                    json_str = json_str[bracket:end+1]

                results = json.loads(json_str)
                if isinstance(results, list):
                    for result in results:
                        local_idx = result.get("idx", -1)
                        new_title = result.get("title", "")
                        if 0 <= local_idx < len(chunk_indices) and new_title:
                            orig_idx = chunk_indices[local_idx]
                            old_title = news_list[orig_idx]["title"]
                            if old_title != new_title:
                                news_list[orig_idx]["title"] = new_title
                                rewritten += 1
                    chunk_ok = True
                    print(f"    改写 {progress} ✅ {len(chunk_indices)}条")
                    break
                if attempt < 2:
                    time.sleep(2)
                    continue
                break
            except Exception:
                if attempt < 2:
                    time.sleep(2)
                    continue
                break

        if not chunk_ok:
            failed += len(chunk_indices)
            print(f"    改写 {progress} ⚠️ 失败")

    if rewritten > 0 or failed > 0:
        print(f"  改写完成: {rewritten} 条成功" + (f", {failed} 条失败" if failed else ""))

def main():
    today_str = date.today().strftime("%Y-%m-%d")
    print("=" * 50)
    print(f"[AI算力每日资讯] {today_str}")
    print("=" * 50)

    # 幂等检查：FORCE_REFRESH=1 时强制重新生成，跳过所有幂等检查
    if os.environ.get("FORCE_REFRESH") != "1":
        today_url = f"https://portfolio-analysis.top/news/data/{today_str}.json"
        try:
            resp = requests.get(today_url, timeout=10, verify=False)
            if resp.status_code == 200:
                d = resp.json()
                if d.get("count", 0) > 0:
                    print(f"✅ OSS 已有今日数据({d['count']}条)，跳过重复生成")
                    return d["count"]
        except Exception:
            pass  # OSS 无数据，正常生成

        # 再尝试本地文件
        today_file = os.path.join(DATA_DIR, f"{today_str}.json")
        if os.path.exists(today_file):
            try:
                with open(today_file, encoding="utf-8") as f:
                    d = json.load(f)
                if d.get("count", 0) > 0:
                    print(f"✅ 今日数据已存在({d['count']}条)，跳过重复生成")
                    print(f"   如需强制重新生成，设置环境变量 FORCE_REFRESH=1")
                    return d["count"]
            except Exception:
                pass  # 文件损坏，重新生成

    print("\n[1/5] RSS采集...")
    all_raw = []
    for label, url in RSS_SOURCES:
        entries = fetch_rss(url, label)
        all_raw.extend(entries)
        print(f"  {label}: {len(entries)}条")
    print(f"  原始采集: {len(all_raw)}条")

    print("\n[2/5] 去重...")
    seen_urls, seen_titles = load_recent_seen(days=7)
    cross_day_dup = 0

    seen = set()
    deduped = []
    for e in all_raw:
        t = e["title"]
        s = e.get("summary", "")
        raw = quick_ai_summary(t, s)
        e["_raw"] = raw
        key = e["title"][:60].strip().lower()
        if key and key not in seen:
            seen.add(key)
            if is_dup_cross_day(e, seen_urls, seen_titles):
                cross_day_dup += 1
                continue
            deduped.append(e)
    print(f"  跨日重复剔除: {cross_day_dup} 条")
    print(f"  去重后候选: {len(deduped)} 条")

    print("\n[3/5] LLM批量分类（判断相关性+影响度）...")
    classifications = llm_classify_batch(deduped)

    news_list = []
    dropped = []
    for cl in classifications:
        idx = cl.get("idx", -1)
        if idx < 0 or idx >= len(deduped):
            continue
        if not cl.get("relevant", False):
            reason = cl.get("reason", "")
            dropped.append(f"{deduped[idx]['title'][:30]}... ({reason})")
            continue
        item = deduped[idx]
        news_list.append({
            "id": len(news_list),
            "title": item["title"],
            "summary": item["_raw"],
            "_raw_summary": item["_raw"],
            "mainline": get_mainline(item["title"]),
            "impact": cl.get("impact", "中"),
            "story_tags": cl.get("story_tags", []),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "time": ""
        })

    if dropped:
        print(f"  LLM过滤不相关: {len(dropped)} 条")
        for t in dropped[:10]:
            print(f"    ✂️ {t}")
        if len(dropped) > 10:
            print(f"    ... 还有 {len(dropped)-10} 条")
    print(f"  LLM判定相关: {len(news_list)} 条")

    # 兜底：相关过少时从高分源补充
    if len(news_list) < 8 and len(classifications) > 0:
        print(f"  ⚠️ 相关不足8条，从高分源补充...")
        for cl in classifications:
            idx = cl.get("idx", -1)
            if idx < 0 or idx >= len(deduped):
                continue
            if cl.get("relevant", False):
                continue
            item = deduped[idx]
            if item.get("source") in ["华尔街见闻", "ServeTheHome", "Tom\'s Hardware"]:
                news_list.append({
                    "id": len(news_list),
                    "title": item["title"],
                    "summary": item["_raw"],
                    "_raw_summary": item["_raw"],
                    "mainline": get_mainline(item["title"]),
                    "impact": "小",
                    "story_tags": [],
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "time": ""
                })
                if len(news_list) >= 8:
                    break
        print(f"  补充后: {len(news_list)} 条")

    print("\n[4/5] 逐条深度分析...")

    if not news_list:
        print("  ⚠️ 无相关新闻，跳过")
        return 0

    apply_ai_analysis(news_list)

    # 移除DeepSeek分析完全失败的条目
    before = len(news_list)
    news_list = [n for n in news_list if not n.get("_deepseek_fully_failed", False)]
    if len(news_list) < before:
        print(f"  🗑️ 移除 {before - len(news_list)} 条分析失败项")

    # 改写标题：早报壳标题本地提取 + 英文标题DeepSeek翻译
    rewrite_titles(news_list)

    # 移除空壳标题条目（早报/早餐类无内容）
    before = len(news_list)
    news_list = [n for n in news_list if not n.get("_is_empty_shell", False)]
    if len(news_list) < before:
        print(f"  🗑️ 移除 {before - len(news_list)} 条空壳标题")

    daily_summary = gen_daily_summary(news_list)

    print("\n[5/5] 写入数据...")
    data = {
        "date": today_str,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "count": len(news_list),
        "news": news_list,
        "daily_summary": daily_summary
    }
    with open(os.path.join(DATA_DIR, f"{today_str}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    update_website_index()

    print(f"\n✅ 完成! 共 {len(news_list)} 条")
    print(f"   主线: A={sum(1 for n in news_list if 'A' in n['mainline'])}, B={sum(1 for n in news_list if 'B' in n['mainline'])}, C={sum(1 for n in news_list if 'C' in n['mainline'])}, D={sum(1 for n in news_list if 'D' in n['mainline'])}")
    print(f"   文件: {os.path.join(DATA_DIR, f'{today_str}.json')}")

    return len(news_list)

if __name__ == "__main__":
    main()
